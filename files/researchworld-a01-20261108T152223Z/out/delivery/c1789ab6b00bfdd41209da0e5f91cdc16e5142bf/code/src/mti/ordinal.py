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


def copeland_values(X, max_models=700):
    """Copeland score (pairwise task-majority wins + 0.5 per tied pair); NaN vector if M is too large for the M x M x n tensor."""
    M, n = X.shape
    if M > max_models: return np.full(M, np.nan)
    W = ((X[:, None, :] > X[None, :, :]).sum(-1) + 0.5 * (X[:, None, :] == X[None, :, :]).sum(-1))   # task wins of j vs k
    beats = (W > n / 2) + 0.5 * (W == n / 2); np.fill_diagonal(beats, 0.0)
    return beats.sum(axis=1)


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
    # stored as float32 (values are multiples of 1/2, exact) and built in column chunks: at M ~ 4500 the dense (M-1, K) matrix is the memory bottleneck
    K = len(tl); dW = np.empty((M - 1, K), np.float32); Xo = X[others]
    for a in range(0, K, 2048):
        O = Xo[:, tl[a:a + 2048]]
        dW[:, a:a + 2048] = wins(lv[None, a:a + 2048], O) - wins(x[tl[a:a + 2048]][None, :], O)
    return others, tl, lv, cost, dW


LAST = {}   # plan of the most recent successful solve: n_tasks_raised, l1 (score points)


def _record(z, cost, tl, lv=None):
    sel = np.asarray(z) > 0.5
    LAST.clear(); LAST.update(K=int(len(set(np.asarray(tl)[sel].tolist()))), L1=float(np.asarray(cost)[sel].sum()),
                              plan={int(t): float(l) for t, l in zip(np.asarray(tl)[sel], np.asarray(lv)[sel])} if lv is not None else None)


def _solve(cost_vec, A_rows, lo, tl, n, objective, cost, time_limit=120, kmax=None):
    K = len(cost_vec)
    # variables z_k (K), plus for objective K (or an L1 objective with at most kmax tasks): r_t (n) indicates task raised
    use_r = objective == "K" or kmax is not None
    nv = K + (n if use_r else 0)
    c = np.zeros(nv)
    if objective == "K": c[K:] = 1
    else: c[:K] = cost
    cons = []
    # at most one level per task
    S = lil_matrix((n, nv))
    for k, t in enumerate(tl): S[t, k] = 1
    cons.append(LinearConstraint(csr_matrix(S), -np.inf, 1))
    if use_r:
        S2 = lil_matrix((n, nv))
        for k, t in enumerate(tl): S2[t, k] = 1
        for t in range(n): S2[t, K + t] = -1
        cons.append(LinearConstraint(csr_matrix(S2), -np.inf, 0))
    if kmax is not None:
        rk = np.zeros((1, nv)); rk[0, K:] = 1; cons.append(LinearConstraint(rk, -np.inf, kmax + 0.5))
    if A_rows is not None and len(lo):
        A = np.zeros((A_rows.shape[0], nv)); A[:, :K] = A_rows
        cons.append(LinearConstraint(csr_matrix(A), lo, np.inf))
    ub = np.ones(nv)
    res = milp(c, constraints=cons, integrality=np.ones(nv), bounds=Bounds(np.zeros(nv), ub),
               options={"time_limit": time_limit, "mip_rel_gap": 0.0})
    return res


def _lazy(X, i, cap, eps, objective, rival_rows_fn, init_active, max_rounds=60, kmax=None):
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
        res = _solve(cost, A_full[idx] if len(idx) else None, rhs_full[idx] if len(idx) else [], tl, n, objective, cost, kmax=kmax)
        if res.status == 2: return INF
        if not res.success: return np.nan          # time limit / numerical failure: reported as NaN, never as infeasible
        z = np.round(res.x[:K])
        z = z.astype(A_full.dtype); viol = np.where(A_full @ z < rhs_full - 1e-9)[0]
        if len(viol) == 0:
            _record(z, cost, tl, lv)
            return float(res.fun)
        active |= set(viol[np.argsort(-(rhs_full[viol] - A_full[viol] @ z))][:25].tolist())
    raise RuntimeError("lazy constraint loop did not converge")


# ---------------------------------------------------------------- Borda
def borda_min_investment(X, i, cap, eps=1e-3, objective="L1", kmax=None):
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
    return _lazy(X, i, cap, eps, objective, rows, top, kmax=kmax)


def others_idx(M, i): return np.array([j for j in range(M) if j != i])


# ---------------------------------------------------------------- Condorcet winner (beats every rival in a strict task-majority)
def condorcet_min_investment(X, i, cap, eps=1e-3, objective="L1", kmax=None):
    M, n = X.shape; x = X[i]
    others = others_idx(M, i)
    W0 = wins(x[None, :], X[others]).sum(axis=1)       # target's pairwise wins vs each rival
    need = n / 2 + 0.5 - W0
    if (need <= 0).all(): return 0.0
    def rows(oth, dW): return dW, need
    order = np.argsort(-need)[:5]
    return _lazy(X, i, cap, eps, objective, rows, order, kmax=kmax)


# ---------------------------------------------------------------- plurality (first-place count, ties split)
def plurality_min_investment(X, i, cap, eps=1e-3, objective="L1", kmax=None):
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
    if kmax is not None:
        cons.append(LinearConstraint((cost > 0).astype(float)[None, :], -np.inf, kmax + 0.5))
    ub = feas.astype(float)
    cvec = (cost if objective == "L1" else (cost > 0).astype(float))
    res = milp(cvec, constraints=cons, integrality=np.ones(2 * n), bounds=Bounds(np.zeros(2 * n), ub),
               options={"mip_rel_gap": 0.0})
    if res.success:
        z = np.round(res.x); LAST.clear(); LAST.update(K=int(((cost > 0) & (z > 0.5)).sum()), L1=float(cost[z > 0.5].sum()),
                                                       plan={int(t % n): float(lvl[t]) for t in np.where((cost > 0) & (z > 0.5))[0]})
        return float(res.fun)
    return INF if res.status == 2 else np.nan



# ---------------------------------------------------------------- Copeland (pairwise task-majority wins, ties 1/2; strictly highest score)
def copeland_min_investment(X, i, cap, eps=1e-3, objective="L1", kmax=None, time_limit=120):
    """MILP. Per rival j: a_j = 1 only if the target wins the task majority (W_ij >= n/2+1/2), g_j = 1 only if W_ij >= n/2 (tie or better);
    the target's pairwise credit is (a_j+g_j)/2. All constraints push a,g up (they can only help the target), so one-sided linking is exact.
    Rival j's Copeland score changes only through its pair with the target: c_j' = c_j + b0_j - b'_j. Need C_i' - c_j' >= 1/2 for every j."""
    from scipy.sparse import vstack
    M, n = X.shape; x = X[i]
    others = others_idx(M, i); R = len(others)
    if M > 2000: raise ValueError("Copeland MILP restricted to M <= 2000 models")
    sc = copeland_values(X, max_models=10**9)
    if sc[i] > np.delete(sc, i).max(): return 0.0
    _, tl, lv, cost, dW = _build(X, i, cap, eps); K = len(tl)
    if K == 0: return INF
    W0 = wins(x[None, :], X[others]).sum(axis=1)
    b0 = (W0 > n / 2) * 1.0 + (W0 == n / 2) * 0.5
    use_r = objective == "K" or kmax is not None
    nz = K; nr = n if use_r else 0
    N = nz + 2 * R + nr; ia, ig, ir = nz, nz + R, nz + 2 * R
    c = np.zeros(N)
    if objective == "K": c[ir:] = 1
    else: c[:nz] = cost
    rows = []; lo = []; hi = []
    def add(r, l, u): rows.append(csr_matrix(r)); lo.append(np.broadcast_to(np.asarray(l, float), (r.shape[0],))); hi.append(np.broadcast_to(np.asarray(u, float), (r.shape[0],)))
    S = np.zeros((n, N)); S[tl, np.arange(K)] = 1; add(S, -np.inf, 1)                       # one level per task
    if use_r:
        S2 = np.zeros((n, N)); S2[tl, np.arange(K)] = 1; S2[np.arange(n), ir + np.arange(n)] = -1; add(S2, -np.inf, 0)
        if kmax is not None:
            r = np.zeros((1, N)); r[0, ir:] = 1; add(r, -np.inf, kmax + 0.5)
    ar = np.arange(R)
    A1 = np.zeros((R, N)); A1[:, :nz] = dW; A1[ar, ia + ar] = -(n / 2 + 0.5); add(A1, -W0, np.inf)    # W_ij >= (n+1)/2 * a_j
    A2 = np.zeros((R, N)); A2[:, :nz] = dW; A2[ar, ig + ar] = -(n / 2); add(A2, -W0, np.inf)          # W_ij >= n/2 * g_j
    A3 = np.zeros((R, N)); A3[ar, ia + ar] = 1; A3[ar, ig + ar] = -1; add(A3, -np.inf, 0)             # a_j <= g_j
    A4 = np.zeros((R, N)); A4[:, ia:ia + R] = 0.5; A4[:, ig:ig + R] = 0.5; A4[ar, ia + ar] += 0.5; A4[ar, ig + ar] += 0.5
    add(A4, sc[others] + b0 + 0.5, np.inf)                                                             # C_i' - c_j' >= 1/2
    res = milp(c, constraints=LinearConstraint(vstack(rows).tocsr(), np.concatenate(lo), np.concatenate(hi)), integrality=np.ones(N),
               bounds=Bounds(np.zeros(N), np.ones(N)), options={"time_limit": time_limit, "mip_rel_gap": 0.0})
    if res.success:
        _record(np.round(res.x[:nz]), cost, tl, lv); return float(res.fun)
    return INF if res.status == 2 else np.nan

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

def copeland_first(X):
    v = copeland_values(X, max_models=10**9)
    return v.argmax() if (v >= v.max() - 1e-12).sum() == 1 else -1

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


def _plan_after(call):
    """run a solve and return (value, (K, L1) of the returned optimal plan)"""
    LAST.clear(); v = call()
    return v, ((LAST.get("K", 0), LAST.get("L1", 0.0)) if np.isfinite(v) else (v, v))


def min_investment_ordinal(rule, X, i, cap, eps=1e-3, measures=("L1", "K", "Linf")):
    """L1: min total points; K: min #tasks; Linf: min uniform jump (bisection).
    K_at_L1: #tasks touched by an L1-optimal plan; L1_lexK: min L1 among K-minimal plans (lexicographic: K first, then L1)."""
    out = {}; f = MIN_INV[rule]
    if "L1" in measures:
        out["L1"], (kk, _) = _plan_after(lambda: f(X, i, cap, eps, "L1")); out["K_at_L1"] = kk
    if "K" in measures:
        out["K"], _ = _plan_after(lambda: f(X, i, cap, eps, "K"))
        if "L1_lexK" in measures:
            out["L1_lexK"] = out["K"] if not np.isfinite(out["K"]) else (0.0 if out["K"] == 0 else f(X, i, cap, eps, "L1", kmax=int(round(out["K"]))))
    if "Linf" in measures: out["Linf"] = linf_ordinal(rule, X, i, cap, eps)
    return out
