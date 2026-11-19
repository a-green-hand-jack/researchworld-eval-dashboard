"""E6: bias of the naive 'worst-slice coverage gap' statistic and a null-referenced version.
A predictor that is exactly conditionally valid (coverage 0.9 in every slice) is evaluated on m test points split into
B equal-mass slices.  Writes results/e6_worst_slice.csv"""
import numpy as np, pandas as pd
rng = np.random.default_rng(0)
ALPHA = 0.1
rows = []
for m in (500, 1000, 2000, 5000, 20000, 100000):
    for B in (5, 10, 20, 50):
        nb = m // B
        sims = rng.binomial(nb, 1 - ALPHA, size=(20000, B)) / nb
        worst = np.abs(sims - (1 - ALPHA)).max(1)
        minc = sims.min(1)
        rows.append(dict(m=m, B=B, n_per_slice=nb, E_worst_gap=worst.mean(), q95_worst_gap=np.quantile(worst, 0.95),
                         E_min_cov=minc.mean(), approx=np.sqrt(2 * np.log(B) * ALPHA * (1 - ALPHA) / nb)))
df = pd.DataFrame(rows)
df.to_csv("/work/results/e6_worst_slice.csv", index=False)
print(df.round(4))
