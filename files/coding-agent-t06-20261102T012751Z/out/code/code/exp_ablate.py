"""Ablation of the ridge penalty (10^-3 in all main runs): relabel/delete budgets for pairs with z>2 on
MT-Bench (all pairs), Arena (150 random pairs) and three NBA seasons (150 random pairs each).
Writes results/ablate_ridge.csv"""
import numpy as np, pandas as pd, zlib
from multiprocessing import Pool
from bt import *
import datasets as ds

BOARDS = {}
RIDGES = [1e-3, 1e-1, 10.0]

def task(a):
    key, i, j, lam = a
    b = BOARDS[key]; b = b.with_counts(b.N); b.lam = b.lam.copy(); b.lam[: b.m] = lam
    th = b.fit()
    return [dict(board=key, ridge=lam, **r) for r in pair_records(b, th, i, j, kinds=("relabel", "drop"), modes=("flip",))]

if __name__ == "__main__":
    rng = np.random.default_rng(11)
    BOARDS["arena"] = ds.arena55k(); BOARDS["mt_human"] = ds.mtbench_human()
    nb = ds.nba_seasons()
    for yr in (1975, 1995, 2015): BOARDS[f"nba{yr}"] = nb[yr]
    T = []
    for key, b in BOARDS.items():
        th = b.fit(); s = th[: b.m]
        allp = [(i, j) for i in range(b.m) for j in range(b.m) if s[i] > s[j]]
        sel = allp if len(allp) <= 150 else [allp[x] for x in rng.choice(len(allp), 150, replace=False)]
        T += [(key, i, j, lam) for (i, j) in sel for lam in RIDGES]
    with Pool(8) as p:
        out = sum(p.map(task, T, chunksize=4), [])
    d = pd.DataFrame(out); d["z"] = d.gap / d.se; d["phi"] = d.k / (d.z * np.sqrt(d.ntouch))
    d.to_csv("/work/results/ablate_ridge.csv", index=False)
    g = d[(d.z > 2) & np.isfinite(d.k)]
    print(g.groupby(["board", "kind", "ridge"]).phi.median().unstack("ridge").round(3))
