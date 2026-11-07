import numpy as np, sys
sys.path.insert(0, "code")
from ppi_lib import *
from ppi_py import ppi_mean_ci
d = np.load("data/galaxies.npz"); Y, F = d["Y"], d["Yhat"]
rng = np.random.default_rng(0)
idx = rng.choice(len(Y), 5000, replace=True); n=300
YL, fL, fU = Y[idx[:n]], F[idx[:n]], F[idx[n:]]
print("ppi_py ++ :", ppi_mean_ci(YL, fL, fU, alpha=0.05))
t, s, b = control_variate_mean(YL, fL[:, None], fU[:, None]); print("mine ++ :", interval(t, s), b)
print("ppi_py vanilla:", ppi_mean_ci(YL, fL, fU, alpha=0.05, lam=1))
t, s = ppi_vanilla(YL, fL, fU); print("mine vanilla", interval(t, s))
r = run_all(YL, fL[:, None], fU[:, None], np.random.default_rng(1))
for k, v in r.items(): print(k, np.round(interval(*v), 4), "width", round(2*1.96*v[1], 4))
