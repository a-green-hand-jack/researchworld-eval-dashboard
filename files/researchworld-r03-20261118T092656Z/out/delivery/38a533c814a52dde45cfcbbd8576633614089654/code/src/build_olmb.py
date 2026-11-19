"""Open LLM Leaderboard 'contents' (commit 9c09a7c) -> data/olmb_matrix.parquet.
usage: python3 -I build_olmb.py IN.parquet OUT.parquet"""
import sys, re
import pandas as pd, numpy as np
src, out = sys.argv[1:3]
o = pd.read_parquet(src)
B = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]
tag = {"IFEval": "ifeval", "BBH": "bbh", "MATH Lvl 5": "math_lvl5", "GPQA": "gpqa", "MUSR": "musr", "MMLU-PRO": "mmlu_pro"}
df = pd.DataFrame({"model_id": o["fullname"], "eval_name": o["eval_name"]})
for b in B:
    df[f"{tag[b]}_norm"] = o[b]          # normalized score, 0-100
for b in B:
    df[f"{tag[b]}_raw"] = o[f"{b} Raw"]  # raw metric, 0-1
df["average_norm"] = o["Average ⬆️"]
df["type"] = o["Type"]; df["type_icon"] = o["T"]
for k, v in {"precision": "Precision", "weight_type": "Weight type", "architecture": "Architecture", "model_sha": "Model sha",
             "license": "Hub License", "hub_likes": "Hub ❤️", "params_b": "#Params (B)", "available_on_hub": "Available on the hub",
             "moe": "MoE", "flagged": "Flagged", "chat_template": "Chat Template", "co2_kg": "CO₂ cost (kg)",
             "merged": "Merged", "official_provider": "Official Providers", "generation": "Generation"}.items():
    df[k] = o[v]
df["license"] = df["license"].replace("", np.nan)
df["submission_date"] = pd.to_datetime(o["Submission Date"].replace("", np.nan))
df["upload_date"] = pd.to_datetime(o["Upload To Hub Date"].replace("", np.nan))
df["base_model_raw"] = o["Base Model"]
bm = o["Base Model"].str.replace(r"\s*\(Merge\)$", "", regex=True)
bm = bm.where(~bm.isin(["", "Removed"]), np.nan)
df["base_model"] = bm                       # NaN if unknown/Removed
df["base_model_known"] = bm.notna()
df["org"] = o["fullname"].str.split("/").str[0]
df["base_org"] = bm.str.split("/").str[0]
# coarse backbone family (heuristic keyword match on base model, falling back to model id)
fam = [("llama", r"llama|nemotron|vicuna"), ("qwen", r"qwen|qwq"), ("mistral", r"mistral|mixtral|nemo|zephyr|openhermes"),
       ("gemma", r"gemma"), ("phi", r"\bphi|/phi"), ("yi", r"/yi[-_]|\byi[-_]|^01-ai"), ("falcon", r"falcon"),
       ("deepseek", r"deepseek"), ("internlm", r"internlm"), ("olmo", r"olmo"), ("smollm", r"smollm"),
       ("stablelm", r"stablelm"), ("gpt-neox/pythia", r"pythia|gpt-neo|gpt-j|opt-"), ("command-r", r"c4ai|command-r"),
       ("solar", r"solar"), ("glm", r"glm"), ("granite", r"granite")]
def family(base, mid):
    for text in (base, mid):
        if isinstance(text, str):
            t = text.lower()
            for name, pat in fam:
                if re.search(pat, t): return name
    return "other"
df["family_heur"] = [family(b, m) for b, m in zip(df.base_model, df.model_id)]
df["family_group"] = df["base_model"].fillna(df["model_id"])   # grouping key: base model (or self if unknown)
df["dup_model_id"] = df["model_id"].duplicated(keep=False)      # same fullname, different precision/sha
df.to_parquet(out, index=False)
sc = [f"{tag[b]}_norm" for b in B]
print(df.shape, "score NaN frac", df[sc].isna().mean().mean(), "dup ids", df.dup_model_id.sum(), "unique ids", df.model_id.nunique())
print("flagged", df.flagged.sum(), "merged", df.merged.sum(), "base unknown", (~df.base_model_known).sum(), "n family_group", df.family_group.nunique())
print(df.family_heur.value_counts().head(12))
