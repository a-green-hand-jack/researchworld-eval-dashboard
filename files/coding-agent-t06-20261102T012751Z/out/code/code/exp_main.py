"""Main experiment: for every item pair of every leaderboard, the minimal number of
vote edits (drop / relabel / insert; greedy refit-verified witness) that (a) reverses
the pair's order ('flip') or (b) reduces the gap to 1.96 IJ-s.e. ('sig'; only for pairs
that are significant at the start).  Writes results/pairs.csv."""
import sys, time
import numpy as np, pandas as pd
from multiprocessing import Pool
from bt import *
import datasets as ds

BOARDS = {}
KINDS = ["drop", "relabel", "insert"]
MAXFRAC = 0.3

def setup():
    BOARDS["arena"] = ds.arena55k()
    BOARDS["mt_human"] = ds.mtbench_human()
    BOARDS["mt_gpt4"] = ds.mtbench_gpt4()
    for yr, b in ds.nba_seasons().items():
        BOARDS[f"nba{yr}"] = b

FIT = {}
def get_fit(key):
    if key not in FIT:
        b = BOARDS[key]; FIT[key] = b.fit()
    return FIT[key]

def task(args):
    key, i, j = args
    return pair_records(BOARDS[key], get_fit(key), i, j, KINDS, extra=dict(board=key), maxfrac=MAXFRAC)

if __name__ == "__main__":
    setup()
    tasks = []
    for key, b in BOARDS.items():
        th = b.fit(); s = th[: b.m]
        for i in range(b.m):
            for j in range(b.m):
                if s[i] > s[j]:
                    tasks.append((key, i, j))
    # biggest boards first for load balance
    tasks.sort(key=lambda t: -BOARDS[t[0]].n)
    print(len(tasks), "pairs", flush=True)
    t0 = time.time()
    with Pool(38) as p:
        out = []
        for n, r in enumerate(p.imap_unordered(task, tasks, chunksize=4)):
            out += r
            if n % 2000 == 0: print(n, time.time() - t0, flush=True)
    df = pd.DataFrame(out)
    df.to_csv("/work/results/pairs.csv", index=False)
    print("done", len(df), time.time() - t0)
