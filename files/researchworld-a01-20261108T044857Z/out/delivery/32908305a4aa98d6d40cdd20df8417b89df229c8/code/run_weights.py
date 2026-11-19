"""Sensitivity of the minimum investment to the task weights of a weighted mean (appendix).
Usage: python3 code/run_weights.py DATASET CAP OUT [--R 500] [--seed 0] [--strata 2,3,5,10,20,50,100]
For each target (chosen by rank under the UNWEIGHTED mean) and each weight vector w (uniform, Dirichlet(1), Dirichlet(5), the n
one-hot vertices) it records the target's rank under w, the weighted gap to the leader, and the exact minimum L1 / K.
"""
import sys, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import data as dt, weighted as wt

ap = argparse.ArgumentParser()
for k in ("dataset", "cap", "out"): ap.add_argument(k)
ap.add_argument("--R", type=int, default=500); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--strata", default="2,3,5,10,20,50,100"); ap.add_argument("--eps", type=float, default=1e-3)
a = ap.parse_args()
X, names, tasks, meta = dt.load(a.dataset); M, n = X.shape
rng = np.random.default_rng(a.seed)
order = np.argsort(-X.mean(1), kind="stable"); targets = order[[int(r) - 1 for r in a.strata.split(",") if int(r) <= M]]
schemes = [("uniform", np.full(n, 1 / n))]
schemes += [(f"dirichlet{al}", rng.dirichlet(np.full(n, float(al)))) for al in (1, 5) for _ in range(a.R)]
if n <= 12: schemes += [(f"onehot:{tasks[t]}", np.eye(n)[t]) for t in range(n)]
rows = []
for i in targets:
    cap = dt.make_cap(a.cap, X, i)
    for name, w in schemes:
        V = X @ w; L1, K = wt.weighted_min_investment(X, i, cap, w, a.eps)
        rows.append(dict(dataset=a.dataset, cap=a.cap, target=names[i], rank_mean=int(rankdata(-X.mean(1), method="min")[i]),
                         scheme=name.split(":")[0], weights=name, rank_w=int(rankdata(-V, method="min")[i]),
                         gap_w=float(np.delete(V, i).max() - V[i]), L1=L1, K=K))
pd.DataFrame(rows).to_csv(a.out, index=False)
