"""E6: promoting a competitor to rank 1 -- dropping vs. injecting votes.

For the LLM leaderboards we take the competitor at rank r (r = 2, 3, 5, 10) and measure the
number of operations needed to make it rank 1 under four threat models:
  drop        : worst-case removal of existing comparisons (greedy),
  inject-free : the adversary adds comparisons of any pair and outcome (greedy),
  stream-omni : battles arrive with pairs drawn from the empirical pair distribution and the
                adversary votes in every battle, choosing the most useful outcome
                (cf. "omnipresent" rigging of Min et al.);
  stream-target: the adversary votes only in battles that involve the target (target wins).
Stream attacks are randomised: 10 seeds.  Output: results/inject.csv

Usage: python -I code/exp_inject.py [--workers 36]
"""
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import Target, greedy, ranking, stream_attack  # noqa: E402
from common import RES, load  # noqa: E402

SETS = ["arena55k", "arena140k", "webdev", "mtbench_human", "mtbench_gpt4"]
RANKS = [2, 3, 5, 10]
SEEDS = 10


def task(args):
    name, rk, kind, seed = args
    d, m = load(name, all_pairs=True)
    th, _, _ = m.fit()
    r = ranking(th, d.K)
    i = r[rk - 1]
    tgt = Target("top", i)
    if kind == "drop":
        v = greedy(m, tgt, "drop", th0=th)["m"]
    elif kind == "inject-free":
        v = greedy(m, tgt, "inject", th0=th)["m"]
    else:
        rng = np.random.default_rng(seed)
        if kind == "stream-omni":
            v = stream_attack(m, tgt, rng)
        else:
            allowed = (d.ga == i) | (d.gb == i)
            v = stream_attack(m, tgt, rng, allowed_groups=allowed, vote_for=i)
    n_i = d.counts_involving([i])
    return dict(dataset=name, N=d.N, K=d.K, rank=rk, item=d.items[i], n_item=n_i, kind=kind, seed=seed, m=v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=36)
    args = ap.parse_args()
    tasks = []
    for n in SETS:
        K = load(n)[0].K
        for rk in RANKS:
            if rk > K:
                continue
            tasks += [(n, rk, "drop", 0), (n, rk, "inject-free", 0)]
            tasks += [(n, rk, k, s) for k in ["stream-omni", "stream-target"] for s in range(SEEDS)]
    with Pool(args.workers) as pool:
        rows = pool.map(task, tasks, chunksize=1)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RES, "inject.csv"), index=False)
    print(df.groupby(["dataset", "rank", "kind"]).m.median().unstack())


if __name__ == "__main__":
    main()
