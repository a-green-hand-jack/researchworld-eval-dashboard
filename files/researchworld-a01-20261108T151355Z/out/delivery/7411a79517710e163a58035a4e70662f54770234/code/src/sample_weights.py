"""results/sample_weights.csv: the rank-stratified target sample of run_core.py/run_hstar.py ('sample', --nsample 100, seed-free) and a rank-interval weight.
Sample = the 20 targets ranked 2-21 under the mean (weight 1 each) + `nsample` log-uniform positions in the remaining ranks (duplicates merged). The weight of a
sampled tail target is the number of tail targets whose rank position is nearest to it (a stratum representative, assumes cost is smooth in rank); weights sum to
the number of non-leader targets. It removes the head-heavy composition of the sample, not sampling variance (no design-based CI).
Usage: python3 src/sample_weights.py [OUT]"""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import data as dt
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[1] / "results/sample_weights.csv")
rows = []
for ds, nsample in (("ollb", 100), ("helm", 100)):
    X, names, tasks, meta = dt.load(ds); M = len(names); mr = rankdata(-X.mean(axis=1), method="min"); order = np.argsort(mr, kind="stable")
    head, tail = order[1:21], order[21:]
    if len(tail) > nsample:
        pos = np.unique(np.round(np.exp(np.linspace(np.log(1), np.log(len(tail)), nsample))).astype(int) - 1)
        near = np.abs(np.arange(len(tail))[:, None] - pos[None, :]).argmin(1); w = np.bincount(near, minlength=len(pos)).astype(float); tsel = tail[pos]
    else: tsel, w = tail, np.ones(len(tail))
    for i in head: rows.append(dict(dataset=ds, target=names[i], target_idx=int(i), rank_mean=int(mr[i]), sampled=True, weight=1.0))
    for i, wi in zip(tsel, w): rows.append(dict(dataset=ds, target=names[i], target_idx=int(i), rank_mean=int(mr[i]), sampled=True, weight=float(wi)))
d = pd.DataFrame(rows); d.to_csv(out, index=False); print(d.groupby("dataset").agg(n=("weight", "size"), wsum=("weight", "sum")))
