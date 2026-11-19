"""plankton / ballots protocols (binary Yhat).

usage: run_special.py CASE N_LAB REPS SEED OUT.csv [NPROC]
CASE:
  plankton_noshift : labeled and unlabeled iid (with replacement) from the 2013 pool, N=10000; truth = 2013 mean of Y.
  plankton_shift   : labeled iid from the 2013 pool, unlabeled (Yhat only) iid from the 2014 pool, N=10000;
                     truth = mean of Y_unlabeled (2014).  Stress test: labeled/unlabeled are NOT exchangeable.
  ballots_sub      : the 1027 labeled ballots; n labeled drawn without replacement, the remaining 1027-n are the unlabeled
                     (Y hidden); truth = mean of all 1027 Y.
  ballots_width    : n labeled drawn without replacement from the 1027, unlabeled = the 78,150 Yhat_unlabeled (no Y exist):
                     only widths are meaningful; "coverage" columns are w.r.t. the 1027-ballot mean and must not be read.
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import os, sys, time, warnings, numpy as np, pandas as pd
from multiprocessing import Pool
from civ import all_intervals
warnings.filterwarnings("ignore")
def _load(p):
    with np.load(p) as z: return {k: z[k] for k in z.files}  # materialise: a lazy NpzFile shared by forked workers corrupts reads


PL, BA = _load("/hutian/data/plankton.npz"), _load("/hutian/data/ballots.npz")


def one(a):
    case, n, seed = a
    rng = np.random.default_rng(seed)
    if case.startswith("plankton"):
        N = 10000
        il = rng.integers(0, len(PL["Y"]), n)
        yl, fl = PL["Y"][il].astype(float), PL["Yhat"][il].astype(float)
        if case == "plankton_noshift":
            iu = rng.integers(0, len(PL["Y"]), N); fu = PL["Yhat"][iu].astype(float); truth = PL["Y"].mean()
        else:
            iu = rng.integers(0, len(PL["Y_unlabeled"]), N); fu = PL["Yhat_unlabeled"][iu].astype(float); truth = PL["Y_unlabeled"].mean()
    else:
        Y, F = BA["Y"].astype(float), BA["Yhat"].astype(float)
        perm = rng.permutation(len(Y)); il = perm[:n]
        yl, fl = Y[il], F[il]; truth = Y.mean()
        fu = F[perm[n:]] if case == "ballots_sub" else BA["Yhat_unlabeled"].astype(float)
    res = all_intervals(yl, fl, None, fu, None, ["lin_f", "iso_f"], rng=rng, boot=True)
    row = {"seed": seed}
    for k, (th, hw) in res.items():
        if k.startswith("_"): row[k] = th
        else: row[k + "_cov"] = float(abs(th - truth) <= hw); row[k + "_w"] = 2 * hw; row[k + "_est"] = th
    return row


if __name__ == "__main__":
    case, n, reps, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    nproc = int(sys.argv[6]) if len(sys.argv) > 6 else 2
    t0 = time.time()
    with Pool(nproc) as p: rows = p.map(one, [(case, n, seed * 1_000_003 + r) for r in range(reps)], chunksize=max(1, reps // 40))
    df = pd.DataFrame(rows); df.insert(0, "n", n); df.insert(0, "dataset", case)
    df["N"] = 10000 if case.startswith("plankton") else (1027 - n if case == "ballots_sub" else len(BA["Yhat_unlabeled"]))
    df.to_csv(out, index=False); print(case, n, "reps", reps, "%.1fs" % (time.time() - t0), flush=True)
