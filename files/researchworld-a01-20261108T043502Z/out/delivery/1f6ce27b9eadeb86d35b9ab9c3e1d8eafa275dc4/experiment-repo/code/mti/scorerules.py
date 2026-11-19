"""Minimum targeted investment for a target model to become first under score-based aggregation rules.

Setting. X: (M, n) score matrix; target model i with scores x (n,). The target may raise its score on task t
to any y_t in [x_t, c_t] (c_t = cap, "headroom"); all other models are fixed. A rule f maps a score vector to a
scalar; the target is first iff f(y) >= tau + eps, tau = max_{j != i} f(X_j) (strict improvement by eps).
Investment measures: L1 = sum(y - x); K = #tasks with y_t > x_t; Linf = max(y - x).
All functions return np.inf when the target cannot become first within the caps.
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
    res = milp(cost, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=integ, bounds=Bounds(lb, ub))
    return float(res.fun - x.sum()) if res.success else INF


def trimmed_L1_lp(x, tau, cap, eps, t):
    """Exact min sum(y-x) s.t. trimmed_mean(y; t) >= tau+eps by enumerating which t tasks end as the dropped top and which t as
    the dropped bottom; each designation is an LP with ordering constraints (top >= kept >= bottom). Small n only."""
    from scipy.optimize import linprog
    c = _caps(x, cap); n = len(x); b = tau + eps; m = n - 2 * t
    if trimmed_v(c, t) < b: return INF
    if trimmed_v(x, t) >= b: return 0.0
    best = INF
    for top in itertools.combinations(range(n), t):
        rest = [k for k in range(n) if k not in top]
        for bot in itertools.combinations(rest, t):
            kept = [k for k in rest if k not in bot]
            A, ub = [], []
            r = np.zeros(n); r[kept] = -1; A.append(r); ub.append(-m * b)           # sum kept >= m b
            for a_ in top:
                for k in kept: r = np.zeros(n); r[k] = 1; r[a_] = -1; A.append(r); ub.append(0)   # y_k <= y_top
            for b_ in bot:
                for k in kept: r = np.zeros(n); r[b_] = 1; r[k] = -1; A.append(r); ub.append(0)   # y_bot <= y_k
            res = linprog(np.ones(n), A_ub=np.array(A), b_ub=ub, bounds=list(zip(x, c)), method="highs")
            if res.success: best = min(best, res.fun - x.sum())
    return float(best)

def trimmed_K_enum(x, tau, cap, eps, t):
    """min #tasks raised (to cap) so that the trimmed mean >= tau+eps; enumerates subsets (n <= ~12)."""
    c = _caps(x, cap); n = len(x); b = tau + eps
    for k in range(n + 1):
        for S in itertools.combinations(range(n), k):
            y = x.copy(); y[list(S)] = c[list(S)]
            if trimmed_v(y, t) >= b - 1e-12: return k
    return INF


# ---------------------------------------------------------------- convex (diminishing-returns) cost: sum of squared gains
def mean_L2(x, tau, cap, eps):
    """min sum(delta^2) s.t. mean(y) >= tau+eps, delta_t in [0, cap_t-x_t]: water-filling delta_t = min(h_t, lam)."""
    c = _caps(x, cap); n = len(x); need = n * (tau + eps) - x.sum(); h = c - x
    if need <= 0: return 0.0
    if h.sum() < need - 1e-12: return INF
    lo, hi = 0.0, h.max()
    for _ in range(100):
        lam = (lo + hi) / 2
        if np.minimum(h, lam).sum() >= need: hi = lam
        else: lo = lam
    return float((np.minimum(h, hi) ** 2).sum())

def min_L2(x, tau, cap, eps):
    c = _caps(x, cap); b = tau + eps
    if (c < b).any(): return INF
    return float((np.maximum(0, b - x) ** 2).sum())

def median_L2(x, tau, cap, eps):
    """odd n only: the m = (n+1)/2 smallest gaps (squared) among tasks that can reach tau+eps."""
    c = _caps(x, cap); n = len(x); b = tau + eps
    if n % 2 == 0: return np.nan
    m = (n + 1) // 2
    gap = np.where(c >= b, np.maximum(0, b - x), INF)
    g = np.sort(gap)[:m]
    return float((g ** 2).sum()) if np.isfinite(g).all() else INF

L2_RULES = {"mean": mean_L2, "min": min_L2, "median": median_L2}


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
    """Minimum investment of target i to be strictly first under a score rule."""
    fv, l1, kk = RULES[rule]
    x = X[i]; vals = fv(X); tau = np.delete(vals, i).max()
    out = {"gap": float(tau - vals[i])}
    if vals[i] > tau: return {**out, **{m: 0.0 for m in measures if m != "L2" or rule in L2_RULES}}
    if "L1" in measures: out["L1"] = l1(x, tau, cap, eps)
    if "K" in measures: out["K"] = kk(x, tau, cap, eps)
    if "Linf" in measures: out["Linf"] = linf_bisect(fv, x, tau, cap, eps)
    if "L2" in measures and rule in L2_RULES: out["L2"] = L2_RULES[rule](x, tau, cap, eps)
    return out
