"""Re-solve every ordinal-rule result reported as infinite (L1 or K) with the strict solver (a MILP that stops without a proof of
infeasibility raises instead of returning inf). Writes results/recheck_inf.csv: file, cap, rule, target_idx, measure, status in {infeasible, finite, unresolved}.
Usage: python3 src/recheck_inf.py [--out results/recheck_inf.csv] DATASET_COLUMN_FILE...   e.g. results/helm_main.csv results/ollb_top500.csv
"""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import ordinal as od, data as dt
args = sys.argv[1:]; OUT = "results/recheck_inf.csv"
if "--out" in args: j = args.index("--out"); OUT = args[j + 1]; args = args[:j] + args[j + 2:]
rows = []
for f in args:
    d = pd.read_csv(f); d = d[d.rule.isin(["borda", "condorcet", "plurality"])]
    for ds, s in d.groupby("dataset"):
        X, *_ = dt.load(ds)
        for _, r in s.iterrows():
            for m in ("L1", "K"):
                if np.isfinite(r[m]): continue
                cap = dt.make_cap(r.cap, X, int(r.target_idx))
                try:
                    v = od.MIN_INV[r.rule](X, int(r.target_idx), cap, 1e-3, m)
                    st = "infeasible" if not np.isfinite(v) else "finite"
                except RuntimeError as e: v, st = np.nan, "unresolved"
                rows.append(dict(file=f, cap=r.cap, rule=r.rule, target_idx=int(r.target_idx), measure=m, value=v, status=st))
        print(f, ds, len(rows), flush=True)
        pd.DataFrame(rows).to_csv(OUT, index=False)
pd.DataFrame(rows).to_csv(OUT, index=False)
print(pd.DataFrame(rows).groupby(["file", "rule", "status"]).size())
