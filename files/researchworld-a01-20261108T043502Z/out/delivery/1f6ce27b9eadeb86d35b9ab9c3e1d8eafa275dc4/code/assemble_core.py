"""Assemble the tidy core result tables from the run files.
Usage: python3 code/assemble_core.py RUNS_DIR OUT_DIR
Writes OUT_DIR/core_ollb.csv and OUT_DIR/core_helm.csv with columns
  dataset, cap, cap_role, rule, target, target_idx, rank_mean, rank_rule, gap, L1, K, Linf, L2, status
cap_role: primary (OLLB emp99; HELM emp99T = transfer assumption), oracle (ceil), sensitivity (all other caps).
status: ok | infeasible (no investment within the cap reaches first; L1 = K = Linf = inf) | censored (solver time limit, L1/K = NaN)
         | already_first (target already first under the rule; zero investment).
Ordinal rules on OLLB exist for the 50 top targets under the mean only (time-limited MILP, M = 4496).
"""
import sys, pathlib
import numpy as np, pandas as pd

runs, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
SRC = {"ollb": ["ollb_primary_closed.csv", "ollb_capsweep_closed.csv", "ollb_primary_ordinal_top50.csv"],
       "helm": ["helm_primary.csv", "helm_capsweep.csv", "copeland_helm.csv"]}
ROLE = {"ollb": {"emp99": "primary", "ceil": "oracle"}, "helm": {"emp99T": "primary", "ceil": "oracle"}}
COLS = ["dataset", "cap", "cap_role", "rule", "target", "target_idx", "rank_mean", "rank_rule", "gap", "L1", "K", "Linf", "L2", "status"]
for ds, files in SRC.items():
    d = pd.concat([pd.read_csv(runs / f) for f in files], ignore_index=True)
    d = d.drop_duplicates(["cap", "rule", "target_idx"], keep="last")
    d["cap_role"] = d.cap.map(ROLE[ds]).fillna("sensitivity")
    for c in COLS:
        if c not in d: d[c] = np.nan
    d["status"] = np.where(d.L1.isna(), "censored", np.where(np.isinf(d.L1), "infeasible", np.where(d.L1 == 0, "already_first", "ok")))
    d = d[COLS].sort_values(["cap", "rule", "rank_mean", "target_idx"], kind="stable")
    d.to_csv(out / f"core_{ds}.csv", index=False)
    print(ds, len(d), d.groupby("cap_role").size().to_dict(), d.status.value_counts().to_dict())
