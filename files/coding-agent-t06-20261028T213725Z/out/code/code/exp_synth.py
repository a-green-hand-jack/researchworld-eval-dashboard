"""E8 (SYNTHETIC data): scaling of worst-case fragility with sample size and design.

Comparisons are simulated from a Bradley-Terry model with K = 20 competitors whose true
strengths are fixed (theta_k = s * Phi^{-1}((k + 0.5)/K), s = 1).  Pairs are sampled
either uniformly ("balanced") or with Zipf(1) popularity weights ("imbalanced").  For
N in {1k, 4k, 16k, 64k} and 10 seeds we compute, for every adjacent pair of the *fitted*
ranking, z, kappa and the greedy minimal number of drops.
Output: results/synth.csv

Usage: python -I code/exp_synth.py [--workers 36]
"""
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import BT, Data, Target, greedy, pair_stats, ranking  # noqa: E402
from common import RES  # noqa: E402

K = 20


def simulate(N, design, rng, s=1.0):
    theta = s * norm.ppf((np.arange(K) + 0.5) / K)
    w = np.ones(K) if design == "balanced" else 1.0 / (1 + rng.permutation(K))
    ii, jj = np.triu_indices(K, 1)
    pw = w[ii] * w[jj]
    pw /= pw.sum()
    pick = rng.choice(len(ii), size=N, p=pw)
    a, b = ii[pick], jj[pick]
    y = (rng.random(N) < 1 / (1 + np.exp(-(theta[a] - theta[b])))).astype(float)
    return pd.DataFrame({"a": [f"m{k:02d}" for k in a], "b": [f"m{k:02d}" for k in b], "y": y, "h": 0})


def task(args):
    N, design, seed = args
    rng = np.random.default_rng(seed)
    df = simulate(N, design, rng)
    d = Data(df)
    m = BT(d, lam=1e-3)
    th, H, p = m.fit()
    r = ranking(th, d.K)
    rows = []
    for k in range(d.K - 1):
        i, j = r[k], r[k + 1]
        st = pair_stats(m, th, H, p, i, j)
        md = greedy(m, Target("pair", i, j), "drop", th0=th)["m"]
        rows.append(dict(N=N, design=design, seed=seed, rank_i=k + 1, **st, m_drop=md))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=36)
    args = ap.parse_args()
    tasks = [(N, dsg, 100 * s + k) for k, N in enumerate([1000, 4000, 16000, 64000])
             for dsg in ["balanced", "imbalanced"] for s in range(10)]
    with Pool(args.workers) as pool:
        rows = sum(pool.map(task, tasks, chunksize=1), [])
    pd.DataFrame(rows).to_csv(os.path.join(RES, "synth.csv"), index=False)
    print("done")


if __name__ == "__main__":
    main()
