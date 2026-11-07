"""Build model x benchmark score matrices (NaN = not evaluated) as .npz files in data/matrices/.

usage: python build_matrices.py <DATA dir> <repo data dir>
Matrices:
  mteb_dense   : MTEB, tasks scored by >=150 models, then models with >=90% of those tasks (near-complete)
  mteb_dense56 : same with >=200 models per task (smaller N, more models)
  mteb_mid     : MTEB, pruned at 60% coverage                      (moderate missingness)
  mteb_sparse  : MTEB, tasks scored by >=50 models, models with >=10 tasks (heavy missingness)
  olb          : Open LLM Leaderboard (6 benchmarks, normalised scores), deduplicated by fullname
  helm         : HELM Lite v1.13.0 core scenarios (10 scenarios)
  helm_mmlu    : HELM MMLU v1.13.0, 57 subjects x 79 LLMs (complete)
  livebench    : LiveBench judgments aggregated per (model, task) (7 tasks)
"""
import json, os, sys
import numpy as np, pandas as pd

def prune(M, thr_row, thr_col, min_rows=0):
    S = M.copy()
    while True:
        ch = False
        r = S.notna().mean(axis=1)
        if (r < thr_row).any():
            S = S[r >= thr_row]; ch = True
        c = S.notna().mean(axis=0)
        if (c < thr_col).any():
            S = S.loc[:, c >= thr_col]; ch = True
        if not ch:
            return S

def save(out, name, M, meta_rows=None, meta_cols=None, note=""):
    M = M.loc[:, M.notna().sum() > 0]
    np.savez_compressed(os.path.join(out, name + ".npz"), Y=M.values.astype(float),
                        models=np.array(M.index.astype(str)), benches=np.array(M.columns.astype(str)))
    if meta_rows is not None:
        meta_rows.reindex(M.index).to_csv(os.path.join(out, name + "_models.csv"))
    if meta_cols is not None:
        meta_cols.reindex(M.columns).to_csv(os.path.join(out, name + "_benches.csv"))
    print(f"{name}: {M.shape}, observed fraction {M.notna().mean().mean():.3f}  {note}", flush=True)

def main(data, repo_data):
    out = os.path.join(repo_data, "matrices"); os.makedirs(out, exist_ok=True)
    # ---------------- MTEB
    proc = os.path.join(data, "processed")
    d = pd.read_parquet(os.path.join(proc, "mteb_long.parquet"))
    mm = pd.read_parquet(os.path.join(proc, "mteb_meta.parquet"))
    d = d[~d.task.isin(["CPUSpeedTask", "GPUSpeedTask"])]
    d = d[(d.score >= -1) & (d.score <= 1)]
    # revisions of one model rarely overlap in tasks (16 conflicts / 85k cells): merge, keep first
    M = d.groupby(["model_dir", "task"]).score.first().unstack()
    tm = json.load(open(os.path.join(repo_data, "mteb_task_meta.json")))
    bmeta = pd.DataFrame({"type": [tm.get(t, {}).get("type", "unknown") for t in M.columns],
                          "n_models": M.notna().sum().values}, index=M.columns)
    mm = mm.sort_values("release_date").groupby("model_dir").agg(
        name=("name", "last"), release_date=("release_date", "max"),
        n_parameters=("n_parameters", "max"), adapted_from=("adapted_from", "last"))
    mm["org"] = [x.split("__")[0] if "__" in x else x for x in mm.index]
    sub = lambda S: S
    def block(tmin, cov):
        T = M[M.columns[M.notna().sum() >= tmin]]
        return T[T.notna().mean(axis=1) >= cov]
    save(out, "mteb_dense", block(150, .9), mm, bmeta)      # ~275 tasks x ~133 models, ~99% observed
    save(out, "mteb_dense56", block(200, .9), mm, bmeta)    # ~56 tasks x ~152 models, ~99.6% observed
    save(out, "mteb_mid", prune(M[M.columns[M.notna().sum() >= 100]], .6, .6), mm, bmeta)
    S = M[M.columns[M.notna().sum() >= 50]]
    save(out, "mteb_sparse", S[S.notna().sum(axis=1) >= 10], mm, bmeta)
    # ---------------- Open LLM Leaderboard
    o = pd.read_parquet(os.path.join(data, "olb", "contents.parquet"))
    cols = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]
    o = o.sort_values("Submission Date").drop_duplicates("fullname", keep="last").set_index("fullname")
    om = o[["Type", "Architecture", "#Params (B)", "Base Model", "Submission Date", "Merged", "Flagged"]].copy()
    save(out, "olb", o[cols].astype(float), om)
    # ---------------- HELM Lite
    h = json.load(open(os.path.join(data, "helm", "core_scenarios.json")))[0]
    names = [x["value"] for x in h["header"]]
    rows = {r[0]["value"]: [c.get("value") if isinstance(c.get("value"), (int, float)) else np.nan for c in r] for r in h["rows"]}
    H = pd.DataFrame.from_dict(rows, orient="index", columns=names).iloc[:, 2:]
    save(out, "helm", H)
    # ---------------- HELM MMLU (57 subjects x 79 LLMs, release v1.13.0 of the HELM MMLU project)
    hm = json.load(open(os.path.join(data, "helm", "mmlu_subjects_v1.13.0.json")))[0]
    hn = [x["value"] for x in hm["header"]]
    hr = {r[0]["value"]: [c.get("value") if isinstance(c.get("value"), (int, float)) else np.nan for c in r] for r in hm["rows"]}
    HM = pd.DataFrame.from_dict(hr, orient="index", columns=hn).iloc[:, 2:]
    save(out, "helm_mmlu", HM)
    # ---------------- LiveBench
    l = pd.read_parquet(os.path.join(data, "livebench", "judgment.parquet"))
    L = l.groupby(["model", "task"]).score.mean().unstack()
    save(out, "livebench", L)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
