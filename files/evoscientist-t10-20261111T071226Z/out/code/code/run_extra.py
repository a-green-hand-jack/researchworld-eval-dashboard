"""Extra experiments: (a) distribution shift (plankton 2013 labeled / 2014 unlabeled),
(b) deployment-style intervals on ballots with the real labeled/unlabeled split,
(c) extension with covariates X on census datasets.
Usage: python run_extra.py [reps]; outputs results/shift_summary.csv, results/ballots_deploy.csv, results/ext_x_summary.csv"""
import sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PYTHONPATH'] = HERE + os.pathsep + os.environ.get('PYTHONPATH', '')
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from methods import run_all, METHODS, RNG_METHODS, cf_gbm_ppi, Z95
from common import run_reps, summarize
from real_lib import load, oracle_cond_moments, DATA

RES = os.path.join(HERE, "..", "results")


def shift_config(cid, n, N, R, shifted):
    d = np.load(os.path.join(DATA, "plankton.npz"))
    Y, F, Fu, Yu = d["Y"], d["Yhat"], d["Yhat_unlabeled"], d["Y_unlabeled"]
    truth = Yu.mean() if shifted else Y.mean()
    pool_u = Fu if shifted else F

    def draw(rng):
        iL = rng.integers(0, len(Y), n)
        iU = rng.integers(0, len(pool_u), N)
        return Y[iL], F[iL], pool_u[iU]
    seed = int(np.random.SeedSequence([20261113, cid]).generate_state(1)[0])
    th, se = run_reps(draw, truth, R, seed)
    rows = summarize(th, se, truth)
    for r in rows:
        r.update(setting="shift(2013->2014)" if shifted else "no-shift control(2013)", n=n, N=N, truth=truth)
    return rows


def ext_x_config(cid, name, n, N, R):
    Y, F, X = load(name)
    truth = Y.mean()
    seed = int(np.random.SeedSequence([20261114, cid]).generate_state(1)[0])
    rng = np.random.default_rng(seed)
    th, se = {}, {}
    for _ in range(R):
        iL, iU = rng.integers(0, len(Y), n), rng.integers(0, len(Y), N)
        res = run_all(Y[iL], F[iL], F[iU], rng, names=["classical", "ppi++", "ppi++_own", "spline4", "cf_iso"])
        res["cf_gbm_fX"] = cf_gbm_ppi(Y[iL], F[iL], F[iU], X[iL], X[iU], rng=rng)
        for m, (t, s) in res.items():
            th.setdefault(m, []).append(float(np.squeeze(t)))
            se.setdefault(m, []).append(float(np.squeeze(s)))
    th = {m: np.array(v) for m, v in th.items()}
    se = {m: np.array(v) for m, v in se.items()}
    rows = summarize(th, se, truth)
    for r in rows:
        r.update(dataset=name, n=n, N=N)
    return rows


def oracle_x(name):
    Y, F, X = load(name)
    g_f = np.load(os.path.join(DATA, f"oracle_{name}.npy"))
    g_fx = oracle_cond_moments(Y, F, X)
    ev_f, ev_fx = np.mean((Y - g_f) ** 2), np.mean((Y - g_fx) ** 2)
    return dict(dataset=name, varY=Y.var(), EV_f=ev_f, EV_fX=ev_fx)


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    t0 = time.time()
    # (a) shift
    cfgs = [(i, n, 10000, shifted) for i, (n, shifted) in enumerate([(n, s) for s in (True, False) for n in (200, 1000)])]
    out = Parallel(n_jobs=4)(delayed(shift_config)(i, n, N, R, s) for i, n, N, s in cfgs)
    pd.DataFrame([r for rows in out for r in rows]).to_csv(os.path.join(RES, "shift_summary.csv"), index=False)
    print("shift done %.0fs" % (time.time() - t0), flush=True)
    # (b) ballots deployment (real split, no ground truth available for the unlabeled part)
    d = np.load(os.path.join(DATA, "ballots.npz"))
    Y, F, Fu = d["Y"].astype(float), d["Yhat"].astype(float), d["Yhat_unlabeled"].astype(float)
    rng = np.random.default_rng(0)
    rows = []
    for nm, (t, s) in run_all(Y, F, Fu, rng).items():
        rows.append(dict(method=nm, estimate=float(np.squeeze(t)), lo=float(np.squeeze(t - Z95 * s)),
                         hi=float(np.squeeze(t + Z95 * s)), width=float(np.squeeze(2 * Z95 * s))))
    pd.DataFrame(rows).to_csv(os.path.join(RES, "ballots_deploy.csv"), index=False)
    # (c) extension with covariates
    ex = Parallel(n_jobs=3)(delayed(oracle_x)(nm) for nm in ("census_income", "census_healthcare", "census_education"))
    pd.DataFrame(ex).to_csv(os.path.join(RES, "ext_x_oracle.csv"), index=False)
    print("oracle-x done %.0fs" % (time.time() - t0), flush=True)
    cfgs = [(nm, n) for nm in ("census_income", "census_healthcare", "census_education") for n in (200, 1000, 2000)]
    Rx = max(R // 4, 200)
    out = Parallel(n_jobs=9)(delayed(ext_x_config)(i, nm, n, 10000, Rx) for i, (nm, n) in enumerate(cfgs))
    pd.DataFrame([r for rows in out for r in rows]).to_csv(os.path.join(RES, "ext_x_summary.csv"), index=False)
    print("all done %.0fs" % (time.time() - t0))
