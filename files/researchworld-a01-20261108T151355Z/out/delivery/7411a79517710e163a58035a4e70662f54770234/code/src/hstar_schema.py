"""Bring the *_hstar.csv files to the schema the figure scripts read: adds `rank_rule` (from the main grid of the same dataset/rule/target)
and `sampled`, `weight` and `hstar_status` in {optimal, already_first, infeasible_at_ceil, not_solved}. `status` (ok/infeasible/censored) is kept. Idempotent. Run after src/sample_weights.py.
Usage: python3 src/hstar_schema.py"""
import pathlib, numpy as np, pandas as pd
R = pathlib.Path(__file__).resolve().parents[1] / "results"
ref = pd.concat([pd.read_csv(R / f, usecols=["dataset", "rule", "target", "rank_rule"]) for f in ["helm_main.csv", "ollb_score.csv", "ollb_ord_ceil.csv"]]).drop_duplicates(["dataset", "rule", "target"])
W = pd.read_csv(R / "sample_weights.csv")[["dataset", "target", "weight"]]
for f in ("helm_hstar.csv", "ollb_hstar.csv", "ollb_hstar_ord.csv"):
    if not (R / f).exists(): continue
    d = pd.read_csv(R / f).drop(columns=[c for c in ("rank_rule", "hstar_status", "sampled", "weight") if c in pd.read_csv(R / f, nrows=0)])
    d = d.merge(ref, on=["dataset", "rule", "target"], how="left")
    d["sampled"] = f.endswith("_ord.csv")      # ollb_hstar_ord: rank-stratified sample, weight = rank-interval weight (src/sample_weights.py); other files: all targets, weight 1
    d = d.merge(W, on=["dataset", "target"], how="left"); d["weight"] = np.where(d.sampled, d.weight, 1.0)
    d["hstar_status"] = np.select([d.status == "censored", d.status == "infeasible", d.hstar == 0], ["not_solved", "infeasible_at_ceil", "already_first"], "optimal")
    d.to_csv(R / f, index=False); print(f, len(d), d.hstar_status.value_counts().to_dict(), "rank_rule missing:", int(d.rank_rule.isna().sum()))
