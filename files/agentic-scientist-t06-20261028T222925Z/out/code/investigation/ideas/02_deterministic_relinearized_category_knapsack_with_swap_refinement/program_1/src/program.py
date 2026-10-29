"""Perturbation finder for Bradley-Terry leaderboard stability (t06).

The evaluator calls ``handle(request) -> response`` with finite JSON-compatible dicts.  The
candidate runs isolated (no files, no network, no shared filesystem) and keeps all state in
process memory.  Every request/response must stay below 64 MiB of UTF-8 JSON.

Array encoding (both directions)
--------------------------------
``{"dtype": "int32" | "float32", "shape": [m], "encoding": "base64", "byte_order": "little",
"data": <base64 of the little-endian bytes>}`` -- exactly these five keys.

Episode protocol (one episode per case x seed; the process may be restarted before each reset)
-----------------------------------------------------------------------------------------------
1. ``{"op": "reset", "seed": int>=0}``
   Clear ALL state and seed any randomness.  The seed only initialises randomness; it never
   identifies the dataset, plane or workload.  Response: exactly ``{"ok": true}``.
2. ``{"op": "load_chunk", "case_token": str, "chunk_index": int, "n_chunks": int (1..4),
   "row_offset": int, "n_rows_total": int, "n_players": int, "player_a": int32[m],
   "player_b": int32[m], "outcome": float32[m]}``   (sent n_chunks times, chunk_index 0..n-1)
   Row r (global index row_offset + i) is one comparison between players ``player_a[r]`` and
   ``player_b[r]`` (ids 0..n_players-1, per-case relabelled); ``outcome`` is 1.0 if player_a
   won, 0.0 if player_b won and 0.5 for a tie.  At most 524,288 rows per chunk.  No names,
   text, dates, labels or scores are ever sent.  Response: exactly ``{"ok": true}``.
3. ``{"op": "propose", "perturbation": "drop" | "flip", "target": {"type": "top1"} |
   {"type": "topk_set", "k": int}, "estimator": {"model": "bradley_terry", "ties": "half",
   "ridge": float, "tol": float}, "max_size": int, "deadline_seconds": float}``
   Return a set of global row indices whose removal ("drop") or outcome reversal y -> 1-y
   ("flip"; tie rows are NOT flippable) changes the target of the fixed estimator:
     * estimator: maximise sum_r [y_r log s(t_a - t_b) + (1-y_r) log s(t_b - t_a)]
       - ridge/2 * ||t||^2 over log-strengths t (float64; s = logistic; ties count as half wins);
       the player set is fixed (players keep their ids even if all their rows are dropped);
     * top1 changes if some player j != leader has t_j > t_leader + tol after the change;
     * topk_set changes if max_{j outside S} t_j > min_{i in S} t_i + tol, S = original top-k.
   Response: ``{"indices": int32[s]}`` (array encoding above; strictly increasing, unique,
   0 <= index < n_rows_total, s <= max_size) plus optional ``"diagnostics"``: a dict of at most
   32 entries mapping names (``[A-Za-z0-9_-][A-Za-z0-9_.-]{0,79}``) to finite numbers.  No other
   keys are allowed; malformed responses score as failures.  The evaluator independently
   re-verifies the set with its own refit; claimed sizes/diagnostics are ignored.  Smaller
   verified sets score higher.  Respond before ``deadline_seconds`` (wall clock, measured by
   the evaluator from the request); late responses are failures.

Determinism: the same seed and inputs must give the same index set (a replay is checked).

Method (deterministic relinearized category knapsack with swap refinement)
--------------------------------------------------------------------------
1. Starter fallback: the one-step AMIP prefix (exponential + binary search, exact refits).
2. Rows are grouped into exchangeable categories: (winner, loser) for decisive rows and the
   unordered pair for ties (drop only).  A perturbation is an integer count vector over
   categories, so a refit only needs the p x p sufficient statistics (cost independent of n).
3. Several (insider, outsider) pairs are scored by the first-order knapsack size at theta0.
   For the best ones, a damped knapsack step is taken and the per-unit influence on
   t_i - t_j is relinearized at every perturbed refit until the exact refit flips the target.
4. Feasible count vectors are pruned (binary search over weakest units, then single-unit
   removals) and refined by 2-for-1 unit swaps, all checked with exact refits.
5. The best vector is materialized (lowest row ids per category), re-verified at row level
   with a small safety margin and used only if strictly smaller than the starter set.
All search effort is bounded by an integer refit cap derived from (n_categories, p, deadline);
the wall clock is only an emergency backstop, so replays give identical index sets.
"""
import base64
import math
import time

import numpy as np

_STATE = {}

_SAFETY_REL = 1e-7
_DAMP = 0.65
_GREEDY_ITERS = 40


def _decode(arr, dtype, expected_len):
    if (not isinstance(arr, dict) or arr.get("dtype") != dtype or arr.get("encoding") != "base64"
            or arr.get("byte_order") != "little"):
        raise ValueError("bad array")
    out = np.frombuffer(base64.b64decode(arr["data"]), dtype=np.dtype(dtype).newbyteorder("<"))
    if out.shape[0] != expected_len or list(arr["shape"]) != [expected_len]:
        raise ValueError("bad array shape")
    return out


def _encode_int32(values):
    arr = np.ascontiguousarray(np.asarray(values, dtype="<i4"))
    return {"dtype": "int32", "shape": [int(arr.shape[0])], "encoding": "base64",
            "byte_order": "little", "data": base64.b64encode(arr.tobytes()).decode("ascii")}


def _pair_stats(p, a, b, y):
    idx = a.astype(np.int64) * p + b.astype(np.int64)
    cnt = np.bincount(idx, minlength=p * p).reshape(p, p).astype(np.float64)
    won = np.bincount(idx, weights=y, minlength=p * p).reshape(p, p)
    lost = np.bincount(idx, weights=1.0 - y, minlength=p * p).reshape(p, p)
    return won + lost.T, cnt + cnt.T


def _fit(S, N, ridge, theta0=None, iters=200, gtol=1e-10):
    p = S.shape[0]
    theta = np.zeros(p) if theta0 is None else theta0.copy()
    score = S.sum(axis=1)

    def objective(t):
        d = t[:, None] - t[None, :]
        return -float((S * np.logaddexp(0.0, -d)).sum()) - 0.5 * ridge * float(t @ t)

    value = objective(theta)
    for _ in range(iters):
        d = theta[:, None] - theta[None, :]
        prob = 1.0 / (1.0 + np.exp(-d))
        grad = score - (N * prob).sum(axis=1) - ridge * theta
        if float(np.max(np.abs(grad))) < gtol:
            break
        w = N * prob * (1.0 - prob)
        hess = -w
        hess[np.diag_indices(p)] += w.sum(axis=1) + ridge
        step = np.linalg.solve(hess, grad)
        t = 1.0
        while True:
            cand = theta + t * step
            cv = objective(cand)
            if cv >= value - 1e-12 * max(1.0, abs(value)) or t < 1e-10:
                break
            t *= 0.5
        theta, value = cand, cv
    return theta


def _neg_hessian(N, theta, ridge):
    d = theta[:, None] - theta[None, :]
    prob = 1.0 / (1.0 + np.exp(-d))
    w = N * prob * (1.0 - prob)
    hess = -w
    hess[np.diag_indices(theta.shape[0])] += w.sum(axis=1) + ridge
    return hess


# ---------------------------------------------------------------------------------------------
# Deterministic effort budget
# ---------------------------------------------------------------------------------------------

def _deterministic_refit_cap(n_cat, p, deadline):
    """Integer refit cap from a fixed (conservative) per-refit cost model, no clock reads."""
    unit = 5e-4 + 2e-8 * float(n_cat) + 4e-7 * p * p + 2e-9 * float(p) ** 3
    cap = int(0.45 * max(float(deadline), 0.0) / unit)
    return int(max(16, min(cap, 4000)))


class _Budget:
    def __init__(self, cap, deadline, started):
        self.cap = int(cap)
        self.used = 0
        self.hard = started + 0.85 * max(float(deadline), 0.0)

    def alive(self):
        # Emergency backstop only; normal runs never reach it.
        return time.monotonic() < self.hard

    def ok(self, limit=None):
        lim = self.cap if limit is None else min(self.cap, int(limit))
        return self.used < lim and self.alive()


# ---------------------------------------------------------------------------------------------
# Categories and count-level refits
# ---------------------------------------------------------------------------------------------

def _build_categories(a, b, y, p):
    """Group rows into exchangeable categories.

    Decisive rows -> (winner, loser); tie rows -> unordered pair (lo, hi) flagged ``tie``.
    Self-pairs (no effect on the fit) and non-standard outcomes are left uncategorized.
    Rows of each category are kept in ascending row-index order.
    """
    n = a.shape[0]
    pp = p * p
    key = np.full(n, -1, dtype=np.int64)
    distinct = a != b
    win_a = distinct & (y == 1.0)
    win_b = distinct & (y == 0.0)
    tie = distinct & (y == 0.5)
    key[win_a] = a[win_a] * p + b[win_a]
    key[win_b] = b[win_b] * p + a[win_b]
    lo, hi = np.minimum(a, b), np.maximum(a, b)
    key[tie] = pp + lo[tie] * p + hi[tie]
    valid = np.flatnonzero(key >= 0)
    rows = valid[np.argsort(key[valid], kind="stable")]
    skeys = key[rows]
    row_cat = np.full(n, -1, dtype=np.int64)
    if skeys.size == 0:
        z = np.zeros(0, dtype=np.int64)
        return {"u": z, "v": z, "tie": np.zeros(0, dtype=bool), "cnt": z, "start": z,
                "rows": z, "row_cat": row_cat, "lin": z}
    uniq, start, cnt = np.unique(skeys, return_index=True, return_counts=True)
    is_tie = uniq >= pp
    base = np.where(is_tie, uniq - pp, uniq)
    u, v = base // p, base % p
    row_cat[rows] = np.repeat(np.arange(uniq.size, dtype=np.int64), cnt)
    return {"u": u.astype(np.int64), "v": v.astype(np.int64), "tie": is_tie,
            "cnt": cnt.astype(np.int64), "start": start.astype(np.int64), "rows": rows,
            "row_cat": row_cat, "lin": (u * p + v).astype(np.int64)}


def _stats_from_counts(S0, N0, cats, x, drop, p):
    """p x p (S, N) after dropping/flipping x[c] units of each category (exact arithmetic)."""
    pp = p * p
    lin, tie = cats["lin"], cats["tie"]
    xf = x.astype(np.float64)
    dec = np.where(tie, 0.0, xf)
    if drop:
        half = np.where(tie, 0.5 * xf, 0.0)
        D = np.bincount(lin, weights=xf, minlength=pp).reshape(p, p)
        W = np.bincount(lin, weights=dec, minlength=pp).reshape(p, p)
        H = np.bincount(lin, weights=half, minlength=pp).reshape(p, p)
        S = S0 - W - H - H.T
        N = N0 - D - D.T
    else:
        F = np.bincount(lin, weights=dec, minlength=pp).reshape(p, p)
        S = S0 - F + F.T
        N = N0
    return np.maximum(S, 0.0), np.maximum(N, 0.0)


class _Ctx:
    pass


def _refit(ctx, x):
    ctx.budget.used += 1
    S, N = _stats_from_counts(ctx.S0, ctx.N0, ctx.cats, x, ctx.drop, ctx.p)
    return _fit(S, N, ctx.ridge, ctx.theta0), N


def _slack(ctx, theta):
    return float(theta[ctx.out_idx].max()) - float(theta[ctx.top_idx].min()) - ctx.thr


def _crossing_pair(ctx, theta):
    i = int(ctx.top_idx[int(np.argmin(theta[ctx.top_idx]))])
    j = int(ctx.out_idx[int(np.argmax(theta[ctx.out_idx]))])
    return i, j


def _effects(ctx, theta, v):
    """First-order change of c^T theta (v = J^-1 c) per unit of each category."""
    cu, cv = ctx.cu, ctx.cv
    dv = v[cu] - v[cv]
    if ctx.drop:
        s = 1.0 / (1.0 + np.exp(-(theta[cu] - theta[cv])))
        resid = np.where(ctx.ctie, 0.5 - s, 1.0 - s)
        return -resid * dv
    return np.where(ctx.ctie, 0.0, -dv)


def _pair_effects(ctx, theta, N, i, j):
    c = np.zeros(ctx.p)
    c[i], c[j] = 1.0, -1.0
    v = np.linalg.solve(_neg_hessian(N, theta, ctx.ridge), c)
    return _effects(ctx, theta, v)


def _knapsack(eff, room, need):
    """Fewest units (largest per-unit gains first) whose linear margin reduction >= need."""
    cand = np.flatnonzero((eff < 0.0) & (room > 0))
    if cand.size == 0:
        return None, cand
    o = cand[np.argsort(eff[cand], kind="stable")]
    cum = np.cumsum(-eff[o] * room[o])
    pos = int(np.searchsorted(cum, need, side="left"))
    if pos >= o.size:
        return None, o
    prev_units = int(room[o[:pos]].sum())
    prev_gain = float(cum[pos - 1]) if pos > 0 else 0.0
    extra = int(math.ceil((need - prev_gain) / (-float(eff[o[pos]]))))
    extra = max(1, min(extra, int(room[o[pos]])))
    return prev_units + extra, o


def _take(o, room, units):
    r = room[o]
    before = np.cumsum(r) - r
    out = np.zeros_like(room)
    out[o] = np.clip(units - before, 0, r)
    return out


# ---------------------------------------------------------------------------------------------
# Search phases
# ---------------------------------------------------------------------------------------------

def _baseline_amip(a, b, y, p, S0, N0, theta0, top, leader, challenger, ridge, tol, drop,
                   max_size, budget):
    """Exact starter one-step AMIP prefix (exponential + binary search). Returns rows or None."""

    def changed(idx):
        budget.used += 1
        ia, ib, iy = a[idx], b[idx], y[idx]
        lin = ia * p + ib
        if drop:
            cnt = np.bincount(lin, minlength=p * p).reshape(p, p).astype(np.float64)
            won = np.bincount(lin, weights=iy, minlength=p * p).reshape(p, p)
            lost = np.bincount(lin, weights=1.0 - iy, minlength=p * p).reshape(p, p)
            S, N = S0 - won - lost.T, N0 - cnt - cnt.T
        else:
            delta = np.bincount(lin, weights=1.0 - 2.0 * iy, minlength=p * p).reshape(p, p)
            S, N = S0 + delta - delta.T, N0
        theta = _fit(np.maximum(S, 0.0), np.maximum(N, 0.0), ridge, theta0)
        return float(theta[~top].max()) > float(theta[top].min()) + tol

    c = np.zeros(p)
    c[leader], c[challenger] = 1.0, -1.0
    v = np.linalg.solve(_neg_hessian(N0, theta0, ridge), c)
    elig = np.arange(a.shape[0]) if drop else np.flatnonzero(y != 0.5)
    dv = v[a[elig]] - v[b[elig]]
    if drop:
        resid = y[elig] - 1.0 / (1.0 + np.exp(-(theta0[a[elig]] - theta0[b[elig]])))
        effect = -resid * dv
    else:
        effect = (1.0 - 2.0 * y[elig]) * dv
    ranked = elig[np.argsort(effect, kind="stable")]
    n = min(len(ranked), int(max_size))
    best = None
    size, last_fail = 1, 0
    while n > 0 and budget.alive():
        if changed(ranked[:size]):
            best = size
            break
        last_fail = size
        if size >= n:
            break
        size = min(2 * size, n)
    if best is not None:
        lo, hi = last_fail, best
        while hi - lo > 1 and budget.alive():
            mid = (lo + hi) // 2
            if changed(ranked[:mid]):
                hi = mid
            else:
                lo = mid
        best = hi
    if best is None:
        return None
    return np.sort(ranked[:best])


def _candidate_pairs(ctx, n_keep):
    """Rank (insider, outsider) pairs by first-order knapsack size at theta0."""
    th = ctx.theta0
    ins = ctx.top_idx[np.argsort(th[ctx.top_idx], kind="stable")][:8]
    n_out = 160 if ctx.k == 1 else 48
    outs = ctx.out_idx[np.argsort(-th[ctx.out_idx], kind="stable")][:n_out]
    Jinv = np.linalg.inv(_neg_hessian(ctx.N0, th, ctx.ridge))
    scored = []
    for i in ins:
        for j in outs:
            v = Jinv[:, i] - Jinv[:, j]
            eff = _effects(ctx, th, v)
            need = float(th[i] - th[j]) + ctx.thr
            if need <= 0.0:
                key = (0, 0.0)
            else:
                units, o = _knapsack(eff, ctx.avail, need)
                if units is None:
                    reach = float((-eff[o] * ctx.avail[o]).sum()) if o.size else 0.0
                    key = (1, -reach / need)
                else:
                    key = (0, float(units))
            scored.append((key, len(scored), int(i), int(j)))
    scored.sort()
    keep = [(i, j) for _, _, i, j in scored[:n_keep]]
    starter = (int(ins[0]), int(outs[0]))
    if starter not in keep:
        keep.append(starter)
    return keep


def _relinearized_greedy(ctx, i, j, limit_size, refit_limit):
    """Damped knapsack steps on t_i - t_j, relinearized at each exact perturbed refit."""
    budget = ctx.budget
    x = np.zeros(ctx.n_cat, dtype=np.int64)
    theta, N = ctx.theta0, ctx.N0
    total = 0
    for it in range(_GREEDY_ITERS):
        if it > 0:
            if not budget.ok(refit_limit):
                return None
            theta, N = _refit(ctx, x)
            if _slack(ctx, theta) > 0.0:
                return x
        need = float(theta[i] - theta[j]) + ctx.thr
        if need <= 0.0:
            return None
        eff = _pair_effects(ctx, theta, N, i, j)
        room = ctx.avail - x
        units, o = _knapsack(eff, room, need)
        if units is None:
            step = int(room[o].sum()) if o.size else 0
        else:
            if total + units > limit_size:
                return None
            step = units if units <= 2 else max(1, int(math.ceil(_DAMP * units)))
        step = min(step, limit_size - total)
        if step <= 0:
            return None
        x = x + _take(o, room, step)
        total += step
    return None


def _prune_counts(ctx, x, refit_limit):
    """Exact-refit pruning: binary search over weakest units, then single-unit removals.

    Returns None if ``x`` is not feasible at category level.
    """
    budget = ctx.budget
    if not budget.ok(refit_limit):
        return x
    theta, N = _refit(ctx, x)
    if _slack(ctx, theta) <= 0.0:
        return None
    i, j = _crossing_pair(ctx, theta)
    eff = _pair_effects(ctx, theta, N, i, j)
    used = np.flatnonzero(x > 0)
    weak = used[np.argsort(-eff[used], kind="stable")]
    units = np.repeat(weak, x[weak])
    lo, hi = 0, int(units.size) - 1
    while lo < hi and budget.ok(refit_limit):
        mid = (lo + hi + 1) // 2
        x2 = x - np.bincount(units[:mid], minlength=ctx.n_cat)
        th2, _ = _refit(ctx, x2)
        if _slack(ctx, th2) > 0.0:
            lo = mid
        else:
            hi = mid - 1
    if lo > 0:
        x = x - np.bincount(units[:lo], minlength=ctx.n_cat)
    for _ in range(3):
        if not budget.ok(refit_limit):
            break
        theta, N = _refit(ctx, x)
        i, j = _crossing_pair(ctx, theta)
        eff = _pair_effects(ctx, theta, N, i, j)
        used = np.flatnonzero(x > 0)
        weak = used[np.argsort(-eff[used], kind="stable")]
        improved = False
        for cidx in weak:
            if int(x.sum()) <= 1 or not budget.ok(refit_limit):
                break
            x2 = x.copy()
            x2[cidx] -= 1
            th2, _ = _refit(ctx, x2)
            if _slack(ctx, th2) > 0.0:
                x = x2
                improved = True
        if not improved:
            break
    return x


def _swap_refine(ctx, x, refit_limit, n_weak=5, n_strong=5, tries=16, passes=16):
    """Replace 2 weak used units by 1 strong available unit while the exact refit stays feasible."""
    budget = ctx.budget
    for _ in range(passes):
        if not budget.ok(refit_limit):
            break
        theta, N = _refit(ctx, x)
        if _slack(ctx, theta) <= 0.0:
            break
        i, j = _crossing_pair(ctx, theta)
        eff = _pair_effects(ctx, theta, N, i, j)
        used = np.flatnonzero(x > 0)
        weak = used[np.argsort(-eff[used], kind="stable")][:n_weak]
        room = ctx.avail - x
        addable = np.flatnonzero((room > 0) & (eff < 0.0))
        strong = addable[np.argsort(eff[addable], kind="stable")][:n_strong]
        combos = []
        for ad in strong:
            for p1 in range(weak.size):
                for p2 in range(p1, weak.size):
                    r1, r2 = int(weak[p1]), int(weak[p2])
                    if r1 == r2 and x[r1] < 2:
                        continue
                    if int(ad) in (r1, r2):
                        continue
                    delta = float(eff[ad] - eff[r1] - eff[r2])
                    combos.append((delta, len(combos), int(ad), r1, r2))
        combos.sort()
        accepted = False
        for _, _, ad, r1, r2 in combos[:tries]:
            if not budget.ok(refit_limit):
                break
            x2 = x.copy()
            x2[r1] -= 1
            x2[r2] -= 1
            x2[ad] += 1
            th2, _ = _refit(ctx, x2)
            if _slack(ctx, th2) > 0.0:
                x = x2
                accepted = True
                break
        if not accepted:
            break
    return x


def _materialize(cats, x):
    used = np.flatnonzero(x > 0)
    if used.size == 0:
        return np.zeros(0, dtype=np.int64)
    parts = [cats["rows"][cats["start"][c]:cats["start"][c] + x[c]] for c in used]
    return np.sort(np.concatenate(parts))


def _verify_rows(ctx, a, b, y, rows, max_size):
    """Row-level exact refit with the evaluator criterion plus a small safety margin."""
    if rows.size == 0 or rows.size > max_size:
        return False
    if rows.size > 1 and not bool(np.all(np.diff(rows) > 0)):
        return False
    if not ctx.drop and bool(np.any(y[rows] == 0.5)):
        return False
    p = ctx.p
    ia, ib, iy = a[rows], b[rows], y[rows]
    lin = ia * p + ib
    if ctx.drop:
        cnt = np.bincount(lin, minlength=p * p).reshape(p, p).astype(np.float64)
        won = np.bincount(lin, weights=iy, minlength=p * p).reshape(p, p)
        lost = np.bincount(lin, weights=1.0 - iy, minlength=p * p).reshape(p, p)
        S, N = ctx.S0 - won - lost.T, ctx.N0 - cnt - cnt.T
    else:
        delta = np.bincount(lin, weights=1.0 - 2.0 * iy, minlength=p * p).reshape(p, p)
        S, N = ctx.S0 + delta - delta.T, ctx.N0
    theta = _fit(np.maximum(S, 0.0), np.maximum(N, 0.0), ctx.ridge, ctx.theta0)
    return _slack(ctx, theta) > 0.0


# ---------------------------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------------------------

def _reset(request):
    seed = request.get("seed")
    if type(seed) is not int or seed < 0:
        raise ValueError("bad seed")
    _STATE.clear()
    _STATE["rng"] = np.random.default_rng(seed)
    return {"ok": True}


def _load_chunk(request):
    n_total, n_chunks, chunk = request["n_rows_total"], request["n_chunks"], request["chunk_index"]
    if chunk == 0:
        _STATE["case_token"] = request["case_token"]
        _STATE["n"] = n_total
        _STATE["p"] = request["n_players"]
        _STATE["a"] = np.zeros(n_total, dtype=np.int64)
        _STATE["b"] = np.zeros(n_total, dtype=np.int64)
        _STATE["y"] = np.zeros(n_total, dtype=np.float64)
        _STATE["loaded"] = set()
        _STATE["n_chunks"] = n_chunks
        _STATE["cache"] = {}
    if request["case_token"] != _STATE.get("case_token") or n_total != _STATE["n"]:
        raise ValueError("inconsistent chunk")
    m = request["player_a"]["shape"][0]
    lo = request["row_offset"]
    _STATE["a"][lo:lo + m] = _decode(request["player_a"], "int32", m)
    _STATE["b"][lo:lo + m] = _decode(request["player_b"], "int32", m)
    _STATE["y"][lo:lo + m] = _decode(request["outcome"], "float32", m)
    _STATE["loaded"].add(chunk)
    _STATE["cache"] = {}
    return {"ok": True}


def _propose(request):
    started = time.monotonic()
    deadline = float(request["deadline_seconds"])
    if _STATE.get("loaded") != set(range(_STATE.get("n_chunks", -1))):
        raise ValueError("data not loaded")
    a, b, y, p = _STATE["a"], _STATE["b"], _STATE["y"], _STATE["p"]
    ridge, tol = float(request["estimator"]["ridge"]), float(request["estimator"]["tol"])
    drop = request["perturbation"] == "drop"
    k = 1 if request["target"]["type"] == "top1" else int(request["target"]["k"])
    max_size = int(request["max_size"])
    cache = _STATE.setdefault("cache", {})
    if "S0" not in cache:
        cache["S0"], cache["N0"] = _pair_stats(p, a, b, y)
    S0, N0 = cache["S0"], cache["N0"]
    empty = np.zeros(0, dtype=np.int64)
    if k < 1 or k >= p:
        return {"indices": _encode_int32(empty), "diagnostics": {"final_size": 0.0}}
    theta0 = _fit(S0, N0, ridge)
    order = np.argsort(-theta0, kind="stable")
    top = np.zeros(p, dtype=bool)
    top[order[:k]] = True
    leader, challenger = int(order[k - 1]), int(order[k])

    if "cats" not in cache:
        cache["cats"] = _build_categories(a, b, y, p)
    cats = cache["cats"]
    n_cat = int(cats["cnt"].size)
    cap = _deterministic_refit_cap(n_cat, p, deadline)
    budget = _Budget(cap, deadline, started)

    base_rows = _baseline_amip(a, b, y, p, S0, N0, theta0, top, leader, challenger, ridge, tol,
                               drop, max_size, budget)
    base_refits = budget.used
    budget.used = 0
    base_size = None if base_rows is None else int(base_rows.size)
    diag = {"baseline_size": float(-1 if base_size is None else base_size),
            "refit_cap": float(cap), "baseline_refits": float(base_refits),
            "n_categories": float(n_cat)}

    def finish(rows, chosen_new):
        rows = empty if rows is None else rows
        diag["final_size"] = float(rows.size)
        diag["chosen_new"] = float(chosen_new)
        diag["refits"] = float(budget.used)
        return {"indices": _encode_int32(rows), "diagnostics": diag}

    upper = max_size if base_size is None else min(max_size, base_size - 1)
    if upper <= 0 or n_cat == 0:
        return finish(base_rows, 0)

    ctx = _Ctx()
    ctx.S0, ctx.N0, ctx.theta0, ctx.ridge, ctx.p, ctx.k = S0, N0, theta0, ridge, p, k
    ctx.drop, ctx.cats, ctx.n_cat, ctx.budget = drop, cats, n_cat, budget
    ctx.thr = tol + _SAFETY_REL * (1.0 + abs(tol))
    ctx.top_idx = np.flatnonzero(top)
    ctx.out_idx = np.flatnonzero(~top)
    ctx.cu, ctx.cv, ctx.ctie = cats["u"], cats["v"], cats["tie"]
    ctx.avail = cats["cnt"] if drop else np.where(cats["tie"], 0, cats["cnt"]).astype(np.int64)

    greedy_end = int(0.40 * cap)
    prune_end = int(0.75 * cap)

    cands = []
    if base_rows is not None:
        rc = cats["row_cat"][base_rows]
        cands.append(np.bincount(rc[rc >= 0], minlength=n_cat).astype(np.int64))
    best_size = min([int(c.sum()) for c in cands]) if cands else max_size

    pairs = _candidate_pairs(ctx, 8 if k == 1 else 12)
    pairs_tried = 0
    greedy_best = -1
    for i, j in pairs:
        if not budget.ok(greedy_end):
            break
        pairs_tried += 1
        limit = min(max_size, int(1.3 * best_size) + 3)
        x = _relinearized_greedy(ctx, i, j, limit, greedy_end)
        if x is not None:
            sz = int(x.sum())
            cands.append(x)
            best_size = min(best_size, sz)
            greedy_best = sz if greedy_best < 0 else min(greedy_best, sz)
    diag["pairs_tried"] = float(pairs_tried)
    diag["greedy_size"] = float(greedy_best)

    cands.sort(key=lambda c: int(c.sum()))
    shortlist = []
    for c in cands:
        if not any(np.array_equal(c, s) for s in shortlist):
            shortlist.append(c)
        if len(shortlist) == 3:
            break
    pruned = []
    for idx, x in enumerate(shortlist):
        share = max(0, prune_end - budget.used) // (len(shortlist) - idx)
        xp = _prune_counts(ctx, x, budget.used + share)
        if xp is not None:
            pruned.append(xp)
    pruned.sort(key=lambda c: int(c.sum()))
    diag["pruned_size"] = float(int(pruned[0].sum()) if pruned else -1)

    swap_gain = 0
    if pruned:
        before = int(pruned[0].sum())
        xs = _swap_refine(ctx, pruned[0], cap)
        if int(xs.sum()) < before:
            xp = _prune_counts(ctx, xs, cap)
            if xp is not None:
                xs = xp
            swap_gain = before - int(xs.sum())
            pruned[0] = xs
            pruned.sort(key=lambda c: int(c.sum()))
    diag["swap_gain"] = float(swap_gain)

    for x in pruned[:3]:
        if int(x.sum()) > upper:
            break
        rows = _materialize(cats, x)
        if _verify_rows(ctx, a, b, y, rows, upper):
            return finish(rows, 1)
    return finish(base_rows, 0)


def handle(request):
    op = request.get("op") if isinstance(request, dict) else None
    if op == "reset":
        return _reset(request)
    if op == "load_chunk":
        return _load_chunk(request)
    if op == "propose":
        return _propose(request)
    raise ValueError("unknown op")
