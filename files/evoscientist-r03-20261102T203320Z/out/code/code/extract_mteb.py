"""Extract the model x task score matrix from the pinned MTEB results checkout.

Usage: python code/extract_mteb.py
Input : data/results/results/<model>/<revision>/<Task>.json   (commit 6dabbcc6...)
Output: data/mteb_long.parquet-like CSV (data/mteb_long.csv.gz): model, revision, task, split, score, n_subsets
        data/mteb_dirs.csv: per (model, revision-dir) file counts
Rules : per task file, eval split = 'test' if present, else 'validation', else 'dev', else first split.
        score = mean over hf_subsets of main_score (x100). Files without main_score are skipped.
"""
import json, os, sys, gzip
import pandas as pd
from concurrent.futures import ProcessPoolExecutor

ROOT = "data/results/results"
PREF = ["test", "validation", "dev"]


def read_task(path):
    try:
        d = json.load(open(path))
    except Exception:
        return None
    sc = d.get("scores")
    if not isinstance(sc, dict) or not sc:
        return None
    split = next((s for s in PREF if s in sc), None)
    if split is None:
        split = next(iter(sc))
    ent = sc[split]
    vals = [e["main_score"] for e in ent if isinstance(e, dict) and isinstance(e.get("main_score"), (int, float))]
    if not vals:
        return None
    return d.get("task_name") or os.path.basename(path)[:-5], split, 100.0 * sum(vals) / len(vals), len(vals)


def do_model(m):
    rows = []
    for rev in sorted(os.listdir(f"{ROOT}/{m}")):
        p = f"{ROOT}/{m}/{rev}"
        if not os.path.isdir(p):
            continue
        for fn in os.listdir(p):
            if not fn.endswith(".json") or fn == "model_meta.json":
                continue
            r = read_task(f"{p}/{fn}")
            if r:
                rows.append((m, rev, r[0], r[1], r[2], r[3]))
    return rows


if __name__ == "__main__":
    models = sorted(m for m in os.listdir(ROOT) if os.path.isdir(f"{ROOT}/{m}"))
    with ProcessPoolExecutor(16) as ex:
        res = list(ex.map(do_model, models, chunksize=4))
    rows = [r for rr in res for r in rr]
    df = pd.DataFrame(rows, columns=["model", "revision", "task", "split", "score", "n_subsets"])
    df.to_csv("data/mteb_long.csv.gz", index=False)
    print(df.shape, df.model.nunique(), df.task.nunique())
    print(df.groupby(["model", "revision"]).size().describe())
