"""Check own PPI/PPI++ implementation against ppi_py v0.2.3."""
import sys, numpy as np
sys.path.insert(0, "src")
from estimators import ppi_scores
from ppi_py import ppi_mean_ci
d = np.load("data/galaxies.npz"); rng = np.random.default_rng(1)
for n, N in [(100, 1000), (500, 5000), (50, 10000)]:
    i = rng.choice(len(d["Y"]), n + N, replace=True)
    Y, f = d["Y"][i[:n]], d["Yhat"][i[:n]]; fu = d["Yhat"][i[n:]]
    a = ppi_mean_ci(Y, f, fu, alpha=0.05)             # PPI++ default (power tuning)
    b = ppi_scores(Y, f, fu, ddof=0)
    a1 = ppi_mean_ci(Y, f, fu, alpha=0.05, lam=1)    # PPI
    b1 = ppi_scores(Y, f, fu, lam=1.0, ddof=0)
    print(n, N, np.abs(np.ravel(a) - np.ravel(b)).max(), np.abs(np.ravel(a1) - np.ravel(b1)).max())
