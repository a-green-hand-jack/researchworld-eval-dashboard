"""OLS-coefficient CI coverage/width on census_* datasets (population = empirical pool, iid resampling).

usage: run_ols.py DATASET N_LAB REPS SEED OUT.csv [NU_MAX [NPROC]]
Regression of Y on the columns of X as supplied in the ppi-python data (no intercept added), truth =
OLS on the whole pool.  Columns: <method>_c<j>_{cov,w}.
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys, time, warnings
import numpy as np, pandas as pd
from multiprocessing import Pool
import ppi_py
from run_real import load
from civ_ols import ols_intervals, Z

warnings.filterwarnings("ignore")


def one(a):
    name, n, N, seed = a
    Y, F, X = load(name)
    truth = np.linalg.lstsq(X, Y, rcond=None)[0]
    rng = np.random.default_rng(seed)
    il, iu = rng.integers(0, len(Y), n), rng.integers(0, len(Y), N)
    out = ols_intervals(X[il], Y[il], F[il], X[iu], F[iu], rng=rng)
    lo, hi = ppi_py.ppi_ols_ci(X[il], Y[il], F[il], X[iu], F[iu], alpha=0.05)
    out["ppi++_lib"] = ((lo + hi) / 2, (hi - lo) / 2)
    lo, hi = ppi_py.ppi_ols_ci(X[il], Y[il], F[il], X[iu], F[iu], alpha=0.05, lam=1)
    out["ppi_lib"] = ((lo + hi) / 2, (hi - lo) / 2)
    row = {"seed": seed}
    for k, (th, hw) in out.items():
        for j in range(len(truth)):
            row[f"{k}_c{j}_cov"] = float(abs(th[j] - truth[j]) <= hw[j]); row[f"{k}_c{j}_w"] = 2 * hw[j]
    return row


if __name__ == "__main__":
    name, n, reps, seed, outf = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    numax = int(sys.argv[6]) if len(sys.argv) > 6 else 20000
    nproc = int(sys.argv[7]) if len(sys.argv) > 7 else 2
    Y, F, X = load(name); N = min(len(Y), numax); t0 = time.time()
    with Pool(nproc) as p: rows = p.map(one, [(name, n, N, seed * 1_000_003 + r) for r in range(reps)], chunksize=max(1, reps // 40))
    df = pd.DataFrame(rows); df.insert(0, "n", n); df.insert(0, "dataset", name); df["N"] = N
    for j, t in enumerate(np.linalg.lstsq(X, Y, rcond=None)[0]): df[f"truth_c{j}"] = t
    df.to_csv(outf, index=False); print(name, n, N, "reps", reps, "%.1fs" % (time.time() - t0), flush=True)
