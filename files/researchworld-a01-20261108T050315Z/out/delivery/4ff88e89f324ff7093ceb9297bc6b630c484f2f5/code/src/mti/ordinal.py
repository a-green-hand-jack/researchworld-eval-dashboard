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
STATUS = set()      # HiGHS statuses seen since the last clear(): 0 optimal, 1 time limit (incumbent returned = upper bound), 2 infeasible


def borda_points(X):
    """(M,) total Borda points: per task, #models strictly below + 0.5 * #ties (self excluded)."""
    return sum(rankdata(X[:, t], method="average") - 1 for t in range(X.shape[1]))


def copeland_scores(X, chunk=256):
    """(M,) Copeland score: #rivals beaten by a strict task-majority + 0.5 * #rivals tied (n/2 tasks each way). Vectorised, O(M^2 n)."""
    M, n = X.shape; out = np.zeros(M)
    for a in range(0, M, chunk):
        W = np.zeros((min(chunk, M - a), M))
        for t in range(n):
            xt = X[:, t]; xa = xt[a:a + chunk, None]
            W += (xa > xt[None, :]) + 0.5 * (xa == xt[None, :])
        beat = (W > n / 2).sum(axis=1) + 0.5 * (W == n / 2).sum(axis=1)
        self_ = np.arange(a, a + len(W)); self_w = W[np.arange(len(W)), self_]        # self-comparison: n/2 -> counted as a tie
        out[a:a + len(W)] = beat - (self_w == n / 2) * 0.5 - (self_w > n / 2)
    return out


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
    """Candidate levels (task t raised to level l) and a lazy accessor for the pairwise-points change dW[j, k] of rival j when
    level k is applied; dW is never materialised in full (M x K can be several GB at M~4500)."""
    M, n = X.shape; x = X[i]; c = np.maximum(np.asarray(cap, float), x)
    others = np.array([j for j in range(M) if j != i])
    L = []   # list of (t, level)
    for t in range(n):
        for l in _levels(X, i, t, c[t], eps): L.append((t, l))
    tl = np.array([t for t, _ in L], int); lv = np.array([l for _, l in L], float)
    cost = lv - x[tl]
    Xo = X[others]
    def dW(rows=slice(None), cols=slice(None)):
        O = Xo[rows][:, tl[cols]]
        return wins(lv[cols][None, :], O) - wins(x[tl[cols]][None, :], O)
    def colsum(chunk=1024):                                 # G[k] = sum_j dW[j, k]
        return np.concatenate([dW(slice(None), slice(a, a + chunk)).sum(axis=0) for a in range(0, len(tl), chunk)]) if len(tl) else np.zeros(0)
    return others, tl, lv, cost, dW, colsum


def _solve(cost_vec, A_rows, lo, tl, n, objective, cost, time_limit=600):
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
    STATUS.add(res.status)
    if res.status == 1 and res.x is not None: res.success = True      # time limit with incumbent: reported as an upper bound (status column)
    return res


def _lazy(X, i, cap, eps, objective, rhs_fn, use_G, init_active, max_rounds=60):
    """Rival constraints A z >= rhs, one per rival j, generated lazily: A[j] = dW[j] (+ G if use_G, the target's own pairwise gain).
    rhs_fn(others) -> rhs (M-1,)."""
    M, n = X.shape
    others, tl, lv, cost, dW, colsum = _build(X, i, cap, eps)
    K = len(tl); rhs_full = rhs_fn(others)
    if K == 0:
        return INF if (rhs_full > 1e-9).any() else 0.0
    G = colsum() if use_G else None
    active = set(init_active)
    for _ in range(max_rounds):
        idx = np.array(sorted(active), int)
        A = dW(idx) + (G[None, :] if use_G else 0.0)
        res = _solve(cost, A if len(idx) else None, rhs_full[idx] if len(idx) else [], tl, n, objective, cost)
        if not res.success: return INF
        z = np.round(res.x[:K]); ch = np.flatnonzero(z > 0.5)
        Az = (dW(slice(None), ch).sum(axis=1) if len(ch) else np.zeros(len(others))) + (G[ch].sum() if use_G else 0.0)
        viol = np.where(Az < rhs_full - 1e-9)[0]
        if len(viol) == 0:
            return float(res.fun)
        active |= set(viol[np.argsort(-(rhs_full[viol] - Az[viol]))][:25].tolist())
    raise RuntimeError("lazy constraint loop did not converge")


# ---------------------------------------------------------------- Borda
def borda_min_investment(X, i, cap, eps=1e-3, objective="L1"):
    """Smallest investment so that target has strictly the highest Borda total (mean rank)."""
    B = borda_points(X)
    M, n = X.shape
    if B[i] > np.delete(B, i).max(): return 0.0
    rhs_fn = lambda others: (B[others] - B[i]) + 0.5      # need B_i - B_j >= 0.5 (half-point granularity); row = target gain G + rival loss dW
    top = np.argsort(-B[others_idx(M, i)])[:5]
    return _lazy(X, i, cap, eps, objective, rhs_fn, True, top)


def others_idx(M, i): return np.array([j for j in range(M) if j != i])


# ---------------------------------------------------------------- Condorcet winner (beats every rival in a strict task-majority)
def condorcet_min_investment(X, i, cap, eps=1e-3, objective="L1"):
    M, n = X.shape; x = X[i]
    others = others_idx(M, i)
    W0 = wins(x[None, :], X[others]).sum(axis=1)       # target's pairwise wins vs each rival
    need = n / 2 + 0.5 - W0
    if (need <= 0).all(): return 0.0
    order = np.argsort(-need)[:5]
    return _lazy(X, i, cap, eps, objective, lambda oth: need, False, order)


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
    res = milp(cvec, constraints=cons, integrality=np.ones(2 * n), bounds=Bounds(np.zeros(2 * n), ub), options={"time_limit": 600})
    STATUS.add(res.status)
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

FIRST = {"borda": borda_first, "condorcet": condorcet_winner, "plurality": plurality_first}
MIN_INV = {"borda": borda_min_investment, "condorcet": condorcet_min_investment, "plurality": plurality_min_investment}


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
