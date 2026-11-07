"""Synthetic pools with known structure: Gaussian-copula equicorrelated config errors; accuracies p_k = m + tau * z_k."""
import numpy as np
from scipy.stats import norm
def make_pool(Kp, N, m=0.3, tau=0.01, rho=0.5, seed=0, outlier=0.0):
    rng = np.random.default_rng(seed)
    p = np.clip(m + tau * rng.standard_normal(Kp), 0.01, 0.99)
    if outlier: p[Kp - 1] = min(p[Kp - 1] + outlier, 0.99)   # one clearly better config (stress case)
    q = rng.standard_normal(N)                       # shared question latent
    U = np.sqrt(rho) * q[None, :] + np.sqrt(1 - rho) * rng.standard_normal((Kp, N))
    Y = U < norm.ppf(p)[:, None]                     # correct iff latent below threshold
    return Y
