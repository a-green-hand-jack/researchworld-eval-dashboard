"""How the worst-case perturbation size scales with the amount of data.

Random subsamples (without replacement) of each board at several fractions; for each we record the
worst-case drop count for (a) the top-1 identity of the subsample and (b) fixed reference pairs of
the full-data ranking (ranks 1v2, 1v3, 2v3, 1v5; only when the subsample preserves the pair's order).
Output: results/subsample.parquet.   Usage: python code/subsample.py [reps]
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

from common import RES, best_k, load_board, top1_k, with_weights

BOARDS = ["arena55k", "arena140k", "webdev", "mtbench_human", "mtbench_gpt4"]
FRACS = [0.05, 0.1, 0.2, 0.4, 0.7, 1.0]
REF = [(1, 2), (1, 3), (2, 3), (1, 5)]
_C = {}


def task(args):
    name, frac, rep = args
    if name not in _C:
        B = load_board(name)
        th = B.fit()[0]
        _C[name] = (B, B.ranking(th))
    B, r0 = _C[name]
    rng = np.random.default_rng([zlib.crc32(name.encode()), int(frac * 1000), rep])
    flat = np.repeat(np.arange(B.W0.size), B.W0.ravel().astype(int))
    keep = rng.choice(flat, size=int(round(frac * B.N)), replace=False)
    W = np.bincount(keep, minlength=B.W0.size).reshape(B.W0.shape).astype(float)
    Bs = with_weights(B, W)
    th, H, _ = Bs.fit()
    row = dict(board=name, frac=frac, rep=rep, n=Bs.N, k_top1=top1_k(Bs, "drop", th))
    for a, b in REF:
        i, j = r0[a - 1], r0[b - 1]
        v = Bs.contrast(i, j)
        gap = float(v @ th)
        row[f"z_{a}{b}"] = gap / float(np.sqrt(v @ np.linalg.solve(H, v)))
        row[f"k_{a}{b}"] = best_k(Bs, i, j, "drop") if gap > 0 else 0
    return row


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    tasks = [(b, f, r) for b in BOARDS for f in FRACS for r in range(reps if f < 1 else 1)]
    t0 = time.time()
    with Pool(int(os.environ.get("NPROC", 4))) as pool:
        rows = pool.map(task, tasks, chunksize=1)
    pd.DataFrame(rows).to_parquet(os.path.join(RES, "subsample.parquet"), index=False)
    print("done %.0fs" % (time.time() - t0))
