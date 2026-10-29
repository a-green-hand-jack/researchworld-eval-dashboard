"""Rigging-style attack: only votes involving the challenger model can be inserted ('insert_target').
Compares with unrestricted insertion for the adjacent claims of the top-10 ranks of each non-NBA board and
the rank-1 claim of each NBA season.  Output: results/claims_target.csv"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
import numpy as np, pandas as pd
from multiprocessing import Pool
from bt import *
from run_claims import BOARDS, OUT


def task(bi):
    b = BOARDS[bi]
    th = fit(b.X, b.W)
    order = np.argsort(-th[:b.n_ent])
    nclaims = 1 if b.name.startswith('nba') else 10
    rows = []
    for r in range(min(nclaims, b.n_ent - 1)):
        i, j = order[r], order[r + 1]
        q = contrast(b.P, i, j)
        row = dict(board=b.name, design=b.design, N=b.N, rank_hi=r + 1, gap=float(q @ th), se_fisher=fisher_se(b, th, q))
        for m in ('flip', 'insert', 'insert_target'):
            row['K_' + m], row['cens_' + m] = min_budget(b, m, q, th)
        rows.append(row)
    return rows

if __name__ == '__main__':
    with Pool(38) as p:
        res = p.map(task, range(len(BOARDS)), chunksize=1)
    pd.DataFrame([r for rs in res for r in rs]).to_csv(os.path.join(OUT, 'claims_target.csv'), index=False)
