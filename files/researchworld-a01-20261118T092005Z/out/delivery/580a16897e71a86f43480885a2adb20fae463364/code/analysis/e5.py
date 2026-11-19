"""E5 summary (appendix): exact vs greedy vs naive developers.  usage: e5.py RAWDIR OUTDIR   reads RAWDIR/e5_*.csv; writes OUTDIR/e5_summary.csv.
Per board, rule, cap B, developer: share of targets for which the developer reaches first place (random: mean feasible share over its 20 draws), among targets where the exact plan exists,
the median depth ratio to the exact depth (targets with exact depth > 0 and a feasible developer), and the cluster-bootstrap (target family) CI of the mean log depth ratio."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from stats import cluster_mean_ci
from families import fam_map
RAW, OUT = sys.argv[1], sys.argv[2]
FAM = {"helm": fam_map("helm")[1], "m39": fam_map("m39")[1]}
d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(RAW, "e5_*.csv")))], ignore_index=True)
d["feasible"] = d.feasible.map(lambda x: 1.0 if str(x) == "True" else (0.0 if str(x) == "False" else float(x))); d["family"] = [FAM[b].get(m, m.split("/")[0]) for b, m in zip(d.board, d.model)]
ex = d[d.developer == "exact"].set_index(["board", "target", "rule", "B"])
rows = []
for (b, r, B, dev), g in d.groupby(["board", "rule", "B", "developer"]):
    g = g.set_index(["board", "target", "rule", "B"]); e = ex.loc[g.index]
    ok = (e.feasible == 1).values
    both = ok & (g.feasible.values > 0) & (e.depth.values > 0)
    ratio = (g.depth.values[both] / e.depth.values[both])
    est = cluster_mean_ci(np.log(ratio), [g.family.values[both]], nboot=2000, seed=4) if both.sum() > 1 else (np.nan,) * 3 + (0,)
    rows.append(dict(board=b, rule=r, B=B, developer=dev, n_targets=int(len(g)), n_exact_feasible=int(ok.sum()), share_feasible=float(g.feasible.values[ok].mean()) if ok.any() else np.nan,
                     n_ratio=int(both.sum()), median_depth_ratio=float(np.median(ratio)) if both.any() else np.nan, mean_log_ratio=est[0], ci_lo=est[1], ci_hi=est[2],
                     share_optimal=float((ratio <= 1 + 1e-6).mean()) if both.any() else np.nan))
o = pd.DataFrame(rows); o.to_csv(os.path.join(OUT, "e5_summary.csv"), index=False)
pd.set_option("display.width", 250); print(o[o.B == 10].pivot_table(index=["board", "rule"], columns="developer", values="median_depth_ratio").round(2)); print(o[o.B == 10].pivot_table(index=["board", "rule"], columns="developer", values="share_feasible").round(2))
