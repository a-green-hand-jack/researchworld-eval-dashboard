"""Starter perturbation finder for Bradley-Terry leaderboard stability (t06).

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

This candidate (program_1): relinearized category knapsack with multi-pair targeting.
  * Rows sharing (winner, loser) -- or the same unordered tie pair -- are exchangeable under the
    estimator, so a perturbation is a vector of integer counts per category and every refit is
    done directly on the p x p sufficient statistics (S, N).
  * For a boundary pair (insider i, outsider j) the margin t_i - t_j is driven below -tol by
    Frank-Wolfe-like fractional-knapsack steps whose per-unit influence is recomputed at the
    current perturbed fit (damped steps, exact refit after each step).
  * Several (i, j) pairs are tried (ranked by a first-order knapsack estimate at the original
    fit); the best feasible count vectors are pruned with exact refits (global weakest-prefix
    removal, then per-category binary search).
  * The starter AMIP prefix search is run first and kept as the fallback whenever the new
    search does not give a strictly smaller set that re-verifies at row level with a safety
    margin above tol.
All loops use stable sorts and fixed orders; work is capped by a deterministic refit budget
derived from deadline_seconds and n_players, with wall-clock checks only as a backstop.
"""
import base64
import time
from types import SimpleNamespace

import numpy as np

_STATE = {}

_SAFETY_REL = 1e-7
_GREEDY_ITERS = 60
_DAMP = 0.7


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


def _solve(H, rhs):
    try:
        out = np.linalg.solve(H, rhs)
        if np.all(np.isfinite(out)):
            return out
    except np.linalg.LinAlgError:
        pass
    try:
        out = np.linalg.lstsq(H, rhs, rcond=None)[0]
        if np.all(np.isfinite(out)):
            return out
    except np.linalg.LinAlgError:
        pass
    return np.zeros_like(rhs, dtype=np.float64)


# --------------------------------------------------------------------------------------------
# Budget and target helpers
# --------------------------------------------------------------------------------------------

class _Budget:
    """Deterministic refit cap (primary) plus a wall-clock backstop."""

    def __init__(self, started, deadline, p):
        self.started = started
        self.deadline = deadline
        self.refits = 0
        est = 5e-4 + 4e-7 * float(p) * float(p)
        self.max_refits = int(min(200000, max(60, 0.5 * deadline / est)))

    def elapsed(self):
        return time.monotonic() - self.started

    def ok(self, time_frac=0.7, refit_frac=1.0):
        return (self.refits < refit_frac * self.max_refits
                and self.elapsed() < time_frac * self.deadline)


def _is_changed(pb, theta, safety):
    return float(theta[~pb.top].max()) > float(theta[pb.top].min()) + pb.tol + safety


def _verify_rows(pb, idx, safety):
    """Row-level exact check (same refit as the starter); success needs margin > tol + safety."""
    idx = np.asarray(idx, dtype=np.int64)
    a, b, y, p = pb.a, pb.b, pb.y, pb.p
    ia, ib, iy = a[idx], b[idx], y[idx]
    lin = ia * p + ib
    if pb.drop:
        cnt = np.bincount(lin, minlength=p * p).reshape(p, p).astype(np.float64)
        won = np.bincount(lin, weights=iy, minlength=p * p).reshape(p, p)
        lost = np.bincount(lin, weights=1.0 - iy, minlength=p * p).reshape(p, p)
        S, N = pb.S0 - won - lost.T, pb.N0 - cnt - cnt.T
    else:
        delta = np.bincount(lin, weights=1.0 - 2.0 * iy, minlength=p * p).reshape(p, p)
        S, N = pb.S0 + delta - delta.T, pb.N0
    pb.budget.refits += 1
    try:
        theta = _fit(np.maximum(S, 0.0), np.maximum(N, 0.0), pb.ridge, pb.theta0)
    except (np.linalg.LinAlgError, ValueError, FloatingPointError):
        return False
    if not np.all(np.isfinite(theta)):
        return False
    return _is_changed(pb, theta, safety)


# --------------------------------------------------------------------------------------------
# Starter AMIP prefix search (fallback)
# --------------------------------------------------------------------------------------------

def _baseline_amip(pb, time_frac=0.6):
    a, b, y, p, theta0 = pb.a, pb.b, pb.y, pb.p, pb.theta0
    leader, challenger = int(pb.order[pb.k - 1]), int(pb.order[pb.k])
    c = np.zeros(p)
    c[leader], c[challenger] = 1.0, -1.0
    v = _solve(_neg_hessian(pb.N0, theta0, pb.ridge), c)
    elig = np.arange(a.shape[0]) if pb.drop else np.flatnonzero(y != 0.5)
    dv = v[a[elig]] - v[b[elig]]
    if pb.drop:
        resid = y[elig] - 1.0 / (1.0 + np.exp(-(theta0[a[elig]] - theta0[b[elig]])))
        effect = -resid * dv
    else:
        effect = (1.0 - 2.0 * y[elig]) * dv
    ranked = elig[np.argsort(effect, kind="stable")]
    n = min(len(ranked), pb.max_size)
    budget = pb.budget
    best = None
    size, last_fail = 1, 0
    while n > 0 and budget.elapsed() < time_frac * budget.deadline:
        if _verify_rows(pb, ranked[:size], 0.0):
            best = size
            break
        last_fail = size
        if size >= n:
            break
        size = min(2 * size, n)
    if best is not None:
        lo, hi = last_fail, best
        while hi - lo > 1 and budget.elapsed() < time_frac * budget.deadline:
            mid = (lo + hi) // 2
            if _verify_rows(pb, ranked[:mid], 0.0):
                hi = mid
            else:
                lo = mid
        best = hi
    if best is None:
        return None
    return np.sort(ranked[:best])


# --------------------------------------------------------------------------------------------
# Category machinery
# --------------------------------------------------------------------------------------------

def _build_categories(pb):
    """Group eligible rows into exchangeable categories.

    Decisive rows are keyed by (winner, loser); tie rows (drop only) by the unordered pair with a
    tie flag.  Self-comparisons have no effect on the fit and are excluded.
    """
    a, b, y, p = pb.a, pb.b, pb.y, pb.p
    win_a, win_b, tie = y == 1.0, y == 0.0, y == 0.5
    elig = (a != b) & (win_a | win_b | (tie if pb.drop else False))
    rows = np.flatnonzero(elig)
    ra, rb, rt = a[rows], b[rows], tie[rows]
    ya = win_a[rows]
    w = np.where(ya, ra, rb)
    l = np.where(ya, rb, ra)
    lo_, hi_ = np.minimum(ra, rb), np.maximum(ra, rb)
    pp = np.int64(p) * np.int64(p)
    key = np.where(rt, pp + lo_ * p + hi_, w * p + l).astype(np.int64)
    if rows.size == 0:
        empty = np.zeros(0, dtype=np.int64)
        return SimpleNamespace(K=0, w=empty, l=empty, tie=np.zeros(0, dtype=bool), avail=empty,
                               start=empty, rows=empty, cat_of_row=np.full(a.shape[0], -1))
    uniq, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    inv = np.asarray(inv).reshape(-1)
    order = np.argsort(inv, kind="stable")
    cat_rows = rows[order]
    start = np.concatenate([[0], np.cumsum(cnt)[:-1]]).astype(np.int64)
    cat_tie = uniq >= pp
    base = np.where(cat_tie, uniq - pp, uniq)
    cat_of_row = np.full(a.shape[0], -1, dtype=np.int64)
    cat_of_row[rows] = inv
    return SimpleNamespace(K=int(uniq.shape[0]), w=(base // p).astype(np.int64),
                           l=(base % p).astype(np.int64), tie=cat_tie,
                           avail=cnt.astype(np.int64), start=start, rows=cat_rows,
                           cat_of_row=cat_of_row)


def _stats_from_counts(pb, cats, counts):
    """Perturbed (S, N) after dropping/flipping counts[k] rows of every category k."""
    S, N = pb.S0.copy(), pb.N0.copy()
    nz = np.flatnonzero(counts)
    if nz.size:
        c = counts[nz].astype(np.float64)
        w, l, t = cats.w[nz], cats.l[nz], cats.tie[nz]
        if pb.drop:
            d = ~t
            np.add.at(S, (w[d], l[d]), -c[d])
            np.add.at(N, (w[d], l[d]), -c[d])
            np.add.at(N, (l[d], w[d]), -c[d])
            if t.any():
                np.add.at(S, (w[t], l[t]), -0.5 * c[t])
                np.add.at(S, (l[t], w[t]), -0.5 * c[t])
                np.add.at(N, (w[t], l[t]), -c[t])
                np.add.at(N, (l[t], w[t]), -c[t])
        else:
            np.add.at(S, (w, l), -c)
            np.add.at(S, (l, w), c)
    return np.maximum(S, 0.0), np.maximum(N, 0.0)


def _fit_counts(pb, cats, counts, theta_init):
    S, N = _stats_from_counts(pb, cats, counts)
    pb.budget.refits += 1
    try:
        theta = _fit(S, N, pb.ridge, theta_init)
    except (np.linalg.LinAlgError, ValueError, FloatingPointError):
        return None
    if not np.all(np.isfinite(theta)):
        return None
    return theta, N


def _category_effects(pb, cats, theta, v):
    """First-order change of the margin c^T theta per unit of each category (v = H^-1 c)."""
    dv = v[cats.w] - v[cats.l]
    if not pb.drop:
        return -dv
    pr = 1.0 / (1.0 + np.exp(-(theta[cats.w] - theta[cats.l])))
    target = np.where(cats.tie, 0.5, 1.0)
    return -(target - pr) * dv


def _knapsack_units(eff, rem, D):
    """Fractional-knapsack allocation (unit cost) covering a margin deficit D > 0.

    Returns (category ids in use order, units per category, covered flag)."""
    usable = np.flatnonzero((eff < 0.0) & (rem > 0))
    if usable.size == 0:
        return usable, np.zeros(0, dtype=np.int64), False
    cand = usable[np.argsort(eff[usable], kind="stable")]
    gain = -eff[cand]
    r = rem[cand]
    cum = np.cumsum(gain * r)
    pos = int(np.searchsorted(cum, D, side="left"))
    if pos >= cand.size:
        return cand, r.astype(np.int64), False
    prev = float(cum[pos - 1]) if pos > 0 else 0.0
    last = int(np.ceil((D - prev) / gain[pos]))
    last = max(1, min(last, int(r[pos])))
    units = np.concatenate([r[:pos], [last]]).astype(np.int64)
    return cand[:pos + 1], units, True


def _relinearized_greedy(pb, cats, i, j, refit_frac):
    """Drive t_i - t_j below -tol with damped knapsack steps relinearized at each refit."""
    counts = np.zeros(cats.K, dtype=np.int64)
    theta, N = pb.theta0, pb.N0
    limit = 4 * pb.max_size + 64
    c = np.zeros(pb.p)
    c[i], c[j] = 1.0, -1.0
    for it in range(_GREEDY_ITERS + 1):
        if it > 0:
            if not pb.budget.ok(0.5, refit_frac):
                return None
            res = _fit_counts(pb, cats, counts, theta)
            if res is None:
                return None
            theta, N = res
            if _is_changed(pb, theta, pb.safety):
                return counts
            if it == _GREEDY_ITERS:
                return None
        D = float(theta[i] - theta[j]) + pb.tol + pb.safety
        D = max(D, pb.safety)
        v = _solve(_neg_hessian(N, theta, pb.ridge), c)
        eff = _category_effects(pb, cats, theta, v)
        cand, units, _ = _knapsack_units(eff, cats.avail - counts, D)
        if cand.size == 0:
            return None
        U = int(units.sum())
        take = U if U <= 4 else max(1, int(np.ceil(_DAMP * U)))
        before = np.cumsum(units) - units
        alloc = np.minimum(units, np.maximum(take - before, 0))
        counts[cand] += alloc
        if int(counts.sum()) > limit:
            return None
    return None


def _prune_counts(pb, cats, counts, i, j):
    """Remove surplus units from a feasible count vector using exact category-level refits."""
    res = _fit_counts(pb, cats, counts, pb.theta0)
    if res is None or not _is_changed(pb, res[0], pb.safety):
        return None
    theta, N = res
    counts = counts.copy()
    c = np.zeros(pb.p)
    c[i], c[j] = 1.0, -1.0

    def feasible(cv, warm):
        r = _fit_counts(pb, cats, cv, warm)
        if r is None or not _is_changed(pb, r[0], pb.safety):
            return None
        return r

    def weakest_first(theta_, N_):
        v = _solve(_neg_hessian(N_, theta_, pb.ridge), c)
        eff = _category_effects(pb, cats, theta_, v)
        nz = np.flatnonzero(counts > 0)
        return nz[np.argsort(-eff[nz], kind="stable")]

    # Step A: drop the largest prefix of weakest units that keeps the target changed.
    order = weakest_first(theta, N)
    units = counts[order]
    cu = np.cumsum(units)
    total = int(cu[-1]) if cu.size else 0

    def removed(m):
        cv = counts.copy()
        cv[order] -= np.minimum(units, np.maximum(m - (cu - units), 0))
        return cv

    lo, hi = 0, total
    while hi - lo > 1 and pb.budget.ok(0.7):
        mid = (lo + hi) // 2
        r = feasible(removed(mid), theta)
        if r is not None:
            lo = mid
        else:
            hi = mid
    if lo > 0:
        counts = removed(lo)
        r = feasible(counts, theta)
        if r is None:  # should not happen; keep the verified vector
            return None
        theta, N = r

    # Step B: per-category binary search of the largest removable count (single-unit test first).
    for _ in range(3):
        improved = False
        for k in weakest_first(theta, N):
            if not pb.budget.ok(0.7):
                return counts
            ck = int(counts[k])
            if ck <= 0:
                continue
            cv = counts.copy()
            cv[k] -= 1
            r = feasible(cv, theta)
            if r is None:
                continue
            best_d, best_r = 1, r
            if ck > 1:
                cv = counts.copy()
                cv[k] = 0
                r = feasible(cv, theta)
                if r is not None:
                    best_d, best_r = ck, r
                else:
                    lo, hi = 1, ck
                    while hi - lo > 1 and pb.budget.ok(0.7):
                        mid = (lo + hi) // 2
                        cv = counts.copy()
                        cv[k] -= mid
                        r = feasible(cv, theta)
                        if r is not None:
                            lo, best_r = mid, r
                        else:
                            hi = mid
                    best_d = lo
            counts[k] -= best_d
            theta, N = best_r
            improved = True
        if not improved:
            break
    return counts


def _candidate_pairs(pb, cats):
    """Rank (insider, outsider) boundary pairs by a first-order knapsack size at theta0."""
    p, k, order, theta0 = pb.p, pb.k, pb.order, pb.theta0
    ins = [int(x) for x in order[:k][::-1][:8]]
    n_out = 30 if k == 1 else 15
    outs = [int(x) for x in order[k:k + n_out]]
    Hinv = _solve(_neg_hessian(pb.N0, theta0, pb.ridge), np.eye(p))
    Hinv = 0.5 * (Hinv + Hinv.T)
    scored = []
    for i in ins:
        for j in outs:
            v = Hinv[:, i] - Hinv[:, j]
            eff = _category_effects(pb, cats, theta0, v)
            D = max(float(theta0[i] - theta0[j]) + pb.tol + pb.safety, pb.safety)
            cand, units, ok = _knapsack_units(eff, cats.avail, D)
            est = float(units.sum()) if ok else float("inf")
            scored.append((est, len(scored), i, j))
    scored.sort(key=lambda s: (s[0], s[1]))
    max_pairs = 8 if k == 1 else 12
    finite = [s for s in scored if np.isfinite(s[0])]
    rest = [s for s in scored if not np.isfinite(s[0])]
    chosen = (finite + rest)[:max_pairs]
    return [(i, j, est) for est, _, i, j in chosen]


def _materialize(cats, counts):
    nz = np.flatnonzero(counts > 0)
    if nz.size == 0:
        return np.zeros(0, dtype=np.int64)
    parts = [cats.rows[cats.start[k]:cats.start[k] + int(counts[k])] for k in nz]
    return np.sort(np.concatenate(parts)).astype(np.int64)


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
    if request["case_token"] != _STATE.get("case_token") or n_total != _STATE["n"]:
        raise ValueError("inconsistent chunk")
    m = request["player_a"]["shape"][0]
    lo = request["row_offset"]
    _STATE["a"][lo:lo + m] = _decode(request["player_a"], "int32", m)
    _STATE["b"][lo:lo + m] = _decode(request["player_b"], "int32", m)
    _STATE["y"][lo:lo + m] = _decode(request["outcome"], "float32", m)
    _STATE["loaded"].add(chunk)
    return {"ok": True}


def _propose(request):
    started = time.monotonic()
    if _STATE.get("loaded") != set(range(_STATE.get("n_chunks", -1))):
        raise ValueError("data not loaded")
    a, b, y, p = _STATE["a"], _STATE["b"], _STATE["y"], _STATE["p"]
    ridge, tol = float(request["estimator"]["ridge"]), float(request["estimator"]["tol"])
    drop = request["perturbation"] == "drop"
    k = 1 if request["target"]["type"] == "top1" else int(request["target"]["k"])
    max_size = int(request["max_size"])
    deadline = float(request["deadline_seconds"])
    empty = {"indices": _encode_int32(np.zeros(0, dtype=np.int64)),
             "diagnostics": {"refits": 0.0}}
    if p < 2 or k < 1 or k >= p or max_size <= 0:
        return empty
    S0, N0 = _pair_stats(p, a, b, y)
    theta0 = _fit(S0, N0, ridge)
    order = np.argsort(-theta0, kind="stable")
    top = np.zeros(p, dtype=bool)
    top[order[:k]] = True
    pb = SimpleNamespace(a=a, b=b, y=y, p=p, ridge=ridge, tol=tol, drop=drop, k=k,
                         max_size=max_size, S0=S0, N0=N0, theta0=theta0, order=order, top=top,
                         safety=_SAFETY_REL * (1.0 + abs(tol)),
                         budget=_Budget(started, deadline, p))

    # 1) Safe fallback: the starter's AMIP prefix search (exact starter criterion).
    baseline = _baseline_amip(pb)
    base_size = int(baseline.shape[0]) if baseline is not None else -1

    # 2) Relinearized knapsack greedy over category counts for several boundary pairs.
    cats = _build_categories(pb)
    diag = {"n_categories": float(cats.K), "baseline_size": float(base_size)}
    candidates = []
    pairs_tried = 0
    lin_lb = -1.0
    if cats.K > 0:
        pairs = _candidate_pairs(pb, cats)
        if pairs and np.isfinite(pairs[0][2]):
            lin_lb = float(pairs[0][2])
        for rank, (i, j, _) in enumerate(pairs):
            if not pb.budget.ok(0.5, 0.4):
                break
            pairs_tried += 1
            cnt = _relinearized_greedy(pb, cats, i, j, 0.4)
            if cnt is not None:
                candidates.append((int(cnt.sum()), rank, i, j, cnt))
        greedy_size = min([c[0] for c in candidates]) if candidates else -1
        # The baseline rows, expressed as category counts, are another pruning seed.
        if baseline is not None:
            cr = cats.cat_of_row[baseline]
            cr = cr[cr >= 0]
            bc = np.bincount(cr, minlength=cats.K).astype(np.int64)
            candidates.append((int(bc.sum()), len(pairs) + 1, int(order[k - 1]), int(order[k]),
                               bc))
        candidates.sort(key=lambda t: (t[0], t[1]))

        # 3) Exact pruning of the most promising feasible count vectors.
        finals = [(s, r, cv) for s, r, _, _, cv in candidates if r <= len(pairs)]
        pruned_best = -1
        for s, r, i, j, cv in candidates[:3]:
            if not pb.budget.ok(0.7):
                break
            pc = _prune_counts(pb, cats, cv, i, j)
            if pc is not None:
                ps = int(pc.sum())
                finals.append((ps, -1, pc))
                pruned_best = ps if pruned_best < 0 else min(pruned_best, ps)
        diag["greedy_size"] = float(greedy_size)
        diag["pruned_size"] = float(pruned_best)
    else:
        finals = []

    # 4) Materialize the smallest candidates, re-verify at row level with a safety margin.
    chosen, chosen_new = baseline, 0.0
    finals.sort(key=lambda t: (t[0], t[1]))
    tries = 0
    for s, _, cv in finals:
        if s <= 0 or s > max_size or (baseline is not None and s >= base_size):
            continue
        if tries >= 3 or pb.budget.elapsed() > 0.85 * deadline:
            break
        tries += 1
        idx = _materialize(cats, cv)
        # Category-level search demanded tol + safety; half of it absorbs warm-start differences.
        if _verify_rows(pb, idx, 0.5 * pb.safety):
            chosen, chosen_new = idx, 1.0
            break
    if chosen is None:
        chosen = np.zeros(0, dtype=np.int64)
    diag.update({"pairs_tried": float(pairs_tried), "linear_estimate": float(lin_lb),
                 "chosen_new": chosen_new, "final_size": float(chosen.shape[0]),
                 "refits": float(pb.budget.refits), "elapsed": float(pb.budget.elapsed())})
    diag = {key: (float(val) if np.isfinite(val) else -1.0) for key, val in diag.items()}
    return {"indices": _encode_int32(chosen), "diagnostics": diag}


def handle(request):
    op = request.get("op") if isinstance(request, dict) else None
    if op == "reset":
        return _reset(request)
    if op == "load_chunk":
        return _load_chunk(request)
    if op == "propose":
        return _propose(request)
    raise ValueError("unknown op")
