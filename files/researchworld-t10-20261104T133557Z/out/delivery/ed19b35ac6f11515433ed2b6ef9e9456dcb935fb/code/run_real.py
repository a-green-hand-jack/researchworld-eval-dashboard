"""Coverage / width of mean-CIs on the ppi-python datasets, resampling from the empirical pool.

usage: run_real.py DATASET N_LAB REPS SEED OUT.csv [NU_MAX [NPROC [LEARNERS_COMMA_SEP]]]
Population = empirical distribution of the (Y, Yhat[, X]) pool; truth = pool mean of Y.
Each replicate draws n labeled and N unlabeled iid (with replacement) from the pool.
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import os, sys, time
from functools import lru_cache
import numpy as np, pandas as pd
from multiprocessing import Pool
from civ import all_intervals

DATA = "/hutian/data/"


@lru_cache(maxsize=None)
def load(name):
    d = np.load(DATA + name + ".npz")
    Y, F = d["Y"].astype(float), d["Yhat"].astype(float)
    X = d["X"].astype(float) if "X" in d else None
    return Y, F, X


def one(args):
    name, n, N, seed, learners = args
    Y, F, X = load(name)
    rng = np.random.default_rng(seed)
    il = rng.integers(0, len(Y), n)
    iu = rng.integers(0, len(Y), N)
    xl = None if X is None else X[il]
    xu = None if X is None else X[iu]
    res = all_intervals(Y[il], F[il], xl, F[iu], xu, learners, rng=rng, boot=bool(int(os.environ.get('BOOT', '0'))))
    truth = Y.mean()
    row = {"seed": seed}
    for k, (th, hw) in res.items():
        if k.startswith("_"):
            row[k] = th
        else:
            row[k + "_cov"] = float(abs(th - truth) <= hw)
            row[k + "_w"] = 2 * hw
            row[k + "_est"] = th
    return row


if __name__ == "__main__":
    name, n, reps, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    numax = int(sys.argv[6]) if len(sys.argv) > 6 else 20000
    Y, F, X = load(name)
    N = min(len(Y), numax)
    if len(sys.argv) > 8:
        learners = [l for l in sys.argv[8].split(",") if l]
    else:
        learners = ["lin_f", "iso_f", "poly_f", "gbm_f"] + (["lin_fX", "gbm_fX"] if X is not None else [])
    t0 = time.time()
    jobs = [(name, n, N, seed * 1_000_003 + r, learners) for r in range(reps)]
    with Pool(int(sys.argv[7]) if len(sys.argv) > 7 else 2) as p:
        rows = p.map(one, jobs, chunksize=max(1, reps // 40))
    df = pd.DataFrame(rows)
    df.insert(0, "n", n); df.insert(0, "dataset", name); df["N"] = N; df["truth"] = Y.mean()
    df.to_csv(out, index=False)
    print(name, n, N, "reps", reps, "time %.1fs" % (time.time() - t0), flush=True)
