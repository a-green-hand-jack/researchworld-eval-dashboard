"""Quick self-tests (run: PYTHONPATH=code python code/tests.py, < 1 min)."""
import numpy as np
from ccp.geometry import SCORES, make_aitchison, helmert_basis
from ccp.conformal import conformal_quantile, beta_params
from ccp.volume import region_mass

rng = np.random.default_rng(0)
# 1. Prop 3: for vertex targets TV / Hellinger / chi2 / KL scores are monotone functions of p = yhat_k
D = 6
yh = rng.dirichlet(np.ones(D), size=500)
k = rng.integers(0, D, 500)
y = np.eye(D)[k]
p = yh[np.arange(500), k]
assert np.allclose(SCORES["tv"](y, yh), 1 - p)
assert np.allclose(SCORES["hellinger"](y, yh) ** 2, 2 - 2 * np.sqrt(p))
assert np.allclose(SCORES["chi2"](y, yh) ** 2, (1 - p) / p)
assert np.allclose(SCORES["kl"](y, yh) ** 2, -np.log(p))
# 2. conformal quantile index
s = np.arange(1, 11, dtype=float)
assert conformal_quantile(s, 0.2) == 9.0          # ceil(11*0.8)=9
assert conformal_quantile(s, 0.05) == np.inf       # ceil(11*0.95)=11 > n
assert beta_params(99, 0.1) == (90, 10)
# 3. clr distance is invariant to closure and equals Euclid in ilr coordinates
V = helmert_basis(D)
assert np.allclose(V.T @ V, np.eye(D - 1)) and np.allclose(V.sum(0), 0)
a = make_aitchison(0.0)
y1, y2 = rng.dirichlet(np.ones(D)), rng.dirichlet(np.ones(D))
assert np.isclose(a(y1, y2), a(3 * y1, y2))
assert np.isclose(a(y1, y2), np.linalg.norm((np.log(y1) - np.log(y2)) @ V))
# 4. importance-sampling mass vs exact ball area in the 3-simplex
m, ess = region_mass({"euclid": SCORES["euclid"]}, np.ones(3) / 3, {"euclid": np.array([0.2])}, a=1.0, n_per=20000, rng=rng)
assert abs(m["euclid"][0] / (np.pi * 0.04 / (np.sqrt(3) / 2)) - 1) < 0.02
# 5. split-CP coverage ~ Beta law mean
n, R = 200, 4000
V_ = [np.sort(rng.uniform(size=n))[int(np.ceil((n + 1) * 0.9)) - 1] for _ in range(R)]
assert abs(np.mean(V_) - 0.9) < 0.005
print("all tests passed")
