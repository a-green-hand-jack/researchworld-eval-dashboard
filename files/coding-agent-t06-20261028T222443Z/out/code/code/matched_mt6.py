"""Equal-size comparison of the same six models under three labelers.

arena55k_mt6 (crowd votes on Chatbot Arena, 1,367 comparisons), mtbench_human (expert votes on MT-Bench
questions) and mtbench_gpt4 (GPT-4 judge on MT-Bench questions) all rank the same six models.  We
subsample every board to the same number of comparisons (that of the smallest board) and recompute
worst-case drop/flip counts for the top-1 identity and every adjacent pair of the subsample's ranking,
plus the pair statistics z and R.
Output: results/matched_mt6.parquet.   Usage: python code/matched_mt6.py [reps]
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import sys
import zlib
from multiprocessing import Pool

import numpy as np
import pandas as pd

from bt import OUT
from common import RES, best_k, load_board, top1_k, with_weights

BOARDS = ["arena55k_mt6", "mtbench_human", "mtbench_gpt4"]
_C = {}


def task(args):
    name, n, rep = args
    if name not in _C:
        _C[name] = load_board(name)
    B = _C[name]
    rng = np.random.default_rng([zlib.crc32(name.encode()), rep + 1])
    flat = np.repeat(np.arange(B.W0.size), B.W0.ravel().astype(int))
    keep = rng.choice(flat, size=n, replace=False) if n < B.N else flat
    W = np.bincount(keep, minlength=B.W0.size).reshape(B.W0.shape).astype(float)
    Bs = with_weights(B, W)
    th, H, p = Bs.fit()
    r = Bs.ranking(th)
    rows = []
    for a in range(B.K - 1):
        i, j = r[a], r[a + 1]
        v = Bs.contrast(i, j)
        u = np.linalg.solve(H, v)
        psi = (Bs.X @ u)[:, None] * (p[:, None] - OUT[None, :])
        se = float(np.sqrt((W * psi ** 2).sum()))
        R = se / float((-psi[W > 0]).max())
        rows.append(dict(board=name, rep=rep, n=int(W.sum()), r=a + 1, pair=f"{B.names[i]}>{B.names[j]}",
                         gap=float(v @ th), z=float(v @ th) / se, R=R,
                         k_drop=best_k(Bs, i, j, "drop"), k_flip=best_k(Bs, i, j, "flip")))
    top = dict(board=name, rep=rep, n=int(W.sum()), r=0, pair="top1",
               k_drop=top1_k(Bs, "drop", th), k_flip=top1_k(Bs, "flip", th),
               order=">".join(B.names[r]))
    return rows + [top]


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    n = min(load_board(b).N for b in BOARDS)
    tasks = [(b, n, r) for b in BOARDS for r in range(reps)] + [(b, 10**9, -1) for b in BOARDS]
    with Pool(int(os.environ.get("NPROC", 4))) as pool:
        out = sum(pool.map(task, tasks, chunksize=2), [])
    pd.DataFrame(out).to_parquet(os.path.join(RES, "matched_mt6.parquet"), index=False)
    print("done, n =", n)
