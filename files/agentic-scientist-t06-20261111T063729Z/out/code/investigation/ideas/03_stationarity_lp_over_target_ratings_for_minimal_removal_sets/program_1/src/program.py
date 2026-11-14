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

try:  # guarded: the stationarity-LP stage is skipped silently when scipy is unavailable
    from scipy.optimize import linprog, minimize
except Exception:  # pragma: no cover
    linprog = None
    minimize = None

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


# ----------------------------------------------------------------------------------------------
# Stationarity-LP stage.
#
# Removing rows R makes theta the exact (ridge) BT MLE iff the gradient of the kept data vanishes:
#     sum_{kept} (p - s)(e_a - e_b) + ridge * theta = 0.
# Rows are aggregated into cells (min(a,b), max(a,b), outcome in canonical orientation) with counts
# n_c; the per-unit gradient column of a cell is (p_c - s_c)(e_ca - e_cb), so for FIXED theta the
# cheapest removal is the LP   min sum(w)  s.t.  A(theta) w = F(theta),  0 <= w <= n.
# The outer search looks for theta with theta[hi] < theta[lo] that minimises this LP value; the
# fractional solution is rounded to rows and accepted only after an exact row-level refit flips.
# ----------------------------------------------------------------------------------------------
class _Timeout(Exception):
    pass


def _sigmoid(x):
    with np.errstate(over="ignore"):
        return 1.0 / (1.0 + np.exp(-x))


def _hessian(a, b, theta, m, ridge):
    p = _sigmoid(theta[a] - theta[b])
    w = p * (1.0 - p)
    h = np.bincount(a * m + b, w, m * m).reshape(m, m)
    h = -(h + h.T)
    h[np.diag_indices(m)] += np.bincount(a, w, m) + np.bincount(b, w, m) + ridge
    return h


def exact_flips(ctx, removed, min_margin=1e-7):
    """Exact row-level refit after removing ``removed``; returns (flips, margin theta[lo]-theta[hi], theta)."""
    ctx["refits"] += 1
    keep = np.ones(ctx["n"], bool)
    keep[np.asarray(removed, dtype=np.int64)] = False
    th = _fit(ctx["a"][keep], ctx["b"][keep], ctx["s"][keep], ctx["m"], ctx["ridge"], ctx["theta0"])
    margin = float(th[ctx["lo"]] - th[ctx["hi"]])
    return margin >= min_margin, margin, th


def polish_drop(ctx, rows, stop_at, max_passes=3):
    """Greedy exact pruning: drop removed rows one at a time while the refit still flips."""
    rows = np.unique(np.asarray(rows, dtype=np.int64))
    ok, _, th = exact_flips(ctx, rows)
    if not ok:
        return rows
    a, b, s, m, n = ctx["a"], ctx["b"], ctx["s"], ctx["m"], ctx["n"]
    for _ in range(max_passes):
        if len(rows) <= 1 or time.monotonic() > stop_at:
            break
        keep = np.ones(n, bool)
        keep[rows] = False
        e = np.zeros(m)
        e[ctx["hi"]], e[ctx["lo"]] = 1.0, -1.0
        v = np.linalg.solve(_hessian(a[keep], b[keep], th, m, ctx["ridge"]), e)
        ra, rb = a[rows], b[rows]
        eff = (_sigmoid(th[ra] - th[rb]) - s[rows]) * (v[ra] - v[rb])
        cur = rows[np.argsort(-eff, kind="stable")].tolist()
        dropped = False
        i = 0
        while i < len(cur) and len(cur) > 1 and time.monotonic() < stop_at:
            trial = cur[:i] + cur[i + 1:]
            ok, _, th2 = exact_flips(ctx, trial)
            if ok:
                cur, th, dropped = trial, th2, True
            else:
                i += 1
        rows = np.unique(np.asarray(cur, dtype=np.int64))
        if not dropped:
            break
    return rows


def build_cells(a, b, s, m):
    """Aggregate rows into cells with orientation-canonical (ca < cb) counts and score cs in {0, .5, 1}."""
    sw = a > b
    ca = np.where(sw, b, a)
    cb = np.where(sw, a, b)
    sc = np.where(sw, 1.0 - s, s)
    j = np.rint(2.0 * sc).astype(np.int64)
    key = (ca * m + cb) * 3 + j
    uniq, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    inv = np.asarray(inv).reshape(-1)
    q = uniq // 3
    return {"C": int(len(uniq)), "m": int(m), "ca": q // m, "cb": q % m, "cs": (uniq % 3) / 2.0,
            "cnt": cnt.astype(np.int64), "order": np.argsort(inv, kind="stable"),
            "starts": np.concatenate([[0], np.cumsum(cnt)[:-1]]).astype(np.int64)}


def counts_to_rows(cells, counts):
    """Concrete row indices (lowest indices of each cell) realising integer per-cell removal counts."""
    parts = []
    for c in np.flatnonzero(counts > 0):
        st0 = int(cells["starts"][c])
        parts.append(cells["order"][st0:st0 + int(counts[c])])
    return np.concatenate(parts).astype(np.int64) if parts else np.zeros(0, dtype=np.int64)


def stationarity_system(cells, theta, ridge):
    """Columns A(theta) (m x C) of per-unit stationarity contributions and F(theta) = full gradient."""
    ca, cb, C, m = cells["ca"], cells["cb"], cells["C"], cells["m"]
    r = _sigmoid(theta[ca] - theta[cb]) - cells["cs"]
    A = np.zeros((m, C))
    cols = np.arange(C)
    A[ca, cols] = r
    A[cb, cols] = -r
    return A, A @ cells["cnt"].astype(float) + ridge * theta


def _cell_selfcheck(ctx, cells):
    """Cell-space gradient must equal the row-level gradient; never throws."""
    try:
        a, b, s, m, ridge = ctx["a"], ctx["b"], ctx["s"], ctx["m"], ctx["ridge"]
        th = ctx["rng"].normal(0.0, 0.3, m)
        r = _sigmoid(th[a] - th[b]) - s
        g = np.bincount(a, r, m) - np.bincount(b, r, m) + ridge * th
        _, F = stationarity_system(cells, th, ridge)
        return bool(np.max(np.abs(g - F)) <= 1e-8 * (1.0 + np.max(np.abs(g))))
    except Exception:
        return False


def lp_min_removal_for_theta(cells, theta, ridge, big_m=50.0, time_limit=10.0):
    """min sum(w) + M sum(u+v)  s.t.  A(theta) w + u - v = F(theta), 0 <= w <= n  (elastic slack u, v >= 0)."""
    if linprog is None:
        return None
    C, m = cells["C"], cells["m"]
    A, F = stationarity_system(cells, theta, ridge)
    c = np.concatenate([np.ones(C), np.full(2 * m, big_m)])
    A_eq = np.hstack([A, np.eye(m), -np.eye(m)])
    ub = np.concatenate([cells["cnt"].astype(float), np.full(2 * m, np.inf)])
    bounds = np.column_stack([np.zeros(C + 2 * m), ub])
    res = linprog(c, A_eq=A_eq, b_eq=F, bounds=bounds, method="highs",
                  options={"time_limit": float(max(0.5, time_limit))})
    if res.status != 0 or res.x is None:
        return None
    w = np.clip(res.x[:C], 0.0, cells["cnt"].astype(float))
    return {"value": float(res.fun), "w": w, "slack": float(np.sum(res.x[C:])), "sum_w": float(np.sum(w))}


def round_lp_counts_to_rows(ctx, cells, w, limit, stop_at):
    """Floor the LP counts, add units in descending fractional order until the exact refit flips
    (bisect on the number added), then greedy influence repair; returns row indices or None."""
    cnt = cells["cnt"]
    base = np.minimum(np.floor(w + 1e-7).astype(np.int64), cnt)
    frac = w - base
    cand = np.flatnonzero((frac > 1e-6) & (base < cnt))
    cand = cand[np.argsort(-frac[cand], kind="stable")]
    room = int(limit - base.sum())
    if room < 0:
        return None
    jmax = min(len(cand), room)

    def rows_for(j):
        counts = base.copy()
        counts[cand[:j]] += 1
        return counts_to_rows(cells, counts)

    ok, _, _ = exact_flips(ctx, rows_for(jmax))
    if ok:
        lo_j, hi_j = -1, jmax
        while hi_j - lo_j > 1 and time.monotonic() < stop_at:
            mid = (lo_j + hi_j) // 2
            if exact_flips(ctx, rows_for(mid))[0]:
                hi_j = mid
            else:
                lo_j = mid
        return rows_for(hi_j)
    rows = rows_for(jmax)
    a, b, s, m, n = ctx["a"], ctx["b"], ctx["s"], ctx["m"], ctx["n"]
    for _ in range(min(8, limit - len(rows))):
        if time.monotonic() > stop_at:
            return None
        ok, _, th = exact_flips(ctx, rows)
        if ok:
            return rows
        keep = np.ones(n, bool)
        keep[rows] = False
        kr = np.flatnonzero(keep)
        infl = _influence(a[kr], b[kr], s[kr], th, ctx["hi"], ctx["lo"], m, ctx["ridge"])
        rows = np.append(rows, kr[int(np.argmin(infl))])
    return rows if exact_flips(ctx, rows)[0] else None


def small_k_search(ctx, cells, kmax, stop_at):
    """Cell-level enumeration of removal multisets of size 1..kmax among the most helpful cells, screened by a
    one-step Newton approximation and confirmed by exact refits. Returns rows of the smallest flipping set."""
    m, hi, lo, ridge, theta0 = ctx["m"], ctx["hi"], ctx["lo"], ctx["ridge"], ctx["theta0"]
    ca, cb, cnt, C = cells["ca"], cells["cb"], cells["cnt"], cells["C"]
    r = _sigmoid(theta0[ca] - theta0[cb]) - cells["cs"]
    pr = _sigmoid(theta0[ca] - theta0[cb])
    cw = cnt * pr * (1.0 - pr)
    h = np.bincount(ca * m + cb, cw, m * m).reshape(m, m)
    H = -(h + h.T)
    H[np.diag_indices(m)] += np.bincount(ca, cw, m) + np.bincount(cb, cw, m) + ridge
    e = np.zeros(m)
    e[hi], e[lo] = 1.0, -1.0
    v = np.linalg.solve(H, e)
    infl = r * (v[ca] - v[cb])
    D = np.zeros((C, m))
    D[np.arange(C), ca] = 1.0
    D[np.arange(C), cb] = -1.0
    order = np.argsort(infl, kind="stable")
    order = order[infl[order] < 0]
    if len(order) == 0:
        return None
    cw1 = pr * (1.0 - pr)  # per-unit Hessian weight
    small = m <= 12
    tlim = {1: 400, 2: 300 if small else 150, 3: 50}
    chunk = max(50, min(5000, int(3e7 / (8.0 * m * m))))
    for k in range(1, kmax + 1):
        if time.monotonic() > stop_at:
            break
        top = order[:tlim.get(k, 30)]
        combos = np.array(list(itertools.combinations_with_replacement(range(len(top)), k)),
                          dtype=np.int64).reshape(-1, k)
        cand = top[combos]
        valid = np.ones(len(cand), bool)
        mult = np.ones(len(cand), dtype=np.int64)
        for t in range(1, k):
            mult = np.where(cand[:, t] == cand[:, t - 1], mult + 1, 1)
            valid &= cnt[cand[:, t]] >= mult
        cand = cand[valid]
        if len(cand) == 0:
            continue
        margins = np.full(len(cand), -np.inf)
        for st0 in range(0, len(cand), chunk):
            if time.monotonic() > stop_at:
                break
            idx = cand[st0:st0 + chunk]
            Dk = D[idx]
            G = np.einsum("pk,pkm->pm", r[idx], Dk)
            W = cw1[idx][:, :, None] * Dk
            Hr = H[None] - np.matmul(W.transpose(0, 2, 1), Dk)
            try:
                step = np.linalg.solve(Hr, G[:, :, None])[:, :, 0]
            except np.linalg.LinAlgError:
                continue
            margins[st0:st0 + len(idx)] = (theta0[lo] + step[:, lo]) - (theta0[hi] + step[:, hi])
        for i in np.argsort(-margins, kind="stable")[:12]:
            if time.monotonic() > stop_at or not np.isfinite(margins[i]):
                break
            rows = counts_to_rows(cells, np.bincount(cand[i], minlength=C))
            if len(rows) <= ctx["cap"] and exact_flips(ctx, rows)[0]:
                return rows
    return None


def target_theta_search(ctx, cells, centers, cap, stop_at, best_rows, stats):
    """Outer search over target ratings theta with theta[lo] = theta[hi] + delta, minimising the stationarity-LP
    value; the LP solutions of the best targets are rounded to rows and accepted only if the exact refit flips.
    Small m: random cloud around the centers + Nelder-Mead; large m: warm-started pairwise local search."""
    m, hi, lo, rng = ctx["m"], ctx["hi"], ctx["lo"], ctx["rng"]
    best = best_rows
    small = m <= 12
    deltas = (0.02, 0.006, 0.002, 5e-4) if small else (1e-3, 3e-4, 1e-4)
    big_m = 50.0
    others = np.array([i for i in range(m) if i != hi and i != lo], dtype=np.int64)
    centers = [np.asarray(c, dtype=float) for c in centers if c is not None]
    if not centers:
        return best

    for di, delta in enumerate(deltas):
        now = time.monotonic()
        if now > stop_at - 0.3:
            break
        limit = cap if best is None else min(cap, len(best) - 1)
        if limit < 1:
            break
        slice_end = now + (stop_at - now) / (len(deltas) - di)
        stats["deltas"] += 1

        def evaluate(theta):
            tl = max(0.5, min(10.0, slice_end - time.monotonic()))
            out = lp_min_removal_for_theta(cells, theta, ctx["ridge"], big_m, tl)
            stats["lps"] += 1
            if out is not None:
                stats["min_value"] = min(stats["min_value"], out["value"])
                if out["slack"] < 1e-6:
                    stats["min_relaxed"] = min(stats["min_relaxed"], out["sum_w"])
            return out

        def try_round(out):
            if out is None or out["sum_w"] > limit + m + 1:
                return None
            rows = round_lp_counts_to_rows(ctx, cells, out["w"], limit, stop_at)
            if rows is None:
                return None
            rows = polish_drop(ctx, rows, stop_at)
            ok, margin, th = exact_flips(ctx, rows)
            if not ok or len(rows) > limit:
                return None
            return rows, th, margin

        targets = []  # (theta, lp output) candidates to round
        if small:
            def make_target(z):
                theta = np.zeros(m)
                theta[others] = z
                theta[hi] = -(delta + float(np.sum(z))) / 2.0
                theta[lo] = theta[hi] + delta
                return theta

            elite = []

            def obj(z):
                if time.monotonic() > slice_end:
                    raise _Timeout()
                out = evaluate(make_target(z))
                val = 1e9 if out is None else out["value"]
                elite.append((val, np.array(z, dtype=float)))
                return val

            try:
                zc = [c[others] for c in centers]
                for z0 in zc:
                    obj(z0)
                if len(others) > 0:
                    cloud_end = now + 0.45 * (slice_end - now)
                    sigmas = (0.01, 0.03, 0.1, 0.3, 1.0)
                    it = 0
                    while time.monotonic() < cloud_end and it < 2500:
                        z0 = zc[int(rng.integers(len(zc)))]
                        obj(z0 + sigmas[int(rng.integers(len(sigmas)))] * rng.standard_normal(len(others)))
                        it += 1
                    elite.sort(key=lambda t: t[0])
                    starts = [z for _, z in elite[:4]]
                    for z0 in starts:
                        if minimize is not None:
                            simplex = np.vstack([z0, z0 + 0.02 * np.eye(len(z0))])
                            minimize(obj, z0, method="Nelder-Mead",
                                     options={"maxfev": 150, "initial_simplex": simplex, "xatol": 1e-6, "fatol": 1e-8})
                        else:
                            zb, vb = z0, min(t[0] for t in elite[:1])
                            for sg in (0.03, 0.01, 0.003, 0.001) * 10:
                                zt = zb + sg * rng.standard_normal(len(zb))
                                vt = obj(zt)
                                if vt < vb:
                                    zb, vb = zt, vt
            except _Timeout:
                pass
            elite.sort(key=lambda t: t[0])
            picks = []
            for val, z in elite:
                if val >= 1e8:
                    break
                if all(np.max(np.abs(z - q)) > 1e-3 for q in picks):
                    picks.append(z)
                if len(picks) >= 3:
                    break
            if elite and elite[0][0] < 1e8:
                stats["best_value"] = min(stats["best_value"], elite[0][0])
            for z in picks:
                theta = make_target(z)
                out = lp_min_removal_for_theta(cells, theta, ctx["ridge"], big_m, 5.0)
                stats["lps"] += 1
                targets.append((theta, out))
        else:
            def shift_target(theta_in):
                theta = np.array(theta_in, dtype=float)
                mid = 0.5 * (theta[hi] + theta[lo])
                theta[hi] = mid - delta / 2.0
                theta[lo] = theta[hi] + delta
                return theta

            theta = shift_target(centers[0])
            out = evaluate(theta)
            cur = np.inf if out is None else out["value"]
            best_theta, best_out = theta, out
            steps = (0.01, 0.003, 0.001, 3e-4)
            evals = 0
            while time.monotonic() < slice_end and evals < 40:
                evals += 1
                i = int(rng.choice([hi, lo])) if rng.random() < 0.5 else int(rng.integers(m))
                j = int(rng.integers(m))
                if j == i:
                    continue
                step = steps[int(rng.integers(len(steps)))] * (1.0 if rng.random() < 0.5 else -1.0)
                cand = best_theta.copy()
                cand[i] += step
                cand[j] -= step
                cand = shift_target(cand)
                out = evaluate(cand)
                if out is not None and out["value"] < cur - 1e-9:
                    cur, best_theta, best_out = out["value"], cand, out
            if np.isfinite(cur):
                stats["best_value"] = min(stats["best_value"], cur)
            targets.append((best_theta, best_out))

        for theta, out in targets:
            if time.monotonic() > stop_at:
                break
            res = try_round(out)
            if res is None:
                continue
            rows, th, margin = res
            if best is None or len(rows) < len(best):
                best = rows
                stats["rounded_k"] = float(len(rows))
                stats["best_margin"] = margin
                centers.append(th)
                limit = min(cap, len(best) - 1)
                if limit < 1:
                    break
    return best


def _extra_stages(ctx, best, order, theta_B, stop_at, diag):
    """Run the cell-level enumeration and the stationarity-LP search; returns a (possibly smaller) row set."""
    a, b, s, m, cap = ctx["a"], ctx["b"], ctx["s"], ctx["m"], ctx["cap"]
    t0 = time.monotonic()
    cur = best
    cells = build_cells(a, b, s, m)
    diag["cells"] = float(cells["C"])
    sc_ok = _cell_selfcheck(ctx, cells)
    diag["selfcheck_ok"] = 1.0 if sc_ok else 0.0
    if not sc_ok:
        return cur
    # Stage 1: tiny multisets of cells (screened by Newton one-step, confirmed exactly).
    try:
        kmax = min(3 if m <= 12 else 2, cap) if cur is None else min(3 if m <= 12 else 2, len(cur) - 1, cap)
        if kmax >= 1:
            found = small_k_search(ctx, cells, kmax, t0 + 0.25 * (stop_at - t0))
            if found is not None and (cur is None or len(found) < len(cur)):
                cur = polish_drop(ctx, found, stop_at)
                diag["enum_k"] = float(len(cur))
    except Exception:
        diag["enum_threw"] = 1.0
    # Stage 2: stationarity-LP over target ratings.
    stats = {"lps": 0, "deltas": 0, "min_relaxed": np.inf, "min_value": np.inf, "best_value": np.inf,
             "rounded_k": 0.0, "best_margin": 0.0}
    try:
        centers = [ctx["theta0"]]
        if cur is not None:
            centers.insert(0, exact_flips(ctx, cur)[2])
        if m <= 12:
            if order is not None and len(order) > 0:
                centers.append(exact_flips(ctx, order[:cap])[2])
            if theta_B is not None:
                centers.append(theta_B)
            stop_lp = stop_at
        else:
            # large m: warm-started local search from one centre (the flipping refit if any)
            if cur is None:
                centers = [theta_B if theta_B is not None else ctx["theta0"]]
            stop_lp = time.monotonic() + 0.6 * max(0.0, stop_at - time.monotonic())
        cur = target_theta_search(ctx, cells, centers, cap, stop_lp, cur, stats)
    except Exception:
        diag["search_threw"] = 1.0
    diag["lps"] = float(stats["lps"])
    diag["deltas"] = float(stats["deltas"])
    diag["min_relaxed_lp"] = float(stats["min_relaxed"]) if np.isfinite(stats["min_relaxed"]) else -1.0
    diag["min_lp_value"] = float(stats["min_value"]) if np.isfinite(stats["min_value"]) else -1.0
    diag["best_lp_value"] = float(stats["best_value"]) if np.isfinite(stats["best_value"]) else -1.0
    diag["rounded_k"] = float(stats["rounded_k"])
    diag["best_margin"] = float(stats["best_margin"])
    return cur


def _analyze(req, st):
    a = np.concatenate([c[0] for c in st["chunks"]]).astype(np.int64)
    b = np.concatenate([c[1] for c in st["chunks"]]).astype(np.int64)
    y = np.concatenate([c[2] for c in st["chunks"]])
    n, m = len(y), int(st["n_models"])
    ridge = float(req["ridge"])
    s = _scores(y) if req.get("tie_as_half_win", True) else np.where(y == 0, 1.0, 0.0)
    hi, lo, cap = int(req["hi"]), int(req["lo"]), int(req["k_cap"])
    stop_at = time.monotonic() + 0.7 * float(req["deadline_seconds"])
    refits = 0
    theta_B = None
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
        theta_B = theta
    base_k = None if best is None else len(best)
    # Stationarity-LP stage: any exception or timeout falls back silently to the row-level candidate above.
    diag = {}
    if best is None or len(best) > 1:
        ctx = {"a": a, "b": b, "s": s, "n": n, "m": m, "ridge": ridge, "hi": hi, "lo": lo, "cap": cap,
               "theta0": theta0, "rng": st["rng"], "refits": 0}
        try:
            cand = _extra_stages(ctx, best, order, theta_B, stop_at, diag)
            if cand is not None and (best is None or len(cand) < len(best)) and 1 <= len(cand) <= cap:
                keep = np.ones(n, bool)
                keep[np.asarray(cand, dtype=np.int64)] = False
                th = _fit(a[keep], b[keep], s[keep], m, ridge)  # cold-start verification
                if th[lo] - th[hi] > 1e-8:
                    best = np.asarray(cand, dtype=np.int64)
            refits += ctx["refits"]
        except Exception:
            diag["stage_threw"] = 1.0
    chosen = np.zeros(0, dtype=np.int64) if best is None else np.unique(np.asarray(best, dtype=np.int64))
    out = {"refits": float(refits), "k": float(len(chosen)), "base_k": float(-1 if base_k is None else base_k)}
    for key, val in diag.items():
        if len(out) >= 32:
            break
        val = float(val)
        out[key] = val if math.isfinite(val) else -1.0
    return {"removed": _encode_u32(chosen), "diagnostics": out}


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
