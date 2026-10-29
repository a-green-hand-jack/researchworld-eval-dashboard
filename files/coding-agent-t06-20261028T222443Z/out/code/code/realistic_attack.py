"""Vote-injection attacks that promote the rank-r competitor to rank 1.

Three attackers, all adding decisive votes only:
  free   : chooses both the battle (any pair observed on the board) and the vote; repeated
           iterated-greedy injection against the current leader (an optimistic attacker).
  target : sees only battles involving its own model t, opponents drawn from t's empirical
           opponent distribution; always votes for t (de-anonymising attacker).
  omni   : receives battles drawn from the board's empirical pair distribution and votes in
           whichever direction helps t most (first-order) on every battle it receives.
Reported cost = number of injected votes until t is ranked first (verified by refit).
Output: results/realistic_attack.parquet.  Usage: python code/realistic_attack.py [reps]
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

from bt import OUT, min_perturbation
from common import RES, load_board

BOARDS = ["arena55k", "arena140k", "webdev", "mtbench_human", "mtbench_gpt4", "arenaJ_crowd",
          "arenaJ_Qwen2-72B-Instruct", "arenaJ_Meta-Llama-3-70B-Instruct"]
RANKS = [2, 3, 5, 10]
_C = {}


def get(name):
    if name not in _C:
        B = load_board(name)
        th = B.fit()[0]
        _C[name] = (B, th, B.ranking(th))
    return _C[name]


def promote_free(B, t):
    W = B.W0.copy()
    total = 0
    for _ in range(50):
        th = B.fit(W)[0]
        r = B.ranking(th)
        if r[0] == t:
            return total
        res = min_perturbation(B, r[0], t, "add", W_start=W)
        if res["k"] is None:
            return None
        W = res["W"]
        total += res["k"]
    return None


def promote_random(B, t, kind, rng, max_votes=10**6):
    n_g = B.W0.sum(1)
    if kind == "target":
        inv = (B.ga == t) | (B.gb == t)
        prob = np.where(inv, n_g, 0.0)
    else:
        prob = n_g.copy()
    prob = prob / prob.sum()
    W = B.W0.copy()
    th, H, p = B.fit(W)
    total = 0
    while total < max_votes:
        others = np.delete(np.arange(B.K), t)
        s = others[np.argmax(th[others])]
        gap = th[s] - th[t]
        if gap < 0:
            return total
        v = np.zeros(B.P); v[t] = 1.0; v[s] = -1.0   # objective g = theta_t - theta_s
        u = np.linalg.solve(H, v)
        ux = B.X @ u
        # per-battle effect on g of a vote for the group's first (y=1) or second (y=0) member
        e1 = ux * (1 - p)
        e0 = ux * (0 - p)
        if kind == "target":
            vote1 = B.ga == t  # always vote for t
        else:
            vote1 = e1 >= e0
        eff = np.where(vote1, e1, e0)
        mean_eff = float(prob @ eff)
        if mean_eff <= 0:
            return None
        m = int(max(1, np.ceil(0.5 * gap / mean_eff)))
        gs = rng.choice(len(prob), size=m, p=prob)
        # apply in order, bisect on overshoot
        def apply(mm):
            W2 = W.copy()
            np.add.at(W2, (gs[:mm], np.where(vote1[gs[:mm]], 2, 0)), 1.0)
            return W2
        W2 = apply(m)
        th2, H2, p2 = B.fit(W2, th)
        if B.ranking(th2)[0] == t and m > 1:
            lo, hi = 0, m
            best = (W2, th2, H2, p2)
            while hi - lo > 1:
                mid = (lo + hi) // 2
                W3 = apply(mid)
                c = B.fit(W3, th)
                if B.ranking(c[0])[0] == t:
                    hi, best = mid, (W3,) + c
                else:
                    lo = mid
            return total + hi
        W, th, H, p = W2, th2, H2, p2
        total += m
    return None


def task(args):
    name, rank, kind, rep = args
    B, th0, r0 = get(name)
    t = r0[rank - 1]
    t0 = time.time()
    if kind == "free":
        k = promote_free(B, t)
    else:
        rng = np.random.default_rng([zlib.crc32(f"{name}|{rank}|{kind}".encode()), rep])
        k = promote_random(B, t, kind, rng)
    return dict(board=name, rank=rank, model=B.names[t], kind=kind, rep=rep, votes=k, N=B.N,
                n_t=float(B.W0.sum(1)[(B.ga == t) | (B.gb == t)].sum()), secs=time.time() - t0)


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    tasks = []
    for b in BOARDS:
        K = get(b)[0].K
        for rk in RANKS:
            if rk <= K:
                tasks.append((b, rk, "free", 0))
                tasks += [(b, rk, kd, r) for kd in ("target", "omni") for r in range(reps)]
    _C.clear()
    t0 = time.time()
    with Pool(int(os.environ.get("NPROC", 4))) as pool:
        rows = pool.map(task, tasks, chunksize=1)
    pd.DataFrame(rows).to_parquet(os.path.join(RES, "realistic_attack.parquet"), index=False)
    print("done %.0fs" % (time.time() - t0))
