"""Feasible-draw counts of a run_robust.py task-subset file (request experiment-repo#9).
Usage: python3 code/feasible_counts.py TASKSUB_CSV OUT_CSV
One row per rule x n x target_rank: draws, feasible (finite L1), already_first (L1 == 0), infeasible, censored (NaN, solver time limit),
feasible_share = feasible / (draws - censored)."""
import sys, numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1]); rows = []
for (rule, n, rk), s in d.groupby(["rule", "n", "target_rank"]):
    v = s.L1.values.astype(float); cen = int(np.isnan(v).sum())
    rows.append(dict(rule=rule, n=n, target_rank=rk, draws=len(s), feasible=int(np.isfinite(v).sum()), already_first=int((v == 0).sum()),
                     infeasible=int(np.isinf(v).sum()), censored=cen, feasible_share=np.isfinite(v).sum() / max(len(s) - cen, 1)))
pd.DataFrame(rows).to_csv(sys.argv[2], index=False)
