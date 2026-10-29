"""E3: sampling uncertainty of the fragility metrics (nonparametric bootstrap).

For each dataset we resample the comparisons with replacement B times, refit, and
recompute the greedy minimal number of drops (and flips) that changes the rank-1
competitor, together with the z-score of the leader's gap to the runner-up.
Output: results/bootstrap.csv

Usage: python -I code/exp_bootstrap.py [--B 200] [--workers 36]
"""
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import pair_stats, ranking  # noqa: E402
from common import DATASETS, RES, load, top1_drop  # noqa: E402

NBA_BOOT = ["nba_1996", "nba_2015"]
_cache = {}


def task(args):
    name, b, seed = args
    if name not in _cache:
        _cache[name] = load(name)
    d, m = _cache[name]
    rng = np.random.default_rng(seed)
    if b == 0:
        C = d.C.copy()  # replicate 0 = original data
    else:
        flat = d.C.ravel()
        C = rng.multinomial(int(flat.sum()), flat / flat.sum()).reshape(d.C.shape).astype(float)
    th, H, p = m.fit(C)
    r = ranking(th, d.K)
    st = pair_stats(m, th, H, p, r[0], r[1], C=C)
    md, lead, chal = top1_drop(m, "drop", C0=C)
    mf, _, _ = top1_drop(m, "flip", C0=C)
    return dict(dataset=name, b=b, seed=seed, leader=d.items[lead], challenger=d.items[chal] if chal is not None else "",
                runner_up=d.items[r[1]], z12=st["z"], kappa12=st["kappa"], m_top1_drop=md, m_top1_flip=mf, N=d.N)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=200)
    ap.add_argument("--workers", type=int, default=36)
    args = ap.parse_args()
    names = list(DATASETS) + NBA_BOOT
    tasks = [(n, b, 10_000 * k + b) for k, n in enumerate(names) for b in range(args.B + 1)]
    with Pool(args.workers) as pool:
        rows = pool.map(task, tasks, chunksize=4)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RES, "bootstrap.csv"), index=False)
    print(df.groupby("dataset").agg(m=("m_top1_drop", "median"), lo=("m_top1_drop", lambda x: x.quantile(.025)),
                                    hi=("m_top1_drop", lambda x: x.quantile(.975)), z=("z12", "median")))


if __name__ == "__main__":
    main()
