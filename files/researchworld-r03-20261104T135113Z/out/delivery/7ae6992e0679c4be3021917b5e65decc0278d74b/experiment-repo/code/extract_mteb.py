"""Extract a long table (model, revision, task, split, score) from the pinned MTEB results checkout.

usage: python extract_mteb.py <results_dir> <out_dir>
Score = `main_score` of the task, averaged over hf_subsets within one split.
Split preference: test > validation > dev > train > first available (recorded in the table).
Files named '* copy.json' (stray duplicates in the repo) are skipped.
"""
import json, os, sys, glob
import pandas as pd

SPLIT_PREF = ["test", "validation", "dev", "train"]

def read_task(f):
    try:
        d = json.load(open(f))
    except Exception:
        return None
    if "scores" not in d or "task_name" not in d:
        return None
    sc = d["scores"]
    split = next((s for s in SPLIT_PREF if s in sc), next(iter(sc), None))
    if split is None or not sc[split]:
        return None
    vals = [e["main_score"] for e in sc[split] if isinstance(e.get("main_score"), (int, float))]
    if not vals:
        return None
    return d["task_name"], split, sum(vals) / len(vals), len(vals), d.get("evaluation_time")

def main(res, out):
    rows, meta = [], []
    for mdir in sorted(os.listdir(res)):
        if not os.path.isdir(os.path.join(res, mdir)):
            continue
        for rev in sorted(os.listdir(os.path.join(res, mdir))):
            p = os.path.join(res, mdir, rev)
            if not os.path.isdir(p):
                continue
            mm = os.path.join(p, "model_meta.json")
            m = {}
            if os.path.exists(mm):
                m = json.load(open(mm))
            meta.append(dict(model_dir=mdir, revision=rev, **{k: m.get(k) for k in
                ["name", "release_date", "n_parameters", "embed_dim", "max_tokens", "license", "open_weights", "adapted_from", "framework"]}))
            for f in glob.glob(os.path.join(p, "*.json")):
                b = os.path.basename(f)
                if b == "model_meta.json" or b.endswith(" copy.json"):
                    continue
                r = read_task(f)
                if r:
                    rows.append((mdir, rev, *r))
    df = pd.DataFrame(rows, columns=["model_dir", "revision", "task", "split", "score", "n_subsets", "eval_time"])
    os.makedirs(out, exist_ok=True)
    df.to_parquet(os.path.join(out, "mteb_long.parquet"))
    pd.DataFrame(meta).astype({"framework": str}).to_parquet(os.path.join(out, "mteb_meta.parquet"))
    print(len(df), df.model_dir.nunique(), df.task.nunique(), flush=True)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
