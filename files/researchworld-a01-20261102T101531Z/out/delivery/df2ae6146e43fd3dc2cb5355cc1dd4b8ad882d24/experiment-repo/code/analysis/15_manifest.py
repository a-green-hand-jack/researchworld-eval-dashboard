"""results/data_manifest.json: sources, snapshot ids, checksums and exclusion counts for the Data table.
Run after 01_build_data.py and 01b_fetch_olb_results.py (needs data/processed/*.json, no network)."""
import json
from common import *
P = f"{ROOT}/data/processed"; man = json.load(open(f"{P}/manifest.json")); om = json.load(open(f"{P}/olb_results_manifest.json"))
helm_files = {k: v for k, v in man.items() if "/helm/" in k}
import glob
names = set(); full = set()
for f in sorted(glob.glob(f"{ROOT}/data/raw/helm/groups/json/mmlu_mmlu_subject:*.json")):
    d = json.load(open(f)); hdr = [h["value"] for h in d["header"]]; ie = hdr.index("EM")
    for r in d["rows"]:
        names.add(r[0]["value"])
        if r[ie].get("value") is None: full.add(r[0]["value"])
H = load_helm(); N = pd.read_csv(f"{P}/helm_mmlu_neval.csv", index_col=0)
o = pd.read_csv(f"{P}/olb_contents.csv"); sub = pd.read_csv(f"{P}/olb_subtask.csv", index_col=0)
fl = o["Flagged"].astype(bool); main = load_olb("main")[0]
out = {
 "retrieved_on": "2026-11-02",
 "licence_note": "licences of the HELM and Open LLM Leaderboard data are not declared in the supplied material; the repository ships fetch scripts and SHA-256 checksums, not copies of the data",
 "sources": {
  "helm_mmlu": {"url": "https://storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/", "snapshot": "HELM MMLU release v1.13.0",
                "files_list": "data/helm_v1.13.0_filelist.txt", "fetch_script": "fetch_helm.sh", "n_files_used": len(helm_files),
                "sha256_of_files": helm_files, "tasks": int(H.shape[1]), "models_after_exclusions": int(H.shape[0]),
                "models_before_exclusions": len(names), "exclusions": {"models_with_missing_subject_cells": len(full)},
                "score": "exact match (EM) in points, per subject; # eval per subject 100-1534 (min %d, max %d)" % (N.values.min(), N.values.max())},
  "open_llm_leaderboard_v2_headline": {"url": "https://huggingface.co/datasets/open-llm-leaderboard/contents", "snapshot_sha": "9c09a7cae43334062a82cb164f2ef255013dafa2",
                "file": "train-00000-of-00001.parquet", "sha256": man.get("data/raw/olb_contents/train-00000-of-00001.parquet"), "tasks": 6,
                "task_names": OLB_TASKS, "rows_total": int(len(o)), "models_main_population": int(len(main)),
                "exclusions": {"flagged": int(fl.sum()), "duplicate_fullname_after_flag_removal": int((~fl).sum() - o[~fl].fullname.nunique()),
                               "merged_flag_rows": int(o["Merged"].astype(bool).sum()), "official_providers_rows": int(o["Official Providers"].astype(bool).sum())},
                "populations": {v: int(len(load_olb(v)[0])) for v in ["all", "main", "nomerge", "official", "small", "chat", "pretrained"]},
                "normalisation": "the leaderboard's own normalised columns (main); raw accuracy columns as sensitivity"},
  "open_llm_leaderboard_v2_subtask": {"url": "https://huggingface.co/datasets/open-llm-leaderboard/results", "snapshot_sha": om["dataset_sha"], "n_result_files": len(om["files"]),
                "sha256_of_files": {k: v["sha256"] for k, v in om["files"].items()}, "tasks": int(sub.shape[1]), "models_used": int(sub.shape[0]),
                "selection_rule": "fixed before looking at the data: models of the main population that have a results directory; top 300 by Average plus 400 random from the rest (numpy seed 20261102); latest results_*.json per model; models lacking any of the 39 sub-tasks dropped",
                "note": "the dataset is about 1.2 GB in total (the supplied data description says 13.6 MB); only the selected files are fetched"}}}
for dst in ("results/data_manifest.json", "data/manifest.json"):   # data/manifest.json is the venue-required path
    json.dump(out, open(f"{ROOT}/{dst}", "w"), indent=1)
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "sha256_of_files"} for k, v in out["sources"].items()}, indent=1, default=str)[:3000])
