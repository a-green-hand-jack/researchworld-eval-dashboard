"""E7 summary (appendix).  usage: e7.py RAWDIR OUTDIR
 e7_margin_slice.csv : per variant (margin eps, slice) and rule: feasible share and median breadth at B = 10, median uncapped depth, median depth ratio to the baseline variant (same target, uncapped), and Kendall tau of the rule order
                       (by median uncapped depth) with the baseline order.
 e7_totalcap.csv     : cap type: a total-depth cap D instead of the per-task cap B (from the frontier files, uncapped per-task): least k with C(k) <= D, per board and rule; share of targets that can reach first place within D."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from stats import kendall_tau
RAW, OUT = sys.argv[1], sys.argv[2]
d = pd.read_csv(os.path.join(RAW, "e7_m6.csv")); d["feasible"] = d.feasible.astype(str) == "True"
d["variant"] = d.slice + "/eps=" + d.eps.map(lambda x: f"{x:g}")
base = d[d.variant == "main/eps=1e-06"]
rows = []
order0 = base[(base.B == 100) & (base.objective == "depth")].groupby("rule").depth.median()
for v, g in d.groupby("variant"):
    dep = g[(g.B == 100) & (g.objective == "depth")]; br = g[(g.B == 10) & (g.objective == "breadth")]
    med = dep.groupby("rule").depth.median()
    tau = kendall_tau(order0.reindex(med.index).values, med.values)
    for rule in med.index:
        a = dep[dep.rule == rule].set_index("target").depth; b0 = base[(base.B == 100) & (base.objective == "depth") & (base.rule == rule)].set_index("target").depth
        ok = (b0 > 0) & a.notna() & b0.reindex(a.index).notna()
        r = (a[ok] / b0.reindex(a.index)[ok])
        bb = br[br.rule == rule]
        rows.append(dict(variant=v, rule=rule, n_targets=int(bb.target.nunique()), feasible_share_B10=float(bb.feasible.mean()), median_breadth_B10=float(bb.breadth.median()) if bb.feasible.any() else np.nan,
                         median_depth_uncapped=float(med[rule]), median_ratio_to_baseline=float(r.median()) if len(r) else np.nan, kendall_tau_rule_order=float(tau), N=int(g.N.iloc[0])))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "e7_margin_slice.csv"), index=False)
tc = []
for bname, f in (("helm_mmlu", "frontier_helm.csv"), ("ollb_bench", "frontier_ollb_m6.csv")):
    p = os.path.join(RAW, f)
    if not os.path.exists(p): continue
    fr = pd.read_csv(p); fr["feasible"] = fr.feasible.astype(str) == "True"; fr = fr[(fr.B == 100) & (fr.incumbent == "own")]
    m = int(fr.k.max())
    for D in (10.0, 20.0, 50.0, 100.0):
        for (rule, t), g in fr.groupby(["rule", "target"]):
            ok = g[g.feasible & (g.depth <= D + 1e-9)]
            tc.append(dict(board=bname, rule=rule, target=t, D=D, k_D=int(ok.k.min()) if len(ok) else m + 1, m=m, reachable=len(ok) > 0))
tc = pd.DataFrame(tc)
if len(tc):
    s = tc.groupby(["board", "rule", "D"]).agg(n_targets=("target", "nunique"), share_reachable=("reachable", "mean"), median_k=("k_D", "median"), m=("m", "first")).reset_index()
    s["median_k_frac"] = s.median_k / s.m
    s.to_csv(os.path.join(OUT, "e7_totalcap.csv"), index=False)
pd.set_option("display.width", 250)
print(pd.DataFrame(rows).round(3).to_string())
