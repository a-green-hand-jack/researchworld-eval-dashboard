"""Starter candidate: influence-guided data removal for Bradley-Terry leaderboards.

The evaluator calls ``handle(request) -> response`` once per operation with finite JSON values.
One episode is: ``reset`` -> ``load_chunk`` x n_chunks -> ``analyze``. Every request is a dict with
an ``op`` key; every response is a dict. All state lives in this process's memory. The evaluator
and this process share no filesystem; never rely on paths.

Operations
----------
{"op": "reset", "seed": int}
    Clear ALL state (table, caches, RNG) and seed the RNG. The seed only initializes randomness
    (tie-breaking, restarts); it never identifies the dataset or the workload.
    Response: exactly {"ok": true}.

{"op": "load_chunk", "chunk_index": int, "n_chunks": int, "n_rows_total": int, "n_models": int,
 "a": ARR, "b": ARR, "y": ARR}
    One slice of the comparison table (chunks arrive in order 0..n_chunks-1; at most 65536 rows per
    chunk; at most 4 chunks). Row j of the concatenated table is "model a[j] vs model b[j]" with
    outcome y[j]: 0 = A wins, 1 = B wins, 2 = tie. Model indices are anonymized integers in
    [0, n_models); rows and model ids are shuffled per episode, so no name, dataset or time order is
    available. ARR = {"dtype": "uint16" | "uint8", "shape": [n], "encoding": "base64-le",
    "data": <base64 of little-endian bytes>}  (a, b: uint16; y: uint8).
    Response: exactly {"ok": true}.

{"op": "analyze", "hi": int, "lo": int, "k_cap": int, "tie_as_half_win": true, "ridge": float,
 "deadline_seconds": float}
    Rating definition used by the evaluator (it is the only judge): Bradley-Terry logistic MLE
    P(a beats b) = sigmoid(theta_a - theta_b), a tie counts as half a win for each side (when
    tie_as_half_win), objective  sum_rows [log(1+exp(d)) - s*d] + ridge/2 * |theta|^2 with
    d = theta_a - theta_b and s in {1, 0, 0.5}; models are ranked by theta, descending.
    Model ``hi`` is currently ranked directly above model ``lo``. Propose a set of at most
    ``k_cap`` rows (global row indices into the concatenated table, unique) whose removal makes the
    evaluator's exact refit rank ``lo`` strictly above ``hi``. Smaller sets score higher
    (score = 1 - k / k_cap when the refit flips, else 0). Answer within ``deadline_seconds``.
    Response: {"removed": {"dtype": "uint32", "shape": [k], "encoding": "base64-le",
    "data": <base64 of little-endian uint32 row indices>},
    "diagnostics": {<name>: <finite number>, ...}}   # "diagnostics" is optional (<= 32 numbers),
    ignored for scoring. No other keys are allowed; any malformed, over-cap, duplicate or
    out-of-range proposal scores 0 for the episode.
"""
import base64
import itertools
import math
import time

import numpy as np

_STATE = {}


def _fresh(seed):
    return {"seed": int(seed), "rng": np.random.default_rng(int(seed)), "chunks": [], "n_chunks": None,
            "n_rows": None, "n_models": None}


def _decode(arr, dtype, n_expected=None):
    if (type(arr) is not dict or arr.get("encoding") != "base64-le" or arr.get("dtype") != np.dtype(dtype).name):
        raise ValueError("bad array")
    out = np.frombuffer(base64.b64decode(arr["data"]), dtype=np.dtype(dtype).newbyteorder("<"))
    if list(arr["shape"]) != [len(out)] or (n_expected is not None and len(out) != n_expected):
        raise ValueError("bad shape")
    return out


def _encode_u32(idx):
    idx = np.asarray(idx, dtype="<u4")
    return {"dtype": "uint32", "shape": [int(len(idx))], "encoding": "base64-le",
            "data": base64.b64encode(idx.tobytes()).decode("ascii")}


def _scores(y):
    return np.where(y == 0, 1.0, np.where(y == 1, 0.0, 0.5))


def _fit(a, b, s, m, ridge, theta0=None, tol=1e-9, max_iter=60):
    th = np.zeros(m) if theta0 is None else theta0.copy()
    ab = a * m + b

    def obj(t):
        d = t[a] - t[b]
        return float(np.sum(np.logaddexp(0.0, d) - s * d) + 0.5 * ridge * float(t @ t))

    f = obj(th)
    for _ in range(max_iter):
        p = 1.0 / (1.0 + np.exp(-(th[a] - th[b])))
        r = p - s
        g = np.bincount(a, r, m) - np.bincount(b, r, m) + ridge * th
        if np.max(np.abs(g)) < tol:
            break
        w = p * (1.0 - p)
        h = np.bincount(ab, w, m * m).reshape(m, m)
        h = -(h + h.T)
        h[np.diag_indices(m)] += np.bincount(a, w, m) + np.bincount(b, w, m) + ridge
        step = np.linalg.solve(h, g)
        t = 1.0
        while True:
            fn = obj(th - t * step)
            if fn <= f + 1e-12 * abs(f) or t < 1e-6:
                break
            t *= 0.5
        th = th - t * step
        f = fn
    return th


def _influence(a, b, s, theta, hi, lo, m, ridge):
    """First-order change of theta[hi]-theta[lo] when each row is removed (negative closes the gap)."""
    p = 1.0 / (1.0 + np.exp(-(theta[a] - theta[b])))
    w = p * (1.0 - p)
    h = np.bincount(a * m + b, w, m * m).reshape(m, m)
    h = -(h + h.T)
    h[np.diag_indices(m)] += np.bincount(a, w, m) + np.bincount(b, w, m) + ridge
    e = np.zeros(m)
    e[hi], e[lo] = 1.0, -1.0
    v = np.linalg.solve(h, e)
    return -(s - p) * (v[a] - v[b])


def _analyze_rowlevel(req, st):
    """Cycle-1 row-level pipeline (influence ranking + re-linearisation + prefix bisection); safety candidate."""
    a = np.concatenate([c[0] for c in st["chunks"]]).astype(np.int64)
    b = np.concatenate([c[1] for c in st["chunks"]]).astype(np.int64)
    y = np.concatenate([c[2] for c in st["chunks"]])
    n, m = len(y), int(st["n_models"])
    ridge = float(req["ridge"])
    s = _scores(y) if req.get("tie_as_half_win", True) else np.where(y == 0, 1.0, 0.0)
    hi, lo, cap = int(req["hi"]), int(req["lo"]), int(req["k_cap"])
    stop_at = time.monotonic() + 0.7 * float(req["deadline_seconds"])
    refits = 0
    theta0 = _fit(a, b, s, m, ridge)

    def flips(removed):
        nonlocal refits
        refits += 1
        keep = np.ones(n, bool)
        keep[removed] = False
        th = _fit(a[keep], b[keep], s[keep], m, ridge, theta0)
        return th[hi] < th[lo]

    def min_prefix(order):
        top = min(cap, len(order))
        if top < 1 or time.monotonic() > stop_at or not flips(order[:top]):
            return None
        lo_k, hi_k = 0, top
        while hi_k - lo_k > 1 and time.monotonic() < stop_at:
            mid = (lo_k + hi_k) // 2
            if flips(order[:mid]):
                hi_k = mid
            else:
                lo_k = mid
        return order[:hi_k]

    # Strategy A: one-shot first-order influence ranking, refit-verified prefix bisection.
    order = np.argsort(_influence(a, b, s, theta0, hi, lo, m, ridge), kind="stable")[:cap]
    best = min_prefix(order)
    # Strategy B: batched re-linearization (recompute influence at the refit after every batch).
    if best is None:
        keep = np.ones(n, bool)
        theta = theta0
        removed = []
        batch = max(1, int(math.ceil(cap / 16)))
        while len(removed) < cap and time.monotonic() < stop_at:
            rows = np.flatnonzero(keep)
            g = _influence(a[rows], b[rows], s[rows], theta, hi, lo, m, ridge)
            take = rows[np.argsort(g, kind="stable")[:min(batch, cap - len(removed))]]
            keep[take] = False
            removed.extend(int(i) for i in take)
            theta = _fit(a[keep], b[keep], s[keep], m, ridge, theta)
            refits += 1
            if theta[hi] < theta[lo]:
                break
        best = min_prefix(np.asarray(removed, dtype=np.int64)) if removed else None
    chosen = np.zeros(0, dtype=np.int64) if best is None else np.asarray(best, dtype=np.int64)
    return {"removed": _encode_u32(chosen), "diagnostics": {"refits": float(refits), "k": float(len(chosen))}}


# ---------------------------------------------------------------------------------------------------
# Cycle 2: cell-aggregated search. A BT fit depends on the rows only through per-(oriented model pair,
# outcome) cell counts, so removing r_c rows of cell c is interchangeable with removing any r_c rows of it.
# ---------------------------------------------------------------------------------------------------
SAFETY = 1e-6   # required refit margin theta[lo]-theta[hi] for a preferred (robust) candidate


class _Ctx:
    pass


def _hess(ca, cb, ab, wq, m, ridge):
    h = np.bincount(ab, wq, m * m).reshape(m, m)
    h = -(h + h.T)
    h[np.diag_indices(m)] += np.bincount(ca, wq, m) + np.bincount(cb, wq, m) + ridge
    return h


def aggregate_cells(a, b, s, m):
    """Collapse rows to cells (oriented pair a<b, outcome o=2*s in {0,1,2}); rows with a==b are ignored.

    Returns dict with cell arrays (ca, cb, cs, cnt), ``order`` (valid row indices sorted by cell id),
    ``starts`` (first position of each cell in ``order``) and ``row_cell`` (cell of each row, -1 if none).
    Removing r units from cell c maps to rows order[starts[c]:starts[c]+r] (distinct, unique).
    """
    n = len(a)
    valid = np.flatnonzero(a != b)
    av, bv, sv = a[valid], b[valid], s[valid]
    sw = av > bv
    ao = np.where(sw, bv, av)
    bo = np.where(sw, av, bv)
    so = np.where(sw, 1.0 - sv, sv)          # swapping the orientation maps score s -> 1 - s
    o = np.rint(2.0 * so).astype(np.int64)
    cell_id = (ao * m + bo) * 3 + o
    uniq, inv, counts = np.unique(cell_id, return_inverse=True, return_counts=True)
    order = valid[np.argsort(cell_id, kind="stable")]
    starts = np.concatenate((np.zeros(1, dtype=np.int64), np.cumsum(counts)[:-1])).astype(np.int64)
    row_cell = np.full(n, -1, dtype=np.int64)
    row_cell[valid] = np.asarray(inv).reshape(-1)
    pair = uniq // 3
    return {"ca": (pair // m).astype(np.int64), "cb": (pair % m).astype(np.int64),
            "cs": (uniq % 3) / 2.0, "cnt": counts.astype(np.float64), "order": order, "starts": starts,
            "row_cell": row_cell}


def fit_weighted_bt(ca, cb, cs, w, m, ridge, theta0=None, tol=1e-10, max_iter=50):
    """Damped-Newton ridge BT fit on cell data: sum_c w_c [log(1+exp(d_c)) - s_c d_c] + ridge/2 |theta|^2."""
    th = np.zeros(m) if theta0 is None else np.array(theta0, dtype=np.float64)
    ab = ca * m + cb

    def obj(t):
        d = t[ca] - t[cb]
        return float(np.sum(w * (np.logaddexp(0.0, d) - cs * d)) + 0.5 * ridge * float(t @ t))

    f = obj(th)
    for _ in range(max_iter):
        p = 1.0 / (1.0 + np.exp(-(th[ca] - th[cb])))
        r = w * (p - cs)
        g = np.bincount(ca, r, m) - np.bincount(cb, r, m) + ridge * th
        if np.max(np.abs(g)) < tol:
            break
        step = np.linalg.solve(_hess(ca, cb, ab, w * p * (1.0 - p), m, ridge), g)
        t = 1.0
        while True:
            fn = obj(th - t * step)
            if fn <= f + 1e-12 * abs(f) or t < 1e-6:
                break
            t *= 0.5
        th = th - t * step
        f = fn
        if t * float(np.max(np.abs(step))) < 1e-14:
            break
    return th


def _cell_margin(ctx, rem, theta0, tol=1e-10):
    """Exact (cell-level) refit after removing ``rem`` units per cell; margin = theta[lo]-theta[hi] > 0 means flip."""
    ctx.nfit += 1
    w = np.maximum(ctx.cnt - rem, 0.0)
    th = fit_weighted_bt(ctx.ca, ctx.cb, ctx.cs, w, ctx.m, ctx.ridge, theta0, tol=tol, max_iter=40)
    return float(th[ctx.lo] - th[ctx.hi]), th


def _cell_state(ctx, rem, theta):
    """Implicit gradient g_c = d(theta_hi - theta_lo)/d(removal of c) = (p_c - s_c)(v[a]-v[b]), v = H^-1 (e_hi - e_lo)."""
    w = np.maximum(ctx.cnt - rem, 0.0)
    p = 1.0 / (1.0 + np.exp(-(theta[ctx.ca] - theta[ctx.cb])))
    q = p * (1.0 - p)
    h = _hess(ctx.ca, ctx.cb, ctx.ab, w * q, ctx.m, ctx.ridge)
    e = np.zeros(ctx.m)
    e[ctx.hi], e[ctx.lo] = 1.0, -1.0
    v = np.linalg.solve(h, e)
    z = v[ctx.ca] - v[ctx.cb]
    return (p - ctx.cs) * z, p, q, z, h


def verify_by_refit(ctx, removed):
    """Exact row-level refit after removing ``removed`` rows; returns margin theta[lo]-theta[hi] (> 0 flips)."""
    keep = np.ones(ctx.n, bool)
    keep[np.asarray(removed, dtype=np.int64)] = False
    ctx.refits += 1
    th = _fit(ctx.a[keep], ctx.b[keep], ctx.s[keep], ctx.m, ctx.ridge, ctx.theta0, tol=1e-10, max_iter=60)
    return float(th[ctx.lo] - th[ctx.hi])


def _register(ctx, cands, rows):
    rows = np.unique(np.asarray(rows, dtype=np.int64))
    if len(rows) == 0 or len(rows) > ctx.cap or int(rows.max()) >= ctx.n or int(rows.min()) < 0:
        return None
    mg = verify_by_refit(ctx, rows)
    cands.append((int(len(rows)), mg, rows))
    return mg


def _cells_to_rows(ctx, rem):
    parts = []
    for c in np.flatnonzero(rem > 0):
        st0 = int(ctx.starts[c])
        parts.append(ctx.order[st0:st0 + int(rem[c])])
    return np.concatenate(parts) if parts else np.zeros(0, dtype=np.int64)


def _rows_to_cells(ctx, rows):
    cid = ctx.row_cell[np.asarray(rows, dtype=np.int64)]
    cid = cid[cid >= 0]
    return np.bincount(cid, minlength=len(ctx.cnt)).astype(np.float64)


def _project(x, cap_, k):
    """Euclidean projection onto {0 <= r <= cap_, sum r <= k}."""
    r0 = np.clip(x, 0.0, cap_)
    if r0.sum() <= k:
        return r0
    lo_t, hi_t = float(np.min(x - cap_)), float(np.max(x))
    for _ in range(80):
        mid = 0.5 * (lo_t + hi_t)
        if np.clip(x - mid, 0.0, cap_).sum() > k:
            lo_t = mid
        else:
            hi_t = mid
    return np.clip(x - 0.5 * (lo_t + hi_t), 0.0, cap_)


def _lmo(g, cap_, k):
    """Linear minimisation over {0 <= r <= cap_, sum r <= k}: fill most negative-gradient cells first."""
    r = np.zeros_like(cap_)
    neg = np.flatnonzero(g < 0)
    if len(neg) == 0:
        return r
    order = neg[np.argsort(g[neg], kind="stable")]
    cs_ = np.cumsum(cap_[order])
    full = int(np.searchsorted(cs_, k, side="right"))
    r[order[:full]] = cap_[order[:full]]
    used = float(cs_[full - 1]) if full > 0 else 0.0
    if full < len(order):
        r[order[full]] = max(0.0, k - used)
    return r


def _pgd(ctx, r, k, iters, stop_at, stop_margin):
    """Frank-Wolfe / projected-gradient ascent of the refit margin with exact line search over a step grid."""
    cnt = ctx.cnt
    mg, th = _cell_margin(ctx, r, ctx.theta_c, tol=1e-9)
    for _ in range(iters):
        if (stop_margin is not None and mg > stop_margin) or time.monotonic() > stop_at:
            break
        g = _cell_state(ctx, r, th)[0]
        sv = _lmo(g, cnt, k)
        gn = max(float(np.max(np.abs(g))), 1e-300)
        eta = max(1.0, k) / gn
        cands = [r + gam * (sv - r) for gam in (1.0, 0.5, 0.25, 0.1, 0.03, 0.01)]
        cands += [_project(r - kap * eta * g, cnt, k) for kap in (1.0, 0.3, 0.1, 0.03, 0.01)]
        best_m, best_r, best_th = mg, None, None
        for rc in cands:
            mc, thc = _cell_margin(ctx, rc, th, tol=1e-9)
            if mc > best_m + 1e-12:
                best_m, best_r, best_th = mc, rc, thc
        if best_r is None:
            break
        r, mg, th = best_r, best_m, best_th
    return mg, r


def relaxed_removal_search(ctx, k, stop_at, r0=None, n_starts=2, iters=40, stop_margin=None, rng=None):
    """Continuous relaxation: fractional removal weights r_c in [0, cnt_c], sum r_c <= k, maximise the refit margin.

    Returns (margin, r) of the best start. margin > 0 means the relaxed (fractional) removal flips the pair.
    """
    cnt = ctx.cnt
    k = float(min(k, cnt.sum()))
    g0 = _cell_state(ctx, np.zeros_like(cnt), ctx.theta_c)[0]
    starts = [_lmo(g0, cnt, k)]
    if r0 is not None and float(np.sum(r0)) > 1e-12:
        starts.append(_project(np.asarray(r0) * (k / float(np.sum(r0))), cnt, k))
    while len(starts) < n_starts and rng is not None:
        x = cnt * rng.random(len(cnt))
        starts.append(_project(x * (k / max(float(x.sum()), 1e-12)), cnt, k))
    best_m, best_r = -np.inf, starts[0]
    for i, r in enumerate(starts):
        if i > 0 and time.monotonic() > stop_at:
            break
        mg, rr = _pgd(ctx, r, k, iters, stop_at, stop_margin)
        if mg > best_m:
            best_m, best_r = mg, rr
        if stop_margin is not None and best_m > stop_margin:
            break
    return best_m, best_r


def _prune(ctx, rem, safety, stop_at):
    """Greedily decrement used cells (large steps first) while the exact refit keeps margin > safety."""
    rem = rem.copy()
    mg, th = _cell_margin(ctx, rem, ctx.theta_c)
    if mg <= safety or rem.sum() <= 0:
        return rem, mg
    step = 1
    while step * 2 <= int(rem.max()):
        step *= 2
    while step >= 1 and time.monotonic() < stop_at:
        improved = True
        while improved and time.monotonic() < stop_at:
            improved = False
            used = np.flatnonzero(rem > 0)
            if len(used) == 0:
                break
            g = _cell_state(ctx, rem, th)[0]
            used = used[np.argsort(-g[used], kind="stable")][:48]
            best_m, best_c, best_d = -np.inf, None, 0
            for c in used:
                d = int(min(step, rem[c]))
                rem[c] -= d
                mc, _ = _cell_margin(ctx, rem, th)
                rem[c] += d
                if mc > safety and mc > best_m:
                    best_m, best_c, best_d = mc, c, d
            if best_c is not None:
                rem[best_c] -= best_d
                mg, th = _cell_margin(ctx, rem, th)
                improved = True
        step //= 2
    return rem, mg


def round_and_repair(ctx, r_frac, kmax, stop_at, safety=SAFETY, ncand=32):
    """Largest-remainder rounding, screened exact greedy repair (<= kmax units), then exact pruning.

    Returns (rem_int, margin); margin > safety means a verified (cell-level) flip.
    """
    cnt = ctx.cnt
    ktot = int(round(float(np.sum(r_frac))))
    fl = np.minimum(np.floor(np.asarray(r_frac) + 1e-9), cnt)
    need = ktot - int(fl.sum())
    if need > 0:
        frac = np.asarray(r_frac) - fl
        cand = np.flatnonzero(cnt - fl > 0)
        fl[cand[np.argsort(-frac[cand], kind="stable")][:need]] += 1.0
    rem = fl
    while rem.sum() > kmax:                      # safety: never exceed the budget
        c = int(np.argmax(rem))
        rem[c] -= 1.0
    mg, th = _cell_margin(ctx, rem, ctx.theta_c)
    while mg <= safety and rem.sum() < kmax and time.monotonic() < stop_at:
        g = _cell_state(ctx, rem, th)[0]
        avail = np.flatnonzero(rem < cnt)
        if len(avail) == 0:
            break
        top = avail[np.argsort(g[avail], kind="stable")[:ncand]]
        total = float(rem.sum())
        u = max(1, int((kmax - total) // 100))
        best_m, best_c, best_d = -np.inf, None, 0
        for c in top:
            d = int(min(u, cnt[c] - rem[c], kmax - total))
            if d < 1:
                continue
            rem[c] += d
            mc, _ = _cell_margin(ctx, rem, th)
            rem[c] -= d
            if mc > best_m:
                best_m, best_c, best_d = mc, c, d
        if best_c is None:
            break
        rem[best_c] += best_d
        mg, th = _cell_margin(ctx, rem, th)
    if mg > safety:
        rem, mg = _prune(ctx, rem, safety, stop_at)
    return rem, mg


def swap_local_search(ctx, rem, stop_at, safety=SAFETY, ncand=24, nused=16, max_pass=60):
    """Exact-refit moves of 1 or 2 units between cells (accept if margin improves); prune when flipped."""
    cnt = ctx.cnt
    rem = rem.copy()
    mg, th = _cell_margin(ctx, rem, ctx.theta_c)
    if mg > safety:
        rem, mg = _prune(ctx, rem, safety, stop_at)
        mg, th = _cell_margin(ctx, rem, th)
    for _ in range(max_pass):
        if time.monotonic() > stop_at:
            break
        used = np.flatnonzero(rem > 0)
        if len(used) == 0:
            break
        g = _cell_state(ctx, rem, th)[0]
        avail = np.flatnonzero(rem < cnt)
        cands = avail[np.argsort(g[avail], kind="stable")[:ncand]]
        used = used[np.argsort(-g[used], kind="stable")][:nused]
        best = (mg + 1e-10 * max(1.0, abs(mg)), None, None, 0)
        for u in used:
            if time.monotonic() > stop_at:
                break
            for c in cands:
                if c == u:
                    continue
                for units in (1, 2):
                    if rem[u] < units or cnt[c] - rem[c] < units:
                        continue
                    rem[u] -= units
                    rem[c] += units
                    mc, _ = _cell_margin(ctx, rem, th)
                    rem[u] += units
                    rem[c] -= units
                    if mc > best[0]:
                        best = (mc, u, c, units)
        if best[1] is None:
            break
        rem[best[1]] -= best[3]
        rem[best[2]] += best[3]
        mg, th = _cell_margin(ctx, rem, th)
        if mg > safety:
            rem, mg = _prune(ctx, rem, safety, stop_at)
            mg, th = _cell_margin(ctx, rem, th)
    return rem, mg


def pair_enumeration_small_k(ctx, t, stop_at, safety=SAFETY, ntop=40, nverify=20):
    """Enumerate all multisets of ``t`` units (t <= 4) over the ntop best cells, screened by the exact
    one-step group-Newton gap change (Woodbury with the t x t interaction matrix), verify the best by exact refit.

    Predicted gap change for removed units U: dG = z_U^T (diag(1/q_U) - K_UU)^-1 (r_U / q_U),
    K = X^T H^-1 X, z = X^T H^-1 (e_hi - e_lo), r = p - s, q = p(1-p).  Returns (rem, margin) or None.
    """
    if t < 1 or t > 4:
        return None
    th = ctx.theta_c
    g, p, q, z, h = _cell_state(ctx, np.zeros_like(ctx.cnt), th)
    hinv = np.linalg.inv(h)
    nt = int(min(ntop, len(g)))
    top = np.argsort(g, kind="stable")[:nt]
    ta, tb = ctx.ca[top], ctx.cb[top]
    kmat = hinv[np.ix_(ta, ta)] - hinv[np.ix_(ta, tb)] - hinv[np.ix_(tb, ta)] + hinv[np.ix_(tb, tb)]
    r_ = (p - ctx.cs)[top]
    q_ = np.maximum(q[top], 1e-300)
    z_ = z[top]
    cnt_ = ctx.cnt[top]
    gap0 = float(th[ctx.hi] - th[ctx.lo])
    combos = np.array(list(itertools.combinations_with_replacement(range(nt), t)), dtype=np.int64)
    scored = []
    for lo_i in range(0, len(combos), 20000):
        if time.monotonic() > stop_at:
            break
        idx = combos[lo_i:lo_i + 20000]
        ok = np.ones(len(idx), bool)
        for j in range(t):
            eq = np.zeros(len(idx))
            for i in range(t):
                eq += (idx[:, i] == idx[:, j])
            ok &= eq <= cnt_[idx[:, j]]
        idx = idx[ok]
        if len(idx) == 0:
            continue
        mm = np.zeros((len(idx), t, t))
        for j in range(t):
            mm[:, j, j] = 1.0 / q_[idx[:, j]]
        mm -= kmat[idx[:, :, None], idx[:, None, :]]
        good = np.linalg.eigvalsh(mm)[:, 0] > 1e-10
        idx, mm = idx[good], mm[good]
        if len(idx) == 0:
            continue
        rhs = r_[idx] / q_[idx]
        sol = np.linalg.solve(mm, rhs[:, :, None])[:, :, 0]
        dg = np.sum(z_[idx] * sol, axis=1)
        scored.append((gap0 + dg, idx))
    if not scored:
        return None
    pred = np.concatenate([s_[0] for s_ in scored])
    allidx = np.concatenate([s_[1] for s_ in scored], axis=0)
    best_rem, best_m = None, -np.inf
    th_w = th
    for j in np.argsort(pred, kind="stable")[:nverify]:
        if time.monotonic() > stop_at:
            break
        rem = np.zeros_like(ctx.cnt)
        for c in allidx[j]:
            rem[top[c]] += 1.0
        mc, _ = _cell_margin(ctx, rem, th_w)
        if mc > best_m:
            best_rem, best_m = rem, mc
    if best_rem is None or best_m <= safety:
        return None
    return best_rem, best_m


def _best_k(cands):
    ks = [c[0] for c in cands if c[1] > 0]
    return min(ks) if ks else None


def _cell_stage(ctx, cands, diag, rng, t0, deadline):
    cap = ctx.cap
    stop_at = t0 + 0.6 * deadline
    stop_relax = t0 + 0.4 * deadline
    cells = aggregate_cells(ctx.a, ctx.b, ctx.s, ctx.m)
    ctx.ca, ctx.cb, ctx.cs, ctx.cnt = cells["ca"], cells["cb"], cells["cs"], cells["cnt"]
    ctx.order, ctx.starts, ctx.row_cell = cells["order"], cells["starts"], cells["row_cell"]
    ctx.ab = ctx.ca * ctx.m + ctx.cb
    diag["cells"] = float(len(ctx.cnt))
    ctx.theta_c = fit_weighted_bt(ctx.ca, ctx.cb, ctx.cs, ctx.cnt, ctx.m, ctx.ridge, ctx.theta0, tol=1e-11, max_iter=80)
    dev = float(np.max(np.abs(ctx.theta_c - ctx.theta0)))
    diag["fit_dev"] = dev
    if not dev < 1e-4:
        return                                    # cell fit disagrees with the row-level fit: do not trust it
    k_known = _best_k(cands)
    warm = None
    row_best = [c for c in cands if c[1] > 0]
    if row_best:
        kb = min(row_best, key=lambda c: c[0])
        warm = _rows_to_cells(ctx, kb[2])

    def record(rem):
        mg = _register(ctx, cands, _cells_to_rows(ctx, rem))
        return mg

    # (a) small budgets: screened exhaustive multiset enumeration
    if k_known is not None and k_known <= 5:
        try:
            while k_known is not None and k_known >= 2 and time.monotonic() < stop_at:
                res = pair_enumeration_small_k(ctx, k_known - 1, stop_at)
                if res is None:
                    break
                mg = record(res[0])
                if mg is None or mg <= 0:
                    break
                diag["enum_improved"] = diag.get("enum_improved", 0.0) + 1.0
                k_known = _best_k(cands)
        except Exception:
            diag["enum_error"] = 1.0
    # (b) relaxed search with budget bisection, then integer rounding / repair / swap polish
    hi_bound = cap if k_known is None else min(cap, k_known - 1)
    sols = {}
    kmin = None
    best_unflipped = None
    if hi_bound >= 1:
        try:
            mg_top, r_top = relaxed_removal_search(ctx, hi_bound, stop_relax, r0=None, n_starts=2, iters=40,
                                                   stop_margin=1e-7, rng=rng)
            diag["relaxed_margin_top"] = float(mg_top)
            if mg_top > 0:
                sols[hi_bound] = r_top
                lo_k, hi_k, best_r = 1, hi_bound, r_top
                while lo_k < hi_k and time.monotonic() < stop_relax:
                    mid = (lo_k + hi_k) // 2
                    mg_m, r_m = relaxed_removal_search(ctx, mid, stop_relax, r0=best_r, n_starts=2, iters=40,
                                                       stop_margin=1e-7, rng=rng)
                    if mg_m > 0:
                        hi_k, best_r = mid, r_m
                        sols[mid] = r_m
                    else:
                        lo_k = mid + 1
                kmin = hi_k
            elif k_known is None:
                # relaxed optimum does not flip within the cap; still try rounding/repair/swap once
                sols[hi_bound] = r_top
        except Exception:
            diag["relax_error"] = 1.0
    diag["relaxed_k_min"] = float(kmin) if kmin is not None else -1.0
    try:
        k_try = kmin if kmin is not None else (hi_bound if (k_known is None and sols) else None)
        attempts = 0
        while k_try is not None and k_try <= hi_bound and attempts < 6 and time.monotonic() < stop_at:
            near = sols.get(k_try)
            if near is None and sols:
                near = sols[min(sols, key=lambda kk: abs(kk - k_try))]
            mg_k, r_k = relaxed_removal_search(ctx, k_try, stop_at, r0=near, n_starts=2, iters=40, rng=rng)
            rem, mg = round_and_repair(ctx, r_k, hi_bound, stop_at)
            attempts += 1
            if mg <= SAFETY and time.monotonic() < stop_at:
                rem, mg = swap_local_search(ctx, rem, stop_at)
            if mg > SAFETY:
                rm = record(rem)
                if rm is not None and rm > 0:
                    hi_bound = min(hi_bound, int(rem.sum()) - 1)
            elif best_unflipped is None or mg > best_unflipped:
                best_unflipped = mg
            k_try += 1
    except Exception:
        diag["round_error"] = 1.0
    if best_unflipped is not None:
        diag["best_unflipped_margin"] = float(best_unflipped)
    # (c) swap polish of the best known verified set (prune + exact swaps), may shave units
    try:
        k_known = _best_k(cands)
        if warm is not None and k_known is not None and time.monotonic() < stop_at:
            rem, mg = swap_local_search(ctx, warm, stop_at)
            if mg > SAFETY and rem.sum() > 0:
                record(rem)
    except Exception:
        diag["swap_error"] = 1.0


def _analyze(req, st):
    t0 = time.monotonic()
    deadline = float(req["deadline_seconds"])
    a = np.concatenate([c[0] for c in st["chunks"]]).astype(np.int64)
    b = np.concatenate([c[1] for c in st["chunks"]]).astype(np.int64)
    y = np.concatenate([c[2] for c in st["chunks"]])
    ctx = _Ctx()
    ctx.a, ctx.b, ctx.n, ctx.m = a, b, len(y), int(st["n_models"])
    ctx.ridge = float(req["ridge"])
    ctx.s = _scores(y) if req.get("tie_as_half_win", True) else np.where(y == 0, 1.0, 0.0)
    ctx.hi, ctx.lo, ctx.cap = int(req["hi"]), int(req["lo"]), int(req["k_cap"])
    ctx.refits = 0
    ctx.nfit = 0
    ctx.theta0 = _fit(a, b, ctx.s, ctx.m, ctx.ridge, tol=1e-10, max_iter=80)
    cands = []
    diag = {}
    k_row = 0
    # Stage 1: cycle-1 row-level pipeline (safety candidate, never worse than cycle 1).
    try:
        resp = _analyze_rowlevel(req, st)
        rows = np.frombuffer(base64.b64decode(resp["removed"]["data"]), dtype="<u4").astype(np.int64)
        k_row = len(rows)
        if k_row > 0:
            _register(ctx, cands, rows)
    except Exception:
        diag["row_error"] = 1.0
    diag["k_rowlevel"] = float(k_row)
    # Stage 2: cell-aggregated relaxed search / exact polish.
    try:
        _cell_stage(ctx, cands, diag, st["rng"], t0, deadline)
    except Exception:
        diag["cell_error"] = 1.0
    safe = [c for c in cands if c[1] >= SAFETY and c[0] <= ctx.cap]
    pool = safe or [c for c in cands if c[1] > 0 and c[0] <= ctx.cap]
    if pool:
        k_f, mg_f, rows_f = min(pool, key=lambda c: (c[0], -c[1]))
        chosen = rows_f
        diag["margin"] = float(mg_f)
    else:
        chosen = np.zeros(0, dtype=np.int64)
        diag["margin"] = -1.0
    diag["k_cell"] = float(len(chosen))
    diag["refits"] = float(ctx.refits)
    diag["cell_fits"] = float(ctx.nfit)
    diag["elapsed"] = float(time.monotonic() - t0)
    diag = {k: (float(v) if np.isfinite(v) else -1.0) for k, v in diag.items()}
    return {"removed": _encode_u32(chosen), "diagnostics": diag}


def handle(request):
    op = request.get("op")
    if op == "reset":
        _STATE.clear()
        _STATE.update(_fresh(request["seed"]))
        return {"ok": True}
    if not _STATE:
        raise RuntimeError("reset required")
    if op == "load_chunk":
        a = _decode(request["a"], np.uint16)
        b = _decode(request["b"], np.uint16, len(a))
        y = _decode(request["y"], np.uint8, len(a))
        if request["chunk_index"] != len(_STATE["chunks"]):
            raise ValueError("chunk out of order")
        _STATE["chunks"].append((a, b, y))
        _STATE.update(n_chunks=request["n_chunks"], n_rows=request["n_rows_total"], n_models=request["n_models"])
        return {"ok": True}
    if op == "analyze":
        if len(_STATE["chunks"]) != _STATE["n_chunks"]:
            raise ValueError("table incomplete")
        return _analyze(request, _STATE)
    raise ValueError("unknown op")
