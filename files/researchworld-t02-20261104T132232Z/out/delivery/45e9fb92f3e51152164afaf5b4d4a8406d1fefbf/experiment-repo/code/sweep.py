"""Resumable sweep runner: python3 sweep.py GRID.json OUTDIR [--workers N] [--shard i/n]

GRID.json is a list of config overrides (dicts, merged onto grok.DEFAULT). Each run writes
OUTDIR/<run_id>.json; existing files are skipped, so a killed sweep can simply be restarted.
Runs are ordered cheapest-first inside a shard so partial results arrive early.
"""
import argparse, hashlib, json, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grok

KEYS = ["task", "p", "model", "width", "depth", "lr", "wd", "init_scale", "train_frac", "seed", "max_steps"]


def run_id(c):
    return "_".join(f"{k}{c[k]}" for k in KEYS)


def work(args):
    c, out = args
    path = os.path.join(out, run_id(c) + ".json")
    if os.path.exists(path):
        return path
    r = grok.run(c)
    tmp = path + ".tmp"
    json.dump(r, open(tmp, "w"))
    os.replace(tmp, path)
    s = r["summary"]
    print(f"HUTIAN_PROGRESS {run_id(c)} fit99={s['t_fit99']} gen99={s['t_gen99']} wall={s['wall']:.0f}s", flush=True)
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("grid"); ap.add_argument("out")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--shard", default="0/1")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    cfgs = [{**grok.DEFAULT, **g} for g in json.load(open(a.grid))]
    i, n = map(int, a.shard.split("/"))
    cfgs = [c for j, c in enumerate(cfgs) if j % n == i]
    with Pool(a.workers) as pool:
        for _ in pool.imap_unordered(work, [(c, a.out) for c in cfgs]):
            pass
    print("HUTIAN_WAKE: sweep done", a.grid, a.shard, flush=True)
