"""Non-adversarial perturbations: random deletion and random win/loss label flips.

For each leaderboard and rate x, R replicates: each comparison is deleted (or, if decisive,
has its winner flipped) independently with probability x; BT is refit and we record whether
the top-1 identity, the top-3 set, or the order of the top-10 changed.
Output: results/random_noise.parquet.  Usage: python code/random_noise.py [R]
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

from common import MAIN_BOARDS, NBA_RECENT, RES, load_board

RATES = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3]
_C = {}


def outcomes(B, W, r0, th0):
    th = B.fit(W, th0)[0]
    r = B.ranking(th)
    t = min(10, B.K)
    return dict(top1=bool(r[0] != r0[0]), top3=bool(set(r[:3]) != set(r0[:3])),
                top10order=bool((r[:t] != r0[:t]).any()))


def task(args):
    name, kind, x, rep = args
    if name not in _C:
        B = load_board(name)
        th = B.fit()[0]
        _C[name] = (B, th, B.ranking(th))
    B, th0, r0 = _C[name]
    rng = np.random.default_rng([zlib.crc32(f"{name}|{kind}|{x}".encode()), rep])
    W0 = B.W0
    if kind == "drop":
        W = rng.binomial(W0.astype(int), 1 - x).astype(float)
    else:  # flip decisive outcomes
        f0 = rng.binomial(W0[:, 0].astype(int), x)
        f2 = rng.binomial(W0[:, 2].astype(int), x)
        W = W0.copy()
        W[:, 0] += f2 - f0
        W[:, 2] += f0 - f2
    return dict(board=name, kind=kind, rate=x, rep=rep, **outcomes(B, W, r0, th0))


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    tasks = [(b, k, x, r) for b in MAIN_BOARDS + NBA_RECENT for k in ("drop", "flip") for x in RATES
             for r in range(R)]
    t0 = time.time()
    with Pool(int(os.environ.get("NPROC", 4))) as pool:
        rows = pool.map(task, tasks, chunksize=20)
    pd.DataFrame(rows).to_parquet(os.path.join(RES, "random_noise.parquet"), index=False)
    print("done %.0fs" % (time.time() - t0))
