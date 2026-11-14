"""Experiment A (real pools) : repeated-sampling coverage / width for the mean of Y.

Scheme 'iid'  : n labeled + N unlabeled drawn i.i.d. (with replacement) from the pool; target = pool mean
                (superpopulation target; the pool plays the role of the data-generating distribution).
Scheme 'fpop' : M=n+N units drawn WITHOUT replacement from the pool; n of them labeled (SRS);
                target = mean of Y over the M units (finite-population / census target).
Two method groups (same seeds => same sampled data for rep r in both groups, so results are paired):
  cheap : analytic / light estimators, many reps
  exp   : ppi-python reference call, gradient-boosting cross-fitting (slow), fewer reps
Usage: python code/run_real.py <scheme> <group> <reps> [dataset ...]
Output: results/real_<scheme>_<group>.csv.gz (one row per rep x method)
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
import sys, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
sys.path.insert(0, "code")
from ppi_lib import run_all

DS = ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare", "census_education"]
SEED = 20261102
GROUPS = {
    "cheap": ["classical", "ppi", "ppi++", "poly2", "poly3", "strat5", "strat10", "spline", "iso_cf", "hgb_cf_SKIP",
              "FP-classical", "FP-f", "FP-poly2", "FP-strat5", "FP-spline", "FP-iso_cf"],
    "exp": ["ppi++py", "hgb_cf", "hgbX_cf"],
}
GROUPS["cheap"] = [m for m in GROUPS["cheap"] if not m.endswith("SKIP")]


def load(ds):
    d = np.load(f"data/{ds}.npz")
    Y, f = d["Y"].astype(float), d["Yhat"].astype(float)
    F = f[:, None]
    if "X" in d.files:
        X = d["X"].astype(float)
        X = X[:, [j for j in range(X.shape[1]) if len(np.unique(X[:, j])) > 1]]
        F = np.column_stack([f, X])
    return Y, F


def one_rep(ds, scheme, group, n, N, rep, Y, F):
    ss = np.random.SeedSequence([SEED, DS.index(ds), 0 if scheme == "iid" else 1, n, N, rep])
    rng = np.random.default_rng(ss)
    P = len(Y)
    if scheme == "iid":
        idx = rng.integers(0, P, n + N)
        truth = Y.mean()
    else:
        idx = rng.choice(P, n + N, replace=False)
        truth = Y[idx].mean()
    L, U = idx[:n], idx[n:]
    res = run_all(Y[L], F[L], F[U], rng, methods=GROUPS[group])
    return [dict(dataset=ds, scheme=scheme, n=n, N=N, rep=rep, method=m, theta=t, sd=s, p=p, truth=truth)
            for m, (t, s, p) in res.items()]


def main():
    scheme, group, reps = sys.argv[1], sys.argv[2], int(sys.argv[3])
    dss = sys.argv[4:] or DS
    rows = []
    t0 = time.time()
    with Parallel(n_jobs=8, batch_size=4) as par:
        for ds in dss:
            Y, F = load(ds)
            if scheme == "iid":
                grid = [(n, 10000) for n in (50, 100, 200, 500, 1000, 2000)]
            else:  # finite population: M fixed = 5000 (or pool/2 if smaller)
                M = min(5000, len(Y) // 2)
                grid = [(int(round(fr * M)), M - int(round(fr * M))) for fr in (0.02, 0.05, 0.1, 0.2, 0.4)]
            for n, N in grid:
                out = par(delayed(one_rep)(ds, scheme, group, n, N, r, Y, F) for r in range(reps))
                rows += [r for o in out for r in o]
                print(f"{ds} {scheme} {group} n={n} N={N} done  t={time.time()-t0:.0f}s", flush=True)
            pd.DataFrame(rows).to_csv(f"results/real_{scheme}_{group}.csv.gz", index=False)


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    main()
