"""All pairwise order claims among the top-10 ranked entities of every board (45 claims per board).
Computes minimal flip budget (exact refit), Fisher SE, bootstrap (iid and, where available, cluster) reversal prob.
Output: results/pairs_top10.csv"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
import numpy as np, pandas as pd
from multiprocessing import Pool
from bt import *
from run_claims import BOARDS, OUT, SEED, bootstrap_thetas

TOPK = 10
B = 300


def task(bi):
    b = BOARDS[bi]
    th = fit(b.X, b.W)
    order = np.argsort(-th[:b.n_ent])
    rng = np.random.default_rng([SEED, 7, bi])
    Tb = bootstrap_thetas(b, th, B, rng)
    Tc = bootstrap_thetas(b, th, B, rng, cluster=True) if b.clusters is not None else None
    k = min(TOPK, b.n_ent)
    rows = []
    for r1 in range(k):
        for r2 in range(r1 + 1, k):
            i, j = order[r1], order[r2]
            q = contrast(b.P, i, j)
            d = float(q @ th)
            K, c = min_budget(b, 'flip', q, th)
            row = dict(board=b.name, design=b.design, N=b.N, rank_hi=r1 + 1, rank_lo=r2 + 1, gap=d,
                       se_fisher=fisher_se(b, th, q), se_boot=float((Tb @ q).std(ddof=1)),
                       p_rev_boot=float(np.mean(Tb @ q < 0)),
                       n_loc=float(b.W[(np.abs(b.X[:, i]) > 0) | (np.abs(b.X[:, j]) > 0)].sum()),
                       K_flip=K, cens_flip=c)
            if Tc is not None:
                row['se_boot_cluster'] = float((Tc @ q).std(ddof=1))
                row['p_rev_boot_cluster'] = float(np.mean(Tc @ q < 0))
            rows.append(row)
    return rows


if __name__ == '__main__':
    with Pool(38) as p:
        res = p.map(task, range(len(BOARDS)), chunksize=1)
    pd.DataFrame([r for rs in res for r in rs]).to_csv(os.path.join(OUT, 'pairs_top10.csv'), index=False)
