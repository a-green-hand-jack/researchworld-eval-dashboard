"""Closed-simplex scores, exact split ranks, and the disclosed synthetic DGP."""
from dataclasses import dataclass
import numpy as np
from scipy.special import softmax, gammaln

SCENARIOS = {
    'dense': ((40., 40.), (0., 0.)),
    'hetero': ((160., 8.), (0., 0.)),
    'zeros': ((40., 40.), (.15, .15)),
    'mixed': ((160., 8.), (.02, .32)),
    'shift': ((160., 8.), (.02, .32)),
}
METHODS = ['Max', 'L2', 'H', 'CLR', 'CLR-e3', 'H-scale', 'H-group',
           'Coord', 'Bonf', 'CLR-e2', 'CLR-e4', 'H-weight', 'Oracle', 'H-Z', 'H-GZ']

def center(x, k):
    phase = 2*np.pi*np.arange(k)/k
    logits = (1.1*np.cos(phase)[None, :] + 1.2*x[:, None]*np.sin(phase)[None, :]
              + .4*x[:, None]**2*np.cos(2*phase)[None, :])
    return softmax(logits, axis=1)

def generate(rng, n, k, scenario, pg=.25):
    x = rng.uniform(-1, 1, n)
    g = (rng.random(n) < pg).astype(int)
    m = center(x, k)
    kap, pi = SCENARIOS[scenario]
    kap = np.asarray(kap)[g]
    y = rng.gamma(kap[:, None]*m)
    y /= y.sum(axis=1, keepdims=True)
    z = rng.random(n) < np.asarray(pi)[g]
    dropped = rng.integers(0, k, n)
    y[np.flatnonzero(z), dropped[z]] = 0.
    y /= y.sum(axis=1, keepdims=True)
    assert np.all(np.isfinite(y)) and np.all(y >= 0)
    # Exact zeros must come only from the disclosed structural-zero mechanism.
    assert np.array_equal((y == 0).any(axis=1), z)
    return dict(x=x, g=g, m=m, y=y, zero=z)

def clr(y, eps=0.):
    a = np.log(y+eps)
    return a-a.mean(axis=-1, keepdims=True)

def scores(m, y):
    delta = np.abs(m-y)
    out = {'Max':delta.max(axis=-1), 'L2':np.linalg.norm(delta, axis=-1),
           'H':np.linalg.norm(np.sqrt(m)-np.sqrt(y), axis=-1)}
    pos = (y > 0).all(axis=-1)
    safe = np.where(y > 0, y, 1.)
    out['CLR'] = np.where(pos, np.linalg.norm(clr(m)-clr(safe), axis=-1), np.inf)
    for name, eps in [('CLR-e2', .01), ('CLR-e3', .001), ('CLR-e4', .0001)]:
        out[name] = np.linalg.norm(clr(m, eps)-clr(y, eps), axis=-1)
    return out

def quantile(s, alpha=.1):
    n = len(s)
    rank = int(np.ceil((n+1)*(1-alpha)))
    if rank > n:
        return np.full(s.shape[1:], np.inf) if s.ndim > 1 else np.inf
    return np.partition(s, rank-1, axis=0)[rank-1]

def oracle_score(m, y, g, scenario):
    """Negative log DGP density relative to half interior / half face measure.

    Each stratum is normalized uniform. Faces get equal weight. Deleting j
    leaves Dirichlet(alpha[-j]), with its unrenormalized concentration vector.
    """
    kap, pi = SCENARIOS[scenario]
    kap = np.asarray(kap)[g]
    pi = np.asarray(pi)[g]
    a = kap[:,None]*m
    positive = y>0
    boundary = ~positive.all(axis=-1)
    aa = np.where(positive,a,0.)
    lognorm = gammaln(aa.sum(axis=-1))-np.where(positive,gammaln(a),0.).sum(axis=-1)
    ll = lognorm+np.where(positive,(a-1)*np.log(np.where(positive,y,1.)),0.).sum(axis=-1)
    dim = positive.sum(axis=-1)
    mass = np.where(boundary,pi,1-pi)
    with np.errstate(divide='ignore'):
        logdensity = np.log(2*mass)+ll-gammaln(dim)
    return np.where(dim >= y.shape[-1]-1,-logdensity,np.inf)

@dataclass
class Calibrator:
    thresholds: dict
    scales: np.ndarray
    scenario: str

    @classmethod
    def fit(cls, pilot, cal, alpha=.1, pg_test=.25, scenario='dense'):
        s = scores(cal['m'], cal['y'])
        ps = scores(pilot['m'], pilot['y'])['H']
        scales = np.array([np.sqrt(np.mean(ps[pilot['g']==g]**2)) for g in (0,1)])
        thresholds = {name:quantile(v, alpha) for name,v in s.items()}
        thresholds['H-scale'] = quantile(s['H']/scales[cal['g']], alpha)
        thresholds['H-group'] = np.array([quantile(s['H'][cal['g']==g], alpha) for g in (0,1)])
        thresholds['H-Z'] = np.array([quantile(s['H'][cal['zero']==z], alpha) for z in (0,1)])
        thresholds['H-GZ'] = np.array([[quantile(s['H'][(cal['g']==g)&(cal['zero']==z)], alpha)
                                      for z in (0,1)] for g in (0,1)])
        residual = np.abs(cal['m']-cal['y'])
        thresholds['Coord'] = quantile(residual, alpha)
        thresholds['Bonf'] = quantile(residual, alpha/residual.shape[1])
        # Exact covariate likelihood ratios; include test mass at infinity.
        w = np.where(cal['g']==1, pg_test/.25, (1-pg_test)/.75)
        order = np.argsort(s['H'])
        cum = np.cumsum(w[order])
        qs = []
        for g in (0,1):
            wx = pg_test/.25 if g else (1-pg_test)/.75
            ix = np.searchsorted(cum, (1-alpha)*(w.sum()+wx), side='left')
            qs.append(s['H'][order[ix]] if ix < len(order) else np.inf)
        thresholds['H-weight'] = np.array(qs)
        thresholds['Oracle'] = quantile(oracle_score(cal['m'],cal['y'],cal['g'],scenario),alpha)
        return cls(thresholds, scales, scenario)

    def contains(self, m, y, g, precomputed=None):
        s = scores(m,y) if precomputed is None else precomputed
        out = {name:s[name] <= self.thresholds[name] for name in s}
        out['H-scale'] = s['H'] <= self.thresholds['H-scale']*self.scales[g]
        out['H-group'] = s['H'] <= self.thresholds['H-group'][g]
        z=(y==0).any(axis=-1).astype(int)
        out['H-Z'] = s['H'] <= self.thresholds['H-Z'][z]
        out['H-GZ'] = s['H'] <= self.thresholds['H-GZ'][g,z]
        out['H-weight'] = s['H'] <= self.thresholds['H-weight'][g]
        out['Oracle'] = oracle_score(m,y,g,self.scenario) <= self.thresholds['Oracle']
        residual = np.abs(m-y)
        for name in ['Coord','Bonf']:
            out[name] = (residual <= self.thresholds[name]).all(axis=-1)
        return out
