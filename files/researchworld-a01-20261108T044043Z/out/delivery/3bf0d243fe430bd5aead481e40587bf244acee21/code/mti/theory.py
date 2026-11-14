"""Closed forms of propositions P1-P3 (story-repo THEORY.md), written from the statements and independent of `scorerules`.
Every function takes the target's scores x, rival level tau, caps c (>= x) and the margin eps and returns (L1, K);
L1 = K = inf when infeasible. The target is first when V(y) >= tau + eps; if V(x) > tau already, the cost is 0.
"""
import numpy as np

INF = np.inf


def p1_mean(x, tau, c, eps):
    n = len(x); h = c - x; need = n * (tau + eps - x.mean())
    if x.mean() > tau: return 0.0, 0
    if h.sum() < need - 1e-12: return INF, INF
    k = int(np.searchsorted(np.cumsum(np.sort(h)[::-1]), need - 1e-12) + 1)   # fewest largest headrooms covering the need
    return need, k


def p2_min(x, tau, c, eps):
    if x.min() > tau: return 0.0, 0
    lvl = tau + eps
    if np.any(c[x < lvl] < lvl - 1e-12): return INF, INF
    d = np.maximum(lvl - x, 0.0)
    return d.sum(), int((d > 0).sum())


def p3_median_odd(x, tau, c, eps):
    n = len(x); assert n % 2 == 1; m = (n + 1) // 2
    if np.median(x) > tau: return 0.0, 0
    lvl = tau + eps
    have = int((x >= lvl).sum()); k = max(m - have, 0)
    low = x < lvl
    d = np.where(c >= lvl - 1e-12, lvl - x, INF)[low]
    d = np.sort(d)
    if k > np.isfinite(d).sum(): return INF, INF
    return float(d[:k].sum()), k
