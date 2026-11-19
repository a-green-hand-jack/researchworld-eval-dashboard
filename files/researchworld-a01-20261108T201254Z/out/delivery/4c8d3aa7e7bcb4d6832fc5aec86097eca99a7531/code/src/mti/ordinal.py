"""Minimum targeted investment under rank-based rules (Borda / mean rank, Condorcet-winner, plurality).

Same setting as scorerules: target i raises y_t in [x_t, c_t]; others fixed; strict improvement uses eps.
A task-level raise to level s+eps passes every model with score <= s on that task. Ties count 1/2.
Exact via MILP (scipy/HiGHS), with lazily generated rival constraints.
"""
import time
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import csr_matrix, lil_matrix
from scipy.stats import rankdata

INF = np.inf
TIME_LIMIT = 120.0     # seconds per MILP solve (HiGHS); a solve that hits it is CENSORED, never reported as infeasible
MIP_REL_GAP = 1e-9     # HiGHS default is 1e-4; tightened so "optimal" means optimal to numerical tolerance
TIE_LEVELS = True      # False: the target never *ties* a rival's score to gain half credit; it may only pass it by eps (eps/ties sensitivity)


def borda_points(X):
    """(M,) total Borda points: per task, #models strictly below + 0.5 * #ties (self excluded)."""
    return sum(rankdata(X[:, t], method="average") - 1 for t in range(X.shape[1]))


def wins(y, s):
    """pairwise outcome of score y vs array s : 1 / .5 / 0"""
    return (y > s) * 1.0 + (y == s) * 0.5


def _levels(X, i, t, c_t, eps):
    x = X[i, t]; others = np.delete(X[:, t], i)
    u = np.unique(others[others >= x])
    cand = np.unique(np.concatenate([u[u > x], u + eps]) if TIE_LEVELS else u + eps)      # tie with s (half credit) or strictly pass s
    cand = cand[(cand <= c_t + 1e-12)]
    # a level only helps if it passes someone new; every candidate does (it passes the model(s) at s)
    return cand


def _build(X, i, cap, eps):
    M, n = X.shape; x = X[i]; c = np.maximum(np.asarray(cap, float), x)
    others = np.array([j for j in range(M) if j != i])
    L = []   # list of (t, level)
    for t in range(n):
        for l in _levels(X, i, t, c[t], eps): L.append((t, l))
    tl = np.array([t for t, _ in L], int); lv = np.array([l for _, l in L], float)
    cost = lv - x[tl]
    # delta w_{j,k} = w(level_k, X_j,t_k) - w(x_t, X_j,t_k) for all other models j
    # float32 (values are multiples of 0.5, exact) and built in column chunks: dense (M-1, K) is the memory bottleneck for low-ranked targets
    dW = np.empty((len(others), len(tl)), np.float32)
    Xo = X[others]
    for a in range(0, len(tl), 2000):
        sl = slice(a, a + 2000); O = Xo[:, tl[sl]]
        dW[:, sl] = wins(lv[None, sl], O) - wins(x[tl[sl]][None, :], O)
    return others, tl, lv, cost, dW


def _solve(cost_vec, A_rows, lo, tl, n, objective, cost, time_limit=None):
    time_limit = TIME_LIMIT if time_limit is None else time_limit
    K = len(cost_vec)
    # variables z_k (K), plus for objective K: r_t (n) indicates task raised
    nv = K + (n if objective == "K" else 0)
    c = np.zeros(nv)
    if objective == "K": c[K:] = 1
    else: c[:K] = cost
    cons = []
    # at most one level per task
    S = lil_matrix((n, nv))
    for k, t in enumerate(tl): S[t, k] = 1
    cons.append(LinearConstraint(csr_matrix(S), -np.inf, 1))
    if objective == "K":
        S2 = lil_matrix((n, nv))
        for k, t in enumerate(tl): S2[t, k] = 1
        for t in range(n): S2[t, K + t] = -1
        cons.append(LinearConstraint(csr_matrix(S2), -np.inf, 0))
    if A_rows is not None and len(lo):
        A = np.zeros((A_rows.shape[0], nv)); A[:, :K] = A_rows
        cons.append(LinearConstraint(csr_matrix(A), lo, np.inf))
    ub = np.ones(nv)
    res = milp(c, constraints=cons, integrality=np.ones(nv), bounds=Bounds(np.zeros(nv), ub),
               options={"time_limit": time_limit, "mip_rel_gap": MIP_REL_GAP})
    return res


def _dual(res):
    b = getattr(res, "mip_dual_bound", None)
    return np.nan if b is None else float(b)


def _fill(info, status, lb=np.nan, ub=np.nan, t0=None, rounds=0):
    if info is not None:
        info.update(status=status, lb=lb, ub=ub, rounds=rounds, secs=(time.time() - t0) if t0 else np.nan)


def _lazy(X, i, cap, eps, objective, rival_rows_fn, init_active, max_rounds=60, info=None):
    """rival_rows_fn(others, dW) -> (use_G, rhs (M-1,)): constraint set (G*use_G + dW) z >= rhs for all rivals, G = column sums of dW
    (rows are materialised only for the active set, so memory stays at one float32 (M-1, K) matrix).
    Returns the minimum (float); INF only if PROVEN infeasible; NaN if the solve was censored (time limit / round limit).
    `info` (dict) receives status in {opt, infeasible, censored}, lb/ub (bounds on the minimum when censored) and wall seconds."""
    t0 = time.time()
    M, n = X.shape
    others, tl, lv, cost, dW = _build(X, i, cap, eps)
    K = len(tl)
    use_G, rhs_full = rival_rows_fn(others, dW)
    G = dW.sum(axis=0, dtype=np.float64) if use_G else 0.0
    def rows_of(idx): return dW[idx].astype(np.float64) + G
    def lhs(z): return dW @ z.astype(np.float32) + (G @ z if use_G else 0.0)
    active = set(init_active)
    for rnd in range(max_rounds):
        idx = np.array(sorted(active), int)
        if K == 0:
            viol = np.where(rhs_full > 1e-9)[0]
            _fill(info, "infeasible" if len(viol) else "opt", t0=t0)
            return INF if len(viol) else 0.0
        res = _solve(cost, rows_of(idx) if len(idx) else None, rhs_full[idx] if len(idx) else [], tl, n, objective, cost)
        if res.status == 2:                       # relaxation (subset of rivals) proven infeasible => full problem infeasible
            _fill(info, "infeasible", t0=t0, rounds=rnd + 1); return INF
        if res.status == 1:                       # time limit: dual bound of the relaxation is a valid lower bound of the full problem
            ub = np.nan
            if res.x is not None:
                z = np.round(res.x[:K])
                if (lhs(z) >= rhs_full - 1e-4).all(): ub = float(res.fun)
            _fill(info, "censored", lb=_dual(res), ub=ub, t0=t0, rounds=rnd + 1)
            return np.nan
        if res.status != 0: raise RuntimeError(f"HiGHS status {res.status}: {res.message}")
        z = np.round(res.x[:K])
        slack = lhs(z) - rhs_full
        viol = np.where(slack < -1e-4)[0]
        if len(viol) == 0:
            _fill(info, "opt", lb=float(res.fun), ub=float(res.fun), t0=t0, rounds=rnd + 1)
            return float(res.fun)
        active |= set(viol[np.argsort(slack[viol])][:25].tolist())
    _fill(info, "censored", lb=float(res.fun), t0=t0, rounds=max_rounds)     # round limit; res.fun is a valid lower bound
    return np.nan


# ---------------------------------------------------------------- Borda
def borda_min_investment(X, i, cap, eps=1e-3, objective="L1", info=None):
    """Smallest investment so that target has strictly the highest Borda total (mean rank)."""
    B = borda_points(X)
    M, n = X.shape
    if B[i] > np.delete(B, i).max(): _fill(info, "opt", 0, 0); return 0.0
    def rows(others, dW):
        # A = G + dW: total pairwise points gained by the target + rival j's loss
        rhs = (B[others] - B[i]) + 0.5                 # need B_i - B_j >= 0.5 (half-point granularity)
        return True, rhs
    top = np.argsort(-B[others_idx(M, i)])[:5]
    return _lazy(X, i, cap, eps, objective, rows, top, info=info)


def others_idx(M, i): return np.array([j for j in range(M) if j != i])


# ---------------------------------------------------------------- Condorcet winner (beats every rival in a strict task-majority)
def condorcet_min_investment(X, i, cap, eps=1e-3, objective="L1", info=None):
    M, n = X.shape; x = X[i]
    others = others_idx(M, i)
    W0 = wins(x[None, :], X[others]).sum(axis=1)       # target's pairwise wins vs each rival
    need = n / 2 + 0.5 - W0
    if (need <= 0).all(): _fill(info, "opt", 0, 0); return 0.0
    def rows(oth, dW): return False, need
    order = np.argsort(-need)[:5]
    return _lazy(X, i, cap, eps, objective, rows, order, info=info)


# ---------------------------------------------------------------- plurality (first-place count, ties split)
def plurality_min_investment(X, i, cap, eps=1e-3, objective="L1", info=None):
    M, n = X.shape; x = X[i]; c = np.maximum(np.asarray(cap, float), x)
    mx = X.max(axis=0)
    ties = (X == mx[None, :]); share = ties / ties.sum(axis=0)[None, :]      # (M,n) credit
    w = share.sum(axis=0) if False else share.sum(axis=1)                       # first-place credit per model
    if w[i] > np.delete(w, i).max() + 1e-12: _fill(info, "opt", 0, 0); return 0.0
    others = others_idx(M, i)
    # per task two options: tie the best rival score (level mo, credit shared) or beat it (level mo+eps, full credit)
    mo = np.array([np.delete(X[:, t], i).max() for t in range(n)])
    m_tied = np.array([(np.delete(X[:, t], i) == mo[t]).sum() for t in range(n)])
    Wt = X[others] == mo[None, :]
    # option arrays (2n): index t -> tie, n+t -> win
    lvl = np.concatenate([mo, mo + eps])
    feas = np.concatenate([(mo > x) & (mo <= c + 1e-12) & TIE_LEVELS, (mo + eps <= c + 1e-12) & True])
    cur_i = share[i]                                                          # target's current credit on t
    new_i = np.concatenate([1.0 / (m_tied + 1), np.ones(n)])
    gain_i = np.where(x[None, :] >= lvl.reshape(2, n), 0.0, 1.0).reshape(2, n)  # placeholder, replaced below
    gain_i = new_i - np.tile(cur_i, 2)
    already = np.tile(x, 2) >= lvl
    gain_i = np.where(already, 0.0, gain_i)
    loss = np.concatenate([share[others] - Wt / (m_tied + 1)[None, :] * 1.0, share[others]], axis=1)
    loss = np.where(already[None, :], 0.0, loss)
    cost = np.where(already, 0.0, lvl - np.tile(x, 2))
    A = gain_i[None, :] + loss
    rhs = (w[others] - w[i]) + 1e-4   # credits are rationals with denominators <= M; 1e-4 >> MILP tolerance
    cons = [LinearConstraint(A, rhs, np.inf)]
    one = np.zeros((n, 2 * n)); one[np.arange(n), np.arange(n)] = 1; one[np.arange(n), n + np.arange(n)] = 1
    cons.append(LinearConstraint(one, -np.inf, 1))
    ub = feas.astype(float)
    cvec = (cost if objective == "L1" else (cost > 0).astype(float))
    t0 = time.time()
    res = milp(cvec, constraints=cons, integrality=np.ones(2 * n), bounds=Bounds(np.zeros(2 * n), ub),
               options={"time_limit": TIME_LIMIT, "mip_rel_gap": MIP_REL_GAP})
    if res.status == 0: _fill(info, "opt", res.fun, res.fun, t0); return float(res.fun)
    if res.status == 2: _fill(info, "infeasible", t0=t0); return INF
    if res.status == 1: _fill(info, "censored", lb=_dual(res), t0=t0); return np.nan
    raise RuntimeError(f"HiGHS status {res.status}: {res.message}")


# ---------------------------------------------------------------- simulation helpers (for bisection on Linf and for tests)
def borda_first(X): B = borda_points(X); return B.argmax() if (B == B.max()).sum() == 1 else -1
def condorcet_winner(X):
    M, n = X.shape
    for j in range(M):
        if all(wins(X[j], X[k]).sum() > n / 2 for k in range(M) if k != j): return j
    return -1
def plurality_first(X):
    mx = X.max(axis=0); ties = (X == mx[None, :]); w = (ties / ties.sum(axis=0)[None, :]).sum(axis=1)
    return w.argmax() if (w >= w.max() - 1e-12).sum() == 1 else -1

FIRST = {"borda": borda_first, "condorcet": condorcet_winner, "plurality": plurality_first}
MIN_INV = {"borda": borda_min_investment, "condorcet": condorcet_min_investment, "plurality": plurality_min_investment}


def linf_ordinal(rule, X, i, cap, eps=1e-3):
    """Exact min over d of the largest single-task jump, on the same discrete level set as the MILP
    (tie with a rival's score, or pass it by eps): the target's score on t is snapped down to the highest level <= x_t + d."""
    M, n = X.shape; x = X[i]; c = np.maximum(np.asarray(cap, float), x); f = FIRST[rule]
    levels = [_levels(X, i, t, c[t], eps) for t in range(n)]
    if f(X) == i: return 0.0
    ds = np.unique(np.concatenate([l - x[t] for t, l in enumerate(levels)])) if any(len(l) for l in levels) else np.array([])
    def ok(d):
        Y = X.copy()
        for t in range(n):
            L = levels[t][levels[t] <= x[t] + d + 1e-12]
            if len(L): Y[i, t] = L.max()
        return f(Y) == i
    if len(ds) == 0 or not ok(ds[-1]): return INF
    lo, hi = -1, len(ds) - 1                      # ok(ds[hi]) true; find the smallest index
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(ds[mid]): hi = mid
        else: lo = mid
    return float(ds[hi])


def min_investment_ordinal(rule, X, i, cap, eps=1e-3, measures=("L1", "K", "Linf")):
    """dict with L1, K, Linf (INF = proven infeasible, NaN = censored by the solver time limit) and per-measure
    `<m>_status` in {opt, infeasible, censored}, `<m>_lb`/`<m>_ub` (bounds on the minimum), `<m>_secs`."""
    out = {}
    for m in ("L1", "K"):
        if m in measures:
            info = {}; out[m] = MIN_INV[rule](X, i, cap, eps, m, info=info)
            out.update({f"{m}_status": info["status"], f"{m}_lb": info["lb"], f"{m}_ub": info["ub"], f"{m}_secs": info["secs"]})
    if "Linf" in measures:
        t0 = time.time(); v = linf_ordinal(rule, X, i, cap, eps)
        out.update(Linf=v, Linf_status="infeasible" if np.isinf(v) else "opt", Linf_secs=time.time() - t0)
    return out
