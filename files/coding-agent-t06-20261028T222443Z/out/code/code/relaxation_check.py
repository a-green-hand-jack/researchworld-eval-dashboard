"""Optimality check of the greedy drop search via a continuous relaxation.

Integer problem:  min sum(delta)  s.t.  theta_i(W0-delta) <= theta_j(W0-delta),  delta integer in [0, W0].
Relaxation: delta real-valued.  Any feasible integer solution is feasible for the relaxation, so the
relaxed optimum (if found globally) lower-bounds the true minimum.  The relaxation is non-convex, so we
use SLSQP from several starts; the result is an empirical (not certified) near-lower bound.
Output: results/relaxation_check.parquet.   Usage: python code/relaxation_check.py
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from bt import OUT, min_perturbation, first_order_k
from common import RES, load_board

BOARDS = ["mtbench_human", "mtbench_gpt4", "arena55k_mt6", "webdev", "nba_2015"]
_C = {}


def get(name):
    if name not in _C:
        B = load_board(name)
        th = B.fit()[0]
        _C[name] = (B, th, B.ranking(th))
    return _C[name]


def relax(B, i, j, greedy_moves, seed=0):
    v = B.contrast(i, j)
    th0, H0, p0 = B.fit()
    u = np.linalg.solve(H0, v)
    eff = (B.X @ u)[:, None] * (p0[:, None] - OUT[None, :])
    cand = set(map(tuple, np.argwhere((B.W0 > 0) & (eff < 0))))
    cand |= set(greedy_moves)
    cand = sorted(cand)
    gi = np.array([c[0] for c in cand]); oi = np.array([c[1] for c in cand])
    ub = B.W0[gi, oi]
    cache = {}

    def solve(d):
        key = d.tobytes()
        if key not in cache:
            W = B.W0.copy()
            W[gi, oi] -= d
            th, H, p = B.fit(W, th0)
            uu = np.linalg.solve(H, v)
            grad_f = (B.X @ uu)[gi] * (p[gi] - OUT[oi])  # d f / d delta
            cache[key] = (float(v @ th), grad_f)
        return cache[key]

    cons = {"type": "ineq", "fun": lambda d: -solve(d)[0] - 1e-6, "jac": lambda d: -solve(d)[1]}
    rng = np.random.default_rng(seed)
    g0 = np.array([greedy_moves.get(c, 0) for c in cand], float)
    starts = [g0, 0.5 * g0, np.minimum(ub, rng.uniform(0, 1, len(ub)) * g0.sum() / max(1, len(ub)) * 2)]
    best, best_x = np.inf, None
    for x0 in starts:
        try:
            r = minimize(lambda d: d.sum(), x0, jac=lambda d: np.ones_like(d), bounds=list(zip(0 * ub, ub)),
                         constraints=[cons], method="SLSQP", options=dict(maxiter=300, ftol=1e-9))
            xc = np.clip(r.x, 0, ub)
            if solve(xc)[0] <= 1e-6 and xc.sum() < best:
                best, best_x = float(xc.sum()), xc
        except Exception:
            pass
    # integer solution obtained by rounding the relaxed one up (then verified by refit)
    k_round = None
    if best_x is not None:
        xr = np.minimum(ub, np.ceil(best_x - 1e-6))
        W = B.W0.copy()
        W[gi, oi] -= xr
        if float(v @ B.fit(W)[0]) < -1e-9:
            k_round = int(xr.sum())
    return best, k_round


def task(args):
    name, ri, rj = args
    B, th, r = get(name)
    i, j = r[ri], r[rj]
    t0 = time.time()
    g = min_perturbation(B, i, j, "drop")
    fo = first_order_k(B, i, j, "drop")
    kstar = min(x for x in (g["k"], fo["k_os"]) if x is not None)
    rl, k_round = relax(B, i, j, g["moves"])
    return dict(board=name, ri=ri + 1, rj=rj + 1, k_iter=g["k"], k_os=fo["k_os"], k_fo=fo["k_fo"],
                k_best=kstar, relax=rl, k_round=k_round, secs=time.time() - t0)


if __name__ == "__main__":
    tasks = []
    for b in BOARDS:
        K = get(b)[0].K
        prs = {(r, r + 1) for r in range(K - 1)} | {(0, j) for j in range(1, min(6, K))}
        tasks += [(b, a, c) for a, c in sorted(prs)]
    _C.clear()
    t0 = time.time()
    with Pool(int(os.environ.get("NPROC", 4))) as pool:
        rows = pool.map(task, tasks, chunksize=1)
    pd.DataFrame(rows).to_parquet(os.path.join(RES, "relaxation_check.parquet"), index=False)
    print("done %.0fs" % (time.time() - t0))
