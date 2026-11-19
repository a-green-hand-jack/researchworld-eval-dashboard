"""Minimum targeted investment under rank-based rules (Borda / mean rank, Condorcet-winner, plurality).

Same setting as scorerules except for the meaning of eps: target i raises y_t in [x_t, c_t]; others fixed.
Feasible set (one for L1, K and Linf, and for FIRST/linf_ordinal): every comparison is a plain strict one, y > s is a win, y == s a
tie (1/2), "first" means a strictly largest total; there is no margin, ordinal outcomes depend on the order only. Because a strict
win is an open condition, the minimum L1 is an infimum; the solvers return the cost of an explicit witness raise in which every
raised task goes either to a rival's score s (tie) or to min(s + eps, c_t) with c_t > s (strictly above s, at most eps above it).
Hence feasibility and K are exact for continuous raises, and the true infimum of L1 lies in [L1 - n*eps, L1] (n = number of tasks:
rounding a continuous raise down to the witness level of its cell costs less than eps per raised task; the K of a witness is not a
valid count for this bound, since the optimal witness may differ from the infimum's allocation). Linf (bisection on
FIRST, tol 1e-6) is the infimum itself. eps is therefore only a witness granularity here (default 1e-3), not a required margin.
Exact via MILP (scipy/HiGHS), with lazily generated rival constraints.
"""
import math
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import csr_matrix, lil_matrix
from scipy.stats import rankdata

INF = np.inf


def borda_points(X):
    """(M,) total Borda points: per task, #models strictly below + 0.5 * #ties (self excluded)."""
    return sum(rankdata(X[:, t], method="average") - 1 for t in range(X.shape[1]))


def wins(y, s):
    """pairwise outcome of score y vs array s : 1 / .5 / 0"""
    return (y > s) * 1.0 + (y == s) * 0.5


def _levels(X, i, t, c_t, eps):
    x = X[i, t]; others = np.delete(X[:, t], i)
    u = np.unique(others[others >= x])
    ties = u[(u > x) & (u <= c_t)]                              # tie with s (half credit)
    above = np.minimum(u + eps, c_t)[u < c_t]                   # strictly above s, within the cap (witness at most eps above s)
    return np.unique(np.concatenate([ties, above]))


def _build(X, i, cap, eps):
    M, n = X.shape; x = X[i]; c = np.maximum(np.asarray(cap, float), x)
    others = np.array([j for j in range(M) if j != i])
    L = []   # list of (t, level)
    for t in range(n):
        for l in _levels(X, i, t, c[t], eps): L.append((t, l))
    tl = np.array([t for t, _ in L], int); lv = np.array([l for _, l in L], float)
    cost = lv - x[tl]
    # delta w_{j,k} = w(level_k, X_j,t_k) - w(x_t, X_j,t_k) for all other models j
    O = X[others][:, tl]                       # (M-1, K)
    dW = wins(lv[None, :], O) - wins(x[tl][None, :], O)
    return others, tl, lv, cost, dW


PLURALITY_MAX_CUTS = 500
PLURALITY_LATTICE_MAX = 10**6
TIME_LIMIT = 120   # seconds per MILP; a run that hits it is reported as NaN (censored), never as infeasible


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
               options={"time_limit": time_limit})
    return res


def _out(v, y, return_y):
    """return_y: also return an optimal raise vector (None when infeasible / censored / nothing to raise)."""
    return (v, y) if return_y else v


def _lazy(X, i, cap, eps, objective, rival_rows_fn, init_active, max_rounds=60, return_y=False):
    """rival_rows_fn(others, dW, G) -> (A (M-1,K), rhs (M-1,)) full constraint set A z >= rhs for all rivals."""
    M, n = X.shape
    others, tl, lv, cost, dW = _build(X, i, cap, eps)
    K = len(tl)
    A_full, rhs_full = rival_rows_fn(others, dW)
    # rows with rhs<=0 are satisfied by z=0 but may be violated later (rival loses points only; rhs<=0 stays satisfied only if A>=0)
    active = set(init_active)
    for _ in range(max_rounds):
        idx = np.array(sorted(active), int)
        if K == 0:
            res = None; z = np.zeros(0)
            viol = np.where(rhs_full > 1e-9)[0]
            return _out(INF if len(viol) else 0.0, None, return_y)
        res = _solve(cost, A_full[idx] if len(idx) else None, rhs_full[idx] if len(idx) else [], tl, n, objective, cost)
        if res.status == 1: return _out(np.nan, None, return_y)          # time limit: censored
        if not res.success: return _out(INF, None, return_y)             # proven infeasible
        z = np.round(res.x[:K])
        viol = np.where(A_full @ z < rhs_full - 1e-9)[0]
        if len(viol) == 0:
            y = X[i].copy()
            for k in np.where(z > 0.5)[0]: y[tl[k]] = lv[k]
            return _out(float(res.fun), y, return_y)
        active |= set(viol[np.argsort(-(rhs_full[viol] - A_full[viol] @ z))][:25].tolist())
    raise RuntimeError("lazy constraint loop did not converge")


# ---------------------------------------------------------------- Borda
def borda_min_investment(X, i, cap, eps=1e-3, objective="L1", return_y=False):
    """Smallest investment so that target has strictly the highest Borda total (mean rank)."""
    B = borda_points(X)
    M, n = X.shape
    if B[i] > np.delete(B, i).max(): return _out(0.0, X[i].copy(), return_y)
    def rows(others, dW):
        G = dW.sum(axis=0)[None, :]                    # total pairwise points gained by target
        A = G + dW                                     # target gain + rival j's loss
        rhs = (B[others] - B[i]) + 0.5                 # need B_i - B_j >= 0.5 (half-point granularity)
        return A, rhs
    top = np.argsort(-B[others_idx(M, i)])[:5]
    return _lazy(X, i, cap, eps, objective, rows, top, return_y=return_y)


def others_idx(M, i): return np.array([j for j in range(M) if j != i])


# ---------------------------------------------------------------- Condorcet winner (beats every rival in a strict task-majority)
def condorcet_min_investment(X, i, cap, eps=1e-3, objective="L1", return_y=False):
    M, n = X.shape; x = X[i]
    others = others_idx(M, i)
    W0 = wins(x[None, :], X[others]).sum(axis=1)       # target's pairwise wins vs each rival
    need = n / 2 + 0.5 - W0
    if (need <= 0).all(): return _out(0.0, X[i].copy(), return_y)
    def rows(oth, dW): return dW, need
    order = np.argsort(-need)[:5]
    return _lazy(X, i, cap, eps, objective, rows, order, return_y=return_y)


# ---------------------------------------------------------------- plurality (first-place count, ties split)
def plurality_min_investment(X, i, cap, eps=1e-3, objective="L1", return_y=False):
    M, n = X.shape; x = X[i]; c = np.maximum(np.asarray(cap, float), x)
    mx = X.max(axis=0)
    ties = (X == mx[None, :]); share = ties / ties.sum(axis=0)[None, :]      # (M,n) credit
    w = share.sum(axis=0) if False else share.sum(axis=1)                       # first-place credit per model
    if plurality_first(X) == i: return _out(0.0, x.copy(), return_y)
    others = others_idx(M, i)
    # per task two options: tie the best rival score (level mo, credit shared) or beat it (level mo+eps, full credit)
    mo = np.array([np.delete(X[:, t], i).max() for t in range(n)])
    m_tied = np.array([(np.delete(X[:, t], i) == mo[t]).sum() for t in range(n)])
    Wt = X[others] == mo[None, :]
    # option arrays (2n): index t -> tie, n+t -> win
    lvw = np.maximum(x, np.minimum(mo + eps, c))               # strictly above the best rival, at most eps above it (or already there)
    lvl = np.concatenate([mo, lvw])
    feas = np.concatenate([(mo > x) & (mo <= c), c > mo])
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
    # Feasibility is exact and independent of the MILP: raising every task to its cap is the best raise for every pairwise lead.
    Yc = X.copy(); Yc[i] = c
    if plurality_first(Yc) != i: return _out(INF, None, return_y)
    # Strict lead without an arbitrary threshold. All credits are multiples of 1/Lc (Lc = lcm of the tie-group sizes involved).
    # Small Lc: integer lattice, "strictly first" is exactly "lead >= 1 unit" and the MILP is exact. Large Lc: the lattice is too fine
    # for a float MILP; solve the relaxation "lead >= 0", check each solution in exact rational arithmetic and cut off (no-good cut on
    # the binaries) the ones that tie or lose; the relaxation contains every strict solution, so the first valid solution is optimal.
    dens = [int(v) for v in np.concatenate([ties.sum(axis=0), m_tied + 1])]
    Lc = math.lcm(*dens)
    if Lc <= PLURALITY_LATTICE_MAX:
        Am = np.rint(A * Lc); ri = np.rint((w[others] - w[i]) * Lc) + 1
    else:
        Am = A; ri = w[others] - w[i]
    cons = [LinearConstraint(Am, ri, np.inf)]
    one = np.zeros((n, 2 * n)); one[np.arange(n), np.arange(n)] = 1; one[np.arange(n), n + np.arange(n)] = 1
    cons.append(LinearConstraint(one, -np.inf, 1))
    ub = feas.astype(float)
    cvec = (cost if objective == "L1" else (cost > 0).astype(float))
    for _ in range(PLURALITY_MAX_CUTS):
        res = milp(cvec, constraints=cons, integrality=np.ones(2 * n), bounds=Bounds(np.zeros(2 * n), ub),
                   options={"time_limit": TIME_LIMIT})
        if res.status == 1 or not res.success: return _out(np.nan, None, return_y)   # the cap raise wins, so a failed solve is numerical: censored
        zz = np.round(res.x); y = x.copy()
        for k in np.where(zz > 0.5)[0]:
            if not already[k]: y[k % n] = lvl[k]
        Y = X.copy(); Y[i] = y
        if plurality_first(Y) == i: return _out(float(res.fun), y, return_y)
        cons.append(LinearConstraint((1 - 2 * zz)[None, :], 1 - zz.sum(), np.inf))
    return _out(np.nan, None, return_y)


# ---------------------------------------------------------------- Copeland (pairwise wins, ties 1/2), exact, full model (M up to ~500)
def copeland_scores(X):
    M, n = X.shape
    P = np.array([[wins(X[j], X[k]).sum() for k in range(M)] for j in range(M)])
    out = (P > n / 2) * 1.0 + (P == n / 2) * 0.5
    np.fill_diagonal(out, 0.0)
    return out.sum(axis=1)


def copeland_min_investment(X, i, cap, eps=1e-3, objective="L1", return_y=False):
    """Smallest investment so that the target has strictly the highest Copeland score (a pairwise win counts 1, a tie 1/2).
    MILP: level binaries z as in Borda; per rival k a pair outcome (B_k: target strictly wins, T_k: tie) that may only be claimed
    when the target's pairwise points allow it (claiming less than the truth can only hurt the target, so the optimum is exact)."""
    M, n = X.shape; x = X[i]
    C = copeland_scores(X)
    if C[i] > np.delete(C, i).max(): return _out(0.0, x.copy(), return_y)
    others, tl, lv, cost, dW = _build(X, i, cap, eps)
    K = len(tl); R = len(others)
    W0 = wins(x[None, :], X[others]).sum(axis=1)
    Xo = X[others]
    P_oo = np.array([[wins(Xo[a], Xo[b]).sum() for b in range(R)] for a in range(R)])
    Co = ((P_oo > n / 2) * 1.0 + (P_oo == n / 2) * 0.5); np.fill_diagonal(Co, 0.0); Co = Co.sum(axis=1)   # rival's score vs the other rivals
    nr = n if objective == "K" else 0
    nv = K + nr + 2 * R; zB = K + nr; zT = zB + R
    c = np.zeros(nv)
    if objective == "K": c[K:K + nr] = 1
    else: c[:K] = cost
    cons = []
    S = lil_matrix((n, nv))
    for k, t in enumerate(tl): S[t, k] = 1
    cons.append(LinearConstraint(csr_matrix(S), -np.inf, 1))
    if objective == "K":
        S2 = lil_matrix((n, nv))
        for k, t in enumerate(tl): S2[t, k] = 1
        for t in range(n): S2[t, K + t] = -1
        cons.append(LinearConstraint(csr_matrix(S2), -np.inf, 0))
    # pair outcomes: W0_k + dW_k z >= (n/2+1/2) B_k + (n/2) T_k ; B_k + T_k <= 1
    A = np.zeros((R, nv)); A[:, :K] = dW; A[np.arange(R), zB + np.arange(R)] -= n / 2 + 0.5; A[np.arange(R), zT + np.arange(R)] -= n / 2
    cons.append(LinearConstraint(csr_matrix(A), -W0, np.inf))
    A = np.zeros((R, nv)); A[np.arange(R), zB + np.arange(R)] = 1; A[np.arange(R), zT + np.arange(R)] = 1
    cons.append(LinearConstraint(csr_matrix(A), -np.inf, 1))
    # C_i - C_j >= 1/2 for every rival j:  sum_k (B_k + T_k/2) + B_j + T_j/2 >= Co_j + 1.5
    A = np.zeros((R, nv))
    A[:, zB:zB + R] = 1; A[:, zT:zT + R] = 0.5
    A[np.arange(R), zB + np.arange(R)] += 1; A[np.arange(R), zT + np.arange(R)] += 0.5
    cons.append(LinearConstraint(csr_matrix(A), Co + 1.5, np.inf))
    integ = np.ones(nv); ub = np.ones(nv)
    res = milp(c, constraints=cons, integrality=integ, bounds=Bounds(np.zeros(nv), ub), options={"time_limit": TIME_LIMIT})
    if res.status == 1: return _out(np.nan, None, return_y)
    if not res.success: return _out(INF, None, return_y)
    y = x.copy()
    for k in np.where(np.round(res.x[:K]) > 0.5)[0]: y[tl[k]] = lv[k]
    return _out(float(res.fun), y, return_y)


# ---------------------------------------------------------------- simulation helpers (for bisection on Linf and for tests)
def borda_first(X): B = borda_points(X); return B.argmax() if (B == B.max()).sum() == 1 else -1
def condorcet_winner(X):
    M, n = X.shape
    for j in range(M):
        if all(wins(X[j], X[k]).sum() > n / 2 for k in range(M) if k != j): return j
    return -1
def plurality_first(X):
    """index of the model with a strictly largest plurality total (first places, ties split), -1 if the maximum is shared;
    exact rational arithmetic (the gaps can be far below any float tolerance when many models tie for first)."""
    from fractions import Fraction
    mx = X.max(axis=0); tot = {}
    for t in range(X.shape[1]):
        idx = np.where(X[:, t] == mx[t])[0]
        for j in idx: tot[int(j)] = tot.get(int(j), Fraction(0)) + Fraction(1, len(idx))
    best = max(tot.values()); top = [j for j, v in tot.items() if v == best]
    return top[0] if len(top) == 1 else -1

def copeland_first(X): C = copeland_scores(X); return C.argmax() if (C >= C.max() - 1e-12).sum() == 1 else -1


FIRST = {"borda": borda_first, "condorcet": condorcet_winner, "plurality": plurality_first, "copeland": copeland_first}
MIN_INV = {"borda": borda_min_investment, "condorcet": condorcet_min_investment, "plurality": plurality_min_investment,
           "copeland": copeland_min_investment}


def linf_ordinal(rule, X, i, cap, eps=1e-3, tol=1e-6):
    c = np.maximum(np.asarray(cap, float), X[i]); f = FIRST[rule]
    def ok(d):
        Y = X.copy(); Y[i] = np.minimum(X[i] + d, c); return f(Y) == i
    if f(X) == i: return 0.0
    hi = float((c - X[i]).max())
    if not ok(hi): return INF
    lo = 0.0
    while hi - lo > tol:
        d = (lo + hi) / 2
        if ok(d): hi = d
        else: lo = d
    return hi


def min_investment_ordinal(rule, X, i, cap, eps=1e-3, measures=("L1", "K", "Linf")):
    out = {}
    if "L1" in measures: out["L1"] = MIN_INV[rule](X, i, cap, eps, "L1")
    if "K" in measures: out["K"] = MIN_INV[rule](X, i, cap, eps, "K")
    if "Linf" in measures: out["Linf"] = linf_ordinal(rule, X, i, cap, eps)
    return out
