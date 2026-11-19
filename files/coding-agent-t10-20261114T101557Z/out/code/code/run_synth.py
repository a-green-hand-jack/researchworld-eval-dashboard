"""Synthetic experiments: coverage and width of all CI methods with known truth.

Usage:
  python run_synth.py --stage dev  --reps 200 --out /work/results/synth_dev.csv
  python run_synth.py --stage main --reps 1000 --out /work/results/synth_main.csv

'dev' uses seed offset 10^6 and is used only to choose the flexible learner;
'main' uses a disjoint seed range and is the one reported in the paper.
"""
import argparse
import os
import sys
import time
from multiprocessing import Pool

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

import ppi_flex as P
import synth as S

NS = [50, 100, 200, 500, 1000]
RATIOS = [1, 4, 16]          # N / n
SEED_OFFSET = {"dev": 1_000_000, "main": 0}

METHODS = ["classical", "ppi", "ppi_pp", "sppi", "cf_hgb", "cf_linear", "cf_spline",
           "ppi_linear_X", "cf_hgb_X", "cf_linear_X", "cf_spline_X"]


def run_cell(args):
    scen, n, ratio, rep, stage = args
    N = n * ratio
    seed = SEED_OFFSET[stage] + 7919 * rep + 104729 * n + 13 * ratio + S.SCENARIOS.index(scen) * 1_000_003
    rng = np.random.default_rng(seed % (2**32))
    YL, fL, fU, XL, XU = S.sample(scen, rng, n, N)
    mu = S.truth(scen)
    use_x = S.HAS_X[scen]
    rows = []
    methods_here = [m for m in METHODS if (use_x or not m.endswith("_X"))]
    out = {}
    base = dict(
        classical=lambda: P.classical(YL),
        ppi=lambda: P.ppi(YL, fL, fU),
        ppi_pp=lambda: P.ppi_pp(YL, fL, fU),
        sppi=lambda: P.sppi(YL, fL, fU),
        cf_hgb=lambda: P.cf_ppi(YL, fL, fU, learner="hgb", seed=rep),
        cf_hgb_shallow=lambda: P.cf_ppi(YL, fL, fU, learner="hgb_shallow", seed=rep),
        cf_linear=lambda: P.cf_ppi(YL, fL, fU, learner="linear", seed=rep),
        cf_spline=lambda: P.cf_ppi(YL, fL, fU, learner="spline", seed=rep),
    )
    if use_x:
        ZL = np.column_stack([fL, XL])
        ZU = np.column_stack([fU, XU])
        base.update(dict(
            ppi_linear_X=lambda: P.ppi_linear(YL, ZL, ZU),
            cf_hgb_X=lambda: P.cf_ppi(YL, ZL, ZU, learner="hgb", seed=rep),
            cf_linear_X=lambda: P.cf_ppi(YL, ZL, ZU, learner="linear", seed=rep),
            cf_spline_X=lambda: P.cf_ppi(YL, ZL, ZU, learner="spline", seed=rep),
        ))
    for m in methods_here:
        est, var = base[m]()
        est_, lo, hi, w = P.wald(est, var)
        rows.append(dict(scenario=scen, n=n, N=N, ratio=ratio, rep=rep, method=m,
                         est=est_, lo=lo, hi=hi, width=w, truth=mu,
                         covered=int(lo <= mu <= hi)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["dev", "main"], default="dev")
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scen", nargs="*", default=S.SCENARIOS)
    ap.add_argument("--procs", type=int, default=36)
    args = ap.parse_args()

    for s in args.scen:
        S.truth(s)  # precompute truth in the parent to avoid repeated work
    cells = [(s, n, r, rep, args.stage) for s in args.scen for n in NS for r in RATIOS
             for rep in range(args.reps)]
    t0 = time.time()
    rows = []
    with Pool(args.procs) as pool:
        for i, res in enumerate(pool.imap_unordered(run_cell, cells, chunksize=4)):
            rows.extend(res)
            if (i + 1) % 2000 == 0:
                print(f"{i+1}/{len(cells)} cells, {time.time()-t0:.0f}s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print("wrote", args.out, df.shape, f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
