"""HELM near-tie table: gap of the ranks 2..11 to the leader under the mean, against the binomial standard error of that gap (independent cell errors, SE_cell = 100*sqrt(p(1-p)/n_eval),
SE_gap = sqrt(sum_t(se_i,t^2 + se_1,t^2))/n).  The models are scored on the same items, so errors are positively correlated and the paired SE is smaller: SE_gap is an upper bound
on the noise of the gap.  Output results/final/helm_near_tie.csv (cost of the mean rule = n(gap+eps), eps = 1e-3).  Usage: python3 src/helm_neartie.py"""
import sys, pathlib
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt
X, names, tasks, _ = dt.load("helm"); n = len(tasks)
ne = pd.read_csv(dt.PROC / "helm_mmlu_neval.csv", index_col=0).loc[tasks, "n_eval"].values
p = np.clip(X / 100, .001, .999); se = 100 * np.sqrt(p * (1 - p) / ne)
m = X.mean(1); o = np.argsort(-m, kind="stable"); rows = []
for k in range(1, 11):
    i, j = o[0], o[k]; d = m[i] - m[j]; sd = np.sqrt((se[i] ** 2 + se[j] ** 2).sum()) / n
    rows.append(dict(rank=k + 1, target=names[j], leader=names[i], mean_gap_points=d, se_gap_independent=sd, gap_over_se=d / sd, L1_mean_rule=n * (d + 1e-3)))
pd.DataFrame(rows).to_csv(pathlib.Path(__file__).resolve().parents[1] / "results/final/helm_near_tie.csv", index=False)
