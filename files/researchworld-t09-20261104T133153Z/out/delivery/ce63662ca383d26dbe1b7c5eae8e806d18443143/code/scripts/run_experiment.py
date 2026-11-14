#!/usr/bin/env python3
"""Run one experiment grid: python scripts/run_experiment.py e1 [--procs 2] [--shard i/k].
Writes results/raw/<exp>/<cell-index>.csv.gz (one per cell; existing cells are skipped => resumable)."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import argparse, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from multiprocessing import Pool
from netgate.experiments import EXPERIMENTS
from netgate.runner import run_cell

ROOT = os.path.join(results_dir(), "raw")


def work(a):
    exp, i, cfg = a
    path = os.path.join(ROOT, exp, f"{i:04d}.csv.gz")
    if os.path.exists(path):
        return i, 0.0
    df = run_cell(cfg)
    df["exp"] = exp; df["cell"] = i
    df.to_csv(path + ".tmp", index=False, compression="gzip"); os.replace(path + ".tmp", path)
    return i, df.secs.iloc[0]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("exp"); ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--shard", default="0/1"); ap.add_argument("--reverse", action="store_true", help="process cells last-to-first (to meet a forward run in the middle)"); a = ap.parse_args()
    cells = EXPERIMENTS[a.exp]()
    sh, k = map(int, a.shard.split("/"))
    jobs = [(a.exp, i, c) for i, c in enumerate(cells) if i % k == sh]
    if a.reverse:
        jobs = jobs[::-1]
    os.makedirs(os.path.join(ROOT, a.exp), exist_ok=True)
    t0 = time.time(); done = 0
    with Pool(a.procs) as pool:
        for i, secs in pool.imap(work, jobs, chunksize=1):
            done += 1
            print(f"{a.exp} cell {i} done ({done}/{len(jobs)}) cell_secs={secs:.1f} elapsed={time.time()-t0:.0f}", flush=True)
    print(f"HUTIAN_WAKE: {a.exp} shard {a.shard} finished in {time.time()-t0:.0f}s", flush=True)
