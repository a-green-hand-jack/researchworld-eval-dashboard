"""E2c: Dirichlet-multinomial targets (counts / N_ann: lattice-valued, many exact zeros), oracle predictor.
Same protocol as E2, split conformal only; Aitchison with two zero-replacement constants. Writes results/e2c_dirmult.csv"""
import sys, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from ccp.geometry import SCORES, make_aitchison
from ccp.synth import SynthProblem
from ccp.conformal import conformal_quantile
from ccp.evalkit import SliceCoverage, MassLookup, quantile_bins

ALPHA, N_CAL, M_TEST, N_CENT, N_BINS = 0.1, 1000, 40000, 150, 10
R = 10 if "--quick" in sys.argv else 100
SC = {k: SCORES[k] for k in ("euclid", "tv", "hellinger", "chi2", "kl")}
SC["aitchison_1e-3"] = make_aitchison(1e-3)
SC["aitchison_1e-2"] = make_aitchison(1e-2)
NAMES = list(SC)


def run_task(D, N_ann, kappa, ps):
    pr = SynthProblem(D=D, family="dirmult", kappa=kappa, tau=1.5, seed=ps, n_ann=N_ann)
    rng = np.random.default_rng(1000 * ps + 17)
    _, mu_t, y_t = pr.sample(M_TEST, rng)
    St = {n: SC[n](y_t, mu_t) for n in NAMES}
    b_conf, _ = quantile_bins(mu_t.max(-1), N_BINS)
    b_min, _ = quantile_bins(np.log(mu_t.min(-1)), N_BINS)
    cc = {n: SliceCoverage(St[n], b_conf, N_BINS) for n in NAMES}
    cm = {n: SliceCoverage(St[n], b_min, N_BINS) for n in NAMES}
    cidx = rng.choice(M_TEST, N_CENT, replace=False)
    ml = {a: MassLookup(mu_t[cidx], SC, a=a, seed=ps) for a in (1.0, 0.5)}
    zero_frac = float((y_t == 0).mean())
    rows = []
    for r in range(R):
        rr = np.random.default_rng([ps, r, 21])
        _, mu_c, y_c = pr.sample(N_CAL, rr)
        for n in NAMES:
            q = conformal_quantile(SC[n](y_c, mu_c), ALPHA)
            a, b = cc[n].per_slice(q), cm[n].per_slice(q)
            rows.append(dict(D=D, N_ann=N_ann, kappa=kappa, prob=ps, rep=r, score=n, cov=cc[n].marginal(q),
                             worst_conf=np.abs(a - 0.9).max(), worst_min=np.abs(b - 0.9).max(),
                             lm1=ml[1.0].mean_log_mass(n, q)[0], lm05=ml[0.5].mean_log_mass(n, q)[0], zero_frac=zero_frac))
    return rows


if __name__ == "__main__":
    t0 = time.time()
    tasks = [(D, N, k, s) for D in (5, 10) for N in (10, 50) for k in (30, 300) for s in range(5)]
    out = Parallel(n_jobs=14)(delayed(run_task)(*t) for t in tasks)
    df = pd.DataFrame([r for rows in out for r in rows])
    df.to_csv("/work/results/e2c_dirmult%s.csv" % ("_quick" if "--quick" in sys.argv else ""), index=False)
    print("done", time.time() - t0)
