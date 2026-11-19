"""Regeneration check: re-run one delivered cell from code/scripts/experiments.py and compare with results/replicates.parquet.
Usage: check_cell.py EXPERIMENT TAG      e.g.  check_cell.py MAIN 'er|M1|bern0.5'   (exit 0 and 'IDENTICAL' if all observed-fit rows agree)"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from netgate.sim import run_cell
from experiments import EXPS, SEEDS

R = os.path.join(os.path.dirname(__file__), "..", "..", "results", "replicates.parquet")
exp, tag = sys.argv[1], sys.argv[2]
spec = {k: v for k, v in next(c for c in EXPS[exp]() if c["tag"] == tag).items() if k != "tag"}
new = run_cell(spec, base_seed=SEEDS.get(exp, 20261102))
new = new[~new.est_name.str.contains("@")].rename(columns={"g": "graph_id", "est_name": "estimator", "est": "tau_hat"})
old = pd.read_parquet(R)
old = old[(old.experiment == exp) & (old.tag == tag) & (old.fit_data == "observed")]
k = ["graph_id", "rep", "estimator"]
m = old.merge(new, on=k, suffixes=("_old", "_new"), how="outer", indicator=True)
bad = (m._merge != "both").sum() + (~np.isclose(m.tau_hat_old, m.tau_hat_new, atol=1e-10, equal_nan=True)).sum()
print(f"{exp} {tag}: {len(m)} rows compared, {bad} differ ->", "IDENTICAL" if bad == 0 else "DIFFERENT")
sys.exit(int(bad > 0))
