"""E4: how fragility scales with the number of comparisons N.

Uniform subsamples (without replacement) of Arena-55k, Arena-140k and MT-Bench-Human at
several fractions, SEEDS draws each.  -> results/e4_scaling.csv (summary rows) and
results/e4_pairs.csv (adjacent pairs).
"""
from common import *  # noqa
import multiprocessing as mp
import numpy as np
import pandas as pd
from lbrobust import data as D
from lbrobust.analysis import analyze_dataset, subsample_data, present_players

FRACS = [0.05, 0.1, 0.2, 0.5, 1.0]
SEEDS = 10


def job(spec):
    name, frac, seed = spec
    d = D.load(name)
    if frac < 1.0:
        d = present_players(subsample_data(d, frac, 1000 * seed + int(frac * 100)))
    pairs, s = analyze_dataset(d, families=("drop", "flip"), top1_cands=3, sig_cands=10)
    s.update(source=name, frac=frac, seed=seed)
    pairs["source"] = name
    pairs["frac"] = frac
    pairs["seed"] = seed
    return pairs[pairs.roles.str.contains("adjacent")], s


if __name__ == "__main__":
    specs = []
    for name in ("arena55k", "arena140k", "mt_human"):
        for frac in FRACS:
            for seed in range(SEEDS if frac < 1.0 else 1):
                specs.append((name, frac, seed))
    with Timer("e4"):
        with mp.Pool(NPROC) as p:
            out = p.map(job, specs, chunksize=1)
    pd.concat([o[0] for o in out]).to_csv(f"{RES}/e4_pairs.csv", index=False)
    pd.DataFrame([o[1] for o in out]).to_csv(f"{RES}/e4_scaling.csv", index=False)
