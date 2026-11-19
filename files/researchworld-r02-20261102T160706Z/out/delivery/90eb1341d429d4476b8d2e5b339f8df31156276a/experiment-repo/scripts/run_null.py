"""C5: null behaviour of the binned conditional-coverage metrics when conditional coverage is EXACT.
Each rep: calibration-induced coverage level p ~ Beta(k, n+1-k) (exact split-conformal law), then y-in-region indicators on
n_test points are Bernoulli(p) independent of x.  Metrics computed with the same code as in E1 (src/cpc/metrics.py)."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from cpc.metrics import binned_gap, wsc

rng = np.random.default_rng(777)
rows = []
n_test, p_x = 2000, 4
for n_cal in [30, 100, 250, 500, 2000]:
    k = int(np.ceil((n_cal + 1) * 0.9))
    for rep in range(500):
        p = rng.beta(k, n_cal + 1 - k)
        X = rng.normal(size=(n_test, p_x))
        g = rng.normal(size=n_test)
        c = rng.random(n_test) < p
        r = dict(n_cal=n_cal, rep=rep, cov10=c.mean(), p_cond=p)
        r["ymax_min"], r["ymax_max"] = binned_gap(c, g)
        r["ent_min"], r["ent_max"] = binned_gap(c, rng.normal(size=n_test))
        r["scale_min"], r["scale_max"] = binned_gap(c, rng.normal(size=n_test), 3)
        r["ymax_gap"] = r["ymax_max"] - r["ymax_min"]
        r["wsc"] = wsc(c, X, rng=np.random.default_rng(rep))
        # oracle pointwise gap with 60 points x 400 draws, true c_i = p everywhere
        ci = rng.binomial(400, p, size=60) / 400
        r["or_gap"] = np.abs(ci - 0.9).mean()
        r["or_rmse"] = np.sqrt(((ci - 0.9) ** 2).mean())
        rows.append(r)
os.makedirs("results/null", exist_ok=True)
pd.DataFrame(rows).to_csv("results/null/null_binned.csv", index=False)
