"""E5: quality of the search and comparison with random perturbations.

(a) Exactness: on MT-Bench (6 models, 45 outcome cells) and on random subsamples of it,
    for every pair whose greedy drop size m <= 4 we enumerate *all* drop multisets of
    size < m and check that none reverses the pair (certifies optimality of greedy).
(b) Randomised restarts: for the leader-vs-challenger pairs of each dataset we run 20
    randomised greedy searches and report whether any beats the deterministic one.
(c) Random vs adversarial: probability that dropping (or flipping) m uniformly random
    comparisons reverses the leader/challenger pair, for m = m*, 10 m*, 1% N, 10% N.
Output: results/exact.csv, results/restarts.csv, results/random.csv

Usage: python -I code/exp_exact.py [--workers 36]
"""
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import (BT, Data, Target, amip_oneshot, exhaustive_no_smaller, greedy,  # noqa: E402
                random_drop_flip_prob, ranking)
from common import DATASETS, LAM, RES, load, load_df, top1_drop  # noqa: E402


def exact_task(args):
    name, n, seed = args
    df = load_df(name)
    if n is not None:
        df = df.sample(n=n, random_state=seed)
    d = Data(df)
    m = BT(d, lam=LAM)
    th, _, _ = m.fit()
    r = ranking(th, d.K)
    rows = []
    for a in range(d.K):
        for b in range(a + 1, d.K):
            tgt = Target("pair", r[a], r[b])
            g = greedy(m, tgt, "drop", th0=th)["m"]
            row = dict(dataset=name, n=n or d.N, seed=seed, rank_i=a + 1, rank_j=b + 1, m_greedy=g,
                       amip_lin=amip_oneshot(m, tgt)[0])
            if 2 <= g <= 4:
                smaller, fits = exhaustive_no_smaller(m, tgt, g)
                row.update(checked=True, exact_smaller=smaller if smaller is not None else -1, fits=fits)
            else:
                row.update(checked=False)
            rows.append(row)
    return rows


def restart_task(args):
    name, seed = args
    d, m = load(name)
    th, _, _ = m.fit()
    md, lead, chal = top1_drop(m, "drop")
    tgt = Target("pair", lead, chal)
    rng = np.random.default_rng(seed)
    best = np.inf
    vals = []
    for _ in range(20):
        v = greedy(m, tgt, "drop", th0=th, rng=rng, q=5)["m"]
        vals.append(v)
        best = min(best, v)
    return dict(dataset=name, m_greedy=md, m_restart_min=best, m_restart_median=float(np.median(vals)),
                m_restart_max=max(vals))


def random_flip_prob(model, target, m, reps, rng):
    d = model.d
    th, _, _ = model.fit()
    flat = d.C.ravel().astype(np.int64)
    hits = 0
    for _ in range(reps):
        ch = rng.multivariate_hypergeometric(flat, m).reshape(d.C.shape)
        C = d.C - ch
        C[:, 2] += ch[:, 0]
        C[:, 0] += ch[:, 2]
        t_split = rng.binomial(ch[:, 1], 0.5)
        C[:, 0] += t_split
        C[:, 2] += ch[:, 1] - t_split
        t, _, _ = model.fit(C, th)
        hits += target.gap(t, d)[0] < 0
    return hits / reps


def random_task(args):
    name, seed = args
    d, m = load(name)
    md, lead, chal = top1_drop(m, "drop")
    tgt = Target("pair", lead, chal)
    rng = np.random.default_rng(seed)
    rows = []
    sizes = {"m*": md, "10m*": 10 * md, "1%N": int(0.01 * d.N), "10%N": int(0.1 * d.N)}
    for lab, k in sizes.items():
        k = int(min(k, d.N - 1))
        if k <= 0:
            continue
        rows.append(dict(dataset=name, m_star=md, size=lab, m=k, kind="drop",
                         p_flip=random_drop_flip_prob(m, tgt, k, 500, rng)))
        rows.append(dict(dataset=name, m_star=md, size=lab, m=k, kind="flip",
                         p_flip=random_flip_prob(m, tgt, k, 500, rng)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=36)
    args = ap.parse_args()
    ex = [("mtbench_human", None, 0), ("mtbench_gpt4", None, 0)]
    ex += [(nm, n, s) for nm in ["mtbench_human", "mtbench_gpt4"] for n in [150, 300, 600] for s in range(10)]
    names = list(DATASETS) + ["nba_1996", "nba_2015"]
    with Pool(args.workers) as pool:
        exact = sum(pool.map(exact_task, ex, chunksize=1), [])
        pd.DataFrame(exact).to_csv(os.path.join(RES, "exact.csv"), index=False)
        rs = pool.map(restart_task, [(n, 7 + k) for k, n in enumerate(names)])
        pd.DataFrame(rs).to_csv(os.path.join(RES, "restarts.csv"), index=False)
        rnd = sum(pool.map(random_task, [(n, 99 + k) for k, n in enumerate(names)]), [])
        pd.DataFrame(rnd).to_csv(os.path.join(RES, "random.csv"), index=False)
    print("done")


if __name__ == "__main__":
    main()
