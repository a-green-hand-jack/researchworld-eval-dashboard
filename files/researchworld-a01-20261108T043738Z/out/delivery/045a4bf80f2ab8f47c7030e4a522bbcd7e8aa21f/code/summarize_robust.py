"""Summarise robustness runs (run_robust.py output) into percentile intervals.
Usage: python3 code/summarize_robust.py IN_CSV OUT_CSV
noise / taskboot files (column `draw`, `target`): per rule and target, 2.5/50/97.5 percentiles of L1 and K over the draws
  (taken over feasible draws), the share of infeasible draws and of censored (NaN, solver time limit) draws, and the median rank
  of the target under the rule itself in the perturbed data.
tasksub files (column `n`, `target_rank`): the same per rule x number of tasks x target rank, over random task subsets.
"""
import sys
import numpy as np, pandas as pd

assert len(sys.argv) == 3 and sys.argv[1] != sys.argv[2], __doc__
d = pd.read_csv(sys.argv[1])
assert "draw" in d or "n" in d, "input is not a run_robust.py output"
keys = ["rule", "n", "target_rank"] if "n" in d else ["rule", "target", "rank_mean_obs"]
rows = []
for k, s in d.groupby(keys):
    r = dict(zip(keys, k)); r["draws"] = len(s)
    for m in ("L1", "K"):
        v = s[m].values.astype(float)
        r[m + "_infeasible"] = float(np.mean(np.isinf(v))); r[m + "_censored"] = float(np.mean(np.isnan(v)))
        f = v[np.isfinite(v)]
        for q in (2.5, 50, 97.5): r[f"{m}_p{q:g}"] = float(np.percentile(f, q)) if len(f) else np.nan
    if "rank_rule" in s: r["rank_rule_median"] = float(s["rank_rule"].median())
    rows.append(r)
pd.DataFrame(rows).to_csv(sys.argv[2], index=False)
