"""E9: design-matched comparison of crowd, expert and LLM-judge labels.

The six MT-Bench models also appear in Chatbot Arena-55k.  We build three label sources on
the *same six competitors* and the *same per-pair numbers of comparisons*:
  crowd  : Arena-55k votes among {gpt-4-0314, claude-1, gpt-3.5-turbo-0314, vicuna-13b,
           alpaca-13b, llama-13b}  (user prompts, crowd labels),
  expert : MT-Bench expert judgments (curated prompts, expert labels),
  gpt4   : MT-Bench GPT-4 pairwise judgments (curated prompts, LLM-judge labels).
For each unordered pair we subsample, from every source, n_pair = min over sources of the
available comparisons (50 random seeds).  Model names are mapped to a common vocabulary.
For each source and seed we compute, for all 15 pairs, z, kappa and the greedy minimal
number of drops, plus the top-1 change size.
Output: results/matched.csv

Usage: python -I code/exp_matched.py [--seeds 50] [--workers 36]
"""
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import BT, Data, Target, greedy, pair_stats, ranking  # noqa: E402
from common import LAM, RES, load_df  # noqa: E402

ARENA_MAP = {"gpt-4-0314": "gpt-4", "claude-1": "claude-v1", "gpt-3.5-turbo-0314": "gpt-3.5-turbo",
             "vicuna-13b": "vicuna-13b", "alpaca-13b": "alpaca-13b", "llama-13b": "llama-13b"}
MT_MAP = {"gpt-4": "gpt-4", "claude-v1": "claude-v1", "gpt-3.5-turbo": "gpt-3.5-turbo",
          "vicuna-13b-v1.2": "vicuna-13b", "alpaca-13b": "alpaca-13b", "llama-13b": "llama-13b"}


def sources():
    a = load_df("arena55k")
    a = a[a.a.isin(ARENA_MAP) & a.b.isin(ARENA_MAP)].copy()
    a["a"], a["b"] = a.a.map(ARENA_MAP), a.b.map(ARENA_MAP)
    out = {"crowd (Arena)": a}
    for nm, lab in [("mtbench_human", "expert (MT-Bench)"), ("mtbench_gpt4", "GPT-4 judge (MT-Bench)")]:
        x = load_df(nm)
        x["a"], x["b"] = x.a.map(MT_MAP), x.b.map(MT_MAP)
        out[lab] = x
    for k, x in out.items():
        x["pair"] = [tuple(sorted(t)) for t in zip(x.a, x.b)]
    return out


def task(args):
    lab, seed, full = args
    src = sources()
    npair = None
    for x in src.values():
        c = x.pair.value_counts()
        npair = c if npair is None else np.minimum(npair, c.reindex(npair.index).fillna(0))
    x = src[lab]
    rng = np.random.default_rng(seed)
    if full:
        df = x
    else:
        parts = [g.iloc[rng.choice(len(g), int(npair[p]), replace=False)] for p, g in x.groupby("pair")]
        df = pd.concat(parts)
    d = Data(df)
    m = BT(d, lam=LAM)
    th, H, p = m.fit()
    r = ranking(th, d.K)
    rows = []
    for a in range(d.K):
        for b in range(a + 1, d.K):
            i, j = r[a], r[b]
            st = pair_stats(m, th, H, p, i, j)
            md = greedy(m, Target("pair", i, j), "drop", th0=th)["m"]
            rows.append(dict(source=lab, seed=seed, full=full, N=d.N, rank_i=a + 1, rank_j=b + 1,
                             item_i=d.items[i], item_j=d.items[j], **st, m_drop=md))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=50)
    ap.add_argument("--workers", type=int, default=36)
    args = ap.parse_args()
    labs = list(sources())
    tasks = [(l, s, False) for l in labs for s in range(args.seeds)] + [(l, 0, True) for l in labs]
    with Pool(args.workers) as pool:
        rows = sum(pool.map(task, tasks, chunksize=1), [])
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RES, "matched.csv"), index=False)
    top = df[df.rank_i == 1].groupby(["source", "seed", "full"]).m_drop.min().reset_index()
    print(top.groupby(["source", "full"]).m_drop.describe())


if __name__ == "__main__":
    main()
