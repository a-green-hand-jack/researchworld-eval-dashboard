"""Sanity check of the importance-sampling reference-mass estimator against the exact area of Euclidean balls inside the 3-simplex."""
import numpy as np, pandas as pd
from ccp.volume import region_mass
from ccp.geometry import SCORES
yh = np.ones(3) / 3
rows = []
for r in (0.05, 0.1, 0.2, 0.3):
    est = [region_mass({"euclid": SCORES["euclid"]}, yh, {"euclid": np.array([r])}, a=1.0, n_per=1500, rng=np.random.default_rng(s))[0]["euclid"][0] for s in range(50)]
    ex = np.pi * r ** 2 / (np.sqrt(3) / 2)   # ball fully inside the triangle (inradius 0.408), simplex area sqrt(3)/2
    rows.append(dict(radius=r, exact=ex, mean_est=np.mean(est), sd_est=np.std(est), rel_bias=np.mean(est) / ex - 1, rel_sd=np.std(est) / ex))
df = pd.DataFrame(rows); df.to_csv("/work/results/check_mass_estimator.csv", index=False); print(df.round(5))
