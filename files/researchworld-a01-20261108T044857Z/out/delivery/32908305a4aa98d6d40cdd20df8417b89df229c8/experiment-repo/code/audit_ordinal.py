"""Audit of the ordinal-rule fix (experiment-repo#6): rows of the ordinal rules before and after the single strict feasible set.
Usage: python3 code/audit_ordinal.py OLD_RESULTS_DIR NEW_RESULTS_DIR OUT_CSV
Every run file that contains borda / condorcet / plurality / copeland rows (runs/, variants/, robust/) is matched row by row between the
old directory (results as of the first delivery) and the new one on (cap, rule, target_idx) for core files or (draw, rule, target, n,
target_rank) for robust files. Per file x rule: rows, rows_new_only, rows_changed (status or L1 or K differs), status flips
(feasible->infeasible and back), and the largest and median absolute L1 change among the changed rows."""
import sys, pathlib, numpy as np, pandas as pd
old, new, out = map(pathlib.Path, sys.argv[1:4]); ORD = ["borda", "condorcet", "plurality", "copeland"]; rows = []
for f in sorted(list(new.glob("runs/*.csv")) + list(new.glob("variants/*.csv")) + list(new.glob("robust/rob_*.csv"))):
    rel = f.relative_to(new); o = old / rel
    n = pd.read_csv(f)
    if "rule" not in n or not n.rule.isin(ORD).any(): continue
    n = n[n.rule.isin(ORD)]
    key = [k for k in ("dataset", "cap", "rule", "target_idx", "draw", "target", "n", "target_rank") if k in n.columns]
    if not o.exists():
        rows.append(dict(file=str(rel), rule="*", rows=len(n), note="no old counterpart")); continue
    p = pd.read_csv(o); p = p[p.rule.isin(ORD)]
    m = n.merge(p, on=key, how="left", suffixes=("", "_old"), indicator=True)
    for rule, s in m.groupby("rule"):
        b = s[s._merge == "both"]
        fin = lambda v: np.isfinite(v.astype(float))
        same = lambda a, c: (a.astype(float).fillna(-1) == c.astype(float).fillna(-1)) | np.isclose(a.astype(float), c.astype(float), rtol=0, atol=1e-9, equal_nan=True)
        chg = ~(same(b.L1, b.L1_old) & same(b.K, b.K_old))
        flip_new_feas = (fin(b.L1) & ~fin(b.L1_old) & b.L1_old.notna()).sum(); flip_new_inf = (~fin(b.L1) & b.L1.notna() & fin(b.L1_old)).sum()
        dl = (b.L1 - b.L1_old).abs()[chg & fin(b.L1) & fin(b.L1_old)]
        rows.append(dict(file=str(rel), rule=rule, rows=len(s), rows_new_only=int((s._merge == "left_only").sum()), rows_changed=int(chg.sum()),
                         censored_new=int(s.L1.isna().sum()), censored_old=int(b.L1_old.isna().sum()), infeasible_new=int(np.isinf(s.L1.astype(float)).sum()),
                         infeasible_to_feasible=int(flip_new_feas), feasible_to_infeasible=int(flip_new_inf),
                         max_abs_dL1=float(dl.max()) if len(dl) else 0.0, median_abs_dL1=float(dl.median()) if len(dl) else 0.0))
pd.DataFrame(rows).to_csv(out, index=False); print(pd.DataFrame(rows).to_string())
