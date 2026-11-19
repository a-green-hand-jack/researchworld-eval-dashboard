"""Matched-N control: MT-Bench (human / GPT-4 judge) subsampled to the number of votes available among the six
matched Arena models (1,367), 30 repetitions each -> results/matched_sub.csv. Run: python code/run_matched_sub.py"""
import os
import numpy as np, pandas as pd
from multiprocessing import Pool
from data import *
from common import *
from run_rankshift_scaling import matched

NTARGET = None


def job(args):
    u, rep, ntarget = args
    ds = {"mt_human": load_mt_human, "mt_gpt4": load_mt_gpt4}[u]()
    rng = np.random.default_rng([99, rep, sum(map(ord, u))])
    cells = subsample_cells(ds, ntarget / len(ds["y"]), rng)
    rows, th, order = pair_table(cells, rng, B=50, modes=("remove", "relabel"), dmax=1)
    for r in rows:
        r["unit"] = u; r["rep"] = rep
    return rows


if __name__ == "__main__":
    nt = len(matched()["y"])
    with Pool(20) as p:
        rows = [r for o in p.map(job, [(u, r, nt) for u in ("mt_human", "mt_gpt4") for r in range(30)]) for r in o]
    pd.DataFrame(rows).to_csv(os.path.join(RES, "matched_sub.csv"), index=False)
    print(len(rows), nt)
