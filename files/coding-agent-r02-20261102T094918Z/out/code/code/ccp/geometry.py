"""Scores (distances / divergences) between compositions y and a predicted composition yhat.

All functions take arrays of shape (..., D) and return shape (...,).  Every score is a
*non-negative, larger = worse* nonconformity score s(y, yhat).  We use square-root forms so
that scores are on a distance scale (this does not matter for split CP, which is invariant
to monotone transformations of the score, but it matters for readability of radii).
"""
import numpy as np

EPS = 1e-12


def clr(x, delta=0.0):
    x = np.asarray(x, dtype=np.float64)
    if delta > 0:
        x = closure_zero_replace(x, delta)
    lx = np.log(np.maximum(x, EPS))
    return lx - lx.mean(-1, keepdims=True)


def closure_zero_replace(x, delta):
    """Multiplicative-style replacement: add delta to every component and renormalise.
    (Simple additive replacement; delta is a hyper-parameter, see paper.)"""
    x = np.asarray(x, dtype=np.float64) + delta
    return x / x.sum(-1, keepdims=True)


def s_euclid(y, yh):
    return np.sqrt(((y - yh) ** 2).sum(-1))


def s_tv(y, yh):
    return 0.5 * np.abs(y - yh).sum(-1)


def s_hellinger(y, yh):
    return np.sqrt(((np.sqrt(y) - np.sqrt(yh)) ** 2).sum(-1))


def s_chi2(y, yh):
    """Pearson chi-square distance, sqrt( sum (y-yh)^2 / yh )."""
    return np.sqrt(((y - yh) ** 2 / np.maximum(yh, EPS)).sum(-1))


def s_kl(y, yh):
    """sqrt of KL(y || yh) (forward KL; finite when y has zeros)."""
    t = np.where(y > 0, y * (np.log(np.maximum(y, EPS)) - np.log(np.maximum(yh, EPS))), 0.0)
    return np.sqrt(np.maximum(t.sum(-1), 0.0))


def s_rkl(y, yh):
    """sqrt of KL(yh || y) (reverse KL; huge when y has zeros -> needs zero replacement)."""
    t = yh * (np.log(np.maximum(yh, EPS)) - np.log(np.maximum(y, EPS)))
    return np.sqrt(np.maximum(t.sum(-1), 0.0))


def make_aitchison(delta):
    def s_aitchison(y, yh):
        return np.sqrt(((clr(y, delta) - clr(yh, delta)) ** 2).sum(-1))
    s_aitchison.__name__ = f"s_aitchison_d{delta}"
    return s_aitchison


SCORES = {
    "euclid": s_euclid,
    "tv": s_tv,
    "hellinger": s_hellinger,
    "chi2": s_chi2,
    "kl": s_kl,
    "aitchison": make_aitchison(1e-6),
}


def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


def make_boxcox(lam):
    """Box-Cox / power distance  ||y^lam - yhat^lam||_2 / lam.  lam=1: Euclid, lam=1/2: Hellinger-type,
    lam->0: log-ratio (uncentred) distance."""
    def s(y, yh):
        return np.sqrt(((np.maximum(y, 0) ** lam - np.maximum(yh, 0) ** lam) ** 2).sum(-1)) / lam
    s.__name__ = f"boxcox_{lam}"
    return s


def helmert_basis(D):
    """Orthonormal basis (D x D-1) of the sum-zero subspace (ilr coordinates of clr vectors)."""
    V = np.zeros((D, D - 1))
    for j in range(1, D):
        V[:j, j - 1] = 1.0 / j
        V[j, j - 1] = -1.0
        V[:, j - 1] /= np.linalg.norm(V[:, j - 1])
    return V


def fit_mahal_ilr(Y, Yh, delta, ridge=1e-3):
    """Global-covariance (ellipsoidal) score in ilr coordinates: s = || W (ilr(y) - ilr(yh)) ||, W = Sigma^{-1/2}
    with Sigma the covariance of the ilr residuals on a *separate* fit set (shrunk towards its mean variance)."""
    V = helmert_basis(Y.shape[1])
    R = (clr(Y, delta) - clr(Yh, delta)) @ V
    S = np.cov(R.T) + ridge * np.trace(np.cov(R.T)) / V.shape[1] * np.eye(V.shape[1])
    w, U = np.linalg.eigh(S)
    W = U @ np.diag(w ** -0.5) @ U.T

    def s_mahal(y, yh):
        return np.sqrt((((clr(y, delta) - clr(yh, delta)) @ V @ W) ** 2).sum(-1))
    s_mahal.__name__ = f"mahal_ilr_d{delta}"
    return s_mahal
