"""Scaling experiment: subsample the Arena human-vote data to N votes (without replacement) and
recompute the adjacent-pair minimal drop/flip budgets.   Usage: python code/exp_scaling.py [nproc]
Output: results/scaling_pairs.csv"""
import os, sys, time
os.environ["OMP_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bt
from bt import Data
from common import load, ROOT

SIZES = [2000, 5000, 10000, 20000, 40000]
DRAWS = 3
_full = None
_cache = {}


def sub(n, draw):
    key = (n, draw)
    if key not in _cache:
        global _full
        if _full is None:
            _full = load("arena55k_human")
        rng = np.random.default_rng(1000 * draw + n)
        idx = np.sort(rng.choice(_full.N, n, replace=False))
        D = _full.subset(idx)
        th = bt.fit_data(D)
        _cache.clear()
        _cache[key] = (D, th)
    return _cache[key]


def task(args):
    n, draw, r = args
    D, th = sub(n, draw)
    rank = np.argsort(-th[:D.M])
    i, j = rank[r], rank[r + 1]
    rec = dict(N=n, draw=draw, rank_i=r, gap=th[i] - th[j], se=bt.se_gap_sandwich(D, th, i, j))
    cnt = np.bincount(np.concatenate([D.a, D.b]), minlength=D.M)
    nij = int(((D.a == i) & (D.b == j)).sum() + ((D.a == j) & (D.b == i)).sum())
    rec["n_inv"] = int(cnt[i] + cnt[j] - nij)
    for mode in ("drop", "flip"):
        res = dict(k=0.0, k_lin=0.0) if th[i] - th[j] < 1e-6 else bt.min_perturbation(D, th, i, j, mode)
        rec["k_" + mode] = res["k"]
        rec["klin_" + mode] = res["k_lin"]
    return rec


if __name__ == "__main__":
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    t0 = time.time()
    tasks = [(n, d, r) for n in SIZES for d in range(DRAWS) for r in range(63)]
    with Pool(nproc) as p:
        recs = p.map(task, tasks, chunksize=4)
    df = pd.DataFrame(recs)
    df["z"] = df.gap / df.se
    df.to_csv(os.path.join(ROOT, "results", "scaling_pairs.csv"), index=False)
    print("done", len(df), round(time.time() - t0), "s")
