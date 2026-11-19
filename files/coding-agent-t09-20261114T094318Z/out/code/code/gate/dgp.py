"""Data-generating process: treatment assignment, exposures, outcome mechanisms.

Notation. Z_i in {0,1} is unit i's treatment, N(i) its neighbours, d_i its degree.
  f1_i = (1/d_i) sum_{j in N(i)} Z_j          (1-hop exposure: share of treated neighbours)
  f2_i = (1/d_i) sum_{j in N(i)} f1_j         (2-step walk exposure, a 2-hop summary)
  x_i ~ N(0,1)                                 (covariate, enters every mechanism additively)
The outcome is Y_i = mu_m(Z_i, f1_i, f2_i, x_i) + noise, where m names a mechanism.
The estimand is the finite-population GATE,
  GATE = (1/n) sum_i [ mu_m(1,1,1,x_i) - mu_m(0,0,0,x_i) ],
which is deterministic given the graph, because mu_m is known and the exposure of
every unit equals 1 (all-treated) or 0 (all-control) under the global contrast.
"""
import numpy as np
import scipy.sparse as sp

# Mechanisms: name -> (description, mean function of (z, f1, f2, x))
MECHS = {
    "M0": ("null: direct effect only", lambda z, f1, f2, x: x + z),
    "M1": ("linear-in-means, 1-hop", lambda z, f1, f2, x: x + z + 2.0 * f1),
    "M2": ("cubic 1-hop exposure", lambda z, f1, f2, x: x + z + 4.0 * f1**3),
    "M3": ("saturating 1-hop exposure", lambda z, f1, f2, x: x + z + 3.0 * (1 - np.exp(-4 * f1)) / (1 - np.exp(-4))),
    "M4": ("linear, 1-hop + 2-step exposure", lambda z, f1, f2, x: x + z + 1.5 * f1 + 1.5 * f2),
    "M5": ("threshold (critical mass) 1-hop", lambda z, f1, f2, x: x + z + 3.0 * (f1 >= 0.5)),
    "M6": ("linear-in-means + community shocks", lambda z, f1, f2, x: x + z + 2.0 * f1),
}
SHOCK_SD = 1.0   # sd of community-level shock (mechanism M6 only)
NOISE_SD = 1.0   # sd of unit-level noise (all mechanisms)


def adjacency(src, dst, n):
    A = sp.coo_matrix((np.ones(len(src)), (src, dst)), shape=(n, n))
    A = (A + A.T).tocsr()
    A.data[:] = 1.0
    return A


def true_gate(mech):
    """Exact finite-population GATE for a mechanism (independent of graph and noise)."""
    f = MECHS[mech][1]
    one = np.ones(1)
    zero = np.zeros(1)
    return float(f(one, one, one, zero)[0] - f(zero, zero, zero, zero)[0])


def assign(design, p, n, rng, labels=None, n_clusters=None):
    """Bernoulli(p) unit assignment, or graph-cluster randomisation (clusters share Z)."""
    if design == "bern":
        return rng.binomial(1, p, size=n).astype(float)
    if design == "gcr":
        b = rng.binomial(1, p, size=n_clusters).astype(float)
        return b[labels]
    raise ValueError(design)


def exposures(A, deg, z):
    f1 = (A @ z) / deg
    f2 = (A @ f1) / deg
    return f1, f2


def simulate(mech, A, deg, z, labels, n_clusters, rng):
    """Draw covariates, noise and shocks and return outcome Y plus exposures."""
    n = len(z)
    f1, f2 = exposures(A, deg, z)
    x = rng.standard_normal(n)
    eps = NOISE_SD * rng.standard_normal(n)
    if mech == "M6":
        shock = SHOCK_SD * rng.standard_normal(n_clusters)[labels]
        eps = eps + shock
    y = MECHS[mech][1](z, f1, f2, x) + eps
    return y, f1, f2, x
