"""Minimum targeted investment for a target model to become first under score-based aggregation rules.

Setting. X: (M, n) score matrix; target model i with scores x (n,). The target may raise its score on task t
to any y_t in [x_t, c_t] (c_t = cap, "headroom"); all other models are fixed. A rule f maps a score vector to a
scalar; the target is first iff f(y) >= tau + eps, tau = max_{j != i} f(X_j) (strict improvement by eps).
Investment measures: L1 = sum(y - x); K = #tasks with y_t > x_t; Linf = max(y - x).
All functions return np.inf when the target cannot become first within the caps (proven); NaN means censored by a solver limit.
"""
import itertools
import numpy as np

INF = np.inf


def _caps(x, cap):
    return np.maximum(np.asarray(cap, float), x)


# ---------------------------------------------------------------- rule values
def mean_v(Y): return np.mean(Y, axis=-1)
def median_v(Y): return np.median(Y, axis=-1)
def min_v(Y): return np.min(Y, axis=-1)
def powmean_v(Y, p=0.0, s=1.0):
    """power mean of (score + s); p=0 geometric. Returned on the score scale (minus s)."""
    Z = Y + s
    return (np.exp(np.mean(np.log(Z), axis=-1)) if p == 0 else np.mean(Z ** p, axis=-1) ** (1 / p)) - s
def trimmed_v(Y, t):
    S = np.sort(Y, axis=-1)
    return S[..., t:Y.shape[-1] - t].mean(axis=-1)


# ---------------------------------------------------------------- mean
def mean_L1(x, tau, cap, eps):
    c = _caps(x, cap); n = len(x); need = n * (tau + eps) - x.sum()
    if need <= 0: return 0.0
    return need if (c - x).sum() >= need - 1e-12 else INF

def mean_K(x, tau, cap, eps):
    c = _caps(x, cap); n = len(x); need = n * (tau + eps) - x.sum()
    if need <= 0: return 0
    h = np.sort(c - x)[::-1]; cs = np.cumsum(h)
    k = np.searchsorted(cs, need - 1e-12) + 1
    return k if k <= n else INF


# ---------------------------------------------------------------- power mean, p<1 (concave), incl. geometric
def powmean_L1(x, tau, cap, eps, p=0.0, s=1.0):
    """min sum(y-x) s.t. powmean(y) >= tau+eps. For concave g the optimum equalises (y+s) at a water level L."""
    c = _caps(x, cap); target = tau + eps
    if powmean_v(x, p, s) >= target: return 0.0
    if powmean_v(c, p, s) < target: return INF
    lo, hi = x.min(), c.max()
    for _ in range(200):
        L = (lo + hi) / 2
        if powmean_v(np.clip(L, x, c), p, s) >= target: hi = L
        else: lo = L
    return float((np.clip(hi, x, c) - x).sum())

def powmean_K(x, tau, cap, eps, p=0.0, s=1.0):
    """min #tasks raised (to cap): additive in g, so greedy on g(c)-g(x)."""
    c = _caps(x, cap); target = tau + eps; n = len(x)
    if powmean_v(x, p, s) >= target: return 0
    g = (lambda v: np.log(v + s)) if p == 0 else (lambda v: ((v + s) ** p - 1) / p)
    gain = np.sort(g(c) - g(x))[::-1]
    need = n * g(target) - g(x).sum()   # powmean>=target  <=> mean g >= g(target) (g increasing for all p<1 as defined)
    cs = np.cumsum(gain); k = np.searchsorted(cs, need - 1e-12) + 1
    return k if k <= n else INF


# ---------------------------------------------------------------- min
def min_L1(x, tau, cap, eps):
    c = _caps(x, cap); b = tau + eps
    if (c < b).any(): return INF
    return float(np.maximum(0, b - x).sum())
def min_K(x, tau, cap, eps):
    c = _caps(x, cap); b = tau + eps
    if (c < b).any(): return INF
    return int((x < b).sum())


# ---------------------------------------------------------------- median
def median_L1(x, tau, cap, eps):
    c = _caps(x, cap); n = len(x); b = tau + eps
    if n % 2:
        m = (n + 1) // 2
        gap = np.where(c >= b, np.maximum(0, b - x), INF)
        g = np.sort(gap)[:m]
        return float(g.sum()) if np.isfinite(g).all() else INF
    return _median_even(x, c, b, "L1")

def median_K(x, tau, cap, eps):
    c = _caps(x, cap); n = len(x); b = tau + eps
    if n % 2:
        m = (n + 1) // 2
        have = int((x >= b).sum()); extra = int(((x < b) & (c >= b)).sum())
        need = max(0, m - have)
        return need if need <= extra else INF
    return _median_even(x, c, b, "K")

def _median_even(x, c, b, mode):
    """median = mean of the two middle values >= b  <=>  h tasks end >= a and h+1 tasks end >= bb, a+bb >= 2b, a>=bb."""
    n = len(x); h = n // 2; best = INF
    if mode == "K":
        V = np.unique(np.concatenate([x, c]))
        for a in V:
            if a < b: continue
            for bb in V:
                if bb > a or a + bb < 2 * b - 1e-12: continue
                best = min(best, _count_even(x, c, a, bb, h))
        return best
    cand = set([b]); 
    for v in list(x) + list(c): cand.add(v); cand.add(2 * b - v)
    for a in cand:
        bb = 2 * b - a
        if a < bb - 1e-12: continue
        ca = np.where(c >= a, np.maximum(0, a - x), INF)
        cb = np.where(c >= bb, np.maximum(0, bb - x), INF)
        for e in range(n):
            if not np.isfinite(cb[e]): continue
            rest = np.delete(ca, e)
            sel = np.sort(rest)[:h]
            if len(sel) < h or not np.isfinite(sel).all(): continue
            best = min(best, cb[e] + sel.sum())
    return float(best)

def _count_even(x, c, a, bb, h):
    freeA = x >= a; nA0 = int(freeA.sum()); rA = max(0, h - nA0)
    P = (x < bb) & (c >= a); Q = (x >= bb) & (x < a) & (c >= a)
    p = min(rA, int(P.sum())); q = rA - p
    if q > int(Q.sum()): return INF
    nB0 = int((x >= bb).sum())
    rB = max(0, h + 1 - nB0 - p)
    # remaining candidates below bb that can reach bb: unused P plus tasks with bb <= c < a
    avail = int(((x < bb) & (c >= bb)).sum()) - p
    if rB > avail: return INF
    return rA + rB


# ---------------------------------------------------------------- trimmed mean (exact for small n via MILP)
def trimmed_L1_milp(x, tau, cap, eps, t):
    """min sum(y-x) s.t. trimmed_mean(y; t) >= tau+eps; exact MILP (assignment formulation), small n only."""
    from scipy.optimize import milp, LinearConstraint, Bounds
    c = _caps(x, cap); n = len(x); b = tau + eps; m = n - 2 * t
    if trimmed_v(c, t) < b: return INF
    if trimmed_v(x, t) >= b: return 0.0
    # vars: y_t (n), s_p (n sorted values), a_tp (n*n binaries)
    ny, ns, na = n, n, n * n; N = ny + ns + na
    M = float(c.max() - x.min() + 1)
    cost = np.zeros(N); cost[:ny] = 1
    rows, lo, hi = [], [], []
    def add(r, l, u): rows.append(r); lo.append(l); hi.append(u)
    for tt in range(n):                      # each task assigned to one position
        r = np.zeros(N); r[ny + ns + tt * n: ny + ns + (tt + 1) * n] = 1; add(r, 1, 1)
    for p in range(n):                       # each position one task
        r = np.zeros(N); r[ny + ns + p: ny + ns + na: n] = 1; add(r, 1, 1)
    for p in range(n - 1):                   # sorted
        r = np.zeros(N); r[ny + p] = -1; r[ny + p + 1] = 1; add(r, 0, np.inf)
    for tt in range(n):                      # s_p <= y_t + M(1-a_tp)
        for p in range(n):
            r = np.zeros(N); r[ny + p] = 1; r[tt] = -1; r[ny + ns + tt * n + p] = M; add(r, -np.inf, M)
    r = np.zeros(N); r[ny + t: ny + n - t] = 1; add(r, m * b, np.inf)
    lb = np.concatenate([x, np.full(ns, -1e3), np.zeros(na)])
    ub = np.concatenate([c, np.full(ns, 1e3), np.ones(na)])
    integ = np.concatenate([np.zeros(ny + ns), np.ones(na)])
    res = milp(cost, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=integ, bounds=Bounds(lb, ub),
               options={"time_limit": 120.0})
    if res.status == 0: return float(res.fun - x.sum())
    return INF if res.status == 2 else np.nan        # time limit (censored) is NaN, never INF


def trimmed1_milp(x, tau, cap, eps, objective="L1"):
    """Exact MILP for the trimmed mean that drops the single best and worst task (t=1): trimmed sum = S - max - min.
    Variables y (n), zmax >= y_t (continuous), zmin >= y_t - M(1-r_t) with sum r = 1 (zmin >= min y; binding at optimum),
    u_t (raise indicators) for objective K. Only n(+n) binaries instead of the n^2 assignment formulation."""
    from scipy.optimize import milp, LinearConstraint, Bounds
    c = _caps(x, cap); n = len(x); b = tau + eps; need = (n - 2) * b
    if trimmed_v(c, 1) < b: return INF
    if trimmed_v(x, 1) >= b: return 0.0 if objective == "L1" else 0
    M = float(c.max() - x.min() + 1)
    # layout: y[0:n], zmax, zmin, r[n], u[n]
    N = 2 * n + 2 + n; iy, izM, izm, ir, iu = 0, n, n + 1, n + 2, 2 * n + 2
    rows, lo, hi = [], [], []
    def add(r, l, u): rows.append(r); lo.append(l); hi.append(u)
    for t in range(n):
        r = np.zeros(N); r[iy + t] = -1; r[izM] = 1; add(r, 0, np.inf)                       # zmax >= y_t
        r = np.zeros(N); r[izm] = 1; r[iy + t] = -1; r[ir + t] = -M; add(r, -M, np.inf)       # zmin >= y_t - M(1-r_t)
        r = np.zeros(N); r[iy + t] = 1; r[iu + t] = -(c[t] - x[t]); add(r, -np.inf, x[t])     # y_t <= x_t + (c_t-x_t) u_t
    r = np.zeros(N); r[ir:ir + n] = 1; add(r, 1, 1)
    r = np.zeros(N); r[iy:iy + n] = 1; r[izM] = -1; r[izm] = -1; add(r, need, np.inf)
    cost = np.zeros(N)
    if objective == "L1": cost[iy:iy + n] = 1
    else: cost[iu:iu + n] = 1
    lb = np.concatenate([x, [-1e3, -1e3], np.zeros(2 * n)]); ub = np.concatenate([c, [1e3, 1e3], np.ones(2 * n)])
    integ = np.concatenate([np.zeros(n + 2), np.ones(2 * n)])
    res = milp(cost, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=integ, bounds=Bounds(lb, ub),
               options={"time_limit": 120.0, "mip_rel_gap": 1e-9})
    if res.status == 0: return float(res.fun - x.sum()) if objective == "L1" else float(round(res.fun))
    return INF if res.status == 2 else np.nan


# ---------------------------------------------------------------- Linf and generic helpers (monotone rules, by bisection)
def linf_bisect(fval, x, tau, cap, eps, tol=1e-7):
    """min d s.t. fval(min(x+d, c)) >= tau+eps. fval maps (n,) -> scalar."""
    c = _caps(x, cap); b = tau + eps
    if fval(x) >= b: return 0.0
    if fval(c) < b: return INF
    lo, hi = 0.0, float((c - x).max())
    while hi - lo > tol:
        d = (lo + hi) / 2
        if fval(np.minimum(x + d, c)) >= b: hi = d
        else: lo = d
    return hi


# ---------------------------------------------------------------- weighted mean (fractional knapsack: raise the heaviest tasks first)
def wmean_L1(x, tau, cap, eps, w):
    c = _caps(x, cap); w = w / w.sum(); need = tau + eps - w @ x
    if need <= 0: return 0.0
    head = c - x
    if (w * head).sum() < need - 1e-12: return INF
    cost = 0.0
    for t in np.argsort(-w, kind="stable"):
        g = w[t] * head[t]
        if g >= need - 1e-15: return float(cost + need / w[t])
        cost += head[t]; need -= g
    return float(cost)

def wmean_K(x, tau, cap, eps, w):
    c = _caps(x, cap); w = w / w.sum(); need = tau + eps - w @ x
    if need <= 0: return 0
    g = np.sort(w * (c - x))[::-1]; cs = np.cumsum(g)
    k = np.searchsorted(cs, need - 1e-12) + 1
    return k if k <= len(x) else INF

def make_wmean(w):
    """(value fn, L1, K) of the weighted mean with fixed non-negative weights w (normalised to sum 1)."""
    w = np.asarray(w, float); w = w / w.sum()
    return (lambda Y: Y @ w, lambda x, tau, cap, eps: wmean_L1(x, tau, cap, eps, w), lambda x, tau, cap, eps: wmean_K(x, tau, cap, eps, w))


RULES = {
    # name: (value fn on (...,n), L1, K)
    "mean": (mean_v, mean_L1, mean_K),
    "geomean": (lambda Y: powmean_v(Y, 0.0), lambda *a: powmean_L1(*a, p=0.0), lambda *a: powmean_K(*a, p=0.0)),
    "harmonic": (lambda Y: powmean_v(Y, -1.0), lambda *a: powmean_L1(*a, p=-1.0), lambda *a: powmean_K(*a, p=-1.0)),
    "median": (median_v, median_L1, median_K),
    "min": (min_v, min_L1, min_K),
}
for _p in (0.5, -0.5, -2.0, -5.0):    # power means with exponent p < 1 interpolate between mean (p=1) and min (p=-inf)
    RULES[f"pow{_p:g}"] = ((lambda Y, _p=_p: powmean_v(Y, _p)), (lambda *a, _p=_p: powmean_L1(*a, p=_p)),
                          (lambda *a, _p=_p: powmean_K(*a, p=_p)))


def min_investment(rule, X, i, cap, eps=1e-3, measures=("L1", "K", "Linf")):
    """Minimum investment of target i to be strictly first under a score rule (`rule` is a RULES key or a (fv, L1, K) triple)."""
    fv, l1, kk = RULES[rule] if isinstance(rule, str) else rule
    x = X[i]; vals = fv(X); tau = np.delete(vals, i).max()
    out = {"gap": float(tau - vals[i])}
    if vals[i] > tau: return {**out, **{m: 0.0 for m in measures}}
    if "L1" in measures: out["L1"] = l1(x, tau, cap, eps)
    if "K" in measures: out["K"] = kk(x, tau, cap, eps)
    if "Linf" in measures: out["Linf"] = linf_bisect(fv, x, tau, cap, eps)
    return out
