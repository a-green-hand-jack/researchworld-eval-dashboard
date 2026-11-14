"""Cost-scale sensitivity: investment measured in task-specific standard deviations instead of points.
Usage: python3 code/run_zcost.py DATASET CAP OUT
The cost of raising task t by d points is d / sigma_t, with sigma_t the across-model standard deviation of task t (same rules, same
caps, same strict-first condition). Rules: mean (fractional knapsack: tasks with the largest sigma first), min (forced:
sum of z-gaps), median for odd n (m cheapest z-gaps). Output L1z (in sigma units) next to the point-L1 optimum from the main runs.
"""
import sys, pathlib
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import data as dt

ds, cap_name, out = sys.argv[1:4]; EPS = 1e-3
X, names, tasks, meta = dt.load(ds); M, n = X.shape
sig = X.std(axis=0, ddof=1)
rank = rankdata(-X.mean(1), method="min")
rows = []
for i in range(M):
    x = X[i]; c = np.maximum(dt.make_cap(cap_name, X, i), x); h = c - x
    for rule, V in (("mean", X.mean(1)), ("min", X.min(1)), ("median", np.median(X, 1))):
        if rule == "median" and n % 2 == 0: continue
        tau = np.delete(V, i).max(); L1z = np.inf;
        if V[i] > tau: L1z = 0.0
        elif rule == "mean":
            need = n * (tau + EPS) - x.sum()
            if h.sum() >= need - 1e-12:
                L1z = 0.0; rem = need
                for t in np.argsort(-sig, kind="stable"):
                    d = min(h[t], rem); L1z += d / sig[t]; rem -= d
                    if rem <= 1e-12: break
        elif rule == "min":
            lvl = tau + EPS
            if not np.any(c[x < lvl] < lvl - 1e-12): L1z = float((np.maximum(lvl - x, 0) / sig).sum())
        else:
            lvl = tau + EPS; m = (n + 1) // 2; k = max(m - int((x >= lvl).sum()), 0)
            d = np.where(c >= lvl - 1e-12, (lvl - x) / sig, np.inf)[x < lvl]; d = np.sort(d)
            if k <= np.isfinite(d).sum(): L1z = float(d[:k].sum())
        rows.append(dict(dataset=ds, cap=cap_name, rule=rule, target=names[i], target_idx=i, rank_mean=int(rank[i]), L1z=L1z))
pd.DataFrame(rows).to_csv(out, index=False)
