"""E4: how fragility scales with the amount of data, and size-matched comparisons.

(a) Subsampling curves: for Arena-55k, Arena-140k, WebDev and MT-Bench (experts) we draw
    random subsamples (without replacement) of fraction f of the comparisons and, for a
    fixed set of pairs (the full-data adjacent pairs among the top 6), compute z, kappa
    and the greedy minimal number of drops.  Also the top-1 change size of the subsample.
(b) Size-matched labeller comparison on MT-Bench: expert judgments subsampled to the
    size of the GPT-4-judge data (N = 2400).
Output: results/size_curves.csv, results/size_matched.csv

Usage: python -I code/exp_size.py [--seeds 20] [--workers 36]
"""
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import Target, greedy, pair_stats, ranking  # noqa: E402
from common import RES, load, top1_drop  # noqa: E402

CURVE_SETS = ["arena55k", "arena140k", "webdev", "mtbench_human", "mtbench_gpt4"]
FRACS = [0.05, 0.1, 0.2, 0.4, 0.7, 1.0]
_cache = {}


def get(name):
    if name not in _cache:
        d, m = load(name)
        th, H, p = m.fit()
        _cache[name] = (d, m, ranking(th, d.K))
    return _cache[name]


def subsample(C, n, rng):
    flat = C.ravel().astype(np.int64)
    return rng.multivariate_hypergeometric(flat, n).reshape(C.shape).astype(float)


def curve_task(args):
    name, f, seed = args
    d, m, r = get(name)
    rng = np.random.default_rng(seed)
    n = int(round(f * d.N))
    C = d.C.copy() if f == 1.0 else subsample(d.C, n, rng)
    th, H, p = m.fit(C)
    rows = []
    for k in range(min(5, d.K - 1)):
        i, j = r[k], r[k + 1]
        st = pair_stats(m, th, H, p, i, j, C=C)
        if st["gap"] > 0:
            md = greedy(m, Target("pair", i, j), "drop", C0=C, th0=th)["m"]
        else:  # already reversed in this subsample
            md = 0
        rows.append(dict(dataset=name, frac=f, n=n, seed=seed, pair=f"{k + 1}-{k + 2}", **st, m_drop=md))
    mt, _, _ = top1_drop(m, "drop", C0=C)
    rows.append(dict(dataset=name, frac=f, n=n, seed=seed, pair="top1", m_drop=mt))
    return rows


def matched_task(args):
    name, n, seed = args
    d, m, r = get(name)
    rng = np.random.default_rng(seed)
    C = subsample(d.C, n, rng) if n < d.N else d.C.copy()
    th, H, p = m.fit(C)
    rr = ranking(th, d.K)
    st = pair_stats(m, th, H, p, rr[0], rr[1], C=C)
    out = dict(dataset=name, n=n, seed=seed, leader=d.items[rr[0]], z12=st["z"], kappa12=st["kappa"])
    out["m_top1_drop"], _, _ = top1_drop(m, "drop", C0=C)
    adj = []
    for k in range(d.K - 1):
        i, j = rr[k], rr[k + 1]
        adj.append(greedy(m, Target("pair", i, j), "drop", C0=C, th0=th)["m"])
    out["m_adj_median"] = float(np.median(adj))
    out["m_adj_min"] = float(np.min(adj))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--workers", type=int, default=36)
    args = ap.parse_args()
    tasks = [(n, f, 1000 * k + s) for k, n in enumerate(CURVE_SETS) for f in FRACS
             for s in range(args.seeds if f < 1 else 1)]
    with Pool(args.workers) as pool:
        rows = sum(pool.map(curve_task, tasks, chunksize=2), [])
    pd.DataFrame(rows).to_csv(os.path.join(RES, "size_curves.csv"), index=False)
    mt = [("mtbench_human", 2400, 500 + s) for s in range(50)] + [("mtbench_gpt4", 2400, 0)] + \
         [("mtbench_human", 3355, 0)]
    with Pool(args.workers) as pool:
        rows = pool.map(matched_task, mt)
    pd.DataFrame(rows).to_csv(os.path.join(RES, "size_matched.csv"), index=False)
    print("done")


if __name__ == "__main__":
    main()
