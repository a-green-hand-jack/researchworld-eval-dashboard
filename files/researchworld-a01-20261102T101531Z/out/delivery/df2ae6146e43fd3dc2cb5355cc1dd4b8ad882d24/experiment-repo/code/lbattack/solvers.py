"""Minimal targeted investment for a target model to become strictly first.

Attack model.  The developer picks a set T of sub-datasets and raises the
target's score on each j in T by at most `delta` points (never above the
ceiling `hi`, default 100); all other scores are unchanged.  All rules here are
monotone in the target's own scores, so using the full allowed boost on the
chosen tasks is optimal and the problem is *which* tasks (min k) -- except for
`l1_cost`, which minimises total points with no per-task cap.

  min_k(S, t, rule, delta)  -> smallest number of targeted tasks (inf if none)
  l1_cost(S, t, rule)       -> smallest total points (cardinal rules only)

Cardinal rules (mean, geo, median, min): the target needs an aggregate above
c = max over rivals; closed forms.  Ordinal rules (borda, plurality,
condorcet): the effect of the boost on the margin to each rival is additive
over tasks, so min_k is a multi-cover 0/1 program (HiGHS via scipy.milp).
"""
import itertools
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from . import rules as R

EPS = 1e-9
INF = float("inf")
_CACHE = {}


def _scores(S, rule):
    """R.scores with a small cache (the O(m^2 n) pairwise rules dominate the run time)."""
    if rule not in ("copeland", "condorcet", "borda", "plurality"):
        return R.scores(S, rule)
    key = (S.shape, hash(S.tobytes()), rule)
    if key not in _CACHE:
        if len(_CACHE) > 12:
            _CACHE.clear()
        _CACHE[key] = R.scores(S, rule)
    return _CACHE[key]


def _boost(s_t, delta, hi):
    return np.minimum(s_t + delta, hi)


# ---------------------------------------------------------------- cardinal
def _threshold(S, t, rule):
    sc = _scores(S, rule)
    return np.delete(sc, t).max()


def _agg_vec(v, rule):
    return R.scores(v[None, :], rule)[0]


def _sep_g(rule):
    """g with  f(s) > f(s')  <=>  sum_j g(s_j) > sum_j g(s'_j)  (separable rules)."""
    if rule == "mean":
        return lambda x: x
    if rule == "geo":
        return lambda x: np.log(x + 1.0)
    if rule.startswith("pmean:"):
        p = float(rule.split(":")[1])
        return (lambda x: (x + 1.0) ** p) if p > 0 else (lambda x: -((x + 1.0) ** p))
    return None


def _subsets(n):
    return ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1).astype(bool)


def _median_even(s, v, c, n, return_set):
    """Exact min k, n even.  median > c  <=>  exists x: #{z >= x} >= h and #{z > 2c - x} >= h+1 (h = n/2), with x
    among the candidate final values; for a fixed x the boost counts follow from the 4 task types."""
    h = n // 2; best = None
    for x in np.unique(np.concatenate([s, v])):
        y = 2 * c - x
        a0 = s >= x - EPS * 0; a1 = v >= x; b0 = s > y + EPS; b1 = v > y + EPS
        dA = max(0, h - int(a0.sum())); dB = max(0, h + 1 - int(b0.sum()))
        ga = (~a0) & a1; gb = (~b0) & b1
        both = np.flatnonzero(ga & gb); onlya = np.flatnonzero(ga & ~gb); onlyb = np.flatnonzero(gb & ~ga)
        for t11 in range(0, min(len(both), max(dA, dB)) + 1):
            ra, rb = max(0, dA - t11), max(0, dB - t11)
            if ra <= len(onlya) and rb <= len(onlyb):
                k = t11 + ra + rb
                if best is None or k < best[0]:
                    best = (k, np.concatenate([both[:t11], onlya[:ra], onlyb[:rb]]).astype(int))
    if best is None:
        return INF
    return (best[0], best[1]) if return_set else best[0]


def min_k_cardinal(S, t, rule, delta, hi=100.0, enum_max=10, return_set=False):
    n = S.shape[1]
    c = _threshold(S, t, rule)
    s = S[t]
    if _agg_vec(s, rule) > c + EPS:
        return (0, np.array([], int)) if return_set else 0
    v = _boost(s, delta, hi)
    if _agg_vec(v, rule) <= c + EPS:
        return INF
    out = lambda k, T: (k, np.asarray(T, int)) if return_set else k
    if n <= enum_max:                       # exact: all subsets, full boost
        Y = _subsets(n)
        Vm = np.where(Y, v[None, :], s[None, :])
        ok = R.scores(Vm, rule) > c + EPS
        cnt = np.where(ok, Y.sum(1), n + 1)
        i = int(np.argmin(cnt))
        return out(int(cnt[i]), np.flatnonzero(Y[i]))
    g = _sep_g(rule)
    if g is not None:                       # separable: take the k largest gains
        gain = g(v) - g(s)
        order = np.argsort(-gain)
        tgt = g(np.delete(S, t, 0)).sum(1).max()
        base = g(s).sum()
        cum = base + np.cumsum(gain[order])
        k = int(np.argmax(cum > tgt + EPS)) + 1
        return out(k, order[:k])
    if rule == "min":
        need = np.flatnonzero(s <= c + EPS)
        return out(len(need), need) if np.all(v[need] > c + EPS) else INF
    if rule == "median" and n % 2 == 0:     # n even: median = mean of the two middle order statistics
        return _median_even(s, v, c, n, return_set)
    if rule == "median":                    # n odd: tasks below c, closest first
        cand = np.flatnonzero((s <= c) & (v > c))
        a = int((s > c).sum()); need = (n + 1) // 2 - a
        if len(cand) < need:
            return INF
        cand = cand[np.argsort(-s[cand])][:need]
        return out(need, cand)
    if rule == "trim":                      # heuristic (upper bound): greedy + prune
        T = []; w = s.copy()
        while _agg_vec(w, rule) <= c + EPS:
            best = None
            for j in range(n):
                if j in T or v[j] <= s[j]:
                    continue
                w2 = w.copy(); w2[j] = v[j]
                val = (_agg_vec(w2, rule), v[j] - s[j])
                if best is None or val > best[0]:
                    best = (val, j)
            if best is None:
                return INF
            T.append(best[1]); w[best[1]] = v[best[1]]
        for j in list(T):                   # prune redundant tasks
            w2 = w.copy(); w2[j] = s[j]
            if _agg_vec(w2, rule) > c + EPS:
                T.remove(j); w = w2
        return out(len(T), T)
    raise ValueError(rule)


EXACT = {"mean": True, "geo": True, "median": True, "min": True, "trim": False,
         "borda": True, "plurality": True, "copeland": True, "condorcet": True}


def is_exact(rule, n, enum_max=10):
    if rule.startswith("pmean:"):
        return True
    return True if (n <= enum_max) else EXACT[rule]


def _enum_min_k(S, t, rule, delta, hi=100.0):
    """Brute force over task subsets (validation / small n)."""
    n = S.shape[1]
    v = _boost(S[t], delta, hi)
    for k in range(0, n + 1):
        for T in itertools.combinations(range(n), k):
            S2 = S.copy()
            idx = list(T)
            S2[t, idx] = v[idx]
            if R.is_first(S2, t, rule):
                return k
    return INF


# ----------------------------------------------------------------- ordinal
def _cmp(a, b):
    return (a > b) + 0.5 * (a == b)


def min_k_ordinal(S, t, rule, delta, hi=100.0, return_set=False, enum_max=10):
    m, n = S.shape
    if rule == "condorcet":
        first = R.is_first(S, t, rule)
    else:
        sc0 = _scores(S, rule); first = bool(sc0[t] > np.delete(sc0, t).max())
    if first:
        return 0
    s = S[t]
    v = _boost(s, delta, hi)
    riv = np.arange(m) != t
    X = S[riv]                                   # rivals
    P0 = _cmp(X, s[None, :])                     # rival-vs-target now
    P1 = _cmp(X, v[None, :])                     # ... after boosting task j
    d = P0 - P1                                  # >=0: rival's loss on task j
    if rule == "condorcet":
        # t beats rival i iff W_i > n/2, W_i = sum_j (1 - P0 + y_j d_ij)
        W0 = (1 - P0).sum(1)
        A, b = d, (n / 2 + 0.25) - W0
    elif rule == "borda":
        sc = _scores(S, "borda")
        D0 = sc[t] - sc[riv]
        a = d.sum(0)                             # target's own gain on task j
        A, b = a[None, :] + d, 0.25 - D0
    elif rule == "copeland":
        W0 = (1 - P0).sum(1)
        b0 = (W0 > n / 2) + 0.5 * (W0 == n / 2)
        base = _scores(S, "copeland")[riv]
        ct = _scores(S, "copeland")[t]
        if n <= enum_max:
            Y = _subsets(n).astype(float)
            W = W0[None, :] + Y @ d.T                            # (2^n, m-1)
            bb = (W > n / 2) + 0.5 * (W == n / 2)
            ok = np.all(bb.sum(1)[:, None] - (base + b0 - bb) >= 0.25, axis=1)
            if not ok.any():
                return INF
            cnt = np.where(ok, Y.sum(1), np.inf); i = int(np.argmin(cnt))
            return (int(cnt[i]), np.flatnonzero(Y[i] > 0.5)) if return_set else int(cnt[i])
        mr = m - 1; Z = np.zeros((mr, mr)); I = np.eye(mr)
        # variables: y (n), u (mr), v (mr);  u_i: W_i >= n/2,  v_i: W_i > n/2
        # W0 + d y >= (n/2) u   ->  -d y + (n/2) u <= W0
        A1 = np.hstack([-d, (n / 2) * I, Z]); u1 = W0
        A2 = np.hstack([-d, Z, (n / 2 + 0.5) * I]); u2 = W0
        half = np.ones((mr, 2 * mr)) * 0.5 + np.hstack([0.5 * I, 0.5 * I])
        A3 = np.hstack([np.zeros((mr, n)), half]); l3 = base + b0 + 0.25
        cons = [LinearConstraint(A1, ub=u1 + 1e-9), LinearConstraint(A2, ub=u2 + 1e-9),
                LinearConstraint(A3, lb=l3 - 1e-6)]
        cvec = np.concatenate([np.ones(n), np.zeros(2 * mr)])
        res = milp(c=cvec, integrality=np.ones(n + 2 * mr), bounds=Bounds(0, 1), constraints=cons)
        if not res.success:
            return INF
        y = res.x[:n]
        return (int(round(res.fun)), np.flatnonzero(y > 0.5)) if return_set else int(round(res.fun))
    elif rule == "plurality":
        top = S.max(0)
        cnt = (S == top).sum(0)
        share = (S == top) / cnt                 # (m, n) share of task win
        Xr = S[riv]
        oth = Xr.max(0)
        co = (Xr == oth).sum(0)
        gt = v > oth + EPS                       # boost makes t the sole best
        eq = np.abs(v - oth) <= EPS              # ... or ties for best
        new_t = np.where(gt, 1.0, np.where(eq, 1.0 / (co + 1), share[t]))
        new_r = np.where(gt[None, :], 0.0,
                         np.where(eq[None, :], (Xr == oth) / (co + 1), share[riv]))
        gain_t = new_t - share[t]
        loss_i = share[riv] - new_r
        D0 = share[t].sum() - share[riv].sum(1)
        A, b = gain_t[None, :] + loss_i, 1e-3 - D0
    else:
        raise ValueError(rule)
    keep = b > 1e-12
    if not keep.any():
        return 0
    A, b = A[keep], b[keep]
    if np.any(A.sum(1) < b - 1e-5):             # even boosting everything fails
        return INF
    if n <= enum_max:  # enumerate task subsets (vectorised); exact and fast
        Y = ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1).astype(float)
        ok = np.all(Y @ A.T >= b[None, :] - 1e-5, axis=1)
        if not ok.any():
            return INF
        cnt = Y.sum(1); cnt[~ok] = np.inf
        i = int(np.argmin(cnt))
        return (int(cnt[i]), np.flatnonzero(Y[i] > 0.5)) if return_set else int(cnt[i])
    res = milp(c=np.ones(n), integrality=np.ones(n),
               bounds=Bounds(0, 1), constraints=LinearConstraint(A, lb=b - 1e-5))
    if not res.success:
        return INF
    return (int(round(res.fun)), np.flatnonzero(res.x > 0.5)) if return_set else int(round(res.fun))


def min_k(S, t, rule, delta, hi=100.0, enum_max=10, return_set=False):
    """delta and hi may be scalars or per-task vectors."""
    S = np.asarray(S, float)
    if rule in R.ORDINAL:
        return min_k_ordinal(S, t, rule, delta, hi, return_set=return_set, enum_max=enum_max)
    return min_k_cardinal(S, t, rule, delta, hi, enum_max=enum_max, return_set=return_set)


# --------------------------------------------------------------------- L1
def l1_cost(S, t, rule, hi=100.0):
    """Min total points added (any distribution over tasks, ceiling hi) for t
    to strictly exceed every rival; infimum (strictness margin ignored).
    mean: gap*n.  geo: water-filling.  min: raise every task to c.
    median: raise the cheapest (n+1)//2-a tasks to c (odd n)."""
    n = S.shape[1]
    c = _threshold(S, t, rule)
    s = S[t]
    if _agg_vec(s, rule) > c:
        return 0.0
    if rule == "mean":
        cost = n * c - s.sum()
        return cost if c < hi else INF
    if rule == "min":
        return float(np.maximum(c - s, 0).sum()) if c < hi else INF
    if rule == "median":
        assert n % 2 == 1
        if c >= hi:
            return INF
        need = (n + 1) // 2
        cost = np.sort(np.maximum(c - s, 0))[:need].sum()
        return float(cost)
    if rule == "geo":  # raise lowest tasks to a common level L (concave g)
        target = n * np.log(c + 1.0)
        if c >= hi:
            return INF
        lo_, hi_ = s.min(), hi
        for _ in range(100):
            L = (lo_ + hi_) / 2
            if np.log(np.maximum(s, L) + 1).sum() >= target:
                hi_ = L
            else:
                lo_ = L
        return float((np.maximum(s, hi_) - s).sum())
    raise ValueError(rule)


# ------------------------------------------------------- G_min with caps / costs
def _g_prime_inv(rule):
    """(g, g', inverse of g' as a function of lambda*w) for strictly concave separable rules."""
    if rule == "geo":
        return (lambda x: np.log(x + 1.0)), (lambda z: 1.0 / z - 1.0)
    p = float(rule.split(":")[1])
    if 0 < p < 1:
        return (lambda x: (x + 1.0) ** p), (lambda z: (z / p) ** (1.0 / (p - 1.0)) - 1.0)
    if p < 0:
        return (lambda x: -((x + 1.0) ** p)), (lambda z: (z / abs(p)) ** (1.0 / (p - 1.0)) - 1.0)
    return None


def g_min(S, t, rule, u, w):
    """Minimal cost sum_j w_j x_j, 0 <= x_j <= u_j, for t to exceed every rival
    (infimum: strictness ignored).  Exact for mean, geo, pmean with p<1, min,
    median (odd n).  Returns nan where no exact method is implemented, inf if infeasible."""
    n = S.shape[1]
    s = S[t]; u = np.broadcast_to(np.asarray(u, float), (n,)).copy(); w = np.broadcast_to(np.asarray(w, float), (n,))
    u = np.maximum(u, 0.0)
    c = _threshold(S, t, rule)
    if _agg_vec(s, rule) > c:
        return 0.0
    if _agg_vec(s + u, rule) <= c:
        return INF
    if rule == "mean":
        need = n * c - s.sum()
        order = np.argsort(w); cost = 0.0
        for j in order:
            take = min(u[j], need)
            if take > 0:
                cost += w[j] * take; need -= take
            if need <= 1e-12:
                break
        return float(cost)
    if rule == "min":
        x = np.maximum(c - s, 0.0)
        return float((w * x).sum()) if np.all(x <= u + 1e-12) else INF
    if rule == "median":
        if n % 2 == 0:
            return float("nan")
        x = np.maximum(c - s, 0.0)
        ok = (x <= u + 1e-12)
        a = int((s > c).sum()); need = (n + 1) // 2 - a
        costs = np.where(s > c, np.inf, np.where(ok, w * x, np.inf))   # only tasks not yet above c can be raised above it
        cs = np.sort(costs)[:need]
        return float(cs.sum()) if np.all(np.isfinite(cs)) else INF
    if rule == "geo" or (rule.startswith("pmean:") and float(rule.split(":")[1]) < 1):
        g, ginv = _g_prime_inv(rule)
        tau = g(np.delete(S, t, 0)).sum(1).max()
        def x_of(lam):
            with np.errstate(all="ignore"):
                y = ginv(lam * w)
            return np.clip(np.nan_to_num(y - s, nan=0.0, posinf=1e9), 0.0, u)
        lo_, hi_ = 1e-12, 1e6
        for _ in range(200):
            lam = np.sqrt(lo_ * hi_)
            if g(s + x_of(lam)).sum() >= tau:
                lo_ = lam
            else:
                hi_ = lam
        return float((w * x_of(lo_)).sum())
    return float("nan")
