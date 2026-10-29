"""E1: adversarial fragility of every dataset (top-1, adjacent pairs, significant pairs).

Outputs results/e1_pairs.csv (one row per analysed pair) and results/e1_summary.csv.
"""
from common import *  # noqa
import multiprocessing as mp
import pandas as pd
from lbrobust import data as D
from lbrobust.analysis import analyze_dataset


def run(name):
    t = time.time()
    d = D.load(name)
    df, s = analyze_dataset(d)
    s["seconds"] = time.time() - t
    print(name, f"{s['seconds']:.1f}s", flush=True)
    return df, s


if __name__ == "__main__":
    names = MAIN + NBA
    with Timer("e1"):
        with mp.Pool(NPROC) as p:
            out = p.map(run, names, chunksize=1)
    pd.concat([o[0] for o in out]).to_csv(f"{RES}/e1_pairs.csv", index=False)
    pd.DataFrame([o[1] for o in out]).to_csv(f"{RES}/e1_summary.csv", index=False)
