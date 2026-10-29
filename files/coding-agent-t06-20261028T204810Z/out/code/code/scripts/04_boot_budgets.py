"""Sampling uncertainty of the headline budgets.  For each dataset we draw B
non-parametric bootstrap replicates of the comparison data, refit, and recompute
 (a) the top-1 budget = min over challengers ranked 2..6 of the budget to overtake
     the replicate's leader, and
 (b) the top-5 budget = min over (i in top-5, j ranked 6..8) of the budget for j
     to overtake i (smallest change of the top-5 set membership among near misses),
for drop / flip / inject.  Output: results/boot_budgets.parquet
"""
import os, sys
import numpy as np
import pandas as pd
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lbstab import attacks, bt
from lbstab.prep import prepare, LLM_SETS, NBA_SEASONS, LAM

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results")
B = 100
KINDS = ("drop", "flip", "inject")


def job(args):
    name, b = args
    c, _ = prepare(name)
    rng = np.random.default_rng(1000 + b)
    if b == 0:
        cb = c          # replicate 0 = original data
    else:
        w = rng.multinomial(int(c.n), c.w / c.w.sum()).astype(float)
        cb = c.copy(w)
    th = bt.fit(cb, LAM)
    order = bt.ranking(th, cb)
    ce = attacks.extend_for_injection(cb)
    out = dict(ds=name, b=b, n=cb.n)
    for kind in KINDS:
        cc = ce if kind == "inject" else cb
        top1 = min(attacks.min_budget(cc, order[0], order[r], kind, LAM, th, prune=True)["k"]
                   for r in range(1, min(6, cb.m)))
        out[f"top1_{kind}"] = top1
        if cb.m >= 8:
            top5 = min(attacks.min_budget(cc, order[a], order[r], kind, LAM, th, prune=True)["k"]
                       for a in range(5) for r in range(5, 8))
            out[f"top5_{kind}"] = top5
    out["top1_z"] = None
    from lbstab.prep import pair_stats
    d, sef, ses, _ = pair_stats(cb, th, order[0], order[1], LAM)
    out["top1_z"] = d / ses
    return out


if __name__ == "__main__":
    names = sys.argv[1:] or (LLM_SETS + ["nba2015", "nba2005", "nba1995"])
    jobs = [(nm, b) for nm in names for b in range(B + 1)]
    with Pool(38) as pool:
        rows = pool.map(job, jobs, chunksize=1)
    pd.DataFrame(rows).to_parquet(os.path.join(OUT, "boot_budgets.parquet"))
