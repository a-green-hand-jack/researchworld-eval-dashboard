"""Semi-synthetic stress test: the same real (Y, Yhat) pools, but the predictor's *output scale* is changed by a
fixed monotone map T (the predictor itself is still fixed; only its reported score is on a different scale).
  rank : T(f) = rank(f)/(pool+1)      (uniformised score; calibration lost)
  expz : T(f) = exp((f-mean)/sd)      (exponential score scale)
Usage: python run_distort.py [reps]; output results/distort_summary.csv"""
import sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PYTHONPATH'] = HERE + os.pathsep + os.environ.get('PYTHONPATH', '')
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from joblib import Parallel, delayed
from common import run_reps, summarize, asym_variances, theory_ratio
from real_lib import load, cached_oracle, theory_real

DS = ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare", "census_education"]
NAMES = ["classical", "ppi++", "ppi++_own", "ppi++_own_t", "spline3", "spline4", "spline4_t", "spline6", "cf_iso"]


def transform(F, kind):
    if kind == "rank":
        return rankdata(F) / (len(F) + 1.0)
    if kind == "expz":
        return np.exp((F - F.mean()) / F.std())
    return F


def config(cid, ds, kind, n, N, R):
    Y, F, _ = load(ds)
    F = transform(F, kind)
    truth = Y.mean()
    seed = int(np.random.SeedSequence([20261115, cid]).generate_state(1)[0])

    def draw(rng):
        iL, iU = rng.integers(0, len(Y), n), rng.integers(0, len(Y), N)
        return Y[iL], F[iL], F[iU]
    th, se = run_reps(draw, truth, R, seed, names=NAMES)
    rows = summarize(th, se, truth)
    tr = theory_ratio(theory_real(Y, F, n, N, cached_oracle(ds)))
    for r in rows:
        r.update(dataset=ds, transform=kind, n=n, N=N, theory_ratio=tr.get(r["method"], np.nan), theory_ratio_eff=tr["efficient"])
    return rows


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    cfgs = [(ds, k, n) for ds in DS for k in ("rank", "expz") for n in (200, 1000)]
    t0 = time.time()
    out = Parallel(n_jobs=28)(delayed(config)(i, ds, k, n, 10000, R) for i, (ds, k, n) in enumerate(cfgs))
    pd.DataFrame([r for rows in out for r in rows]).to_csv(os.path.join(HERE, "..", "results", "distort_summary.csv"), index=False)
    print("done %.0fs" % (time.time() - t0))
