"""Search-episode simulator on a cached outcome matrix Y[K,N] (config x question, 0/1 correctness).
Optimizers operate on a dev slice Yd = Y[:, D]; reporting methods turn an episode into a score estimate / CI."""
import numpy as np
from scipy import stats, optimize

N_INSTR = 8   # world A: config id = demo*8 + instr (matches common.config_list)
STRUCT = np.array([[k % 8, k // 8] for k in range(40)])   # per-config factor levels; set per world via set_struct()
def set_struct(S):
    global STRUCT; STRUCT = np.asarray(S)

# ---------------------------------------------------------------- utilities
def argmax_rand(v, rng):
    c = np.flatnonzero(v >= v.max() - 1e-12)
    return c[rng.integers(len(c))] if len(c) > 1 else c[0]

def wilson(x, n, z=1.959964):
    p = x / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h

# ---------------------------------------------------------------- optimizers
# each returns dict(k=chosen config id, vis=ids that were evaluated on the FULL dev set)
def opt_grid(Yd, space, rng, **kw):
    s = Yd[space].mean(1)
    return dict(k=space[argmax_rand(s, rng)], vis=space)

def opt_random(Yd, space, rng, B=8, **kw):
    sub = rng.choice(space, min(B, len(space)), replace=False)
    s = Yd[sub].mean(1)
    return dict(k=sub[argmax_rand(s, rng)], vis=sub)

def opt_sh(Yd, space, rng, frac=0.5, **kw):
    """Successive halving over questions (best-arm-identification style). Total budget = frac*K*n (config,question) evals."""
    n = Yd.shape[1]; K0 = len(space); perm = rng.permutation(n)
    R = max(1, int(np.ceil(np.log2(K0)))); T = frac * K0 * n
    alive = np.array(space); m_prev = 0
    for r in range(R):
        if len(alive) == 1: break
        p = int(T / (len(alive) * R))
        m = int(min(n, max(m_prev + 1, m_prev + p)))
        cols = perm[:m]; s = Yd[alive][:, cols].mean(1)
        keep = max(1, int(np.ceil(len(alive) / 2)))
        order = np.argsort(-(s + 1e-9 * rng.random(len(s))))
        alive = alive[order[:keep]]; m_prev = m
    k = alive[0] if len(alive) == 1 else alive[argmax_rand(Yd[alive].mean(1), rng)]
    return dict(k=k, vis=np.array([k]))

def _neighbors(k, space_set):
    """configs in the space that differ from k in exactly one factor"""
    d = (STRUCT != STRUCT[k]).sum(1)
    return [int(x) for x in np.flatnonzero(d == 1) if int(x) in space_set]

def opt_minibatch(Yd, space, rng, T=30, bfrac=0.25, full_every=10, explore=0.5, **kw):
    """MIPRO-like: propose candidates (random / neighbour of incumbent), score on a random minibatch,
    periodically evaluate the incumbent on the full dev set; final = best full-dev score."""
    n = Yd.shape[1]; b = int(max(5, min(n, round(bfrac * n)))); sset = set(int(x) for x in space)
    sums, cnt, full = {}, {}, {}
    best = None
    for t in range(T):
        if best is None or rng.random() < explore: cand = int(rng.choice(space))
        else:
            nb = _neighbors(best, sset); cand = int(rng.choice(nb)) if nb else int(rng.choice(space))
        mb = rng.choice(n, b, replace=False)
        sums[cand] = sums.get(cand, 0) + Yd[cand, mb].sum(); cnt[cand] = cnt.get(cand, 0) + b
        best = max(sums, key=lambda c: (sums[c] / cnt[c], rng.random()))
        if (t + 1) % full_every == 0 and best not in full: full[best] = Yd[best].mean()
    if best not in full: full[best] = Yd[best].mean()
    ks = np.array(list(full)); v = np.array([full[k] for k in ks])
    return dict(k=ks[argmax_rand(v, rng)], vis=ks)

def opt_greedy(Yd, space, rng, sweeps=3, **kw):
    """Coordinate ascent over the factor axes with full-dev evaluation."""
    sset = set(int(x) for x in space); cur = int(rng.choice(space)); cache = {}
    def ev(c):
        if c not in cache: cache[c] = Yd[c].mean()
        return cache[c]
    for _ in range(sweeps):
        changed = False
        for axis in rng.permutation(STRUCT.shape[1]):
            others = [a for a in range(STRUCT.shape[1]) if a != axis]
            cands = [c for c in sset if all(STRUCT[c, a] == STRUCT[cur, a] for a in others)]
            v = np.array([ev(c) for c in cands]); best = cands[argmax_rand(v, rng)]
            if ev(best) > ev(cur) + 1e-12: cur = best; changed = True
        if not changed: break
    return dict(k=cur, vis=np.array(list(cache)))

OPTS = dict(grid=opt_grid, random=opt_random, sh=opt_sh, minibatch=opt_minibatch, greedy=opt_greedy)

# ---------------------------------------------------------------- reporting methods
def boot_optimism(Yd, space, rng, opt, nb=100, oob=False, **kw):
    """Search-replay bootstrap: rerun the optimizer on bootstrap resamples of the dev set."""
    n = Yd.shape[1]; app = np.empty(nb); orig = np.empty(nb); oobacc = np.full(nb, np.nan)
    mu = Yd.mean(1)
    for b in range(nb):
        idx = rng.integers(n, size=n)
        r = OPTS[opt](Yd[:, idx], space, rng, **kw); k = r['k']
        app[b] = Yd[k, idx].mean(); orig[b] = mu[k]
        if oob:
            msk = np.ones(n, bool); msk[idx] = False
            if msk.any(): oobacc[b] = Yd[k, msk].mean()
    return app, orig, oobacc

def maxt_bounds(Yv, kpos, rng, alpha=0.05, nmult=1000):
    """Simultaneous (max-t, Gaussian-multiplier bootstrap) interval for config at row kpos among rows of Yv (all fully evaluated)."""
    m, n = Yv.shape; mu = Yv.mean(1)
    sd = np.sqrt(np.maximum(mu * (1 - mu), 1.0 / (4 * n)))
    Xc = (Yv - mu[:, None]) / sd[:, None]
    G = rng.standard_normal((nmult, n)) @ Xc.T / np.sqrt(n)
    c2 = np.quantile(np.abs(G).max(1), 1 - alpha); c1 = np.quantile(G.max(1), 1 - alpha)
    se = sd[kpos] / np.sqrt(n)
    return mu[kpos], (mu[kpos] - c2 * se, mu[kpos] + c2 * se), mu[kpos] - c1 * se, c2

def cond_winner(Yv, kpos, alpha=0.05, rng=None):
    """Conditional (polyhedral / truncated-Gaussian) inference for the argmax winner (Lee et al. 2016; Andrews et al. 2024 style).
    Returns median-unbiased estimate and equal-tailed (1-alpha) CI for theta_k given k = argmax."""
    m, n = Yv.shape; mu = Yv.mean(1)
    # accuracies are discrete, so exact ties with the winner are common; emulate random tie-breaking by a uniform jitter
    # of width 1/n on the tied estimates (the winner receives the largest jitter among the tied set)
    rng = rng or np.random.default_rng(0)
    tied = np.flatnonzero(mu >= mu[kpos] - 1e-12)
    if len(tied) > 1:
        mu = mu.copy(); mu[tied] += rng.uniform(-0.5 / n, 0.5 / n, len(tied)); mu[kpos] = mu[tied].max() + 1e-12
    S = np.cov(Yv) / n if m > 1 else np.array([[mu[0] * (1 - mu[0]) / n]])
    S = S + 1e-12 * np.eye(m)
    k = kpos; sk = S[k, k]; c = S[:, k] / sk
    z = mu - c * mu[k]
    a_c = np.delete(c, k) - c[k]       # (e_j - e_k)^T c
    a_z = np.delete(z, k) - z[k]       # (e_j - e_k)^T z   ;  constraint: a_c * t + a_z <= 0
    lo, hi = -np.inf, np.inf
    for ac, az in zip(a_c, a_z):
        if abs(ac) < 1e-14: continue
        bound = -az / ac
        if ac > 0: hi = min(hi, bound)
        else: lo = max(lo, bound)
    t = mu[k]; sd = np.sqrt(sk)
    def F(theta):  # truncated normal cdf at t (numerically stable in both tails)
        a, b, x = (lo - theta) / sd, (hi - theta) / sd, (t - theta) / sd
        if a > 0:   # work with survival functions / logs
            la, lx, lb = stats.norm.logsf(a), stats.norm.logsf(x), (stats.norm.logsf(b) if np.isfinite(b) else -np.inf)
            return (1 - np.exp(lx - la)) / (1 - np.exp(lb - la))
        if b < 0:   # lower-tail logs
            lb_, lx = stats.norm.logcdf(b), stats.norm.logcdf(x); la = stats.norm.logcdf(a) if np.isfinite(a) else -np.inf
            return (np.exp(lx - lb_) - np.exp(la - lb_)) / (1 - np.exp(la - lb_))
        den = stats.norm.cdf(b) - stats.norm.cdf(a)
        return (stats.norm.cdf(x) - stats.norm.cdf(a)) / den
    L, U = t - 400 * sd, t + 40 * sd
    def inv(q):  # F decreasing in theta; unbounded solutions are clipped to the ends of the bracket
        fl, fu = F(L) - q, F(U) - q
        if fl < 0: return L
        if fu > 0: return U
        return optimize.brentq(lambda th: F(th) - q, L, U, xtol=1e-6)
    return inv(0.5), (inv(1 - alpha / 2), inv(alpha / 2)), (lo, hi)

def ladder(Yd, space, rng, eta):
    """Ladder (Blum & Hardt 2015) as the search-and-report mechanism: process candidates in random order,
    accept a new best only if its dev score beats the current best by > eta; report the rounded incumbent score."""
    order = rng.permutation(space); best = order[0]; s = Yd[best].mean(); s = np.round(s / eta) * eta
    for c in order[1:]:
        v = Yd[c].mean()
        if v > s + eta: best = c; s = np.round(v / eta) * eta
    return best, s

def eb_winner(Yv, kpos, z=1.959964):
    """Empirical-Bayes (normal-normal) shrinkage for config kpos among the m fully evaluated configs (winner's-curse correction).
    theta_k = g + d_k with d_k ~ N(0, tau^2) exchangeable; the dev means have paired sampling covariance S/n. The grand mean g is
    estimated by the average of the dev means (error variance u = 1'S1/m^2); tau^2 by moments on the centred means.
    Returns point estimate and two intervals: (posterior) est +- z sqrt(u + B v_k) and (unshrunk) est +- z sqrt(u + v_k)."""
    m, n = Yv.shape; mu = Yv.mean(1)
    if m < 3: return mu[kpos], (mu[kpos], mu[kpos]), (mu[kpos], mu[kpos])
    S = np.cov(Yv) / n; P = np.eye(m) - 1.0 / m
    Sc = P @ S @ P; v = np.maximum(np.diag(Sc), 0) * m / (m - 1)
    u = S.sum() / m ** 2
    dev = mu - mu.mean(); tau2 = max(0.0, (dev @ dev) / (m - 1) - v.sum() / m)
    B = tau2 / (tau2 + v[kpos] + 1e-18)
    est = mu.mean() + B * dev[kpos]
    sp = np.sqrt(u + B * v[kpos]); sw = np.sqrt(u + v[kpos])
    return est, (est - z * sp, est + z * sp), (est - z * sw, est + z * sw)
