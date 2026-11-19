"""Duplicate-name rule sensitivity (external-review request #6.3a).
Usage: python3 src/analyze_dup_rule.py     (reads results/ollb_score_{ceil,emp95}.csv [rule 'best'] and results/ollb_dup_{first,latest,worst}.csv)
Writes results/analysis/duplicate_rule_sensitivity.csv (group medians, feasible share, change against 'best') and duplicate_rule_leaders.csv
(leader and runner-up score under mean / median / min). Groups are by rank under the plain mean WITHIN each variant's own matrix;
the median L1 treats infeasible targets as +inf (so inf when more than half are infeasible) and `L1_med_feas` is over feasible targets only.
"""
import pathlib, sys
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
R = ROOT / "results"; OUT = R / "analysis"
GROUPS = {"2": (2, 2), "6-10": (6, 10), "31-100": (31, 100), "101-500": (101, 500), "3-5": (3, 5), "11-30": (11, 30), ">500": (501, 10**6)}
cells = [("ceil", "mean"), ("ceil", "median"), ("ceil", "min"), ("emp95", "mean")]
parts = {}
best = pd.concat([pd.read_csv(R / f"ollb_score_{c}.csv") for c in ("ceil", "emp95")]); parts["best"] = best[best.rule.isin(["mean", "median", "min"])]
for v in ("first", "latest", "worst"): parts[v] = pd.read_csv(R / f"ollb_dup_{v}.csv")
rows = []
for v, d in parts.items():
    d = d.copy(); d["L1"] = pd.to_numeric(d.L1, errors="coerce")
    for cap, rule in cells:
        s = d[(d.cap == cap) & (d.rule == rule)]
        for g, (lo, hi) in GROUPS.items():
            x = s[(s.rank_mean >= lo) & (s.rank_mean <= hi)]
            if not len(x): continue
            f = x.L1[np.isfinite(x.L1)]
            rows.append(dict(dup_rule=v, cap=cap, rule=rule, group=g, n_targets=len(x), infeasible_rate=float((x.feasible == 0).mean()),
                             L1_med=float(np.median(x.L1)), L1_med_feas=float(f.median()) if len(f) else np.nan))
D = pd.DataFrame(rows)
b = D[D.dup_rule == "best"].set_index(["cap", "rule", "group"])
D["L1_med_vs_best"] = [r.L1_med - b.L1_med.get((r.cap, r.rule, r.group), np.nan) for r in D.itertuples()]
D["L1_med_vs_best_rel"] = [(r.L1_med / b.L1_med.get((r.cap, r.rule, r.group), np.nan) - 1) if np.isfinite(r.L1_med) else np.nan for r in D.itertuples()]
D["infeasible_rate_vs_best"] = [r.infeasible_rate - b.infeasible_rate.get((r.cap, r.rule, r.group), np.nan) for r in D.itertuples()]
D.to_csv(OUT / "duplicate_rule_sensitivity.csv", index=False)

# leaders: reconstruct score matrices
from mti import data as dt
import os
lead = []
for v, path in [("best", dt.PROC / "ollb6.csv")] + [(v, dt.PROC / f"ollb6_dup_{v}.csv.gz") for v in ("first", "latest", "worst")]:
    d = pd.read_csv(path); d = d[~d.Flagged].reset_index(drop=True); X = d[dt.OLLB_TASKS].values
    for rule, f in [("mean", lambda X: X.mean(1)), ("median", lambda X: np.median(X, 1)), ("min", lambda X: X.min(1))]:
        val = f(X); o = np.argsort(-val, kind="stable")
        lead.append(dict(dup_rule=v, rule=rule, n_models=len(d), leader=d.fullname[o[0]], leader_precision=d.Precision[o[0]], leader_score=val[o[0]],
                         runner_up=d.fullname[o[1]], runner_up_score=val[o[1]], margin=val[o[0]] - val[o[1]]))
pd.DataFrame(lead).to_csv(OUT / "duplicate_rule_leaders.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(pd.DataFrame(lead).round(3).to_string())
print(D.pivot_table(index=["cap", "rule", "group"], columns="dup_rule", values="L1_med").reindex(columns=["best", "first", "latest", "worst"]).round(2).to_string())
print(D.pivot_table(index=["cap", "rule", "group"], columns="dup_rule", values="infeasible_rate").reindex(columns=["best", "first", "latest", "worst"]).round(3).loc[("emp95", "mean")])
