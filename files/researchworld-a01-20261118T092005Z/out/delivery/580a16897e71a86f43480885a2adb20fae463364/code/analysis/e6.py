"""E6 summary: first place with confidence.  usage: e6.py RAWDIR OUTDIR   reads RAWDIR/e6_*.csv; writes OUTDIR/e6_summary.csv and e6_topnoise.csv.
CIs: cluster bootstrap over target families (union with per-target-model identity is not needed here: one incumbent per rule and sub-board)."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from stats import cluster_mean_ci
from families import fam_map
RAW, OUT = sys.argv[1], sys.argv[2]
FAM = {"helm": fam_map("helm")[1], "m39": fam_map("m39")[1]}
d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(RAW, "e6_*.csv")))], ignore_index=True)
d["family"] = [FAM[b].get(m, m.split("/")[0]) for b, m in zip(d.board, d.model)]
rows, rows2 = [], []
for (b, r, c), g in d.groupby(["board", "rule", "c"]):
    f = g[g.feasible]
    est = cluster_mean_ci(f.p_first_plan.values, [f.family.values], nboot=2000, seed=3) if len(f) else (np.nan,) * 3 + (0,)
    rows.append(dict(board=b, rule=r, c=c, n_targets=len(g), n_feasible=len(f), median_depth=f.depth.median() if len(f) else np.nan, median_breadth=f.breadth.median() if len(f) else np.nan,
                     p_first_plan_mean=est[0], p_first_plan_lo=est[1], p_first_plan_hi=est[2], n_families=est[3], p_first_plan_min=f.p_first_plan.min() if len(f) else np.nan))
for (b, r), g in d[d.c == 0].groupby(["board", "rule"]):
    n1 = g[g.rank_rule > 1]
    rows2.append(dict(board=b, rule=r, n_targets=len(g), n_not_first=len(n1), share_p_first_ge_5pct=float((g.p_first_unboosted >= 0.05).mean()), share_notfirst_z0_lt_2=float((n1.z0 < 2).mean()) if len(n1) else np.nan,
                      median_z0_notfirst=float(n1.z0.median()) if len(n1) else np.nan, mean_p_first_unboosted=float(g.p_first_unboosted.mean()), nsub=int(g.nsub.iloc[0]), R=int(g.R.iloc[0])))
rows3 = []
for (b, r), g in d[d.rule.isin(["mean", "zmean", "median", "min"])].groupby(["board", "rule"]):
    best = []
    for t, gt in g.groupby("target"):
        ok = gt[gt.feasible & (gt.p_first_plan >= 0.9)].sort_values("c")
        z = gt[gt.c == 0].iloc[0]
        best.append(dict(reached=len(ok) > 0, c=ok.c.iloc[0] if len(ok) else np.nan, depth=ok.depth.iloc[0] if len(ok) else np.nan, depth0=z.depth, family=z.family))
    q = pd.DataFrame(best); r_ = q[q.reached]
    rows3.append(dict(board=b, rule=r, n_targets=len(q), share_reaching_p90=float(q.reached.mean()), median_c_needed=r_.c.median() if len(r_) else np.nan, median_depth_at_p90=r_.depth.median() if len(r_) else np.nan,
                      median_depth_c0=q.depth0.median(), median_ratio=float((r_.depth / r_.depth0.where(r_.depth0 > 0)).median()) if len(r_) else np.nan, max_c_grid=float(g.c.max())))
pd.DataFrame(rows3).to_csv(os.path.join(OUT, "e6_confidence.csv"), index=False); print(pd.DataFrame(rows3).round(3).to_string())
pd.DataFrame(rows).to_csv(os.path.join(OUT, "e6_summary.csv"), index=False); pd.DataFrame(rows2).to_csv(os.path.join(OUT, "e6_topnoise.csv"), index=False)
pd.set_option("display.width", 250); print(pd.DataFrame(rows).round(3).to_string()); print(pd.DataFrame(rows2).round(3).to_string())
