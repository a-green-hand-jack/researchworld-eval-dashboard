"""Data-generating processes with known truth. Real-data DGPs resample i.i.d. (with replacement) from the full
(Y, Yhat) pairs of an example data set, so the target is the exact mean of Y in that empirical population."""
import numpy as np
from scipy.special import expit, logit
D = '/work/data/'

TRANSFORMS = {
    'id':    lambda f: f,
    'logit': lambda f: logit(np.clip(f, 1e-3, 1 - 1e-3)),   # classifier scores on the logit scale
    'pow3':  lambda f: f ** 3,                              # distorted (non-calibrated) probability scores
    'exp':   lambda f: np.exp(f / 4.0),                     # convex monotone distortion of a continuous predictor
    'sqrt':  lambda f: np.sqrt(np.maximum(f, 0)),           # concave monotone distortion (nonnegative predictors)
}

class PopDGP:
    def __init__(self, name, transform='id', y=None, f=None, f_unl_pool=None, truth=None):
        if y is None:
            d = np.load(D + name + '.npz'); y = d['Y'].astype(float); f = d['Yhat'].astype(float)
        self.y = y; self.f = TRANSFORMS[transform](f); self.name = f'{name}|{transform}'
        self.truth = float(y.mean()) if truth is None else truth
        self.f_unl_pool = None if f_unl_pool is None else TRANSFORMS[transform](f_unl_pool)
        self.P = len(y)
    def sample(self, rng, n, N):
        i = rng.integers(0, self.P, n + N)
        if self.f_unl_pool is not None:   # distribution-shift case: unlabeled predictions come from another population
            return self.y[i[:n]], self.f[i[:n]], self.f_unl_pool[rng.integers(0, len(self.f_unl_pool), N)]
        return self.y[i[:n]], self.f[i[:n]], self.f[i[n:]]

class SynthQuad:
    """f ~ N(0,1); Y = a f + c (f^2-1)/sqrt2 + sigma eps.  E[Y]=0, Var(h)=c^2 (nonlinear part of E[Y|f]), residual var sigma^2."""
    def __init__(self, a=1.0, c=0.0, sigma=1.0):
        self.a, self.c, self.sigma = a, c, sigma; self.truth = 0.0; self.name = f'quad(a={a},c={c},s={sigma})'
    def sample(self, rng, n, N):
        f = rng.standard_normal(n + N)
        y = self.a * f + self.c * (f ** 2 - 1) / np.sqrt(2) + self.sigma * rng.standard_normal(n + N)
        return y[:n], f[:n], f[n:]
    def moments(self):
        V = 1.0; return dict(var_f=V, slope=self.a, var_h=self.c ** 2, sig2=self.sigma ** 2, var_y=self.a ** 2 + self.c ** 2 + self.sigma ** 2)

class SynthLogit:
    """Classifier that outputs logit-scale scores: f ~ N(mu, s^2), Y ~ Bernoulli(expit(f)).  E[Y|f] = expit(f) (nonlinear in f)."""
    def __init__(self, mu=-1.0, s=2.0):
        self.mu, self.s = mu, s; self.name = f'logit(mu={mu},s={s})'
        z, w = np.polynomial.hermite_e.hermegauss(200); w = w / w.sum()
        ff = mu + s * z; g = expit(ff)
        self.truth = float((w * g).sum()); vf = (w * ff ** 2).sum() - mu ** 2
        cov = (w * g * ff).sum() - self.truth * mu; self._mom = (w, ff, g, vf, cov)
    def sample(self, rng, n, N):
        f = self.mu + self.s * rng.standard_normal(n + N)
        y = (rng.random(n + N) < expit(f)).astype(float)
        return y[:n], f[:n], f[n:]
    def moments(self):
        w, ff, g, vf, cov = self._mom; b = cov / vf; th = self.truth
        var_g = (w * g ** 2).sum() - th ** 2; var_h = var_g - b * b * vf
        return dict(var_f=vf, slope=b, var_h=var_h, sig2=(w * g * (1 - g)).sum(), var_y=th * (1 - th))

def asym_vars(mom, n, N):
    """Asymptotic variances (of sqrt-free estimator) of: classical, PPI (lam=1; needs Cov), PPI++ (optimal lam), efficient."""
    m = n + N; V, b, vh, s2, vy = mom['var_f'], mom['slope'], mom['var_h'], mom['sig2'], mom['var_y']
    classical = vy / n
    ppipp = (s2 + vh) / n + b * b * V / m
    eff = s2 / n + (b * b * V + vh) / m
    return dict(classical=classical, ppipp=ppipp, eff=eff)
