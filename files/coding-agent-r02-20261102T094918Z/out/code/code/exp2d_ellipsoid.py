"""E2d: ellipsoidal baseline (global-covariance Mahalanobis score in ilr coordinates, fitted on 2000 separate points)
vs. the isotropic scores, oracle predictor, same protocol as E2 (subset of cells).  Writes results/e2d_ellipsoid.csv"""
import sys, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from ccp.geometry import SCORES, fit_mahal_ilr
from ccp.synth import SynthProblem
from ccp.conformal import conformal_quantile
from ccp.evalkit import SliceCoverage, MassLookup, quantile_bins

ALPHA, N_CAL, M_TEST, N_CENT, NB = 0.1, 1000, 40000, 150, 10
R = 10 if "--quick" in sys.argv else 100


def run(fam, D, kappa, ps):
    pr = SynthProblem(D=D, family=fam, kappa=kappa, tau=1.5, seed=ps, mu_floor=0.3 if fam == "additive" else 0.0)
    rng = np.random.default_rng(1000 * ps + 7)
    _, mu_t, y_t = pr.sample(M_TEST, rng)
    _, mu_f, y_f = pr.sample(2000, np.random.default_rng(4242 + ps))     # separate fit set for the covariance
    SC = dict(SCORES)
    SC["mahal_ilr"] = fit_mahal_ilr(y_f, mu_f, 1e-6)
    names = list(SC)
    St = {n: SC[n](y_t, mu_t) for n in names}
    b_conf, _ = quantile_bins(mu_t.max(-1), NB)
    b_min, _ = quantile_bins(np.log(mu_t.min(-1)), NB)
    cc = {n: SliceCoverage(St[n], b_conf, NB) for n in names}
    cm = {n: SliceCoverage(St[n], b_min, NB) for n in names}
    cidx = rng.choice(M_TEST, N_CENT, replace=False)
    ml = MassLookup(mu_t[cidx], SC, a=1.0, seed=ps)
    rows = []
    for r in range(R):
        rr = np.random.default_rng([ps, r, 99])
        _, mu_c, y_c = pr.sample(N_CAL, rr)
        for n in names:
            q = conformal_quantile(SC[n](y_c, mu_c), ALPHA)
            a, b = cc[n].per_slice(q), cm[n].per_slice(q)
            rows.append(dict(family=fam, D=D, kappa=kappa, prob=ps, rep=r, score=n, cov=cc[n].marginal(q),
                             G=max(np.abs(a - 0.9).max(), np.abs(b - 0.9).max()), lm1=ml.mean_log_mass(n, q)[0]))
    return rows


if __name__ == "__main__":
    t0 = time.time()
    tasks = [(f, D, k, s) for f in ("dirichlet", "logistic_normal", "additive") for D in (5, 10) for k in (100, 300) for s in range(5)]
    out = Parallel(n_jobs=14)(delayed(run)(*t) for t in tasks)
    df = pd.DataFrame([r for rows in out for r in rows])
    df.to_csv("/work/results/e2d_ellipsoid%s.csv" % ("_quick" if "--quick" in sys.argv else ""), index=False)
    print("done", time.time() - t0)
