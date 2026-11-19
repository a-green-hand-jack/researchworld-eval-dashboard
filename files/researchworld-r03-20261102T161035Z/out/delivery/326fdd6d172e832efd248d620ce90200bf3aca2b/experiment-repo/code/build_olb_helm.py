"""Build Open LLM Leaderboard (raw scores x100) and HELM Lite core-scenario matrices.
usage: build_olb_helm.py OLB_PARQUET HELM_CORE_JSON OUT_DIR"""
import json, sys, os, pandas as pd, numpy as np
olb, helm, out = sys.argv[1:4]
d = pd.read_parquet(olb)
B = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]
d = d[~d["Flagged"].astype(bool)].copy()
d = d.sort_values("Submission Date").drop_duplicates("fullname", keep="last")
m = d.set_index("fullname")[[b + " Raw" for b in B]].rename(columns=lambda c: c.replace(" Raw", "")) * 100
meta = d.set_index("fullname")[["#Params (B)", "Submission Date", "Type", "Architecture", "Base Model"]]
m = m.dropna(how="all")
m.index.name = "model"
m.to_csv(os.path.join(out, "olb_matrix.csv")); meta.loc[m.index].to_csv(os.path.join(out, "olb_meta.csv"))
print("OLB", m.shape, "complete rows", m.notna().all(axis=1).sum())
t = json.load(open(helm))[0]
cols = [h["value"] for h in t["header"]]
rows = {r[0]["value"]: [c.get("value") if isinstance(c, dict) else c for c in r] for r in t["rows"]}
h = pd.DataFrame(rows, index=cols).T.drop(columns=["Model", "Mean win rate"]).astype(float) * 100
h.index.name = "model"
h.to_csv(os.path.join(out, "helm_lite_matrix.csv"))
print("HELM", h.shape, "observed", h.notna().mean().mean())
