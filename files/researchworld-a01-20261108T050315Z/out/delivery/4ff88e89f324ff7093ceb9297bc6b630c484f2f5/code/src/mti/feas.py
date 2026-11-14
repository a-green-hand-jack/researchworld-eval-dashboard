"""Feasibility-side quantities that need only the rule evaluated at one candidate edit (no optimisation).

All rules here are monotone in the target's own scores (raising a score never lowers the target's standing nor raises a rival's), hence
 * the target can become first under cap c iff it is first at y = c (every task raised to its cap);
 * the smallest uniform lift d* (y = min(x + d, top)) equals Linf* of the free-subset problem under the ceiling cap;
 * feasibility is monotone in every cap family parameter, so minimal feasible parameters follow by bisection.
Tie convention as in the solvers: score rules need f(y) >= tau + eps, ordinal rules a strict (half-point) win.
"""
import numpy as np
from . import scorerules as sr, ordinal as od

INF = np.inf


class Rival:
    """Fixed rival information for one (X, i, rule): is_first(y) says whether the target at scores y is strictly first."""
    def __init__(self, X, i, rule, eps):
        self.X, self.i, self.rule, self.eps = X, i, rule, eps
        M, n = X.shape; self.n = n; self.others = np.delete(np.arange(M), i); self.Xo = X[self.others]
        if rule in sr.RULES or rule.startswith("trimmed"):
            self.f = sr.RULES[rule][0] if rule in sr.RULES else (lambda y, t=int(rule[7:]): sr.trimmed_v(y, t))
            v = self.f(self.Xo); self.tau = float(v.max())
        elif rule == "borda":
            self.B = od.borda_points(X); self.w0 = od.wins(X[i][None, :], self.Xo)
        elif rule not in ("condorcet", "plurality"): raise KeyError(rule)

    def is_first(self, y):
        r = self.rule
        if r == "condorcet": return bool((od.wins(y[None, :], self.Xo).sum(axis=1) > self.n / 2).all())
        if r == "borda":
            d = od.wins(y[None, :], self.Xo) - self.w0                       # target's pairwise gain vs each rival, per task
            Bj = self.B[self.others] - d.sum(axis=1); Bi = self.B[self.i] + d.sum()
            return bool(Bi > Bj.max() + 1e-12)
        if r == "plurality":
            Y = self.X.copy(); Y[self.i] = y; return od.plurality_first(Y) == self.i
        return bool(self.f(y) >= self.tau + self.eps - 1e-12)


def _bisect(ok, lo, hi, tol=1e-9):
    """smallest p in [lo, hi] with ok(p) (ok monotone, ok(hi) known True)"""
    if ok(lo): return lo
    while hi - lo > tol * max(1.0, abs(hi)):
        m = (lo + hi) / 2
        if ok(m): hi = m
        else: lo = m
    return hi


def feasible_at(riv, cap):
    y = np.maximum(np.asarray(cap, float), riv.X[riv.i]); return riv.is_first(y)


def uniform_lift(riv, top):
    """smallest d with y = min(x + d, top) first (inf if not first even at top); equals Linf* under the ceiling cap"""
    x = riv.X[riv.i]; top = np.broadcast_to(top, x.shape)
    if not riv.is_first(np.maximum(top, x)): return INF
    return _bisect(lambda d: riv.is_first(np.minimum(x + d, np.maximum(top, x))), 0.0, float((np.maximum(top, x) - x).max()))


def min_front_margin(riv, top):
    """smallest margin m with cap = min(best rival + m, top) feasible; inf if infeasible at the ceiling"""
    x = riv.X[riv.i]; fr = riv.Xo.max(axis=0); top = np.broadcast_to(top, x.shape)
    if not riv.is_first(np.maximum(top, x)): return INF
    ok = lambda m: riv.is_first(np.maximum(np.minimum(fr + m, top), x))
    return _bisect(ok, 0.0, float((top - fr).max()) + 1e-9 if (top - fr).max() > 0 else 0.0) if not ok(0.0) else 0.0


def min_emp_multiplier(riv, top, hq):
    """smallest mu with cap = min(x + mu * max(hq, 0), top) feasible; inf if infeasible even for mu = 1e3 (tasks with hq <= 0 stay fixed)"""
    x = riv.X[riv.i]; top = np.broadcast_to(top, x.shape); hq = np.maximum(hq, 0)
    cap = lambda mu: np.maximum(np.minimum(x + mu * hq, top), x)
    if not riv.is_first(cap(1e3)): return INF
    return _bisect(lambda mu: riv.is_first(cap(mu)), 0.0, 1e3)


def proportional_allocation(riv, cap):
    """smallest lambda in [0,1] with y = x + lambda (c - x) first, and its total cost lambda * sum(c - x) (headroom-proportional spread of
    the investment over all tasks); (inf, inf) if infeasible"""
    x = riv.X[riv.i]; c = np.maximum(np.asarray(cap, float), x)
    if not riv.is_first(c): return INF, INF
    lam = _bisect(lambda l: riv.is_first(x + l * (c - x)), 0.0, 1.0)
    return lam, float(lam * (c - x).sum())
