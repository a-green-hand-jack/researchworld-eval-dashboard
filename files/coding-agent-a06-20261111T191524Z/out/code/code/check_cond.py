"""Sanity check of the conditional (polyhedral) winner inference on continuous Gaussian data (should give ~95% coverage)."""
import sys; sys.path.insert(0, "/work/code")
import numpy as np
from sim_lib import cond_winner
rng = np.random.default_rng(5); K = 40; n = 200; R = 1000
theta = rng.normal(0.45, 0.02, K); A = rng.normal(size=(K, 3)); Sig = 0.01 * (A @ A.T / 3 * 0.5 + np.eye(K) * 0.5); Lc = np.linalg.cholesky(Sig)
cov = 0
for r in range(R):
    X = theta[:, None] + Lc @ rng.normal(size=(K, n)); k = int(np.argmax(X.mean(1)))
    med, (lo, hi), _ = cond_winner(X, k, rng=rng); cov += lo <= theta[k] <= hi
print(f"Gaussian-data coverage of the conditional 95% interval: {cov/R:.3f} (R={R})")
