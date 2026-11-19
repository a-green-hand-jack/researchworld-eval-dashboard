"""Fixed-score mean intervals. All inputs are arrays of repeated independent trials.
Finite-sample CP guarantees are mathematical (real arithmetic); numerical endpoints
are padded outwards. Beta-quantile library errors are not formally verified.
"""
import numpy as np
from scipy.special import betaincinv, ndtri

ALPHA = 0.05
PAD = 1e-10


def cp(t, m, error=ALPHA):
    """Equal-tailed CP, including m=0 -> [0,1]. Broadcast arrays."""
    t, m = np.broadcast_arrays(np.asarray(t, dtype=float), np.asarray(m, dtype=float))
    if np.any(t < 0) or np.any(t > m) or np.any(m < 0):
        raise ValueError('invalid binomial counts')
    a = betaincinv(np.maximum(t, 1), np.maximum(m-t+1, 1), error/2)
    b = betaincinv(np.maximum(t+1, 1), np.maximum(m-t, 1), 1-error/2)
    a = np.where((t == 0) | (m == 0), 0., a)
    b = np.where((t == m) | (m == 0), 1., b)
    return np.maximum(0., a-PAD), np.minimum(1., b+PAD)


def box_simplex(c, low, high, maximize=False):
    """Greedy primal locates a dual threshold, then evaluates a valid dual bound.
    For min, lambda+sum min_{l<=w<=u}(c-lambda)w is always a LOWER
    certificate, independently of approximate primal feasibility. For max use
    max instead. Arrays rows=trials, columns=bins. K<=8, 1e-10 padding dominates
    elementary-double-arithmetic error for inputs in [0,1].
    """
    c, low, high = [np.atleast_2d(np.asarray(v, float)) for v in (c, low, high)]
    if c.shape != low.shape or c.shape != high.shape:
        raise ValueError('shapes must match')
    bad = (np.sum(low, axis=1) > 1+PAD) | (np.sum(high, axis=1) < 1-PAD)
    order = np.argsort(-c if maximize else c, axis=1, kind='stable')
    costs = np.take_along_axis(c, order, axis=1)
    cap = np.take_along_axis(high-low, order, axis=1)
    residual = np.maximum(0., 1-low.sum(axis=1))
    stop = np.sum(np.cumsum(cap, axis=1) < residual[:, None], axis=1)
    stop = np.clip(stop, 0, c.shape[1]-1)
    lam = costs[np.arange(len(costs)), stop]
    diff = c-lam[:, None]
    if maximize:
        vertex = np.where(diff >= 0, high, low)
    else:
        vertex = np.where(diff >= 0, low, high)
    result = lam+np.sum(diff*vertex, axis=1)
    result = result + (PAD if maximize else -PAD)
    result[bad | ~np.isfinite(result)] = 1. if maximize else 0.
    return np.clip(result, 0., 1.)


def partition_cp(t, counts, uc, error=ALPHA, known_weights=None):
    k = t.shape[1]
    if k == 1:
        return cp(t[:, 0], counts[:, 0], error)
    if known_weights is not None:
        a, b = cp(t, counts, error/k)
        weights = np.broadcast_to(known_weights, t.shape)
        return np.clip((a*weights).sum(1)-PAD, 0, 1), np.clip((b*weights).sum(1)+PAD, 0, 1)
    a, b = cp(t, counts, error/(2*k))
    l, u = cp(uc, uc.sum(1)[:, None], error/(2*k))
    return box_simplex(a, l, u), box_simplex(b, l, u, maximize=True)


def wald(center, var, error=ALPHA):
    radius = ndtri(1-error/2)*np.sqrt(np.maximum(0., var))
    low, high = np.clip(center-radius, 0., 1.), np.clip(center+radius, 0., 1.)
    bad = ~np.isfinite(low) | ~np.isfinite(high)
    return np.where(bad, 0., low), np.where(bad, 1., high)


def counts8(s, y=None):
    b, size = s.shape
    ids = np.minimum((s*8).astype(int), 7)
    if np.any(ids < 0):
        raise ValueError('scores outside [0,1]')
    flat = ids+8*np.arange(b)[:, None]
    counts = np.bincount(flat.ravel(), minlength=b*8).reshape(b, 8)
    total = None if y is None else np.bincount(flat.ravel(), weights=y.ravel(), minlength=b*8).reshape(b, 8)
    return counts, total


def aggregate(v, name):
    if name == 'all':
        return v.sum(1, keepdims=True)
    if name == 'half':
        return v.reshape(len(v), 2, 4).sum(2)
    if name == 'tails':
        return np.column_stack((v[:, :2].sum(1)+v[:, 6:].sum(1), v[:, 2:6].sum(1)))
    if name == 'four':
        return v.reshape(len(v), 4, 2).sum(2)
    if name == 'eight':
        return v
    raise ValueError(name)


def bin_wald(t, c, u, n, N):
    mean_y = t.sum(1)/n
    p = np.divide(t, c, out=np.broadcast_to(mean_y[:, None], t.shape).copy(), where=c > 0)
    h = p/(1+n/N)
    center = mean_y + ((u/N-c/n)*h).sum(1)
    residual_mean = mean_y-(c*h).sum(1)/n
    residual_second = (t-2*t*h+c*h*h).sum(1)/n
    var_l = np.maximum(0., residual_second-residual_mean**2)*n/(n-1)
    mean_u = (u*h).sum(1)/N
    var_u = np.maximum(0., (u*h*h).sum(1)/N-mean_u**2)*N/(N-1)
    return wald(center, var_l/n+var_u/N), (c == 0).sum(1)


def shortest(candidates):
    low = np.column_stack([x[0] for x in candidates])
    high = np.column_stack([x[1] for x in candidates])
    chosen = np.argmin(high-low, axis=1)
    rows = np.arange(len(chosen))
    return (low[rows, chosen], high[rows, chosen]), chosen


def all_intervals(y, sl, su, true_tail_weights=None):
    b, n = y.shape
    N = su.shape[1]
    mean_y, mean_l, mean_u = y.mean(1), sl.mean(1), su.mean(1)
    var_y = y.var(1, ddof=1)
    results = {'label_wald': wald(mean_y, var_y/n), 'label_cp': cp(y.sum(1), n)}
    pooled_mean = (sl.sum(1)+su.sum(1))/(n+N)
    pooled_var = (np.square(sl).sum(1)+np.square(su).sum(1)-(n+N)*pooled_mean**2)/(n+N-1)
    cov = ((y-mean_y[:, None])*(sl-mean_l[:, None])).sum(1)/(n-1)
    # A truly constant score gives zero contrast, including cancellation tolerance.
    constant = np.ptp(sl, axis=1)+np.ptp(su, axis=1) == 0
    lam = np.divide(cov, (1+n/N)*pooled_var, out=np.zeros_like(cov), where=(pooled_var > 1e-14) & ~constant)
    for name, coefficient in [('ppi', np.ones(b)), ('ppi_pp', lam)]:
        residual = y-coefficient[:, None]*sl
        center = mean_y+coefficient*(mean_u-mean_l)
        variance = residual.var(1, ddof=1)/n+coefficient**2*su.var(1, ddof=1)/N
        results[name] = wald(center, variance)
    c8, t8 = counts8(sl, y)
    u8, _ = counts8(su)
    counts, successes, uc = {}, {}, {}
    empties = {}
    for part in ['all', 'half', 'tails', 'four', 'eight']:
        counts[part], successes[part], uc[part] = [aggregate(v, part) for v in (c8, t8, u8)]
        if part != 'all':
            results['wald_'+part], empties[part] = bin_wald(successes[part], counts[part], uc[part], n, N)
    candidates, adjusted = [results['label_cp']], [cp(y.sum(1), n, ALPHA/4)]
    for part in ['half', 'tails', 'four']:
        results['cp_'+part] = partition_cp(successes[part], counts[part], uc[part])
        candidates.append(results['cp_'+part])
        adjusted.append(partition_cp(successes[part], counts[part], uc[part], ALPHA/4))
    results['safe_cp'], safe_chosen = shortest(adjusted)
    results['unsafe_cp'], unsafe_chosen = shortest(candidates)
    if true_tail_weights is not None:
        results['oracle_mass_cp'] = partition_cp(successes['tails'], counts['tails'], uc['tails'], known_weights=true_tail_weights)
    diagnostics = {'lambda': lam, 'safe_choice': safe_chosen, 'unsafe_choice': unsafe_chosen, **{'empty_'+k: v for k, v in empties.items()}}
    return results, diagnostics
