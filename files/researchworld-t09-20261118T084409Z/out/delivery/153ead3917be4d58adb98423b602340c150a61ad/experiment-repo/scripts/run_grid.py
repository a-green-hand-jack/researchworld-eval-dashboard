"""Run an experiment grid: python scripts/run_grid.py <grid> [--workers 2] [--seed 0] [--R N] [--out results/raw]
Cells are cached under $NETGATE_WORK/<grid>/ so an interrupted run resumes."""
import argparse
import hashlib
import json
import os
import pickle
import sys
import time
from multiprocessing import Pool

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from netgate.grids import GRIDS  # noqa: E402
from netgate.runner import run_cell  # noqa: E402

WORK = os.environ.get("NETGATE_WORK", "work")


def key(cfg):
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:16]


def flat(prefix, d, out):
    for k, v in d.items():
        if isinstance(v, dict):
            flat(prefix + k + ".", v, out)
        elif not isinstance(v, (list, tuple)):
            out[prefix + k] = v


def work(args):
    cfg, seed, wd = args
    f = os.path.join(wd, key(cfg) + ".pkl")
    if os.path.exists(f):
        return f
    rows = run_cell(cfg, seed)
    meta = {}
    flat("", {k: cfg[k] for k in ("graph", "out", "design", "stag", "obs") if k in cfg}, meta)
    meta["tag"] = cfg.get("tag", "")
    meta["n_rep_cfg"] = cfg["n_rep"]
    for r in rows:
        r.update(meta)
    with open(f + ".tmp", "wb") as fh:
        pickle.dump(rows, fh)
    os.replace(f + ".tmp", f)
    return f


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("grid"); ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--R", type=int, default=None)
    ap.add_argument("--out", default="results/raw"); ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--reverse", action="store_true", help="process the cells from the end (a second runner sharing the cache of a running one); implies no final table")
    a = ap.parse_args()
    cells = GRIDS[a.grid](**({"R": a.R} if a.R else {}))
    if a.limit:
        cells = cells[:a.limit]
    wd = os.path.join(WORK, a.grid + (f"_R{a.R}" if a.R else "")); os.makedirs(wd, exist_ok=True)
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time(); files = []
    with Pool(a.workers) as pool:
        todo = cells[::-1] if a.reverse else cells
        for i, f in enumerate(pool.imap_unordered(work, [(c, a.seed, wd) for c in todo])):
            files.append(f)
            if i % 10 == 0:
                print(f"[{a.grid}] {i + 1}/{len(cells)} cells, {time.time() - t0:.0f}s", flush=True)
    if a.reverse:
        print(f"[{a.grid}] reverse runner done, {time.time() - t0:.0f}s", flush=True)
        sys.exit(0)
    rows = []
    for c in cells:
        rows += pickle.load(open(os.path.join(wd, key(c) + ".pkl"), "rb"))
    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(a.out, a.grid + ".parquet"), index=False)
    print((os.environ.get("NETGATE_WAKE_PREFIX", "")) + f"grid {a.grid} done: {len(df)} rows, {time.time() - t0:.0f}s", flush=True)
