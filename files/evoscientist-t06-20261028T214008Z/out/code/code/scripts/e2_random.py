"""E2: random (non-adversarial) perturbation baseline.

For each dataset, kind in {drop, flip, add}, rate in RATES and SEEDS random draws, refit and
record whether the top-1 changes, Kendall tau to the original scores and the fraction of
originally-significant (z>=1.96) orderings that are reversed.  -> results/e2_random.csv
"""
from common import *  # noqa
import multiprocessing as mp
import numpy as np
import pandas as pd
from lbrobust import data as D
from lbrobust.perturb import Searcher
from lbrobust.analysis import random_perturb

RATES = [0.001, 0.003, 0.01, 0.03, 0.1]
SEEDS = 100


def run(name):
    d = D.load(name)
    S = Searcher(d)
    rows = []
    for kind in ("drop", "flip", "add"):
        for r_i, rate in enumerate(RATES):
            for s in range(SEEDS):
                seed = 10_000 * r_i + s
                o = random_perturb(d, kind, rate, seed, S=S)
                o.update(dataset=d.meta["name"], kind=kind, rate=rate, seed=seed, N=d.N,
                         m=int(round(rate * d.N)))
                rows.append(o)
    print(name, flush=True)
    return rows


if __name__ == "__main__":
    with Timer("e2"):
        with mp.Pool(NPROC) as p:
            out = p.map(run, MAIN + NBA, chunksize=1)
    pd.DataFrame([r for o in out for r in o]).to_csv(f"{RES}/e2_random.csv", index=False)
