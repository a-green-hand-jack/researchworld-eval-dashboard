"""E5: sampling uncertainty of the fragility measures (nonparametric bootstrap over comparisons).

B bootstrap replicates of each main dataset (and B_NBA of each NBA season); the full analysis
(top-1, significant pairs, adjacent pairs) is recomputed on each replicate.
-> results/e5_bootstrap.csv
"""
from common import *  # noqa
import multiprocessing as mp
import pandas as pd
from lbrobust import data as D
from lbrobust.analysis import analyze_dataset, bootstrap_data, present_players

B = 50
B_NBA = 10


def job(spec):
    name, b = spec
    d = present_players(bootstrap_data(D.load(name), seed=777 + b))
    _, s = analyze_dataset(d, top1_cands=3, sig_cands=10)
    s.update(source=name, boot=b)
    return s


if __name__ == "__main__":
    specs = [(n, b) for n in MAIN for b in range(B)] + [(n, b) for n in NBA for b in range(B_NBA)]
    with Timer("e5"):
        with mp.Pool(NPROC) as p:
            out = p.map(job, specs, chunksize=1)
    pd.DataFrame(out).to_csv(f"{RES}/e5_bootstrap.csv", index=False)
