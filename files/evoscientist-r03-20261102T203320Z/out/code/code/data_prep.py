"""Build the model x benchmark score matrices used in all experiments.

Outputs (data/processed/*.csv, rows=models, cols=benchmarks, NaN=missing):
  mteb_wide.csv   : MTEB tasks covered by >= 100 models (sparse, 'wide' condition)
  mteb_dense.csv  : largest (greedily found) complete block with >= 120 models (dense condition)
  mteb_eng_dense.csv: complete block restricted to the English-only tasks of the dense block (not used by default)
  olb.csv, helm.csv, livebench.csv : small LLM-leaderboard matrices (complete)
  mteb_task_type.csv : heuristic task-type (from task name) for MTEB tasks
Usage: python code/data_prep.py
"""
import json, os, re
import numpy as np, pandas as pd

os.makedirs("data/processed", exist_ok=True)


def mteb():
    df = pd.read_csv("data/mteb_long.csv.gz")
    # average over revision directories of the same model (same weights, re-runs / re-uploads)
    g = df.groupby(["model", "task"]).score.mean().reset_index()
    W = g.pivot(index="model", columns="task", values="score")
    return W


def task_type(t):
    if "Classification" in t and ("Pair" in t or t in ("SprintDuplicateQuestions", "TwitterSemEval2015", "TwitterURLCorpus")):
        return "PairClf"
    if t in ("SprintDuplicateQuestions", "TwitterSemEval2015", "TwitterURLCorpus"):
        return "PairClf"
    if "Classification" in t or t in ("Banking77Classification",):
        return "Clf"
    if "Clustering" in t:
        return "Clust"
    if t.startswith("STS") or t in ("BIOSSES", "SICK-R", "SICKR"):
        return "STS"
    if t in ("AskUbuntuDupQuestions", "MindSmallReranking", "SciDocsRR", "StackOverflowDupQuestions"):
        return "Rerank"
    if t == "SummEval":
        return "Summ"
    return "Retr/Other"


def dense_block(W, alpha=1.0):
    """Greedy: start from tasks with >=min_models observed; iteratively drop the row or column with the
    most missing cells (ties: column first) until complete; stop when complete."""
    X = W.notna().values.astype(int)
    rows = np.arange(X.shape[0]); cols = np.arange(X.shape[1])
    # initial: keep tasks with >= min_models, models with >= 30 tasks
    while True:
        sub = X[np.ix_(rows, cols)]
        miss = (1 - sub)
        if miss.sum() == 0:
            break
        rm, cm = miss.sum(1), miss.sum(0)
        # benefit per removed line: removing a row loses len(cols) cells, a column loses len(rows) cells
        # choose line maximizing missing cells removed per cell lost
        rs, cs = alpha * rm / len(cols), cm / len(rows)
        if rs.max() >= cs.max():
            rows = np.delete(rows, rs.argmax())
        else:
            cols = np.delete(cols, cs.argmax())
    return W.iloc[rows, cols]


if __name__ == "__main__":
    W = mteb()
    print("MTEB raw:", W.shape, "observed frac", W.notna().mean().mean().round(3))
    # wide sparse matrix
    cov = W.notna().sum()
    Ww = W.loc[:, cov >= 100]
    Ww = Ww.loc[Ww.notna().sum(axis=1) >= 20]
    Ww.to_csv("data/processed/mteb_wide.csv")
    print("mteb_wide", Ww.shape, "observed", Ww.notna().mean().mean().round(3))
    # dense
    D = dense_block(W.loc[:, cov >= 100].loc[W.notna().sum(axis=1) >= 20])
    D.to_csv("data/processed/mteb_dense.csv")
    print("mteb_dense", D.shape)
    base = W.loc[:, cov >= 100].loc[W.notna().sum(axis=1) >= 20]
    for a, nm in [(0.6, "mteb_mid")]:
        B = dense_block(base, alpha=a)
        B.to_csv(f"data/processed/{nm}.csv")
        print(nm, B.shape)
    pd.Series({t: task_type(t) for t in W.columns}, name="type").to_csv("data/processed/mteb_task_type.csv")
    print(pd.Series({t: task_type(t) for t in D.columns}).value_counts())

    # Open LLM Leaderboard (v2), raw scores, complete rows, non-flagged, dedup by fullname
    o = pd.read_parquet("data/extra/olb.parquet")
    cols = ["IFEval Raw", "BBH Raw", "MATH Lvl 5 Raw", "GPQA Raw", "MUSR Raw", "MMLU-PRO Raw"]
    o = o[~o["Flagged"].astype(bool)].drop_duplicates("fullname").dropna(subset=cols)
    O = o.set_index("fullname")[cols].astype(float) * 100
    O.columns = [c.replace(" Raw", "") for c in cols]
    O.to_csv("data/processed/olb.csv")
    print("olb", O.shape, O.describe().loc[["mean", "std"]].round(1).to_dict())

    # HELM Lite v1.13.0 core scenarios, 'Accuracy' table (10 scenarios)
    h = json.load(open("data/extra/helm_core.json"))[0]
    names = [c["value"] for c in h["header"]]
    rows = []
    for r in h["rows"]:
        rows.append([c.get("value") for c in r])
    H = pd.DataFrame(rows, columns=names).set_index("Model")
    H = H.drop(columns=["Mean win rate"]).apply(pd.to_numeric, errors="coerce") * 100
    print("helm raw", H.shape, "missing cells", int(H.isna().sum().sum()))
    H.to_csv("data/processed/helm.csv")

    # LiveBench: mean judged score per (model, task) in percent
    l = pd.read_parquet("data/extra/lb.parquet")
    L = l.groupby(["model", "task"]).score.mean().unstack() * 100  # sparse: not every model has every task
    print("livebench", L.shape, "missing", int(L.isna().sum().sum()))
    L.to_csv("data/processed/livebench.csv")
