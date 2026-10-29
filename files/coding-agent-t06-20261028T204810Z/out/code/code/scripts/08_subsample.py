"""Does collecting more comparisons make a leaderboard robust?  We subsample the
Arena-140k and WebDev-10k data to a share s of the comparisons (R replicates),
and for a fixed set of target pairs (adjacent pairs among the full-data top-10)
recompute z and the deletion / flip budgets.  Output: results/subsample.parquet
"""
import os, sys
import numpy as np
import pandas as pd
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lbstab import attacks, bt
from lbstab.prep import prepare, pair_stats, LAM

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results")
SETS = ["arena140k", "webdev10k", "arena55k"]
SHARES = [0.05, 0.1, 0.25, 0.5, 1.0]
REPS = 8


def job(args):
    name, share, rep = args
    c, df = prepare(name)
    th0 = bt.fit(c, LAM)
    order0 = bt.ranking(th0, c)
    targets = [(order0[r], order0[r + 1]) for r in range(9)]
    rng = np.random.default_rng(rep * 7919 + int(share * 1000))
    if share < 1.0:
        w = rng.multivariate_hypergeometric(c.w.astype(np.int64), int(round(share * c.n))).astype(float)
        cs = c.copy(w)
    else:
        cs = c
    th = bt.fit(cs, LAM)
    rows = []
    for (i, j) in targets:
        d, sef, ses, _ = pair_stats(cs, th, i, j, LAM)
        sgn = 1 if d > 0 else -1
        a, b = (i, j) if d > 0 else (j, i)   # attack the order observed in the subsample
        row = dict(ds=name, share=share, rep=rep, i=int(i), j=int(j), N=cs.n, delta=d, z=abs(d) / ses,
                   same_order=float(sgn > 0))
        for kind in ("drop", "flip"):
            row[f"k_{kind}"] = attacks.min_budget(cs, a, b, kind, LAM, th, prune=True)["k"]
        rows.append(row)
    return rows


if __name__ == "__main__":
    jobs = [(s, sh, r) for s in SETS for sh in SHARES for r in range(REPS if sh < 1 else 1)]
    with Pool(38) as pool:
        res = pool.map(job, jobs, chunksize=1)
    out = pd.DataFrame([r for rs in res for r in rs])
    out.to_parquet(os.path.join(OUT, "subsample.parquet"))
    out["frac"] = out.k_drop / out.N
    print(out.groupby(["ds", "share"])[["z", "k_drop", "frac", "same_order"]].median())
