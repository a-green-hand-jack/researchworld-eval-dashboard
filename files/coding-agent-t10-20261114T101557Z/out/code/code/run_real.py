"""Real-data experiments on the PPI example pools (ppi-python v0.2.3 datasets).

Each pool (Y, Yhat[, covariates]) is treated as the finite population.  Labeled and unlabeled
samples are drawn i.i.d. WITH replacement from the pool (independently), so the sampling model
is exactly the i.i.d. model of the paper and the target is the pool mean of Y.

Usage:
  python run_real.py --stage dev  --reps 200  --out /work/results/real_dev.csv
  python run_real.py --stage main --reps 1000 --out /work/results/real_main.csv
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

NS = [50, 100, 200, 500, 1000]
RATIOS = [1, 4, 16]
SEED_OFFSET = {"dev": 1_000_000, "main": 0}

# (dataset, regime) pairs; regime 'f' uses only the prediction, 'fX' also uses covariates
CONFIGS = [
    ("galaxies", "f"),
    ("forest", "f"),
    ("gene_expression", "f"),
    ("alphafold", "f"),
    ("alphafold", "fX"),
    ("census_income", "f"),
    ("census_income", "fX"),
    ("census_healthcare", "f"),
    ("census_healthcare", "fX"),
    ("census_education", "f"),
    ("census_education", "fX"),
]

METHODS_F = ["classical", "ppi", "ppi_pp", "sppi", "cf_hgb", "cf_linear", "cf_spline"]
METHODS_FX = ["ppi_linear_X", "cf_hgb_X", "cf_linear_X", "cf_spline_X"]

_POOL = {}


def get_pool(name, regime):
    key = (name, regime)
    if key not in _POOL:
        Y, f, X = P.load_real(name, "fX" if regime == "fX" else "f")
        _POOL[key] = (Y, f, X)
    return _POOL[key]


def run_cell(args):
    cfg_idx, n, ratio, rep, stage = args
    name, regime = CONFIGS[cfg_idx]
    N = n * ratio
    Y, f, X = get_pool(name, regime)
    M = len(Y)
    rng = np.random.default_rng([SEED_OFFSET[stage], cfg_idx, n, ratio, rep])
    iL = rng.integers(0, M, size=n)
    iU = rng.integers(0, M, size=N)
    YL, fL = Y[iL], f[iL]
    fU = f[iU]
    if regime == "fX":
        XL, XU = X[iL], X[iU]
        ZL = np.column_stack([fL, XL])
        ZU = np.column_stack([fU, XU])
    mu = Y.mean()
    methods = METHODS_F + (METHODS_FX if regime == "fX" else [])
    calls = dict(
        classical=lambda: P.classical(YL),
        ppi=lambda: P.ppi(YL, fL, fU),
        ppi_pp=lambda: P.ppi_pp(YL, fL, fU),
        sppi=lambda: P.sppi(YL, fL, fU),
        cf_hgb=lambda: P.cf_ppi(YL, fL, fU, learner="hgb", seed=rep),
        cf_linear=lambda: P.cf_ppi(YL, fL, fU, learner="linear", seed=rep),
        cf_spline=lambda: P.cf_ppi(YL, fL, fU, learner="spline", seed=rep),
    )
    if regime == "fX":
        calls.update(dict(
            ppi_linear_X=lambda: P.ppi_linear(YL, ZL, ZU),
            cf_hgb_X=lambda: P.cf_ppi(YL, ZL, ZU, learner="hgb", seed=rep),
            cf_linear_X=lambda: P.cf_ppi(YL, ZL, ZU, learner="linear", seed=rep),
            cf_spline_X=lambda: P.cf_ppi(YL, ZL, ZU, learner="spline", seed=rep),
        ))
    rows = []
    for m in methods:
        t0 = time.perf_counter()
        est, var = calls[m]()
        dt = time.perf_counter() - t0
        e, lo, hi, w = P.wald(est, var)
        rows.append(dict(dataset=name, regime=regime, n=n, N=N, ratio=ratio, rep=rep, method=m,
                         est=e, lo=lo, hi=hi, width=w, truth=mu, covered=int(lo <= mu <= hi),
                         seconds=dt))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["dev", "main"], default="dev")
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=36)
    ap.add_argument("--configs", nargs="*", type=int, default=None)
    ap.add_argument("--ns", nargs="*", type=int, default=None)
    ap.add_argument("--ratios", nargs="*", type=int, default=None)
    args = ap.parse_args()
    ns = NS if args.ns is None else args.ns
    ratios = RATIOS if args.ratios is None else args.ratios

    cfg_ids = list(range(len(CONFIGS))) if args.configs is None else args.configs
    for i in cfg_ids:  # load pools in parent so forked workers share them
        get_pool(*CONFIGS[i])
    cells = [(i, n, r, rep, args.stage) for i in cfg_ids for n in ns for r in ratios
             for rep in range(args.reps)]
    t0 = time.time()
    rows = []
    with Pool(args.procs) as pool:
        for k, res in enumerate(pool.imap_unordered(run_cell, cells, chunksize=8)):
            rows.extend(res)
            if (k + 1) % 5000 == 0:
                print(f"{k+1}/{len(cells)} cells, {time.time()-t0:.0f}s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print("wrote", args.out, df.shape, f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
