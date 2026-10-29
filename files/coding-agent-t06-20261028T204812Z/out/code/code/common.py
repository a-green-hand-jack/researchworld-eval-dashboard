import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
import btlib

RES = os.environ.get("RES_DIR", "/work/results")
_G = {}


def _pair_job(args):
    i, j, modes = args
    b = _G["board"]
    th = b.base_fit()
    c = b.contrast(i, j)
    _, se = b.class_effects(th, b.W0, c)
    g = float(c @ th)
    n = b.comparisons_per_model()
    h2h = b.W0[((b.A == i) & (b.B == j)) | ((b.A == j) & (b.B == i))].sum()
    row = dict(i=i, j=j, gap=g, se=se, z=g / se, n_i=n[i], n_j=n[j], n_ij=n[i] + n[j] - h2h, h2h=h2h)
    for m in modes:
        r = b.attack(i, j, m)
        row["K_" + m] = r["K"]
        row["Klin_" + m] = r["K_lin"] if r["K_lin"] is not None else np.nan
    return row


def pair_scan(board, pairs=None, modes=("remove", "flip", "add"), nmin=0, procs=1):
    """attack every pair (i ranked above j).  pairs: list of (i,j) or None for all pairs among models with >=nmin comparisons."""
    th = board.base_fit()
    n = board.comparisons_per_model()
    rank = np.empty(board.m, int)
    rank[board.ranking()] = np.arange(board.m)
    if pairs is None:
        ids = [k for k in range(board.m) if n[k] >= nmin]
        pairs = [(i, j) for i in ids for j in ids if th[i] > th[j]]
    jobs = [(i, j, modes) for i, j in pairs]
    _G["board"] = board
    if procs > 1 and len(jobs) > 20:
        with Pool(procs) as p:
            rows = p.map(_pair_job, jobs, chunksize=max(1, len(jobs) // (procs * 8)))
    else:
        rows = [_pair_job(j) for j in jobs]
    df = pd.DataFrame(rows)
    df["rank_i"] = rank[df.i.values] + 1
    df["rank_j"] = rank[df.j.values] + 1
    df["name_i"] = [board.names[k] for k in df.i]
    df["name_j"] = [board.names[k] for k in df.j]
    df["N"] = board.n_total
    return df
