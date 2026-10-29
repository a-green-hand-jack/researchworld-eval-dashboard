"""Influence summaries for every pair in results/pairs.parquet.

For a pair (i above j) with contrast f = theta_i - theta_j and per-comparison first-order drop
effects psi_c (change in f when comparison c is removed):
  se_ij   = sqrt(sum_c psi_c^2)              infinitesimal-jackknife (sandwich) standard error
  z_ij    = f / se_ij
  psimax  = max_c (-psi_c)                   largest single-comparison reduction of f
  R       = se_ij / psimax                   "evidence spread"; first-order drop count k >= z_ij * R
  R_flip, R_add analogously with per-unit relabel / injection effects.
Output: results/pair_influence.parquet.   Usage: python code/pair_influence.py
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
from multiprocessing import Pool

import numpy as np
import pandas as pd

from bt import OUT
from common import RES, load_board

_C = {}


def task(args):
    name, pairs = args
    B = load_board(name)
    th, H, p = B.fit()
    r = B.ranking(th)
    rows = []
    for ri, rj in pairs:
        i, j = r[ri - 1], r[rj - 1]
        v = B.contrast(i, j)
        f = float(v @ th)
        u = np.linalg.solve(H, v)
        ux = B.X @ u
        psi = ux[:, None] * (p[:, None] - OUT[None, :])
        W = B.W0
        se = float(np.sqrt((W * psi ** 2).sum()))
        has = W > 0
        psimax = float((-psi[has]).max())
        flip = np.minimum(ux[:, None] * (0 - OUT[None, :]), ux[:, None] * (1 - OUT[None, :]))
        fmax = float((-flip[has]).max())
        obs = W.sum(1) > 0
        add = np.minimum(ux * (0 - p), ux * (1 - p))[obs]
        amax = float((-add).max())
        se_model = float(np.sqrt(v @ u))
        rows.append(dict(board=name, ri=ri, rj=rj, gap=f, se_ij=se, se_model=se_model, z_ij=f / se,
                         psimax=psimax, R=se / psimax, R_flip=se / fmax, R_add=se / amax,
                         n_eff_ij=float((W * np.abs(psi)).sum() ** 2 / (W * psi ** 2).sum())))
    return rows


if __name__ == "__main__":
    P = pd.read_parquet(os.path.join(RES, "pairs.parquet"))
    pr = P[["board", "ri", "rj"]].drop_duplicates()
    tasks = [(b, list(zip(g.ri, g.rj))) for b, g in pr.groupby("board")]
    with Pool(4) as pool:
        out = sum(pool.map(task, tasks, chunksize=1), [])
    pd.DataFrame(out).to_parquet(os.path.join(RES, "pair_influence.parquet"), index=False)
    print(len(out), "pairs")
