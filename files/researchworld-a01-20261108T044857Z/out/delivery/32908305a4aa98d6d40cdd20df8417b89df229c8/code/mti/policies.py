"""An optimal L1 raise vector y* for the score rules mean, median, min (companion of scorerules.*_L1; used by run_survival.py).
Each function returns y (n,) with y >= x, y <= max(cap, x) and rule(y) >= tau + eps, of the same cost as scorerules.<rule>_L1, or None
when infeasible. The optimum is not unique for the mean (any split of the needed total within the headroom): the vector returned
concentrates the raise on the largest headrooms (so it also has the minimum number of raised tasks K)."""
import numpy as np
from . import scorerules as sr


def mean_y(x, tau, cap, eps):
    c = sr._caps(x, cap); n = len(x); need = n * (tau + eps) - x.sum(); y = x.copy()
    if need <= 0: return y
    if (c - x).sum() < need - 1e-12: return None
    for t in np.argsort(-(c - x), kind="stable"):
        take = min(c[t] - x[t], need); y[t] += take; need -= take
        if need <= 1e-12: break
    return y


def min_y(x, tau, cap, eps):
    c = sr._caps(x, cap); b = tau + eps
    return None if (c < b).any() else np.maximum(x, b)


def median_y(x, tau, cap, eps):
    c = sr._caps(x, cap); n = len(x); b = tau + eps
    if n % 2:
        m = (n + 1) // 2
        gap = np.where(c >= b, np.maximum(0, b - x), np.inf)
        sel = np.argsort(gap, kind="stable")[:m]
        if not np.isfinite(gap[sel]).all(): return None
        y = x.copy(); y[sel] = np.maximum(x[sel], b); return y
    h = n // 2; best = np.inf; arg = None          # even n: the two middle values u >= v with u + v >= 2b (see scorerules._median_even)
    cand = {b}
    for v in list(x) + list(c): cand.add(v); cand.add(2 * b - v)
    for a in cand:
        bb = 2 * b - a
        if a < bb - 1e-12: continue
        ca = np.where(c >= a, np.maximum(0, a - x), np.inf); cb = np.where(c >= bb, np.maximum(0, bb - x), np.inf)
        for e in range(n):
            if not np.isfinite(cb[e]): continue
            rest = [k for k in range(n) if k != e]; sel = np.array(rest)[np.argsort(ca[rest], kind="stable")[:h]]
            if len(sel) < h or not np.isfinite(ca[sel]).all(): continue
            cost = cb[e] + ca[sel].sum()
            if cost < best - 1e-12: best = cost; arg = (a, bb, e, sel)
    if arg is None: return None
    a, bb, e, sel = arg; y = x.copy(); y[e] = max(x[e], bb); y[sel] = np.maximum(x[sel], a)
    return y


Y = {"mean": mean_y, "median": median_y, "min": min_y}
