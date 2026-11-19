"""Simplex helpers, compositional scores, and Dirichlet utilities."""
import numpy as np
from scipy.special import gammaln, softmax

EPS_DEFAULT = 1e-3


def closure(a):
    a = np.asarray(a, float)
    return a / a.sum(-1, keepdims=True)


def replace_zeros(y, eps=EPS_DEFAULT):
    """Additive zero replacement then closure (keeps strictly positive vectors)."""
    return closure(np.asarray(y, float) + eps)


def clr(y):
    ly = np.log(y)
    return ly - ly.mean(-1, keepdims=True)


# ---- scores s(y, p): y target on simplex (n,D) or (m,D); p prediction (n,D) or (D,) ----
def score_l2(y, p, **kw):
    return np.sqrt(((y - p) ** 2).sum(-1))


def score_l1(y, p, **kw):  # total variation distance
    return 0.5 * np.abs(y - p).sum(-1)


def score_hell(y, p, **kw):
    return np.sqrt(((np.sqrt(y) - np.sqrt(p)) ** 2).sum(-1))


def score_kl(y, p, eps=EPS_DEFAULT, **kw):  # KL(y || p), 0 log 0 = 0
    p = replace_zeros(p, 1e-9)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(y > 0, y * (np.log(np.where(y > 0, y, 1.0)) - np.log(p)), 0.0)
    return t.sum(-1)


def score_ait(y, p, eps=EPS_DEFAULT, **kw):
    return np.sqrt(((clr(replace_zeros(y, eps)) - clr(replace_zeros(p, eps))) ** 2).sum(-1))


def score_linf(y, p, **kw):
    return np.abs(y - p).max(-1)


def dirichlet_logpdf(y, alpha):
    return gammaln(alpha.sum(-1)) - gammaln(alpha).sum(-1) + ((alpha - 1) * np.log(y)).sum(-1)


def make_score_nll(phi):
    def score_nll(y, p, eps=EPS_DEFAULT, **kw):
        return -dirichlet_logpdf(replace_zeros(y, eps), phi * replace_zeros(p, 1e-9))
    return score_nll


BASE_SCORES = {"l2": score_l2, "l1": score_l1, "hell": score_hell, "kl": score_kl,
               "ait": score_ait, "linf": score_linf}


def fit_dirichlet_precision(Y, P, eps=EPS_DEFAULT):
    """MLE of a single precision phi given predicted means P (Dirichlet(phi*P))."""
    from scipy.optimize import minimize_scalar
    Yr, Pr = replace_zeros(Y, eps), replace_zeros(P, 1e-9)
    f = lambda lp: -dirichlet_logpdf(Yr, np.exp(lp) * Pr).mean()
    r = minimize_scalar(f, bounds=(-2, 9), method="bounded")
    return float(np.exp(r.x))


def uniform_simplex(m, D, rng):
    return rng.dirichlet(np.ones(D), size=m)
