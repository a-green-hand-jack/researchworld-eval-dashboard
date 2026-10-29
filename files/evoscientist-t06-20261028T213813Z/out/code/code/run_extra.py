"""Secondary experiments (python run_extra.py <part>), parts: size | bootK | noise | ties
  size  : Arena vote-subsampling -> how minimal flip budget scales with N          -> results/size_scaling.csv
  bootK : sampling uncertainty of K*_flip for the top claims (bootstrap datasets)    -> results/boot_K.csv
  noise : random vote flips / random vote removal vs. ranking changes (Kendall tau)  -> results/random_noise.csv
  ties  : sensitivity of K*_flip to dropping ties (all non-NBA boards)               -> results/ties_sens.csv
"""
import os, sys, time
os.environ.setdefault('OMP_NUM_THREADS', '1')
import numpy as np
import pandas as pd
from multiprocessing import Pool
from scipy.stats import kendalltau
from bt import *
from run_claims import BOARDS, OUT, SEED

NBOOT_K = 20


def sub_board(b, W):
    nb = Board(b.name, b.dataset, b.design, b.ents, b.X, W, ins_ok=b.ins_ok, meta=b.meta)
    nb.n_ent = b.n_ent
    return nb


def top_claims(b, th, ncl):
    order = np.argsort(-th[:b.n_ent])
    return order, [(order[r], order[r + 1], r) for r in range(min(ncl, b.n_ent - 1))]


# ---------------------------------------------------------------- size scaling
def _fixed_pairs():
    """Pairs among the full-data top-10 of Arena-55k with Fisher z >= 8 (well-resolved claims fixed across subsamples)."""
    b = BOARDS[0]
    th = fit(b.X, b.W)
    order = np.argsort(-th)[:10]
    out = []
    for x in range(10):
        for y in range(x + 1, 10):
            q = contrast(b.P, order[x], order[y])
            if (q @ th) / fisher_se(b, th, q) >= 8:
                out.append((int(order[x]), int(order[y])))
    return out


def size_task(args):
    frac, rep = args
    b = BOARDS[0]
    rng = np.random.default_rng([SEED, 1, int(frac * 1000), rep])
    flat = b.W.ravel().astype(np.int64)
    n_sub = int(round(frac * b.N))
    if frac < 1:
        Ws = rng.multivariate_hypergeometric(flat, n_sub).reshape(b.C, 3).astype(float)
    else:
        Ws = b.W.copy()
    nb = sub_board(b, Ws)
    th = fit(nb.X, nb.W)
    rows = []
    for (i, j) in _fixed_pairs():
        q = contrast(nb.P, i, j)
        gap = float(q @ th)
        K = 0 if gap <= 0 else min_budget(nb, 'flip', q, th)[0]
        rows.append(dict(frac=frac, rep=rep, N=nb.N, i=i, j=j, gap=gap, se_fisher=fisher_se(nb, th, q), K_flip=K))
    return rows


# ---------------------------------------------------------------- bootstrap of K*
def bootk_task(bi):
    b = BOARDS[bi]
    rng = np.random.default_rng([SEED, 2, bi])
    probs = (b.W / b.W.sum()).ravel()
    th0 = fit(b.X, b.W)
    rows = []
    for k in range(NBOOT_K + 1):
        if k == 0:
            Wb = b.W
        elif b.clusters is not None:
            Wb = b.cluster_resample(rng)
        else:
            Wb = rng.multinomial(b.N, probs).reshape(b.C, 3).astype(float)
        nb = sub_board(b, Wb)
        th = fit(nb.X, nb.W, th0)
        order, cl = top_claims(nb, th, 5)
        for i, j, r in cl:
            q = contrast(nb.P, i, j)
            K, c = min_budget(nb, 'flip', q, th)
            rows.append(dict(board=b.name, dataset=b.dataset, draw=k, N=nb.N, rank_hi=r + 1, gap=float(q @ th), K_flip=K, cens=c))
    return rows


# ---------------------------------------------------------------- random noise vs ranking
def noise_task(bi):
    b = BOARDS[bi]
    rng = np.random.default_rng([SEED, 3, bi])
    th0 = fit(b.X, b.W)
    nr = b.n_ent
    rank0 = th0[:nr]
    top1 = int(np.argmax(rank0)); top3 = set(np.argsort(-rank0)[:3])
    rows = []
    for eps in (0.01, 0.02, 0.05, 0.10, 0.20):
        for kind in ('flip', 'remove'):
            for rep in range(30):
                W = b.W.copy()
                if kind == 'flip':
                    for c_col, o_col in ((0, 1), (1, 0)):
                        m = rng.binomial(b.W[:, c_col].astype(int), eps)
                        W[:, c_col] -= m
                        W[:, o_col] += m
                else:
                    for c_col in range(3):
                        W[:, c_col] -= rng.binomial(b.W[:, c_col].astype(int), eps)
                th = fit(b.X, W, th0)
                tau = kendalltau(rank0, th[:nr])[0]
                rows.append(dict(board=b.name, dataset=b.dataset, design=b.design, N=b.N, eps=eps, kind=kind, rep=rep,
                                 tau=tau, top1_same=int(np.argmax(th[:nr]) == top1),
                                 top3_same=int(set(np.argsort(-th[:nr])[:3]) == top3)))
    return rows


# ---------------------------------------------------------------- ties sensitivity
def ties_task(bi):
    b = BOARDS[bi]
    W = b.W.copy(); W[:, 2] = 0
    nb = sub_board(b, W)
    th = fit(nb.X, nb.W)
    order, cl = top_claims(nb, th, 10)
    rows = []
    for i, j, r in cl:
        q = contrast(nb.P, i, j)
        K, c = min_budget(nb, 'flip', q, th)
        rows.append(dict(board=b.name, N_noties=nb.N, rank_hi=r + 1, gap=float(q @ th), K_flip_noties=K))
    return rows


if __name__ == '__main__':
    part = sys.argv[1]
    t0 = time.time()
    with Pool(38) as pool:
        if part == 'size':
            tasks = [(f, r) for f in (0.02, 0.05, 0.1, 0.25, 0.5) for r in range(8)] + [(1.0, 0)]
            res = pool.map(size_task, tasks, chunksize=1); fn = 'size_scaling.csv'
        elif part == 'bootK':
            res = pool.map(bootk_task, range(len(BOARDS)), chunksize=1); fn = 'boot_K.csv'
        elif part == 'noise':
            res = pool.map(noise_task, range(len(BOARDS)), chunksize=1); fn = 'random_noise.csv'
        elif part == 'ties':
            res = pool.map(ties_task, [i for i, b in enumerate(BOARDS) if not b.name.startswith('nba')], chunksize=1)
            fn = 'ties_sens.csv'
    pd.DataFrame([r for rs in res for r in rs]).to_csv(os.path.join(OUT, fn), index=False)
    print(part, 'done', round(time.time() - t0), 's')
