"""Closed-form (population) quantities used as predictors.

lev_theory : design leverage L = dbar' Sigma^{-1} dbar of the 1-hop *fraction* model
             y ~ 1 + z + s  (s = fraction of treated neighbours), for Bernoulli(p) and for
             cluster-randomised designs (cluster labels given).
proj_bias_bern : asymptotic (n->inf) bias of the same estimator for  y = beta z + gamma g(s),
             g(0)=0, g(1)=1, under Bernoulli(p) (exact binomial moments, any degree sequence).
"""
import numpy as np
import scipy.sparse as sp
from scipy.stats import binom


def lev_theory(world, design, clusters=None):
    p = design.get("p", 0.5)
    v = p * (1 - p)
    n = world.n
    if design["type"] == "bern":
        q = np.mean(1.0 / world.deg)
        return (1.0 + 1.0 / q) / v
    K = clusters.max() + 1
    B = sp.csr_matrix((np.ones(n), (np.arange(n), clusters)), shape=(n, K))
    M = (world.A @ B).tocsr()  # n x K neighbour counts per cluster
    Dinv = sp.diags(1.0 / world.deg)
    Mf = Dinv @ M
    rho = float(np.asarray(Mf[np.arange(n), clusters]).mean())
    q = float(Mf.multiply(Mf).sum() / n)
    return (q - 2 * rho + 1) / (q - rho ** 2) / v


def proj_bias_bern(world, p, g):
    """bias of ols_s GATE estimate for y = beta z + gamma g(s) per unit gamma (multiply by gamma)."""
    degs, cnt = np.unique(world.deg.astype(int), return_counts=True)
    Eg = Egs = 0.0
    for d, c in zip(degs, cnt):
        k = np.arange(d + 1)
        pm = binom.pmf(k, d, p)
        s = k / d
        gs = g(s)
        Eg += c * (pm * gs).sum()
        Egs += c * (pm * gs * s).sum()
    n = world.n
    Eg /= n
    Egs /= n
    cov = Egs - p * Eg
    var = p * (1 - p) * np.mean(1.0 / world.deg)
    kappa = cov / var
    return kappa - (g(np.array(1.0)) - g(np.array(0.0)))
