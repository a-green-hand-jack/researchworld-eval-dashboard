"""Uncertainty due to the finite question pool: bootstrap the pool (N questions resampled with replacement) to create alternative worlds,
and recompute the exhaustive-search optimism at n=50,100,400 in each. Usage: python exp_poolboot.py WORLD..."""
import sys; sys.path.insert(0, "/work/code")
import numpy as np, pandas as pd
sys.argv = sys.argv[:1] + sys.argv[1:]
from exp_main import get_world
rows = []
for w in sys.argv[1:]:
    Y0 = get_world(w).astype(np.float32); N = Y0.shape[1]; rng = np.random.default_rng(2024)
    for b in range(200):
        Y = Y0[:, rng.integers(N, size=N)]; th = Y.mean(1)
        for n in (50, 100, 400):
            R = 400; idx = rng.integers(N, size=(R, n)); S = np.stack([Y[:, i].mean(1) for i in idx]) + 1e-9 * rng.random((R, Y.shape[0]))
            k = S.argmax(1); rows.append(dict(world=w, rep=b, n=n, gap=float((S[np.arange(R), k] - th[k]).mean() * 100)))
d = pd.DataFrame(rows); d.to_csv("/work/results/sim/poolboot.csv", index=False)
print(d.groupby(['world', 'n']).gap.agg(['mean', lambda x: np.percentile(x, 2.5), lambda x: np.percentile(x, 97.5)]).round(2))
