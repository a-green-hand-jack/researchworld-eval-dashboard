"""Tidy HELM Lite v1.13.0 core_scenarios 'Accuracy' table -> wide parquet.
usage: python3 -I build_helm_lite.py RAWDIR OUT.parquet"""
import json, sys, re
import pandas as pd
raw, out = sys.argv[1:3]
tabs = json.load(open(f"{raw}/groups_core_scenarios.json"))
acc = [t for t in tabs if t["title"] == "Accuracy"][0]
schema = json.load(open(f"{raw}/schema.json"))
meta = {m["display_name"]: m for m in schema["models"]}
hdr = [h["value"] for h in acc["header"]]
rows = []
for r in acc["rows"]:
    d = {"model": r[0]["value"]}
    # deployment-style model name taken from run_spec_names of a scenario cell
    names = set()
    for c in r[2:]:
        for rs in c.get("run_spec_names", []):
            m = re.search(r"model=([^,]+)", rs)
            if m: names.add(m.group(1))
    d["model_run_name"] = ";".join(sorted(names))
    for h, c in zip(hdr[1:], r[1:]):
        d[h] = c.get("value")
    m = meta.get(d["model"], {})
    d["creator_organization"] = m.get("creator_organization")
    d["access"] = m.get("access")
    d["release_date"] = m.get("release_date")
    d["num_parameters"] = m.get("num_parameters")
    rows.append(d)
df = pd.DataFrame(rows)
metric_cols = [h for h in hdr[2:]]  # 10 scenarios (excluding Mean win rate)
ren = {"Mean win rate": "helm_mean_win_rate"}
short = {"NarrativeQA - F1": "narrativeqa_f1", "NaturalQuestions (open-book) - F1": "naturalquestions_openbook_f1",
         "NaturalQuestions (closed-book) - F1": "naturalquestions_closedbook_f1", "OpenbookQA - EM": "openbookqa_em",
         "MMLU - EM": "mmlu_em", "MATH - Equivalent (CoT)": "math_equiv_cot", "GSM8K - EM": "gsm8k_em",
         "LegalBench - EM": "legalbench_em", "MedQA - EM": "medqa_em", "WMT 2014 - BLEU-4": "wmt14_bleu4"}
assert set(short) == set(metric_cols), metric_cols
df = df.rename(columns={**ren, **short})
df["release_date"] = pd.to_datetime(df["release_date"])
df["unmatched_meta"] = df["creator_organization"].isna()
print(df.shape, "dup models:", df.model.duplicated().sum(), "unmatched meta:", df.unmatched_meta.sum())
sc = list(short.values())
print("missing frac", df[sc].isna().mean().mean()); print(df[sc].isna().sum()[lambda s: s > 0])
print(df[df.unmatched_meta].model.tolist())
df.to_parquet(out, index=False)
