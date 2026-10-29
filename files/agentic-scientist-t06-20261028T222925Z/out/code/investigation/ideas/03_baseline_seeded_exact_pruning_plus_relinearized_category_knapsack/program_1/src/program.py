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

Method (baseline-seeded exact pruning plus relinearized category knapsack)
--------------------------------------------------------------------------
1. ``_baseline_amip``: the starter one-step influence (AMIP) prefix with exponential + binary
   search.  It is the fallback answer and seed A.
2. Rows are grouped into exchangeable categories: decisive rows by (winner, loser) (droppable or
   flippable), ties by unordered pair (drop only).  A perturbation is an integer count vector over
   categories; refits run on p x p sufficient statistics (``_stats_from_counts``).
3. ``_prune_baseline_seed``: the starter row set as a count vector, reduced by exact-refit pruning
   (``_prune_counts``: binary search over the weakest units, then single-unit removal passes).
4. ``_candidate_pairs`` + ``_relinearized_greedy``: for several (insider, outsider) boundary pairs,
   damped fractional-knapsack steps whose per-unit margin influence is recomputed at every exact
   refit; each feasible result is pruned.
5. ``_swap_refine``: 2-for-1 unit swaps on the best count vector, then re-pruning.
6. ``_verify_rows``: the smallest candidate that passes a row-level refit (warm and cold start)
   with a safety margin is returned; otherwise the starter set.
Effort is set by an integer refit cap (``_deterministic_refit_cap``); the wall clock is only an
emergency backstop.  No randomness is used.
"""
import base64
import math
import time

import numpy as np

_STATE = {}

_SAFETY = 1e-6          # relative safety margin on the target change (>= 1e-7 * (1 + |tol|))
_DAMPING = 0.65         # fraction of the first-order knapsack size taken per relinearized step
_KEEP_RECORDS = 6       # smallest feasible count vectors kept for row-level verification
_SRC_BASE, _SRC_SEED, _SRC_KNAP, _SRC_SWAP = 0, 1, 2, 3


class _Budget(Exception):
    """Raised when the refit cap of the current phase (or the emergency backstop) is reached."""


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
        step = _solve(hess, grad)
        t = 1.0
        while True:
            cand = theta + t * step
            cv = objective(cand)
            if cv >= value - 1e-12 * max(1.0, abs(value)) or t < 1e-10:
                break
            t *= 0.5
        theta, value = cand, cv
        if t < 1e-10:
            break  # line search stalled: at numerical precision
    return theta


def _solve(H, rhs):
    try:
        return np.linalg.solve(H, rhs)
    except np.linalg.LinAlgError:
        return np.linalg.lstsq(H, rhs, rcond=None)[0]


def _neg_hessian(N, theta, ridge):
    d = theta[:, None] - theta[None, :]
    prob = 1.0 / (1.0 + np.exp(-d))
    w = N * prob * (1.0 - prob)
    hess = -w
    hess[np.diag_indices(theta.shape[0])] += w.sum(axis=1) + ridge
    return hess


def _row_perturbed_stats(S0, N0, a, b, y, p, idx, drop):
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
    return np.maximum(S, 0.0), np.maximum(N, 0.0)


def _margin(theta, top, tol):
    """> 0 iff the target changed: max outsider beats min insider by more than tol."""
    return float(theta[~top].max()) - float(theta[top].min()) - tol


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


# ----------------------------------------------------------------------------------------------
# Starter one-shot AMIP prefix (fallback answer and seed A)
# ----------------------------------------------------------------------------------------------

def _baseline_amip(a, b, y, p, S0, N0, theta0, top, leader, challenger, ridge, tol, drop,
                   max_size, started, deadline):
    """Starter: rank rows by first-order effect on t_leader - t_challenger; smallest verifying
    prefix by exponential + binary search with exact row-level refits."""
    budget = 0.5 * deadline  # backstop only; the search is O(log n) refits

    def changed(idx):
        S, N = _row_perturbed_stats(S0, N0, a, b, y, p, idx, drop)
        theta = _fit(S, N, ridge, theta0)
        return float(theta[~top].max()) > float(theta[top].min()) + tol

    c = np.zeros(p)
    c[leader], c[challenger] = 1.0, -1.0
    v = _solve(_neg_hessian(N0, theta0, ridge), c)
    elig = np.arange(a.shape[0]) if drop else np.flatnonzero(y != 0.5)
    dv = v[a[elig]] - v[b[elig]]
    if drop:
        resid = y[elig] - 1.0 / (1.0 + np.exp(-(theta0[a[elig]] - theta0[b[elig]])))
        effect = -resid * dv
    else:
        effect = (1.0 - 2.0 * y[elig]) * dv
    ranked = elig[np.argsort(effect, kind="stable")]
    n = min(len(ranked), int(max_size))
    refits = 0
    best = None
    size, last_fail = 1, 0
    while n > 0 and time.monotonic() - started < budget:
        refits += 1
        if changed(ranked[:size]):
            best = size
            break
        last_fail = size
        if size >= n:
            break
        size = min(2 * size, n)
    if best is not None:
        lo, hi = last_fail, best
        while hi - lo > 1 and time.monotonic() - started < budget:
            mid = (lo + hi) // 2
            refits += 1
            if changed(ranked[:mid]):
                hi = mid
            else:
                lo = mid
        best = hi
    chosen = np.sort(ranked[:best]) if best is not None else np.zeros(0, dtype=np.int64)
    return chosen.astype(np.int64), refits


# ----------------------------------------------------------------------------------------------
# Exchangeable categories and count-vector refits
# ----------------------------------------------------------------------------------------------

def _build_categories(a, b, y, p, drop):
    """Decisive rows -> category (winner, loser); ties -> (lo, hi), drop only.  Self-pairs and
    non-standard outcomes are excluded.  Rows inside a category are kept in increasing index."""
    n = a.shape[0]
    pp = p * p
    distinct = a != b
    dec1 = (y == 1.0) & distinct
    dec0 = (y == 0.0) & distinct
    dec = dec1 | dec0
    tie = (y == 0.5) & distinct if drop else np.zeros(n, dtype=bool)
    w = np.where(dec0, b, a)
    l = np.where(dec0, a, b)
    lo = np.minimum(a, b)
    hi = np.maximum(a, b)
    code = np.full(n, -1, dtype=np.int64)
    code[dec] = (w * p + l)[dec]
    code[tie] = pp + (lo * p + hi)[tie]
    rows = np.flatnonzero(code >= 0).astype(np.int64)
    cat_of_row = np.full(n, -1, dtype=np.int64)
    if rows.size == 0:
        empty = np.zeros(0, dtype=np.int64)
        return {"cw": empty, "cl": empty, "tie": np.zeros(0, dtype=bool), "counts": empty,
                "rows_sorted": empty, "starts": empty, "cat_of_row": cat_of_row,
                "idx_wl": empty, "idx_lw": empty}
    uniq, inv, counts = np.unique(code[rows], return_inverse=True, return_counts=True)
    inv = np.asarray(inv, dtype=np.int64).reshape(-1)
    cat_tie = uniq >= pp
    base = np.where(cat_tie, uniq - pp, uniq)
    cw = (base // p).astype(np.int64)
    cl = (base % p).astype(np.int64)
    rows_sorted = rows[np.argsort(inv, kind="stable")]
    starts = np.concatenate(([0], np.cumsum(counts)[:-1])).astype(np.int64)
    cat_of_row[rows] = inv
    return {"cw": cw, "cl": cl, "tie": cat_tie, "counts": counts.astype(np.int64),
            "rows_sorted": rows_sorted, "starts": starts, "cat_of_row": cat_of_row,
            "idx_wl": cw * p + cl, "idx_lw": cl * p + cw}


def _stats_from_counts(x, cats, S0, N0, p, drop):
    """Sufficient statistics after dropping/flipping x[c] units of every category c."""
    nz = np.flatnonzero(x)
    xv = x[nz].astype(np.float64)
    i1, i2 = cats["idx_wl"][nz], cats["idx_lw"][nz]
    idx = np.concatenate((i1, i2))
    pp = p * p
    if drop:
        half = cats["tie"][nz]
        sw1 = np.where(half, -0.5 * xv, -xv)
        sw2 = np.where(half, -0.5 * xv, 0.0)
        dS = np.bincount(idx, weights=np.concatenate((sw1, sw2)), minlength=pp).reshape(p, p)
        dN = np.bincount(idx, weights=np.concatenate((-xv, -xv)), minlength=pp).reshape(p, p)
        S, N = S0 + dS, N0 + dN
    else:
        dS = np.bincount(idx, weights=np.concatenate((-xv, xv)), minlength=pp).reshape(p, p)
        S, N = S0 + dS, N0
    return np.maximum(S, 0.0), np.maximum(N, 0.0)


def _take(order, caps, m, size):
    """Count vector taking the first m units along `order`, at most caps[c] from category c."""
    out = np.zeros(size, dtype=np.int64)
    if m <= 0 or order.size == 0:
        return out
    c = caps[order]
    before = np.cumsum(c) - c
    out[order] = np.clip(m - before, 0, c)
    return out


def _knapsack(eff, rem, need):
    """Greedy fractional knapsack over helpful categories (eff < 0) with remaining capacity.
    Returns (order, units, reachable): units needed to lower the linearised gap by `need`."""
    cand = np.flatnonzero((eff < 0.0) & (rem > 0))
    if cand.size == 0:
        return None, 0, False
    o = cand[np.argsort(eff[cand], kind="stable")]
    gain = -eff[o] * rem[o]
    cg = np.cumsum(gain)
    kk = int(np.searchsorted(cg, need, side="left"))
    if kk >= o.size:
        return o, int(rem[o].sum()), False
    before_units = int(rem[o[:kk]].sum())
    before_gain = float(cg[kk - 1]) if kk > 0 else 0.0
    extra = int(math.ceil((need - before_gain) / float(-eff[o[kk]])))
    extra = min(max(extra, 0), int(rem[o[kk]]))
    return o, max(1, before_units + extra), True


class _Search:
    """Shared state of the category-level search: refit counter, budget, best feasible sets."""

    def __init__(self, cats, S0, N0, theta0, top, ridge, tol, drop, max_size, started, deadline):
        self.cats = cats
        self.cw, self.cl, self.ctie = cats["cw"], cats["cl"], cats["tie"]
        self.cap_counts = cats["counts"]
        self.ncat = int(self.cw.shape[0])
        self.S0, self.N0, self.theta0 = S0, N0, theta0
        self.p = int(theta0.shape[0])
        self.top = top
        self.top_idx = np.flatnonzero(top)
        self.out_idx = np.flatnonzero(~top)
        self.ridge, self.tol, self.drop = ridge, tol, drop
        self.safety = _SAFETY * (1.0 + abs(tol))
        self.max_size = int(max_size)
        self.started, self.deadline = started, deadline
        self.count = 0
        self.limit = 0
        self.emergency = False
        self.records = []
        self.seq = 0
        self.src_best = {_SRC_SEED: math.inf, _SRC_KNAP: math.inf, _SRC_SWAP: math.inf}
        self.baseline_size = math.inf

    def refit(self, x, warm):
        if self.count >= self.limit:
            raise _Budget()
        if time.monotonic() - self.started > 0.85 * self.deadline:
            self.emergency = True
            raise _Budget()
        self.count += 1
        S, N = _stats_from_counts(x, self.cats, self.S0, self.N0, self.p, self.drop)
        return _fit(S, N, self.ridge, warm), N

    def feasible(self, theta):
        if not np.all(np.isfinite(theta)):
            return False
        return _margin(theta, self.top, self.tol) > self.safety

    def boundary(self, theta):
        i = int(self.top_idx[int(np.argmin(theta[self.top_idx]))])
        j = int(self.out_idx[int(np.argmax(theta[self.out_idx]))])
        return i, j

    def direction(self, theta, N, i, j):
        c = np.zeros(self.p)
        c[i], c[j] = 1.0, -1.0
        return _solve(_neg_hessian(N, theta, self.ridge), c)

    def unit_effects(self, theta, v):
        """First-order change of the gap t_i - t_j from perturbing one more unit of each
        category, with v = H^{-1}(e_i - e_j) at the current fit."""
        dv = v[self.cw] - v[self.cl]
        if not self.drop:
            return -dv
        pw = 1.0 / (1.0 + np.exp(-(theta[self.cw] - theta[self.cl])))
        return np.where(self.ctie, (pw - 0.5) * dv, -(1.0 - pw) * dv)

    def best_known(self):
        best = self.baseline_size
        if self.records:
            best = min(best, self.records[0][0])
        return best

    def record(self, x, src, theta, N):
        size = int(x.sum())
        if size <= 0 or size > self.max_size:
            return
        if size < self.src_best.get(src, math.inf):
            self.src_best[src] = size
        if len(self.records) >= _KEEP_RECORDS and size >= self.records[-1][0]:
            return
        self.seq += 1
        self.records.append((size, self.seq, src, x.copy(), theta.copy(), N.copy()))
        self.records.sort(key=lambda r: (r[0], r[1]))
        del self.records[_KEEP_RECORDS:]


def _deterministic_refit_cap(n_categories, p, deadline):
    """Integer refit budget from problem size and the requested deadline (no clock reads)."""
    per_refit = 2.0e-3 + 2.5e-6 * p * p + 2.0e-7 * n_categories  # conservative seconds/refit
    cap = int(0.35 * max(float(deadline), 0.0) / per_refit)
    return max(40, min(5000, cap))


def _prune_counts(ctx, x, theta, N, src):
    """Exact-refit pruning of a feasible count vector: binary search over the weakest units
    (current-fit influence), then single-unit removal passes."""
    x = x.copy()
    i, j = ctx.boundary(theta)
    eff = ctx.unit_effects(theta, ctx.direction(theta, N, i, j))
    nz = np.flatnonzero(x > 0)
    o = nz[np.argsort(-eff[nz], kind="stable")]  # weakest (least helpful) first
    lo, hi = 0, int(x.sum())
    best_theta, best_N = theta, N
    while hi - lo > 1:
        mid = (lo + hi) // 2
        xt = x - _take(o, x, mid, ctx.ncat)
        th, Nt = ctx.refit(xt, theta)
        if ctx.feasible(th):
            lo, best_theta, best_N = mid, th, Nt
            ctx.record(xt, src, th, Nt)
        else:
            hi = mid
    if lo > 0:
        x = x - _take(o, x, lo, ctx.ncat)
        theta, N = best_theta, best_N
    while int(x.sum()) > 1:
        i, j = ctx.boundary(theta)
        eff = ctx.unit_effects(theta, ctx.direction(theta, N, i, j))
        nz = np.flatnonzero(x > 0)
        o = nz[np.argsort(-eff[nz], kind="stable")]
        improved = False
        for c in o:
            if int(x.sum()) <= 1:
                break
            xt = x.copy()
            xt[c] -= 1
            th, Nt = ctx.refit(xt, theta)
            if ctx.feasible(th):
                x, theta, N = xt, th, Nt
                ctx.record(x, src, theta, N)
                improved = True
        if not improved:
            break
    return x, theta, N


def _prune_baseline_seed(ctx, base_rows):
    """Seed A: the starter AMIP row set as a category count vector, pruned by exact refits."""
    if base_rows.size == 0:
        return
    cid = ctx.cats["cat_of_row"][base_rows]
    cid = cid[cid >= 0]
    if cid.size == 0:
        return
    x = np.bincount(cid, minlength=ctx.ncat).astype(np.int64)
    theta, N = ctx.refit(x, ctx.theta0)
    if not ctx.feasible(theta):
        return
    ctx.record(x, _SRC_SEED, theta, N)
    _prune_counts(ctx, x, theta, N, _SRC_SEED)


def _candidate_pairs(ctx, n_keep, starter_pair):
    """Boundary (insider, outsider) pairs ranked by first-order knapsack size at theta0; the
    starter pair is always included."""
    th = ctx.theta0
    H = _neg_hessian(ctx.N0, th, ctx.ridge)
    try:
        Hinv = np.linalg.inv(H)
    except np.linalg.LinAlgError:
        Hinv = np.linalg.pinv(H)
    ins = ctx.top_idx[np.argsort(th[ctx.top_idx], kind="stable")][:6]
    outs = ctx.out_idx[np.argsort(-th[ctx.out_idx], kind="stable")][:12]
    scored = []
    for i in ins:
        for j in outs:
            v = Hinv[:, i] - Hinv[:, j]
            eff = ctx.unit_effects(th, v)
            need = float(th[i] - th[j]) + ctx.tol + 2.0 * ctx.safety
            o, units, ok = _knapsack(eff, ctx.cap_counts, need)
            score = float(units) if (o is not None and ok) else math.inf
            scored.append((score, len(scored), int(i), int(j)))
    scored.sort()
    keep = []
    for score, seq, i, j in scored:
        if (i, j) == starter_pair:
            keep.append((score, seq, i, j))
        elif len([1 for r in keep if (r[2], r[3]) != starter_pair]) < n_keep - 1 \
                and math.isfinite(score):
            keep.append((score, seq, i, j))
    if not any((r[2], r[3]) == starter_pair for r in keep):
        keep.append((math.inf, len(scored), starter_pair[0], starter_pair[1]))
    keep.sort()
    return [(r[2], r[3]) for r in keep]


def _relinearized_greedy(ctx, i, j):
    """Damped fractional-knapsack steps on the gap t_i - t_j, relinearising the per-unit
    influence at every exact refit; the first feasible vector is pruned."""
    x = np.zeros(ctx.ncat, dtype=np.int64)
    theta, N = ctx.theta0, ctx.N0
    while True:
        lim = ctx.max_size
        best = ctx.best_known()
        if math.isfinite(best):
            lim = min(lim, int(1.3 * best + 3))
        eff = ctx.unit_effects(theta, ctx.direction(theta, N, i, j))
        need = float(theta[i] - theta[j]) + ctx.tol + 2.0 * ctx.safety
        rem = ctx.cap_counts - x
        o, units, _ = _knapsack(eff, rem, need)
        if o is None:
            return None
        step = max(1, int(math.ceil(_DAMPING * units)))
        x = x + _take(o, rem, step, ctx.ncat)
        if int(x.sum()) > lim:
            return None
        theta, N = ctx.refit(x, theta)
        if not np.all(np.isfinite(theta)):
            return None
        if ctx.feasible(theta):
            ctx.record(x, _SRC_KNAP, theta, N)
            return _prune_counts(ctx, x, theta, N, _SRC_KNAP)


def _swap_refine(ctx, x, theta, N, width=6, max_tries=24):
    """2-for-1 unit swaps (remove two weak units, add one strong unit) ordered by the linear
    change of the boundary gap; every accepted swap is followed by re-pruning."""
    while int(x.sum()) >= 2:
        i, j = ctx.boundary(theta)
        eff = ctx.unit_effects(theta, ctx.direction(theta, N, i, j))
        gap = float(theta[i] - theta[j]) + ctx.tol
        nz = np.flatnonzero(x > 0)
        weak = nz[np.argsort(-eff[nz], kind="stable")][:width]
        rem = ctx.cap_counts - x
        free = np.flatnonzero((rem > 0) & (eff < 0.0))
        strong = free[np.argsort(eff[free], kind="stable")][:width]
        cands = []
        for ai in range(weak.size):
            for bi in range(ai, weak.size):
                c1, c2 = int(weak[ai]), int(weak[bi])
                if c1 == c2 and x[c1] < 2:
                    continue
                for d in strong:
                    d = int(d)
                    if d == c1 or d == c2:
                        continue
                    pred = gap - float(eff[c1]) - float(eff[c2]) + float(eff[d])
                    cands.append((pred, len(cands), c1, c2, d))
        cands.sort()
        accepted = False
        for _, _, c1, c2, d in cands[:max_tries]:
            xt = x.copy()
            xt[c1] -= 1
            xt[c2] -= 1
            xt[d] += 1
            th, Nt = ctx.refit(xt, theta)
            if ctx.feasible(th):
                ctx.record(xt, _SRC_SWAP, th, Nt)
                x, theta, N = _prune_counts(ctx, xt, th, Nt, _SRC_SWAP)
                accepted = True
                break
        if not accepted:
            break
    return x, theta, N


def _materialize(cats, x):
    """Rows for a count vector: the lowest row indices of each category (deterministic)."""
    nz = np.flatnonzero(x > 0)
    if nz.size == 0:
        return np.zeros(0, dtype=np.int64)
    starts, rows_sorted = cats["starts"], cats["rows_sorted"]
    parts = [rows_sorted[starts[c]:starts[c] + int(x[c])] for c in nz]
    return np.sort(np.concatenate(parts)).astype(np.int64)


def _verify_rows(a, b, y, p, S0, N0, theta0, rows, drop, ridge, top, tol, safety, max_size):
    """Row-level re-verification (warm and cold start) with a safety margin."""
    if rows.size == 0 or rows.size > max_size:
        return False
    if rows.size != np.unique(rows).size:
        return False
    S, N = _row_perturbed_stats(S0, N0, a, b, y, p, rows, drop)
    for warm in (theta0, None):
        th = _fit(S, N, ridge, warm)
        if not np.all(np.isfinite(th)) or not _margin(th, top, tol) > safety:
            return False
    return True


def _improve(ctx, base_rows, starter_pair):
    cap = _deterministic_refit_cap(ctx.ncat, ctx.p, ctx.deadline)
    # Phase 1 (guaranteed first): exact pruning of the starter seed.
    ctx.limit = max(1, int(0.4 * cap))
    try:
        _prune_baseline_seed(ctx, base_rows)
    except _Budget:
        pass
    n_pairs = 0
    # Phase 2: relinearized multi-pair knapsack with pruning.
    if not ctx.emergency and ctx.count < cap:
        phase_end = ctx.count + int(0.8 * (cap - ctx.count))
        pairs = _candidate_pairs(ctx, max(2, min(6, cap // 150)), starter_pair)
        n_pairs = len(pairs)
        for t, (i, j) in enumerate(pairs):
            if ctx.emergency or ctx.count >= phase_end:
                break
            ctx.limit = ctx.count + max(1, (phase_end - ctx.count) // (len(pairs) - t))
            try:
                _relinearized_greedy(ctx, i, j)
            except _Budget:
                pass
    # Phase 3: 2-for-1 swap refinement of the best vector.
    if not ctx.emergency and ctx.records and ctx.count < cap:
        ctx.limit = cap
        _, _, _, x, theta, N = ctx.records[0]
        try:
            _swap_refine(ctx, x, theta, N)
        except _Budget:
            pass
    return cap, n_pairs


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
    S0, N0 = _pair_stats(p, a, b, y)
    theta0 = _fit(S0, N0, ridge)
    order = np.argsort(-theta0, kind="stable")
    top = np.zeros(p, dtype=bool)
    top[order[:k]] = True
    leader, challenger = int(order[k - 1]), int(order[k])

    base_rows, base_refits = _baseline_amip(a, b, y, p, S0, N0, theta0, top, leader, challenger,
                                            ridge, tol, drop, max_size, started, deadline)
    chosen, source = base_rows, _SRC_BASE
    diag = {"baseline_size": float(base_rows.size), "baseline_refits": float(base_refits),
            "seed_prune_size": -1.0, "knapsack_size": -1.0, "swap_size": -1.0,
            "refits": 0.0, "refit_cap": 0.0, "n_categories": 0.0, "n_pairs": 0.0,
            "emergency": 0.0, "search_error": 0.0, "verify_failures": 0.0}
    safety = _SAFETY * (1.0 + abs(tol))
    try:
        if max_size > 0 and _margin(theta0, top, tol) <= 0.0:
            cats = _build_categories(a, b, y, p, drop)
            ctx = _Search(cats, S0, N0, theta0, top, ridge, tol, drop, max_size, started,
                          deadline)
            diag["n_categories"] = float(ctx.ncat)
            if ctx.ncat > 0:
                if base_rows.size > 0:
                    ctx.baseline_size = int(base_rows.size)
                cap, n_pairs = _improve(ctx, base_rows, (leader, challenger))
                diag["refits"], diag["refit_cap"] = float(ctx.count), float(cap)
                diag["n_pairs"], diag["emergency"] = float(n_pairs), float(ctx.emergency)
                for key, src in (("seed_prune_size", _SRC_SEED), ("knapsack_size", _SRC_KNAP),
                                 ("swap_size", _SRC_SWAP)):
                    if math.isfinite(ctx.src_best[src]):
                        diag[key] = float(ctx.src_best[src])
                limit = int(base_rows.size) if base_rows.size > 0 else max_size + 1
                failures = 0
                for size, _, src, x, _, _ in ctx.records:
                    if size >= limit or time.monotonic() - started > 0.92 * deadline:
                        break
                    rows = _materialize(cats, x)
                    if _verify_rows(a, b, y, p, S0, N0, theta0, rows, drop, ridge, top, tol,
                                    safety, max_size):
                        chosen, source = rows, src
                        break
                    failures += 1
                diag["verify_failures"] = float(failures)
    except Exception:  # never let the search break the (verified) starter answer
        chosen, source = base_rows, _SRC_BASE
        diag["search_error"] = 1.0
    diag["final_size"] = float(chosen.size)
    diag["chosen_source"] = float(source)
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
