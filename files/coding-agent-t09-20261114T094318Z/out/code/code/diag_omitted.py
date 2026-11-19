"""Diagnostic for the two-hop omitted-variable bias (paper Sec. 5, Fig. 2 discussion).

Under M4, Y = x + Z + 1.5 f1 + 1.5 f2 + noise. Regressing Y on (1, Z, f1) omits f2.
We estimate the linear projection of f2 on (1, Z, f1) under Bernoulli(p) assignment and
compare the projection slope on f1 with the observed R2 bias of M4 in E1.
Output: /work/results/diag_omitted.csv
"""
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, "/work/code")
from gate import dgp, graphs  # noqa: E402

rows = []
for name in ["stanford3", "egofb", "ba_n5000_m3", "er_n5000_d20"]:
    g = graphs.load_cached(name)
    A = dgp.adjacency(g["src"], g["dst"], g["n"])
    deg = np.asarray(A.sum(axis=1)).ravel()
    for p in [0.1, 0.5]:
        rng = np.random.default_rng(7)
        cs, bs = [], []
        for _ in range(20):
            z = rng.binomial(1, p, g["n"]).astype(float)
            f1, f2 = dgp.exposures(A, deg, z)
            X = np.column_stack([np.ones_like(z), z, f1])
            coef = np.linalg.lstsq(X, f2, rcond=None)[0]
            cs.append(coef[1])
            bs.append(coef[2])
        rows.append(dict(graph=name, p=p, slope_f2_on_Z=np.mean(cs), slope_f2_on_f1=np.mean(bs),
                         implied_bias_scale=1.5 * np.mean(bs)))
out = pd.DataFrame(rows)
out.to_csv("/work/results/diag_omitted.csv", index=False)
print(out.round(3).to_string())
