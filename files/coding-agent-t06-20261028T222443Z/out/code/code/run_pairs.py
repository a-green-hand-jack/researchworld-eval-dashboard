"""Worst-case perturbation sizes for ranking-relevant pairs on every leaderboard.

For every leaderboard in derived/ (and tie-free variants of the LLM boards) and every pair in
  adjacent pairs (r, r+1), top-1 pairs (1, j<=8), top-3 boundary pairs (i<=3, 4<=j<=10)
we compute, for each perturbation type (drop / flip / add / add_target), the smallest number
of comparisons found by the iterated greedy search (verified by an exact refit), plus the
one-shot first-order (AMIP-style) estimates and pair statistics.
Output: results/pairs.parquet.     Usage: python code/run_pairs.py [--quick]
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import Board, min_perturbation, first_order_k, pair_stats  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DER = os.path.join(ROOT, "derived")
RES = os.path.join(ROOT, "results")
MODES = ["drop", "flip", "add"]
LLM_BOARDS = ["arena55k", "arena140k", "webdev", "mtbench_human", "mtbench_gpt4", "arena55k_mt6",
              "arenaJ_crowd", "arenaJ_Athene-70B", "arenaJ_Meta-Llama-3-70B-Instruct",
              "arenaJ_Meta-Llama-3-8B-Instruct", "arenaJ_Mistral-7B-Instruct-v0.1",
              "arenaJ_Qwen2-72B-Instruct"]

_BOARDS = {}


def load(name):
    if name not in _BOARDS:
        base = name.replace("__noties", "")
        df = pd.read_parquet(os.path.join(DER, base + ".parquet"))
        if name.endswith("__noties"):
            df = df[df.y != 0.5]
            from data_prep import filter_min
            df = filter_min(df)
        B = Board(df)
        th, H, _ = B.fit()
        _BOARDS[name] = (B, th, H, B.ranking(th))
    return _BOARDS[name]


def pair_list(K):
    s = set()
    for r in range(K - 1):
        s.add((r, r + 1))
    for j in range(1, min(8, K)):
        s.add((0, j))
    for i in range(min(3, K)):
        for j in range(3, min(10, K)):
            s.add((i, j))
    return sorted(s)


def task(args):
    name, ri, rj = args
    B, th, H, rank = load(name)
    i, j = rank[ri], rank[rj]
    st = pair_stats(B, i, j, th, H)
    rows = []
    for mode in MODES:
        t = time.time()
        res = min_perturbation(B, i, j, mode)
        fo = first_order_k(B, i, j, mode)
        rows.append(dict(board=name, ri=ri + 1, rj=rj + 1, name_i=B.names[i], name_j=B.names[j],
                         mode=mode, k=res["k"], verified=res["verified"], iters=res.get("iters"),
                         k_fo=fo.get("k_fo"), k_os=fo.get("k_os"), N=B.N, K=B.K,
                         secs=time.time() - t, **st))
    return rows


def main():
    quick = "--quick" in sys.argv
    boards = list(LLM_BOARDS) + [b + "__noties" for b in LLM_BOARDS]
    boards += sorted(f[:-8] for f in os.listdir(DER) if f.startswith("nba_") and f.endswith(".parquet"))
    if quick:
        boards = ["mtbench_human", "webdev"]
    tasks = []
    for b in boards:
        B, th, H, rank = load(b)
        tasks += [(b, ri, rj) for ri, rj in pair_list(B.K)]
    # big boards first for load balance
    tasks.sort(key=lambda t: -load(t[0])[0].K)
    _BOARDS.clear()
    print(len(tasks), "pair tasks", flush=True)
    t0 = time.time()
    out = []
    with Pool(int(os.environ.get("NPROC", 4))) as pool:
        for n, rows in enumerate(pool.imap_unordered(task, tasks, chunksize=1)):
            out += rows
            if n % 500 == 0:
                print(n, "%.0fs" % (time.time() - t0), flush=True)
    df = pd.DataFrame(out).sort_values(["board", "mode", "ri", "rj"]).reset_index(drop=True)
    os.makedirs(RES, exist_ok=True)
    df.to_parquet(os.path.join(RES, "pairs_quick.parquet" if quick else "pairs.parquet"), index=False)
    print("done %.0fs" % (time.time() - t0), "unverified:", int((~df.verified).sum()))


if __name__ == "__main__":
    main()
