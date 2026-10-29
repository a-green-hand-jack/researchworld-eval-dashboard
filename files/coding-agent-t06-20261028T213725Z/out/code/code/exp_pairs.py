"""E1/E2: worst-case perturbation sizes for many ranked pairs in every dataset.

For each dataset (and each NBA season) we fit Bradley-Terry, rank the competitors and
evaluate a set of pairs (i ranked above j): all adjacent pairs, all pairs within the
top 10, and the leader against ranks 2..11.  For every pair we record
  * z-score of the gap, influence concentration kappa, local sample size,
  * greedy worst-case number of drops / flips / free injections that reverse the pair,
  * one-shot AMIP (linear prediction and refit-verified), head-to-head baseline,
  * composition of the worst-case drop set.
Output: results/pairs.csv

Usage: python -I code/exp_pairs.py [--workers 36]
"""
import argparse
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import Target, amip_oneshot, greedy, headtohead, pair_stats, ranking  # noqa: E402
from common import DATASETS, RAW_JUDGES, RES, category, load, nba_seasons  # noqa: E402

_cache = {}


def get(name):
    if name not in _cache:
        d, m = load(name, all_pairs=not name.startswith("nba_"))
        th, H, p = m.fit()
        _cache[name] = (d, m, th, H, p, ranking(th, d.K))
    return _cache[name]


def pairs_for(K):
    s = set()
    for r in range(K - 1):
        s.add((r, r + 1))
    for r in range(min(K, 10)):
        for q in range(r + 1, min(K, 10)):
            s.add((r, q))
    for q in range(1, min(K, 12)):
        s.add((0, q))
    return sorted(s)


def composition(d, th, ops, i, j):
    tot = up = h2h = inv_i = inv_j = 0
    for (mode, g, o, _), k in ops.items():
        a, b = d.ga[g], d.gb[g]
        tot += k
        if (o == 2 and th[a] < th[b]) or (o == 0 and th[a] > th[b]):
            up += k
        if {a, b} == {i, j}:
            h2h += k
        inv_i += k * (i in (a, b))
        inv_j += k * (j in (a, b))
    if tot == 0:
        return dict(share_upset=np.nan, share_h2h=np.nan, share_i=np.nan, share_j=np.nan)
    return dict(share_upset=up / tot, share_h2h=h2h / tot, share_i=inv_i / tot, share_j=inv_j / tot)


def task(args):
    name, ri, rj = args
    d, m, th, H, p, r = get(name)
    i, j = r[ri], r[rj]
    tgt = Target("pair", i, j)
    t0 = time.time()
    st = pair_stats(m, th, H, p, i, j)
    gd = greedy(m, tgt, "drop", th0=th)
    gf = greedy(m, tgt, "flip", th0=th)
    lin, refit = amip_oneshot(m, tgt)
    row = dict(dataset=name, category=category(name), N=d.N, K=d.K, rank_i=ri + 1, rank_j=rj + 1,
               item_i=d.items[i], item_j=d.items[j], **st,
               m_drop=gd["m"], refits_drop=gd["refits"], m_flip=gf["m"],
               amip_lin=lin, amip_refit=refit,
               **composition(d, th, gd["ops"], i, j))
    if rj < 10:  # costlier baselines only for top-10 pairs
        row["m_h2h"] = headtohead(m, tgt)
        if not name.startswith("nba_"):
            row["m_inject"] = greedy(m, tgt, "inject", th0=th)["m"]
    row["seconds"] = time.time() - t0
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=36)
    ap.add_argument("--out", default=os.path.join(RES, "pairs.csv"))
    args = ap.parse_args()
    names = list(DATASETS) + RAW_JUDGES + nba_seasons()
    tasks = []
    for n in names:
        K = get(n)[0].K
        tasks += [(n, a, b) for a, b in pairs_for(K)]
    _cache.clear()
    # big datasets first for load balancing
    tasks.sort(key=lambda t: (t[0].startswith("nba_"), t[0].startswith("mtbench")))
    print(len(tasks), "tasks", flush=True)
    rows = []
    with Pool(args.workers) as pool:
        for k, row in enumerate(pool.imap_unordered(task, tasks, chunksize=1)):
            rows.append(row)
            if k % 200 == 0:
                print(k, row["dataset"], row["rank_i"], row["rank_j"], row["m_drop"], f'{row["seconds"]:.1f}s',
                      flush=True)
    df = pd.DataFrame(rows).sort_values(["dataset", "rank_i", "rank_j"])
    df.to_csv(args.out, index=False)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
