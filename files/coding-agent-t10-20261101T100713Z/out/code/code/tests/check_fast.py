"""Sanity check: fast.py == ppi_py / methods.py on random data."""
import sys; sys.path.insert(0, "..")
import numpy as np
from ppi_py import ppi_mean_ci, classical_mean_ci
import fast, methods
rng = np.random.default_rng(0)
mx = 0
for t in range(20):
    n, N = int(rng.integers(20, 300)), int(rng.integers(100, 3000))
    Fu = rng.normal(size=N) + 0.3; F = rng.normal(size=n) + 0.3; Y = 1.2 * F + rng.normal(size=n) * 0.7 + 0.5
    for name, fn, ref in [("classical", lambda *a: (a[0].mean(), a[0].std() / np.sqrt(len(a[0]))), lambda: classical_mean_ci(Y, alpha=.05)),
                          ("ppi++", lambda *a: fast.ppi_pp(*a, ddof=0), lambda: ppi_mean_ci(Y, F, Fu, alpha=.05))]:
        th, se = fn(Y, F, Fu); lo, hi = ref(); lo, hi = float(np.ravel(lo)[0]), float(np.ravel(hi)[0])
        mx = max(mx, abs(th - (lo + hi) / 2), abs(1.959964 * se - (hi - lo) / 2))
    perm = rng.permutation(n)
    th, se = fast.aipw_lin(Y, F, Fu, perm)
    # reference: methods.aipw_from_g with the same folds
    folds = perm % 5; gL = np.empty(n); gU = np.zeros(N)
    for k in range(5):
        m = methods.make_learner("lin").fit(F[folds != k][:, None], Y[folds != k])
        gL[folds == k] = m.predict(F[folds == k][:, None]); gU += m.predict(Fu[:, None]) / 5
    th2, se2 = methods.aipw_from_g(Y, gL, gU)
    mx = max(mx, abs(th - th2), abs(se - se2))
print("max abs discrepancy", mx)
assert mx < 1e-6
