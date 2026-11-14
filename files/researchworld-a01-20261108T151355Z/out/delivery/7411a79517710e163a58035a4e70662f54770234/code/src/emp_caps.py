"""results/empirical_gains.csv: the 540 OLLB (fine-tune, base) pairs x 6 tasks, gain = fine-tune score - base score (normalised OLLB scores), long format;
results/emp_caps.csv: the emp95/emp99 per-task cap values used (OLLB) and how they are transferred to HELM (MMLU-PRO quantile for every subject), plus the pooled scalars.
Usage: python3 src/emp_caps.py"""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt
R = pathlib.Path(__file__).resolve().parents[1] / "results"
d = pd.read_csv(dt.PROC / "ollb6.csv"); d = d[~d.Flagged]; idx = d.set_index("fullname")
p = d[(d["Base Model"].isin(idx.index)) & (d["Base Model"] != d.fullname)]
g = p[dt.OLLB_TASKS].values - idx.loc[p["Base Model"], dt.OLLB_TASKS].values
long = pd.DataFrame([dict(model_pair=f"{m} <- {b}", fine_tune=m, base=b, task=t, gain=float(g[k, j])) for k, (m, b) in enumerate(zip(p.fullname, p["Base Model"])) for j, t in enumerate(dt.OLLB_TASKS)])
long.to_csv(R / "empirical_gains.csv", index=False)
rows = []
for q in (95, 99):
    pt, n = dt.empirical_gain_caps(q); pool, _ = dt.empirical_gain_caps(q, pooled=True)
    for j, t in enumerate(dt.OLLB_TASKS): rows.append(dict(quantile=q, dataset="ollb", task=t, cap_gain=float(pt[j]), n_pairs=n, variant=f"emp{q}"))
    rows.append(dict(quantile=q, dataset="helm", task="every one of the 57 subjects", cap_gain=float(pt[dt.OLLB_TASKS.index("MMLU-PRO")]), n_pairs=n, variant=f"emp{q} (MMLU-PRO quantile transferred)"))
    for ds in ("ollb", "helm"): rows.append(dict(quantile=q, dataset=ds, task="all tasks (pooled scalar)", cap_gain=float(pool), n_pairs=n, variant=f"emp{q}pool"))
pd.DataFrame(rows).to_csv(R / "emp_caps.csv", index=False); print(len(long), "gain rows;", pd.DataFrame(rows).to_string())
