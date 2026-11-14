"""Add the columns feasible/status/seed to result CSVs that lack them (written by driver versions before these columns existed, or by drivers
whose rows carry only some of them). Rules: the investment columns present among L1,K,Linf (hstar: hstar; flip: d95) decide the status:
NaN -> 'censored', +inf -> 'infeasible', else 'ok'. Missing seed is filled with 0 (every driver's default seed; the run_all.sh jobs never change it).
Old rows: censoring by solver time limits was not recorded by the oldest code version (infeasible rows there are exact).
Usage: python3 src/finalize.py CSV [CSV ...]   (in place; idempotent)"""
import sys, numpy as np, pandas as pd
for f in sys.argv[1:]:
    d = pd.read_csv(f); add = [c for c in ("status", "feasible", "seed") if c not in d]
    if not add: print(f, "complete"); continue
    cols = [c for c in ("hstar",) if c in d] or ([c for c in ("L1", "K", "Linf") if c in d] or [c for c in ("d95",) if c in d])
    m = d[cols].values.astype(float)
    if "status" not in d: d["status"] = np.where(np.isnan(m).any(1), "censored", np.where(np.isinf(m).any(1), "infeasible", "ok"))
    if "feasible" not in d: d["feasible"] = d.status == "ok"
    if "seed" not in d: d["seed"] = 0
    d.to_csv(f, index=False); print(f, "added", add, d.status.value_counts().to_dict())
