"""Build standardized score matrices (CSV, rows=models, cols=benchmarks, NaN=missing) in /work/data/proc.
Inputs are in /work/data (see README for how they were downloaded)."""
import json, os, re
import numpy as np, pandas as pd
D = "/work/data"; OUT = f"{D}/proc"; os.makedirs(OUT, exist_ok=True)

# ---------------- MTEB ----------------
M = pd.read_csv(f"{D}/mteb_proc/mteb_full_matrix.csv", index_col=0)
meta = pd.read_csv(f"{D}/mteb_proc/mteb_task_meta.csv").drop_duplicates("task").set_index("task")
mm = pd.read_csv(f"{D}/mteb_proc/mteb_model_meta.csv", index_col=0)
bad = [t for t in M.columns if M[t].max() > 100 or M[t].min() < -100]
print("MTEB tasks dropped for out-of-range scores:", bad)
M = M.drop(columns=bad)
def guess_type(t):
    if t in meta.index: return meta.loc[t, "type"]
    for k, v in [("PairClassification", "PairClassification"), ("Classification", "Classification"), ("Clustering", "Clustering"),
                 ("Reranking", "Reranking"), ("Retrieval", "Retrieval"), ("STS", "STS"), ("Summarization", "Summarization"),
                 ("BitextMining", "BitextMining")]:
        if k.lower() in t.lower(): return v
    return "Other"
tt = pd.Series({t: guess_type(t) for t in M.columns}); tt.name = "type"
tl = pd.Series({t: (meta.loc[t, "langs"] if t in meta.index and isinstance(meta.loc[t, "langs"], str) else "unk") for t in M.columns}, name="langs")
tm = pd.concat([tt, tl], axis=1); tm["n_models"] = M.notna().sum(axis=0)
tm.to_csv(f"{OUT}/mteb_task_info.csv")
M.to_csv(f"{OUT}/mteb_all.csv")
mm.to_csv(f"{OUT}/mteb_model_info.csv")
def dense_block(M, tmin, mmin):
    T = M.columns[M.notna().sum(axis=0) >= tmin]; S = M[T]
    S = S[S.notna().sum(axis=1) >= mmin]
    return S.loc[:, S.notna().sum(axis=0) >= 30]   # guard: columns must keep >= 30 observations after the row filter
S = dense_block(M, 100, 60); S.to_csv(f"{OUT}/mteb_main.csv")   # main MTEB condition
print("mteb_main", S.shape, S.notna().mean().mean())
S = dense_block(M, 150, 80); S.to_csv(f"{OUT}/mteb_dense.csv")
print("mteb_dense", S.shape, S.notna().mean().mean())
Te = [t for t in M.columns if tm.loc[t, "langs"] == "eng"]
S = dense_block(M[Te], 60, 40); S.to_csv(f"{OUT}/mteb_eng.csv")
print("mteb_eng", S.shape, S.notna().mean().mean())

# ---------------- Open LLM leaderboard ----------------
o = pd.read_parquet(f"{D}/openllm/contents.parquet")
cols = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]
o = o[~o["Flagged"]].drop_duplicates("fullname").set_index("fullname")
O = o[cols].astype(float); O.to_csv(f"{OUT}/openllm.csv")
o[["Submission Date", "#Params (B)", "Base Model", "Type"]].to_csv(f"{OUT}/openllm_info.csv")
print("openllm", O.shape)

# ---------------- HELM Lite ----------------
def table(f, title_prefix, metric=None):
    j = json.load(open(f)); out = {}
    for t in j:
        if not t["title"].startswith(title_prefix): continue
        h = [x["value"] for x in t["header"]]
        mi = h.index(metric) if metric else None
        for r in t["rows"]:
            v = r[mi].get("value") if mi is not None else None
            out[r[0]["value"]] = v
    return out
H = {}
core = json.load(open(f"{D}/helm/core_scenarios.json"))[0]
hdr = [x["value"] for x in core["header"]]
core_cols = {}
for ci, c in enumerate(hdr[2:], start=2):
    core_cols[c] = {r[0]["value"]: r[ci].get("value") for r in core["rows"]}
Hc = pd.DataFrame(core_cols).astype(float)
Hc.to_csv(f"{OUT}/helm_core10.csv")
fine = {k: v for k, v in core_cols.items() if not k.startswith(("MMLU", "LegalBench", "WMT"))}
for g, metric in [("mmlu", "EM"), ("legalbench", "EM"), ("wmt_14", "BLEU-4")]:
    j = json.load(open(f"{D}/helm/g_{g}.json"))
    for t in j[1:]:
        h = [x["value"] for x in t["header"]]; mi = h.index(metric)
        fine[f"{g}:{t['title']}"] = {r[0]["value"]: r[mi].get("value") for r in t["rows"]}
Hf = pd.DataFrame(fine).astype(float); Hf.to_csv(f"{OUT}/helm_fine.csv")
print("helm core", Hc.shape, Hc.notna().mean().mean(), "fine", Hf.shape, Hf.notna().mean().mean())

# ---------------- LiveBench ----------------
d = pd.read_parquet(f"{D}/livebench/judgment.parquet")
L = d.groupby(["model", "task"]).score.mean().unstack() * 100
L = L[L.notna().sum(axis=1) >= 5]; L.to_csv(f"{OUT}/livebench.csv")
print("livebench", L.shape, L.notna().mean().mean())
