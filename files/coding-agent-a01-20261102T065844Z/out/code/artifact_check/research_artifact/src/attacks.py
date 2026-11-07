"""Exact score-space attacks. Infinity is represented by d+1 for support costs.

All public functions accept a complete nonnegative matrix; no training response
is estimated. Even-dimensional medians use the average of the middle two values.
"""
from __future__ import annotations
import itertools
import numpy as np
from scipy.optimize import brentq

RULES = ("mean", "median", "geometric", "minimum")
TOL = 1e-12

def aggregate(x, rule, axis=-1, weights=None):
    if rule == "mean":
        return np.average(x, axis=axis, weights=weights)
    if rule == "median":
        return np.median(x, axis=axis)
    if rule == "minimum":
        return np.min(x, axis=axis)
    if rule == "geometric":
        with np.errstate(divide="ignore"):
            return np.exp(np.mean(np.log(x), axis=axis))
    raise ValueError(rule)

def thresholds(x, rule, margin=0., weights=None):
    scores = aggregate(x, rule, weights=weights)
    if len(scores) < 2:
        raise ValueError("At least two entries required")
    order = np.argsort(scores, kind="stable")
    tau = np.full(len(scores), scores[order[-1]])
    tau[order[-1]] = scores[order[-2]]
    return tau + margin

def caps(x, kind="perfect", rho=1.):
    if kind == "perfect":
        end = np.ones(x.shape[1])
    elif kind == "observed":
        end = x.max(axis=0)
    else:
        raise ValueError(kind)
    return x + rho * (end - x)

def _prefix_cost(gains, required, tol=TOL):
    n, d = gains.shape
    cumulative = np.c_[np.zeros(n), np.cumsum(np.sort(gains, axis=1)[:, ::-1], axis=1)]
    sufficient = cumulative >= required[:, None] - tol
    result = np.argmax(sufficient, axis=1)
    result[~sufficient.any(axis=1)] = d+1
    return result

def all_subsets(d):
    if d > 16:
        raise ValueError("Exhaustive solver restricted to d<=16")
    masks = ((np.arange(2**d)[:, None] >> np.arange(d)) & 1).astype(bool)
    return masks[np.argsort(masks.sum(axis=1), kind="stable")]

def min_support(x, u, tau, rule, weights=None):
    """Minimum changed coordinates to achieve score >= tau, using endpoint u.

    Monotonicity means a feasible attack can always be pushed to its endpoints.
    Median for even d<=16 is exhaustively solved, other cases are analytic.
    """
    x, u, tau = np.asarray(x), np.asarray(u), np.asarray(tau)
    n, d = x.shape
    assert u.shape == x.shape and tau.shape == (n,)
    assert (u >= x-TOL).all()
    if rule == "mean":
        w = np.full(d, 1/d) if weights is None else np.asarray(weights)/np.sum(weights)
        return _prefix_cost((u-x)*w, tau - x@w)
    if rule == "geometric":
        # Zero coordinates must all be changed whenever the threshold is positive.
        zero = x == 0
        impossible = (u <= 0).any(axis=1) & (tau > TOL)
        base = np.where(zero, u, x)
        with np.errstate(divide="ignore", invalid="ignore"):
            gains = np.where(zero, 0., np.log(u)-np.log(x))
            required = d*np.log(tau) - np.log(base).sum(axis=1)
        gains = np.nan_to_num(gains, nan=0., neginf=0., posinf=0.)
        k = _prefix_cost(gains, required, tol=d*TOL) + zero.sum(axis=1)
        k[(k > d) | impossible] = d+1
        k[tau <= TOL] = 0
        return k
    if rule == "minimum":
        k = (x < tau[:, None]-TOL).sum(axis=1)
        k[(u < tau[:, None]-TOL).any(axis=1)] = d+1
        return k
    if rule == "median" and d % 2:
        h = (d+1)//2
        already = (x >= tau[:, None]-TOL).sum(axis=1)
        possible = (u >= tau[:, None]-TOL).sum(axis=1)
        k = np.maximum(h-already, 0)
        k[possible < h] = d+1
        return k
    if rule == "median" and d <= 16:
        masks = all_subsets(d)
        y = np.where(masks[None, :, :], u[:, None, :], x[:, None, :])
        sufficient = aggregate(y, rule) >= tau[:, None]-TOL
        k = masks.sum(axis=1)[np.argmax(sufficient, axis=1)]
        k[~sufficient.any(axis=1)] = d+1
        return k
    raise NotImplementedError((rule, d))

def min_mass_one(x, u, tau, rule):
    """Infimum normalized L1 score increase; the threshold includes any margin."""
    x, u = np.asarray(x), np.asarray(u)
    d = len(x)
    if aggregate(x, rule) >= tau-TOL:
        return 0.
    if aggregate(u, rule) < tau-TOL:
        return np.inf
    if rule == "mean":
        return max(0., tau - x.mean())
    if rule == "minimum":
        return np.maximum(tau-x, 0).sum()/d
    if rule == "geometric":
        if (u <= 0).any():
            return np.inf
        def error(level):
            with np.errstate(divide="ignore"):
                return np.log(np.minimum(u, np.maximum(x, level))).sum() - d*np.log(tau)
        lo = max(np.nextafter(0., 1.), min(float(x.min()), tau)/2)
        level = brentq(error, lo, float(u.max()), xtol=1e-14)
        return (np.minimum(u, np.maximum(x, level))-x).sum()/d
    if rule == "median" and d % 2:
        h = (d+1)//2
        costs = np.where(u >= tau-TOL, np.maximum(tau-x, 0), np.inf)
        return np.sort(costs)[:h].sum()/d
    if rule == "median":
        # y_(m)>=a and y_(m+1)>=b, a+b=2*tau, a<=b.
        # Choose m upper coordinates and one additional lower coordinate.
        m = d//2
        best = np.inf
        for upper in itertools.combinations(range(d), m):
            upper = np.asarray(upper)
            for lower in set(range(d))-set(upper):
                lo = max(0., 2*tau-u[upper].min())
                hi = min(tau, u[lower])
                if lo > hi+TOL:
                    continue
                candidates = np.clip(np.r_[lo, hi, x[lower], 2*tau-x[upper]], lo, hi)
                costs = (np.maximum(2*tau-candidates[:, None]-x[upper], 0).sum(axis=1)
                         + np.maximum(candidates-x[lower], 0))
                best = min(best, costs.min())
        return best/d
    raise ValueError(rule)

def support_witness(x, u, tau, rule):
    """Return a minimum-support endpoint witness for one target."""
    d = len(x)
    k = min_support(x[None], u[None], np.array([tau]), rule)[0]
    if k > d:
        return None
    if k == 0:
        return np.array([], dtype=int)
    if rule == "mean":
        selected = np.argsort(-(u-x), kind="stable")[:k]
    elif rule == "geometric":
        zeros = np.flatnonzero(x == 0)
        positive = np.flatnonzero(x > 0)
        order = positive[np.argsort(-np.log(u[positive]/x[positive]), kind="stable")]
        selected = np.r_[zeros, order[:k-len(zeros)]]
    elif rule == "minimum":
        selected = np.flatnonzero(x < tau-TOL)
    elif d % 2:
        selected = np.flatnonzero((x < tau-TOL) & (u >= tau-TOL))[:k]
    else:
        for mask in all_subsets(d):
            if mask.sum() == k and aggregate(np.where(mask, u, x), rule) >= tau-TOL:
                selected = np.flatnonzero(mask)
                break
    y = x.copy()
    y[selected] = u[selected]
    assert aggregate(y, rule) >= tau-10*TOL
    assert len(selected) == k
    return selected
