"""OLMB v2 per-subtask results (open-llm-leaderboard/results @ aa81ecc, latest results file per model) -> wide parquet.
usage: python3 -I build_olmb_subtasks.py RAWDIR OLMB_MATRIX.parquet OUT.parquet"""
import sys, os, json, glob
import pandas as pd, numpy as np
raw, olmb, out = sys.argv[1:4]
sel = json.load(open(f"{raw}/_selected_files.json"))
rows, bad = [], []
for model, f in sel.items():
    p = os.path.join(raw, f.replace("/", "__"))
    if not os.path.exists(p): bad.append((model, "missing")); continue
    try: d = json.load(open(p))
    except Exception as e: bad.append((model, "json")); continue
    r = d["results"]; x = {"model_id": model, "results_file": f.rsplit("/", 1)[1], "eval_date": d.get("date")}
    for k, v in r.items():
        if k.startswith("leaderboard_bbh_"): x["bbh_" + k[len("leaderboard_bbh_"):]] = v.get("acc_norm,none")
        elif k.startswith("leaderboard_gpqa_"): x["gpqa_" + k[len("leaderboard_gpqa_"):]] = v.get("acc_norm,none")
        elif k.startswith("leaderboard_musr_"): x["musr_" + k[len("leaderboard_musr_"):]] = v.get("acc_norm,none")
        elif k.startswith("leaderboard_math_") and k != "leaderboard_math_hard":
            x["math_" + k[len("leaderboard_math_"):]] = v.get("exact_match,none")
    if "leaderboard_ifeval" in r:
        x["ifeval_prompt_strict_acc"] = r["leaderboard_ifeval"].get("prompt_level_strict_acc,none")
        x["ifeval_inst_strict_acc"] = r["leaderboard_ifeval"].get("inst_level_strict_acc,none")
    if "leaderboard_mmlu_pro" in r: x["mmlu_pro_acc"] = r["leaderboard_mmlu_pro"].get("acc,none")
    rows.append(x)
df = pd.DataFrame(rows)
bench = [c for c in df if c not in ("model_id", "results_file", "eval_date")]
for c in bench: df[c] = pd.to_numeric(df[c], errors="coerce")
df["eval_date"] = pd.to_datetime(df["eval_date"], unit="s", errors="coerce")
# metadata from the OLMB contents matrix (first row per model_id; n_contents_rows flags duplicates by precision)
o = pd.read_parquet(olmb)
cnt = o.groupby("model_id").size().rename("n_contents_rows")
keep = ["model_id", "base_model", "base_model_known", "org", "base_org", "family_heur", "family_group", "type", "params_b", "license",
        "merged", "flagged", "official_provider", "moe", "submission_date", "upload_date", "architecture"]
m = o.drop_duplicates("model_id")[keep].merge(cnt, on="model_id")
df = df.merge(m, on="model_id", how="left")
df["in_contents"] = df.n_contents_rows.notna()
print(df.shape, "benchmarks", len(bench), "failed", len(bad), bad[:5])
print("missing frac", df[bench].isna().mean().mean()); print(df[bench].isna().mean().sort_values().tail(5))
print("rows with any NaN", df[bench].isna().any(axis=1).sum(), "in contents", df.in_contents.sum())
print(bench)
df.to_parquet(out, index=False)
