"""Extract MTEB results (pinned checkout) into one tidy table.

usage: python src/data_mteb.py <results_dir> <out_dir>

One row per (model dir, revision dir, task file): main_score aggregated over the
chosen split (rule below), evaluation_time, n_subsets. Model metadata (release_date,
n_parameters) is read from model_meta.json of each revision directory.
Split rule (primary): 'test' if present, else 'validation', else 'dev', else the
only/first split. Within a split main_score is the unweighted mean over hf_subsets
(ablation columns: main_score_eng = mean over subsets whose languages are all eng-*;
main_score_first = first subset entry).
"""
import json, os, sys, glob
import pandas as pd

SPLIT_PREF = ["test", "validation", "dev"]

def pick_split(scores):
    for s in SPLIT_PREF:
        if s in scores:
            return s
    return sorted(scores)[0]

def main(res, out):
    rows, metas = [], []
    for mdir in sorted(os.listdir(res)):
        if not os.path.isdir(f"{res}/{mdir}"):
            continue
        for rev in sorted(os.listdir(f"{res}/{mdir}")):
            d = f"{res}/{mdir}/{rev}"
            if not os.path.isdir(d):
                continue
            meta = {}
            if os.path.exists(f"{d}/model_meta.json"):
                try:
                    meta = json.load(open(f"{d}/model_meta.json"))
                except Exception:
                    meta = {}
            metas.append(dict(model=mdir, revision=rev, name=meta.get("name"),
                              release_date=meta.get("release_date"),
                              n_parameters=meta.get("n_parameters"),
                              embed_dim=meta.get("embed_dim"),
                              adapted_from=meta.get("adapted_from")))
            for f in os.listdir(d):
                if not f.endswith(".json") or f == "model_meta.json":
                    continue
                try:
                    j = json.load(open(f"{d}/{f}"))
                except Exception:
                    continue
                sc = j.get("scores")
                if not isinstance(sc, dict) or not sc:
                    continue
                sp = pick_split(sc)
                ent = [e for e in sc[sp] if isinstance(e, dict) and isinstance(e.get("main_score"), (int, float))]
                if not ent:
                    continue
                ms = [e["main_score"] for e in ent]
                eng = [e["main_score"] for e in ent if e.get("languages") and all(l.startswith("eng") for l in e["languages"])]
                rows.append(dict(model=mdir, revision=rev, task=j.get("task_name", f[:-5]), split=sp,
                                 n_subsets=len(ms), main_score=sum(ms) / len(ms),
                                 main_score_eng=(sum(eng) / len(eng)) if eng else float("nan"),
                                 main_score_first=ms[0],
                                 evaluation_time=j.get("evaluation_time"),
                                 mteb_version=j.get("mteb_version")))
    os.makedirs(out, exist_ok=True)
    pd.DataFrame(rows).to_parquet(f"{out}/mteb_long.parquet")
    pd.DataFrame(metas).to_parquet(f"{out}/mteb_models.parquet")
    print(len(rows), "rows;", len(metas), "model-revisions")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
