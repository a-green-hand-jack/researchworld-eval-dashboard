"""Minimum targeted investment under rank-based rules (Borda / mean rank, Condorcet-winner, plurality).

Same setting as scorerules: target i raises y_t in [x_t, c_t]; others fixed; strict improvement uses eps.
A task-level raise to level s+eps passes every model with score <= s on that task. Ties count 1/2.
Exact via MILP (scipy/HiGHS), with lazily generated rival constraints.
"""
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
    cand = np.unique(np.concatenate([u[u > x], u + eps]))      # tie with s (half credit) or strictly pass s
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
    O = X[others][:, tl]                       # (M-1, K)
    dW = wins(lv[None, :], O) - wins(x[tl][None, :], O)
    return others, tl, lv, cost, dW


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


def _lazy(X, i, cap, eps, objective, rival_rows_fn, init_active, max_rounds=60):
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
            return INF if len(viol) else 0.0
        res = _solve(cost, A_full[idx] if len(idx) else None, rhs_full[idx] if len(idx) else [], tl, n, objective, cost)
        if res.status == 1: return np.nan          # time limit: censored
        if not res.success: return INF             # proven infeasible
        z = np.round(res.x[:K])
        viol = np.where(A_full @ z < rhs_full - 1e-9)[0]
        if len(viol) == 0:
            return float(res.fun)
        active |= set(viol[np.argsort(-(rhs_full[viol] - A_full[viol] @ z))][:25].tolist())
    raise RuntimeError("lazy constraint loop did not converge")


# ---------------------------------------------------------------- Borda
def borda_min_investment(X, i, cap, eps=1e-3, objective="L1"):
    """Smallest investment so that target has strictly the highest Borda total (mean rank)."""
    B = borda_points(X)
    M, n = X.shape
    if B[i] > np.delete(B, i).max(): return 0.0
    def rows(others, dW):
        G = dW.sum(axis=0)[None, :]                    # total pairwise points gained by target
        A = G + dW                                     # target gain + rival j's loss
        rhs = (B[others] - B[i]) + 0.5                 # need B_i - B_j >= 0.5 (half-point granularity)
        return A, rhs
    top = np.argsort(-B[others_idx(M, i)])[:5]
    return _lazy(X, i, cap, eps, objective, rows, top)


def others_idx(M, i): return np.array([j for j in range(M) if j != i])


# ---------------------------------------------------------------- Condorcet winner (beats every rival in a strict task-majority)
def condorcet_min_investment(X, i, cap, eps=1e-3, objective="L1"):
    M, n = X.shape; x = X[i]
    others = others_idx(M, i)
    W0 = wins(x[None, :], X[others]).sum(axis=1)       # target's pairwise wins vs each rival
    need = n / 2 + 0.5 - W0
    if (need <= 0).all(): return 0.0
    def rows(oth, dW): return dW, need
    order = np.argsort(-need)[:5]
    return _lazy(X, i, cap, eps, objective, rows, order)


# ---------------------------------------------------------------- plurality (first-place count, ties split)
def plurality_min_investment(X, i, cap, eps=1e-3, objective="L1"):
    M, n = X.shape; x = X[i]; c = np.maximum(np.asarray(cap, float), x)
    mx = X.max(axis=0)
    ties = (X == mx[None, :]); share = ties / ties.sum(axis=0)[None, :]      # (M,n) credit
    w = share.sum(axis=0) if False else share.sum(axis=1)                       # first-place credit per model
    if w[i] > np.delete(w, i).max() + 1e-12: return 0.0
    others = others_idx(M, i)
    # per task two options: tie the best rival score (level mo, credit shared) or beat it (level mo+eps, full credit)
    mo = np.array([np.delete(X[:, t], i).max() for t in range(n)])
    m_tied = np.array([(np.delete(X[:, t], i) == mo[t]).sum() for t in range(n)])
    Wt = X[others] == mo[None, :]
    # option arrays (2n): index t -> tie, n+t -> win
    lvl = np.concatenate([mo, mo + eps])
    feas = np.concatenate([(mo > x) & (mo <= c + 1e-12), (mo + eps <= c + 1e-12) & True])
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
    res = milp(cvec, constraints=cons, integrality=np.ones(2 * n), bounds=Bounds(np.zeros(2 * n), ub),
               options={"time_limit": TIME_LIMIT})
    if res.status == 1: return np.nan
    return float(res.fun) if res.success else INF


# ---------------------------------------------------------------- Copeland (pairwise wins, ties 1/2), exact, full model (M up to ~500)
def copeland_scores(X):
    M, n = X.shape
    P = np.array([[wins(X[j], X[k]).sum() for k in range(M)] for j in range(M)])
    out = (P > n / 2) * 1.0 + (P == n / 2) * 0.5
    np.fill_diagonal(out, 0.0)
    return out.sum(axis=1)


def copeland_min_investment(X, i, cap, eps=1e-3, objective="L1"):
    """Smallest investment so that the target has strictly the highest Copeland score (a pairwise win counts 1, a tie 1/2).
    MILP: level binaries z as in Borda; per rival k a pair outcome (B_k: target strictly wins, T_k: tie) that may only be claimed
    when the target's pairwise points allow it (claiming less than the truth can only hurt the target, so the optimum is exact)."""
    M, n = X.shape; x = X[i]
    C = copeland_scores(X)
    if C[i] > np.delete(C, i).max(): return 0.0
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
    if res.status == 1: return np.nan
    return float(res.fun) if res.success else INF


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
