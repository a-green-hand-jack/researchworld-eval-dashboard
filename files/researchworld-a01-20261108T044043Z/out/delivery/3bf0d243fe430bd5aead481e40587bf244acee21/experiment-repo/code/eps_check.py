"""Margin-grid check for the ordinal solvers: the strict-win margin eps = 1e-3 of the core tables against eps = 1e-5 on the same
targets (HELM: all 79 models, cap emp99T; OLLB: the 50 best models, cap emp99).  A finite margin eps costs at most eps per raised task
over the infimum of the open-strict problem, except when a cap lies within eps of the rival score that must be passed.
Usage: python3 code/eps_check.py RESULTS_DIR OUT_CSV  (reads variants/eps1e5_{helm,ollb}.csv and core_{helm,ollb}.csv)"""
import sys, pathlib
import numpy as np, pandas as pd
R = pathlib.Path(sys.argv[1]); NT = {"helm": 57, "ollb": 6}; CAP = {"helm": "emp99T", "ollb": "emp99"}; rows = []
for ds in ("helm", "ollb"):
    a = pd.read_csv(R / "variants" / f"eps1e5_{ds}.csv"); b = pd.read_csv(R / f"core_{ds}.csv"); b = b[b.cap == CAP[ds]]
    m = a.merge(b, on=["rule", "target_idx"], suffixes=("_small", "_big"))
    for rule, s in m.groupby("rule"):
        f = np.isfinite(s.L1_small) & np.isfinite(s.L1_big) & (s.L1_big > 0); d = (s.L1_big - s.L1_small)[f]
        rows.append(dict(dataset=ds, cap=CAP[ds], rule=rule, n_targets=len(s), n_positive_cost=int(f.sum()),
                         feasibility_flips=int((np.isinf(s.L1_small) != np.isinf(s.L1_big)).sum()), K_changed=int((s.K_small != s.K_big)[f].sum()),
                         L1_diff_median=float(d.median()), L1_diff_max=float(d.max()), L1_diff_min=float(d.min()),
                         rel_diff_max_cost_gt_1=float((d / s.L1_small[f])[s.L1_small[f] > 1].max()), bound_n_eps=NT[ds] * 1e-3,
                         n_above_bound=int((d > NT[ds] * 1e-3 + 1e-6).sum()), Linf_diff_max=float((s.Linf_big - s.Linf_small)[f].abs().max())))
pd.DataFrame(rows).to_csv(sys.argv[2], index=False); print(pd.DataFrame(rows).round(5).to_string())
