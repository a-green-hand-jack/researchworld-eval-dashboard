"""Memory-lean exact MILPs for Borda and Condorcet-winner minimum investment on a full board (thousands of models).

Same model, same constraints, same solver call (ordinal._solve) as ordinal.borda_min_investment / condorcet_min_investment; the difference is that the
(M-1) x K matrix dW of every rival's pairwise change at every candidate level is never built. A rival's row is computed when the rival enters the
active set, the column sums G come from sorted scores, and a candidate solution (at most one level per task) is checked against all rivals by
adding up the n per-task changes. tests/test_ordinal_lean.py checks equality with the dense code on random boards and on OLLB targets.
"""
import numpy as np
from . import ordinal as od

INF = np.inf


def _setup(X, i, cap, eps):
    M, n = X.shape; x = X[i]; c = np.maximum(np.asarray(cap, float), x)
    oth = od.others_idx(M, i)
    tl, lv = [], []
    for t in range(n):
        for l in od._levels(X, i, t, c[t], eps): tl.append(t); lv.append(l)
    return oth, np.array(tl, int), np.array(lv, float)


def _colwins(v, s_sorted):
    """sum over the sorted sample of w(v, s) = #(s<v) + 0.5 #(s==v), v an array"""
    return np.searchsorted(s_sorted, v, side="left") + 0.5 * (np.searchsorted(s_sorted, v, side="right") - np.searchsorted(s_sorted, v, side="left"))


def _min_inv(rule, X, i, cap, eps, objective, max_rounds=80):
    M, n = X.shape; x = X[i]
    oth, tl, lv = _setup(X, i, cap, eps); K = len(tl); cost = lv - x[tl]
    O = X[oth]                                             # (M-1, n)
    if rule == "borda":
        B = od.borda_points(X)
        if B[i] > np.delete(B, i).max(): return 0.0
        rhs = (B[oth] - B[i]) + 0.5
        G = np.zeros(K)
        for t in range(n):
            m = tl == t; s = np.sort(O[:, t]); G[m] = _colwins(lv[m], s) - _colwins(np.full(m.sum(), x[t]), s)
        order = np.argsort(-B[oth])[:5]
    else:
        W0 = od.wins(x[None, :], O).sum(axis=1); rhs = n / 2 + 0.5 - W0
        if (rhs <= 0).all(): return 0.0
        G = np.zeros(K); order = np.argsort(-rhs)[:5]
    if K == 0: return INF if (rhs > 1e-9).any() else 0.0
    row = lambda j: (G if rule == "borda" else 0.0) + od.wins(lv, O[j][tl]) - od.wins(x[tl], O[j][tl])      # A_j (K,)
    active = list(order); aset = set(active)
    for _ in range(max_rounds):
        A = np.array([row(j) for j in active]); res = od._solve(cost, A, rhs[active], tl, n, objective, cost)
        if res.status == 1: return np.nan
        if not res.success: return INF
        z = np.round(res.x[:K]); ks = np.where(z > 0.5)[0]
        # change in w of the target against every rival, summed over the chosen levels
        dW = sum(od.wins(lv[k], O[:, tl[k]]) - od.wins(x[tl[k]], O[:, tl[k]]) for k in ks) if len(ks) else np.zeros(M - 1)
        Az = (G @ z if rule == "borda" else 0.0) + dW
        viol = np.where(Az < rhs - 1e-9)[0]
        if len(viol) == 0: return float(res.fun)
        for j in viol[np.argsort(-(rhs[viol] - Az[viol]))][:25]:
            if j not in aset: aset.add(j); active.append(j)
    raise RuntimeError("lazy loop did not converge")


def borda_min_investment(X, i, cap, eps=1e-3, objective="L1"): return _min_inv("borda", X, i, cap, eps, objective)
def condorcet_min_investment(X, i, cap, eps=1e-3, objective="L1"): return _min_inv("condorcet", X, i, cap, eps, objective)
