"""Leaf-task board from the Open LLM Leaderboard `results` dataset (src/fetch_ollb_results.py): models x 38 leaf tasks (raw accuracy x 100).
Usage: python3 src/build_leaf.py JSONL OUT_DIR   -> OUT_DIR/ollb_leaf.csv (+ ollb_leaf_manifest.json)
Leaves: 23 BBH subtasks + 3 GPQA + 3 MUSR (acc_norm), 7 MATH-hard subtasks (exact_match), IFEval (mean of prompt_level_strict_acc and inst_level_strict_acc, as
the leaderboard does), MMLU-PRO (acc).  One run per model: the newest run (largest `date`) that has all 38 leaves; models whose `fullname` is flagged in `contents`
are dropped.  The 6-benchmark aggregate of the same runs (item-weighted mean of each benchmark's leaves) is checked against the official `... Raw` columns of
`contents` (reported in the manifest).  No floor normalisation is applied (raw accuracy).
"""
import sys, json, hashlib, pathlib
import numpy as np, pandas as pd
jl, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
W = {}
rows = []; shas = []
for l in open(jl):
    r = json.loads(l); shas.append(f"{r['path']} {r['sha256']}")
    R = r["results"] or {}
    for k, v in (r["n_samples"] or {}).items(): W.setdefault(k, v["effective"])
    leaves = {}
    for k, v in R.items():
        if not k.startswith("leaderboard_"): continue
        if k.startswith("leaderboard_bbh_") or k.startswith("leaderboard_gpqa_") or k.startswith("leaderboard_musr_"): m = v.get("acc_norm,none")
        elif k.startswith("leaderboard_math_") and k.endswith("_hard") and k != "leaderboard_math_hard": m = v.get("exact_match,none")
        elif k == "leaderboard_mmlu_pro": m = v.get("acc,none")
        elif k == "leaderboard_ifeval":
            a, b = v.get("prompt_level_strict_acc,none"), v.get("inst_level_strict_acc,none"); m = (a + b) / 2 if isinstance(a, float) and isinstance(b, float) else None
        else: continue
        leaves[k] = m * 100 if isinstance(m, (int, float)) else np.nan
    rows.append(dict(fullname=r["model_name"], date=float(r["date"]) if r["date"] is not None else np.nan, path=r["path"], **leaves))
d = pd.DataFrame(rows)
tasks = sorted(c for c in d.columns if c.startswith("leaderboard_"))
print("runs", len(d), "leaf columns", len(tasks), "models", d.fullname.nunique())
d = d[d[tasks].notna().all(axis=1)]
print("runs with all leaves", len(d), "models", d.fullname.nunique())
d = d.sort_values(["fullname", "date"]).drop_duplicates("fullname", keep="last")
c = pd.read_csv(pathlib.Path(__file__).resolve().parents[1] / "data/processed/ollb6.csv")
fl = set(c[c.Flagged].fullname); d = d[~d.fullname.isin(fl)]
d = d.merge(c[["fullname", "Merged", "Average"]], on="fullname", how="left")
d = d.reset_index(drop=True)
# validation against the official raw aggregates
grp = {"BBH Raw": [t for t in tasks if "_bbh_" in t], "GPQA Raw": [t for t in tasks if "_gpqa_" in t], "MUSR Raw": [t for t in tasks if "_musr_" in t],
       "MATH Lvl 5 Raw": [t for t in tasks if "_math_" in t], "IFEval Raw": ["leaderboard_ifeval"], "MMLU-PRO Raw": ["leaderboard_mmlu_pro"]}
j = d.merge(c, on="fullname", suffixes=("", "_c")); val = {}
for g, ts in grp.items():
    w = np.array([W[t] for t in ts], float); agg = (j[ts].values * w).sum(axis=1) / w.sum() / 100; off = j[g]; ok = off.notna()
    val[g] = dict(n=int(ok.sum()), corr=float(np.corrcoef(agg[ok], off[ok])[0, 1]), median_abs_diff=float((agg[ok] - off[ok]).abs().median()),
                  mean_diff=float((agg[ok] - off[ok]).mean()))
out.mkdir(parents=True, exist_ok=True)
d[["fullname", "date", "Merged", "Average"] + tasks].to_csv(out / "ollb_leaf.csv", index=False)
json.dump(dict(models=len(d), leaves=len(tasks), tasks=tasks, benchmarks=grp, weights={t: W[t] for t in tasks}, files_sha256_of_sorted_path_sha=hashlib.sha256("\n".join(sorted(shas)).encode()).hexdigest(),
               n_files=len(shas), validation_vs_official_raw=val), open(out / "ollb_leaf_manifest.json", "w"), indent=1)
print(len(d), "models x", len(tasks), "leaves"); print(json.dumps(val, indent=1))
