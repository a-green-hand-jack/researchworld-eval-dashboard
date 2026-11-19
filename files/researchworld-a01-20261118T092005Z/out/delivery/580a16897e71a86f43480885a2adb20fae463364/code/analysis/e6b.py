"""E6b summary: first place with confidence on a wider margin grid and with the margin defined by the sd of the boosted plan.
usage: e6b.py RAWDIR OUTDIR   reads RAWDIR/e6b_*.csv (scripts/run_e6b.py); writes OUTDIR/e6b_confidence.csv (per board, rule, variant: share of targets reaching P(first) >= 0.9,
median margin multiple c needed, median depth at that c and its ratio to the depth at c = 0) and OUTDIR/e6b_curve.csv (mean P(first) over feasible targets per c, cluster-bootstrap CI over families)."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from stats import cluster_mean_ci
from families import fam_map
RAW, OUT = sys.argv[1], sys.argv[2]
FAM = {"helm": fam_map("helm")[1], "m39": fam_map("m39")[1]}
d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(RAW, "e6b_*.csv")))], ignore_index=True)
d["family"] = [FAM[b].get(m, m.split("/")[0]) for b, m in zip(d.board, d.model)]
d0 = d[(d.variant == "unit") & (d.c == 0)].set_index(["board", "target", "rule"]).depth
rows, curve = [], []
for (b, r, v), g in d.groupby(["board", "rule", "variant"]):
    best = []
    for t, gt in g.groupby("target"):
        ok = gt[gt.feasible & (gt.p_first_plan >= 0.9)].sort_values("c")
        z = d0.get((b, t, r), np.nan)
        best.append(dict(reached=len(ok) > 0, c=ok.c.iloc[0] if len(ok) else np.nan, depth=ok.depth.iloc[0] if len(ok) else np.nan, depth0=z))
    q = pd.DataFrame(best); rq = q[q.reached]
    cmax = g.c.max(); fmax = g[(g.c == cmax) & g.feasible]
    rows.append(dict(board=b, rule=r, variant=v, n_targets=len(q), share_reaching_p90=float(q.reached.mean()), median_c_needed=rq.c.median() if len(rq) else np.nan,
                     median_depth_at_p90=rq.depth.median() if len(rq) else np.nan, median_depth_c0=q.depth0.median(),
                     median_ratio=float((rq.depth / rq.depth0.where(rq.depth0 > 0)).median()) if len(rq) else np.nan,
                     max_c_grid=cmax, share_feasible_at_max_c=float(len(fmax) / q.shape[0]), mean_p_first_at_max_c=float(fmax.p_first_plan.mean()) if len(fmax) else np.nan,
                     median_sd_rounds=float(g.sd_rounds.median())))
    for c, gc in g.groupby("c"):
        f = gc[gc.feasible]
        est = cluster_mean_ci(f.p_first_plan.values, [f.family.values], nboot=2000, seed=3) if len(f) else (np.nan,) * 3 + (0,)
        curve.append(dict(board=b, rule=r, variant=v, c=c, n_feasible=len(f), p_first_plan_mean=est[0], p_first_plan_lo=est[1], p_first_plan_hi=est[2], n_families=est[3],
                          median_depth=f.depth.median() if len(f) else np.nan, median_breadth=f.breadth.median() if len(f) else np.nan, median_sd_used=gc.sd_used.median()))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "e6b_confidence.csv"), index=False); pd.DataFrame(curve).to_csv(os.path.join(OUT, "e6b_curve.csv"), index=False)
pd.set_option("display.width", 250); print(pd.DataFrame(rows).round(3).to_string())
