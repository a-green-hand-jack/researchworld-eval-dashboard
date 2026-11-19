"""Simplex geometry helpers: closure, CLR, distances."""
import numpy as np
from scipy.special import gammaln, digamma

EPS = 1e-12


def closure(a):
    a = np.asarray(a, float)
    return a / a.sum(-1, keepdims=True)


def clr(y, eps=EPS):
    ly = np.log(np.maximum(y, eps))
    return ly - ly.mean(-1, keepdims=True)


def inv_clr(z):
    z = z - z.max(-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(-1, keepdims=True)


def replace_zeros(y, delta=1e-4):
    """Multiplicative zero replacement (Martin-Fernandez 2003 style)."""
    y = np.asarray(y, float)
    z = y <= 0
    if not z.any():
        return y
    nz = z.sum(-1, keepdims=True)
    out = np.where(z, delta, y * (1 - delta * nz))
    return out


def dirichlet_logpdf(y, alpha):
    y = np.maximum(y, EPS)
    return gammaln(alpha.sum(-1)) - gammaln(alpha).sum(-1) + ((alpha - 1) * np.log(y)).sum(-1)


def sample_dirichlet(rng, alpha, size=None):
    """alpha: (..., K); returns (size, ..., K) via gamma."""
    shape = (size,) + alpha.shape if size else alpha.shape
    g = rng.gamma(np.broadcast_to(alpha, shape))
    g = np.maximum(g, 1e-300)
    return g / g.sum(-1, keepdims=True)


def uniform_simplex(rng, m, K):
    return rng.dirichlet(np.ones(K), size=m)


def simplex_lebesgue_volume(K):
    """(K-1)-dim volume of the simplex w.r.t. Lebesgue measure on its first K-1 coordinates."""
    return float(np.exp(-gammaln(K)))
