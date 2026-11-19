"""Synthetic item-level worlds with the same factorial config structure as the real grid.
correct[c,i] = 1[ a + mu_c + sqrt(rho)*z_i + sqrt(1-rho)*u_ci > 0 ],  z,u ~ N(0,1)
=> P(correct_c) = Phi(a + mu_c); latent correlation between configs = rho (item-shared difficulty)."""
import numpy as np
from scipy import stats
from sel import FACTORS, levels_cfg, cfg_levels

def make_mu(spread, rng, inter=0.3, K=72):
    """mu_c = additive factor effects + interaction, standardised to have SD `spread` (in probit units)."""
    eff = [rng.standard_normal(F) for F in FACTORS]
    mu = np.zeros(K)
    for c in range(K):
        l = cfg_levels(c)
        mu[c] = sum(eff[f][l[f]] for f in range(3))
    mu += inter * np.sqrt(3) * rng.standard_normal(K)
    mu = (mu - mu.mean()) / mu.std()
    return spread * mu

def acc_from_mu(a, mu): return stats.norm.cdf(a + mu)

def draw_items(mu, a, rho, N, rng):
    K = len(mu)
    z = rng.standard_normal((N, 1)); u = rng.standard_normal((N, K))
    return ((a + mu[None, :] + np.sqrt(rho) * z + np.sqrt(1 - rho) * u) > 0).astype(np.uint8)
