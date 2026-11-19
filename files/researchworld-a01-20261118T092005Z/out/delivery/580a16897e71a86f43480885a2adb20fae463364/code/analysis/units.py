"""R5: is the ordering of the rules by price the same under the cost units points / sigma / headroom / convex2?
usage: units.py RAWDIR OUTDIR  reads RAWDIR/units_*.csv (scripts/run_units.py); writes OUTDIR/units.csv (contract table) and OUTDIR/units_tau.csv.
Per (board, unit, rule): median over targets (top-30 by the official rule, own-leader incumbent, target not already first under the rule) of the least cost under a per-task cap
(infeasible = infinite), the median breadth fraction k/m (breadth objective), the share feasible, and the rank of the rule among the rules by median cost.
Kendall tau (cluster bootstrap by target family is not applicable to a 4-unit rank comparison; the tau between unit pairs is given as is) between the rule orderings of unit pairs."""
import sys, os, glob, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from stats import kendall_tau
RAW, OUT = sys.argv[1], sys.argv[2]
u = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{RAW}/units_*.csv"))]); BOARD = {"helm": "helm_mmlu", "m6raw": "ollb_bench_raw", "m39": "ollb_sub"}
u["board"] = u.board.map(BOARD)
rows = []
for (board, cap), g in u.groupby(["board", "capname"]):
    for unit, gu in g.groupby("unit"):
        dep = gu[gu.objective == "depth"].set_index(["target", "rule"]); br = gu[gu.objective == "breadth"].set_index(["target", "rule"])
        for rule in gu.rule.unique():
            d = dep.xs(rule, level="rule"); b = br.xs(rule, level="rule")
            pos = d[~(d.cost <= 1e-12)]          # not already first under this rule
            cost = pos.cost.where(pos.feasible, np.inf)
            kf = (b.loc[pos.index].breadth / b.loc[pos.index].m).where(b.loc[pos.index].feasible, np.inf)
            rows.append(dict(board=board, rule=rule, unit=unit, cap=cap, n_targets=len(pos), share_feasible=float(pos.feasible.mean()) if len(pos) else np.nan,
                             median_cost=float(np.median(cost)) if len(pos) else np.nan, median_k_frac=float(np.median(kf)) if len(pos) else np.nan,
                             median_depth_points=float(np.median(pos.depth_points.where(pos.feasible, np.inf))) if len(pos) else np.nan, approx=bool(pos.approx.any()) if len(pos) else False))
r = pd.DataFrame(rows)
r["rank_by_cost"] = r.groupby(["board", "unit", "cap"]).median_cost.rank(method="min")
r["rank_by_breadth"] = r.groupby(["board", "unit", "cap"]).median_k_frac.rank(method="min")
os.makedirs(OUT, exist_ok=True); r.to_csv(f"{OUT}/units.csv", index=False)
taus = []
for (board, cap), g in r.groupby(["board", "cap"]):
    for met in ("rank_by_cost", "rank_by_breadth"):
        P = g.pivot(index="rule", columns="unit", values=met).dropna()
        for a, b in itertools.combinations(P.columns, 2):
            taus.append(dict(board=board, cap=cap, metric=met, unit_a=a, unit_b=b, kendall_tau=kendall_tau(P[a], P[b]), n_rules=len(P)))
t = pd.DataFrame(taus); t.to_csv(f"{OUT}/units_tau.csv", index=False)
print(r[r.cap == "cap"].pivot_table(index=["board", "unit"], columns="rule", values="median_cost").round(2).to_string())
print(t[t.cap == "cap"].round(2).to_string())
