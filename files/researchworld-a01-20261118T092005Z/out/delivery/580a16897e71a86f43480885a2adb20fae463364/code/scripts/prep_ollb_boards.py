"""Build the Open LLM Leaderboard boards: (a) m=6 normalised benchmark board from `contents`; (b) m=39 raw sub-task board
from `results`, joined to `contents` on (fullname, model sha) and accepted only where the results file reproduces the
contents row (IFEval and MMLU-PRO raw scores agree to 1e-3).  usage: prep_ollb_boards.py CONTENTS_PARQUET OUT_DIR"""
import sys, os, numpy as np, pandas as pd
cp, out = sys.argv[1], sys.argv[2]
c = pd.read_parquet(cp)
r = pd.read_parquet(os.path.join(out, "ollb_results_leaf.parquet"))
BEN = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]
meta = ["eval_name", "fullname", "Model sha", "Type", "#Params (B)", "Available on the hub", "MoE", "Flagged", "Merged", "Base Model",
        "Submission Date", "Hub License", "Official Providers", "Precision", "Average ⬆️"]
c["main_slice"] = (~c.Merged) & (~c.Flagged) & c["Available on the hub"]
m6 = c[["eval_name"] + [x for x in meta if x != "eval_name"] + ["main_slice"] + BEN + [b + " Raw" for b in BEN]].copy()
m6.to_csv(os.path.join(out, "ollb_m6_contents.csv"), index=False)
leaf = [x for x in r.columns if x.startswith("leaderboard_") and not x.endswith(("__se", "__n", "__prompt_level_strict_acc", "__inst_level_strict_acc"))]
assert len(leaf) == 39, len(leaf)
r["key"] = r.model_name + "|" + r.model_sha; c["key"] = c.fullname + "|" + c["Model sha"]
m = c.merge(r, on="key", how="inner", suffixes=("", "_r"))
m["disc"] = (m["IFEval Raw"] - m["leaderboard_ifeval"]).abs() + (m["MMLU-PRO Raw"] - m["leaderboard_mmlu_pro"]).abs()
m = m.sort_values("disc").drop_duplicates("eval_name", keep="first")
n_all = len(m); m = m[m.disc < 1e-3]
print("contents rows", len(c), "with a results file", n_all, "reproduced (disc<1e-3)", len(m), "of which main slice", int(m.main_slice.sum()))
sub = m[["eval_name"] + leaf].copy(); sub[leaf] = sub[leaf] * 100.0
sub.to_csv(os.path.join(out, "ollb_sub_scores.csv"), index=False)
se = m[["eval_name"] + [x + "__se" for x in leaf]].copy()
se.columns = ["eval_name"] + leaf
for x in leaf: se[x] = pd.to_numeric(se[x], errors="coerce") * 100.0
se.to_csv(os.path.join(out, "ollb_sub_se.csv"), index=False)
nn = m.reindex(columns=["eval_name"] + [x + "__n" for x in leaf]).copy(); nn.columns = ["eval_name"] + leaf
nn.to_csv(os.path.join(out, "ollb_sub_n.csv"), index=False)
print("sub-task NaN cells", int(sub[leaf].isna().sum().sum()), "se NaN", int(se[leaf].isna().sum().sum()))
