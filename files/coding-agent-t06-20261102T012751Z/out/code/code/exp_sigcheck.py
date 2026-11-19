"""Check that 'sig' witnesses (gap reduced to 1.96 x original IJ s.e.) also lose significance when
the s.e. is recomputed on the edited board.  Writes results/sigcheck.csv"""
import numpy as np, pandas as pd
from bt import *
import datasets as ds
rng = np.random.default_rng(7)
rows = []
boards = {"arena": ds.arena55k(), "mt_human": ds.mtbench_human(), "mt_gpt4": ds.mtbench_gpt4()}
for yr in (1995, 2005, 2015):
    boards[f"nba{yr}"] = ds.nba_seasons()[yr]
for key, b in boards.items():
    th = b.fit(); s = th[: b.m]
    cand = [(i, j) for i in range(b.m) for j in range(b.m) if s[i] > s[j] and (s[i] - s[j]) / b.ij_se(th, i, j) > 1.96]
    for idx in rng.choice(len(cand), min(40, len(cand)), replace=False):
        i, j = cand[idx]
        se = b.ij_se(th, i, j)
        for kind in ("drop", "relabel", "insert"):
            r = min_edits(b, i, j, kind, int(0.3 * b.n), th0=th, zcrit=1.96, with_N=True)
            if not np.isfinite(r["k"]):
                continue
            b2 = b.with_counts(r["N"]); th2 = b2.fit(theta0=th)
            z2 = (th2[i] - th2[j]) / b2.ij_se(th2, i, j)
            rows.append(dict(board=key, kind=kind, k=r["k"], z0=(s[i] - s[j]) / se, z_after=z2))
d = pd.DataFrame(rows); d.to_csv("/work/results/sigcheck.csv", index=False)
print(d.groupby("kind").z_after.describe())
print("share with z_after<=1.96+0.05:", (d.z_after <= 2.01).mean())
