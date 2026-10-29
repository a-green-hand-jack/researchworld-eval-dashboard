"""Ablations of modelling choices: tie handling, entity filter, ridge strength,
and the aggregation rule's sensitivity measured on adjacent pairs.
For every variant: all adjacent pairs of the leaderboard, budgets for drop and
flip, plus z and n_h.  Output: results/ablations.parquet
"""
import os, sys
import numpy as np
import pandas as pd
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lbstab import attacks, bt, data
from lbstab.bt import cells_from_frame
from lbstab.prep import filter_entities, pair_stats

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results")
SETS = ["arena55k", "arena140k", "webdev10k", "mtbench_human", "mtbench_gpt4", "arenaST_human",
        "arenaST_Athene-70B", "nba2015", "nba2005"]
VARIANTS = {
    "base": dict(ties="half", min_n=100, lam=1e-2),
    "ties_dropped": dict(ties="drop", min_n=100, lam=1e-2),
    "no_filter": dict(ties="half", min_n=0, lam=1e-2),
    "filter500": dict(ties="half", min_n=500, lam=1e-2),
    "ridge1": dict(ties="half", min_n=100, lam=1.0),
}


def job(args):
    name, vname = args
    v = VARIANTS[vname]
    df, names, home = data.load(name)
    if v["ties"] == "drop":
        df = df[df.y != 0.5]
    min_n = 0 if name.startswith("nba") else v["min_n"]
    if min_n > 0:
        df, names = filter_entities(df, names, min_n)
    else:
        df, names = filter_entities(df, names, 1)
    c = cells_from_frame(df, names, home=home)
    lam = v["lam"]
    th = bt.fit(c, lam)
    order = bt.ranking(th, c)
    cnt = pd.concat([df.a, df.b]).value_counts().reindex(range(c.m)).fillna(0).values
    rows = []
    for r in range(c.m - 1):
        i, j = order[r], order[r + 1]
        d, sef, ses, _ = pair_stats(c, th, i, j, lam)
        row = dict(ds=name, variant=vname, rank_i=r, delta=d, z=d / ses, n_i=cnt[i], n_j=cnt[j], n=c.n, m=c.m,
                   name_i=names[i], name_j=names[j])
        for kind in ("drop", "flip"):
            row[f"k_{kind}"] = attacks.min_budget(c, i, j, kind, lam, th, prune=True)["k"]
        rows.append(row)
    return rows


if __name__ == "__main__":
    jobs = [(s, v) for s in SETS for v in VARIANTS if not (s.startswith("nba") and v in ("no_filter", "filter500"))]
    with Pool(38) as pool:
        res = pool.map(job, jobs, chunksize=1)
    out = pd.DataFrame([r for rs in res for r in rs])
    out.to_parquet(os.path.join(OUT, "ablations.parquet"))
    out["nh"] = out.n_i * out.n_j / (out.n_i + out.n_j)
    out["C"] = out.k_drop / (out.z * np.sqrt(out.nh))
    print(out[out.z > 0.5].groupby(["ds", "variant"]).agg(m=("m", "first"), n=("n", "first"), C=("C", "median"),
                                                          kd=("k_drop", "median"), z=("z", "median")))
