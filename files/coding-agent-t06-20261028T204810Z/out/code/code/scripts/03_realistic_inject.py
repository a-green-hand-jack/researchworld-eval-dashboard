"""Vote injection when the adversary cannot choose the match-up (Arena-style random
pairing).  Battles arrive as random pairs drawn from the empirical match-up
distribution of the dataset; the adversary votes only on battles involving one
of the two targets (j wins whenever j plays; i loses whenever i plays) and skips
the rest.  We report the number of adversarial votes V and battles seen T
needed until j overtakes i, over S random seeds, alongside the optimal
free-choice injection budget from 01_budgets.py.

Output: results/realistic_inject.parquet
"""
import os, sys
import numpy as np
import pandas as pd
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lbstab import bt
from lbstab.attacks import extend_for_injection
from lbstab.prep import prepare, LAM

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results")
SETS = ["arena55k", "arena140k", "webdev10k", "arenaST_human"]
S = 20
TOPK = 10
G = {}


def simulate(args):
    name, i, j, seed = args
    ce, theta0, pair_p, pairs, cell_of = G[name]
    rng = np.random.default_rng(seed)
    w = ce.w.copy()
    V = T = 0
    theta = theta0
    # draw battles in growing batches; record each adversarial vote's cell
    while True:
        batch = max(50, T // 2)
        draws = rng.choice(len(pairs), size=batch, p=pair_p)
        votes = []
        for t, d in enumerate(draws):
            a, b = pairs[d]
            if j in (a, b):
                winner, loser = j, (b if a == j else a)
            elif i in (a, b):
                loser, winner = i, (b if a == i else a)
            else:
                continue
            votes.append((t, cell_of[(winner, loser)]))
        w_new = w.copy()
        for _, cidx in votes:
            w_new[cidx] += 1
        th = bt.fit(ce.copy(w_new), LAM, theta)
        if th[i] - th[j] < 0:
            # bisect on the number of votes from this batch
            lo, hi = 0, len(votes)
            while hi - lo > 1:
                mid = (lo + hi) // 2
                w_mid = w.copy()
                for _, cidx in votes[:mid]:
                    w_mid[cidx] += 1
                thm = bt.fit(ce.copy(w_mid), LAM, theta)
                if thm[i] - thm[j] < 0:
                    hi = mid
                else:
                    lo = mid
            V += hi
            T += votes[hi - 1][0] + 1
            return dict(ds=name, i=i, j=j, seed=seed, V=V, T=T)
        w, theta = w_new, th
        V += len(votes)
        T += batch
        if V > 10 * ce.n:
            return dict(ds=name, i=i, j=j, seed=seed, V=np.inf, T=np.inf)


def setup(name):
    c, df = prepare(name)
    theta = bt.fit(c, LAM)
    ce = extend_for_injection(c)
    # empirical match-up distribution
    a = np.minimum(df.a.values, df.b.values)
    b = np.maximum(df.a.values, df.b.values)
    cnt = pd.Series(list(zip(a, b))).value_counts()
    pairs = list(cnt.index)
    pair_p = (cnt.values / cnt.values.sum()).astype(float)
    # cell index for "winner beats loser" in the (a<b) orientation of ce
    cell_of = {}
    for n in range(len(ce.w)):
        if ce.y[n] == 1.0:
            cell_of[(ce.a[n], ce.b[n])] = n
        elif ce.y[n] == 0.0:
            cell_of[(ce.b[n], ce.a[n])] = n
    G[name] = (ce, theta, pair_p, pairs, cell_of)
    order = bt.ranking(theta, c)
    return [(name, int(order[r]), int(order[r + 1])) for r in range(TOPK - 1)]


if __name__ == "__main__":
    jobs = []
    for nm in SETS:
        for (n_, i, j) in setup(nm):
            jobs += [(n_, i, j, s) for s in range(S)]
    with Pool(38) as pool:
        rows = pool.map(simulate, jobs, chunksize=2)
    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(OUT, "realistic_inject.parquet"))
    print(df.groupby(["ds", "i", "j"])[["V", "T"]].median())
