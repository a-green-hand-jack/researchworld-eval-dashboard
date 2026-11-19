"""Exposure diagnostics used in the text (paper Sec. 5.2 and 5.1).

For each graph, under Bernoulli(0.5) and graph-cluster(0.5) assignment, reports
  - the share of units whose one-hop exposure is <= 0.1 or >= 0.9 ("extreme" exposure),
  - Var(f2)/Var(f1), the relative variation of the two-step exposure.
Averages over 10 draws with seed 3. Output: /work/results/diag_exposure.csv
"""
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, "/work/code")
from gate import dgp, graphs  # noqa: E402

rows = []
for name in ["stanford3", "egofb", "ba_n5000_m3"]:
    g = graphs.load_cached(name)
    A = dgp.adjacency(g["src"], g["dst"], g["n"])
    deg = np.asarray(A.sum(axis=1)).ravel()
    rng = np.random.default_rng(3)
    v1, v2 = [], []
    ext = {"bern": [], "gcr": []}
    for _ in range(10):
        z = dgp.assign("bern", 0.5, g["n"], rng)
        f1, f2 = dgp.exposures(A, deg, z)
        v1.append(f1.var())
        v2.append(f2.var())
        ext["bern"].append(np.mean((f1 <= 0.1) | (f1 >= 0.9)))
        z = dgp.assign("gcr", 0.5, g["n"], rng, g["labels"], g["n_clusters"])
        f1, _ = dgp.exposures(A, deg, z)
        ext["gcr"].append(np.mean((f1 <= 0.1) | (f1 >= 0.9)))
    rows.append(dict(graph=name, var_f2_over_var_f1=np.mean(v2) / np.mean(v1),
                     extreme_share_bern=np.mean(ext["bern"]), extreme_share_gcr=np.mean(ext["gcr"])))
out = pd.DataFrame(rows)
out.to_csv("/work/results/diag_exposure.csv", index=False)
print(out.round(3).to_string())
