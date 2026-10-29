"""E7: robustness of the conclusions to modelling choices.

Variants: ridge penalty lam in {1e-5, 1e-3 (default), 1e-1, 1}; ties counted as half wins
(default) vs. ties discarded; minimum number of comparisons per competitor 100 (default)
vs. 500.  For each variant we report the greedy top-1 drop size and the median greedy drop
size over adjacent pairs among the top 10.
Output: results/ablation.csv

Usage: python -I code/exp_ablation.py [--workers 36]
"""
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd  # noqa: E402

from bt import Target, greedy, pair_stats, ranking  # noqa: E402
from common import RES, load, load_df, top1_drop  # noqa: E402
from prep_data import filter_rare  # noqa: E402

SETS = ["arena55k", "arena140k", "webdev", "mtbench_human", "mtbench_gpt4",
        "judge_Qwen2-72B-Instruct", "judge_Meta-Llama-3-70B-Instruct", "nba_1996", "nba_2015"]
VARIANTS = [("lam", 1e-5), ("lam", 1e-3), ("lam", 1e-1), ("lam", 1.0), ("ties", "drop"), ("minn", 500)]


def task(args):
    name, (kind, val) = args
    df = load_df(name)
    lam = 1e-3
    if kind == "lam":
        lam = val
    elif kind == "ties":
        df = df[df.y != 0.5]
    elif kind == "minn":
        df = filter_rare(df, val)
    d, m = load(name, lam=lam, df=df)
    th, H, p = m.fit()
    r = ranking(th, d.K)
    st = pair_stats(m, th, H, p, r[0], r[1])
    mt, lead, chal = top1_drop(m, "drop")
    adj = [greedy(m, Target("pair", r[k], r[k + 1]), "drop", th0=th)["m"] for k in range(min(9, d.K - 1))]
    return dict(dataset=name, variant=f"{kind}={val}", N=d.N, K=d.K, leader=d.items[lead], z12=st["z"],
                m_top1=mt, m_top1_frac=mt / d.N, adj_median=float(np.median(adj)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=36)
    args = ap.parse_args()
    tasks = [(n, v) for n in SETS for v in VARIANTS]
    with Pool(args.workers) as pool:
        rows = pool.map(task, tasks, chunksize=1)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RES, "ablation.csv"), index=False)
    print(df.to_string())


if __name__ == "__main__":
    main()
