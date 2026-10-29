"""Main experiment: for every leaderboard (Arena, MT-Bench x3, NBA seasons) and every rank claim
('model at rank r scores above model at rank r+1', plus 'rank 1 above rank k', k=3..5), compute
  * the full-data BT gap, Fisher z, bootstrap z and bootstrap reversal probability,
  * the minimal number of modified votes that reverses the claim: flips, removals, insertions (exact refit),
  * first-order (influence-function) estimates and a naive direct-vote-only flip baseline.
Output: results/claims.csv      (run: python run_claims.py ; ~ few minutes on 40 cores)
"""
import os, sys, time
os.environ.setdefault('OMP_NUM_THREADS', '1')
import numpy as np
import pandas as pd
from multiprocessing import Pool
from bt import *
from data_loaders import load_arena, load_arena140k, load_mtbench, load_nba

SEED = 20261028
B_BOOT = 500
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
os.makedirs(OUT, exist_ok=True)

BOARDS = [load_arena(), load_arena140k()] + load_mtbench() + load_nba()


def bootstrap_thetas(b, th0, B, rng, cluster=False):
    out = np.empty((B, b.P))
    probs = (b.W / b.W.sum()).ravel()
    for k in range(B):
        if cluster and b.clusters is not None:
            Wb = b.cluster_resample(rng)
        else:
            Wb = rng.multinomial(b.N, probs).reshape(b.C, 3).astype(float)
        out[k] = fit(b.X, Wb, th0)
    return out


def claims_for(b, th):
    nr = b.n_ent
    order = np.argsort(-th[:nr])
    cl = [(r, r + 1, 'adj') for r in range(nr - 1)]
    cl += [(0, k, 'top1') for k in (2, 3, 4) if k < nr]
    return order, cl


def run_board(args):
    bi, only = args  # only: None => all claims, else list of claim indices
    b = BOARDS[bi]
    th = fit(b.X, b.W)
    order, cl = claims_for(b, th)
    rng = np.random.default_rng([SEED, bi])
    Tb = bootstrap_thetas(b, th, B_BOOT, rng)
    Tc = bootstrap_thetas(b, th, B_BOOT, rng, cluster=True) if b.clusters is not None else None
    rows = []
    idxs = range(len(cl)) if only is None else only
    for ci in idxs:
        r1, r2, typ = cl[ci]
        i, j = order[r1], order[r2]
        q = contrast(b.P, i, j)
        d = float(q @ th)
        db = Tb @ q
        row = dict(board=b.name, dataset=b.dataset, design=b.design, year=b.meta.get('year', np.nan),
                   n_ent=b.n_ent, N=b.N, claim_type=typ, rank_hi=r1 + 1, rank_lo=r2 + 1,
                   ent_hi=b.ents[i], ent_lo=b.ents[j], gap=d,
                   n_loc=float(b.W[(np.abs(b.X[:, i]) > 0) | (np.abs(b.X[:, j]) > 0)].sum()),
                   n_direct=float(b.W[(np.abs(b.X[:, i]) > 0) & (np.abs(b.X[:, j]) > 0)].sum()),
                   se_fisher=fisher_se(b, th, q), se_boot=float(db.std(ddof=1)),
                   p_rev_boot=float(np.mean(db < 0) + 0.5 * np.mean(db == 0)))
        if Tc is not None:
            dc = Tc @ q
            row['se_boot_cluster'] = float(dc.std(ddof=1))
            row['p_rev_boot_cluster'] = float(np.mean(dc < 0))
        for mode in ('flip', 'remove', 'insert'):
            K, cens = min_budget(b, mode, q, th)
            row[f'K_{mode}'] = K
            row[f'cens_{mode}'] = cens
        row['K_lin_flip'] = linear_budget(b, 'flip', q, th)
        row['K_lin_remove'] = linear_budget(b, 'remove', q, th)
        row['K_direct_flip'] = direct_flip_budget(b, i, j, q, th)
        rows.append(row)
    return rows


if __name__ == '__main__':
    t0 = time.time()
    tasks = []
    for bi, b in enumerate(BOARDS):
        if b.name.startswith('arena'):  # split the claims over workers; bootstrap is repeated per worker (cheap, same seed)
            nr = b.n_ent
            ncl = (nr - 1) + 3
            tasks += [(bi, [c]) for c in range(ncl)]
        else:
            tasks.append((bi, None))
    with Pool(38) as pool:
        res = pool.map(run_board, tasks, chunksize=1)
    df = pd.DataFrame([r for rs in res for r in rs])
    df.to_csv(os.path.join(OUT, 'claims.csv'), index=False)
    print(df.groupby('board').size().head(), len(df), 'rows', round(time.time() - t0), 's')
