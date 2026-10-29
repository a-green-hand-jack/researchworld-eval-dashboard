"""Sampling uncertainty of the fragility metric itself.

For each leaderboard we draw B nonparametric bootstrap resamples of the comparisons, refit BT,
and recompute the worst-case top-1 perturbation size (drop / flip / add) of the resampled board.
Also records whether the resampled leader equals the original leader.
Output: results/bootstrap_k.parquet.  Usage: python code/bootstrap_k.py [B]
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import sys
import time
import zlib
from multiprocessing import Pool

import numpy as np
import pandas as pd

from common import MAIN_BOARDS, NBA_RECENT, RES, load_board, resample_weights, top1_k, with_weights

_C = {}


def task(args):
    name, rep = args
    if name not in _C:
        B = load_board(name)
        th = B.fit()[0]
        _C[name] = (B, B.ranking(th)[0])
    B, leader = _C[name]
    rng = np.random.default_rng(zlib.crc32(name.encode()) * 1000 + rep)
    Bb = with_weights(B, resample_weights(B, rng))
    th, H, _ = Bb.fit()
    r = Bb.ranking(th)
    v = Bb.contrast(r[0], r[1])
    z = float(v @ th / np.sqrt(v @ np.linalg.solve(H, v)))
    row = dict(board=name, rep=rep, N=B.N, same_leader=bool(r[0] == leader), z_top=z)
    for mode in ("drop", "flip", "add"):
        row["k_" + mode] = top1_k(Bb, mode, th)
    return row


if __name__ == "__main__":
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    tasks = [(b, r) for b in MAIN_BOARDS + NBA_RECENT for r in range(nb)]
    t0 = time.time()
    with Pool(int(os.environ.get("NPROC", 4))) as pool:
        rows = pool.map(task, tasks, chunksize=4)
    pd.DataFrame(rows).to_parquet(os.path.join(RES, "bootstrap_k.parquet"), index=False)
    print("done %.0fs" % (time.time() - t0))
