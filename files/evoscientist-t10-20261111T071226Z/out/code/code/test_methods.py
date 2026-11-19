"""Sanity checks: own PPI++ == ppi_py when lam in [0,1]; unbiasedness on synthetic data."""
import numpy as np
from methods import *

rng = np.random.default_rng(0)
n, N = 300, 5000
f = rng.normal(size=n + N)
Y = 0.8 * f + rng.normal(size=n + N) + 3.0
Yl, Fl, Fu = Y[:n], f[:n], f[n:]
for nm, fn in METHODS.items():
    print(nm, fn(Yl, Fl, Fu))
print("cf_iso", cf_isotonic_ppi(Yl, Fl, Fu, rng=np.random.default_rng(1)))
a, b = ppipp_own(Yl, Fl, Fu), ppipp_pkg(Yl, Fl, Fu)
print("own vs pkg", a, b)
assert abs(a[0] - b[0]) < 1e-3 * max(1, abs(a[0])) and abs(a[1] - b[1]) < 5e-3 * a[1], "own PPI++ differs from ppi_py"
# unbiasedness / coverage quick check with truth 3.0
cov = {k: 0 for k in list(METHODS) + ["cf_iso"]}
R = 300
for r in range(R):
    f = rng.normal(size=n + N)
    Y = 3.0 + f + 0.5 * (f ** 2 - 1) + rng.normal(size=n + N)
    res = run_all(Y[:n], f[:n], f[n:], rng)
    for k, (t, s) in res.items():
        cov[k] += abs(t - 3.0) <= Z95 * s
print({k: v / R for k, v in cov.items()})
print("OK")
