"""E3b: predictor misfit.  Targets: Dirichlet-multinomial (N_ann=50, kappa=100) around mu(x); predictor
yhat(x) = softmax((log mu(x) + s * h(x)) / T), h a fixed random smooth function (unit-variance logit error), T<1 = over-confident.
Slices use yhat (what the user observes).  Writes results/e3b_misfit.csv"""
import sys, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from ccp.geometry import SCORES, softmax, make_aitchison
from ccp.synth import SynthProblem
from ccp.conformal import conformal_quantile
from ccp.evalkit import SliceCoverage, MassLookup, quantile_bins

ALPHA, N_CAL, M_TEST, N_CENT, NB = 0.1, 1000, 40000, 150, 10
R = 10 if "--quick" in sys.argv else 100
SC = {k: SCORES[k] for k in ("euclid", "tv", "hellinger", "chi2", "kl")}
SC["aitchison_1e-2"] = make_aitchison(1e-2)
NAMES = list(SC)


def run(D, s_err, T, ps):
    pr = SynthProblem(D=D, family="dirmult", kappa=100, tau=1.5, seed=ps, n_ann=50)
    rg = np.random.default_rng(555 + ps)
    C2 = rg.normal(size=(pr.p, pr.p)) / np.sqrt(pr.p); B2 = rg.normal(size=(pr.p, D)) / np.sqrt(pr.p)
    def predict(X, mu):
        h = np.sin(X @ C2) @ B2
        h = h / 0.7                      # ~unit variance
        return softmax((np.log(mu) + s_err * h) / T)
    rng = np.random.default_rng(900 + ps)
    Xt, mu_t, y_t = pr.sample(M_TEST, rng); P_t = predict(Xt, mu_t)
    St = {n: SC[n](y_t, P_t) for n in NAMES}
    b_conf, _ = quantile_bins(P_t.max(-1), NB)
    b_min, _ = quantile_bins(np.log(np.maximum(P_t.min(-1), 1e-12)), NB)
    cc = {n: SliceCoverage(St[n], b_conf, NB) for n in NAMES}
    cm = {n: SliceCoverage(St[n], b_min, NB) for n in NAMES}
    cidx = rng.choice(M_TEST, N_CENT, replace=False)
    ml = MassLookup(P_t[cidx], SC, a=1.0, seed=ps)
    rows = []
    for r in range(R):
        rr = np.random.default_rng([ps, r, 33])
        Xc, mu_c, y_c = pr.sample(N_CAL, rr); P_c = predict(Xc, mu_c)
        for n in NAMES:
            q = conformal_quantile(SC[n](y_c, P_c), ALPHA)
            a, b = cc[n].per_slice(q), cm[n].per_slice(q)
            rows.append(dict(D=D, s_err=s_err, T=T, prob=ps, rep=r, score=n, cov=cc[n].marginal(q), G_conf=np.abs(a - 0.9).max(),
                             G_min=np.abs(b - 0.9).max(), min_conf=a.min(), cov_dec1=a[0], lm1=ml.mean_log_mass(n, q)[0],
                             kl_pred=float((mu_t * (np.log(mu_t) - np.log(np.maximum(P_t, 1e-12)))).sum(-1).mean())))
    return rows


if __name__ == "__main__":
    t0 = time.time()
    tasks = [(10, s, T, ps) for (s, T) in ((0.0, 1.0), (1.0, 1.0), (1.0, 0.5), (2.0, 0.5)) for ps in range(5)]
    out = Parallel(n_jobs=14)(delayed(run)(*t) for t in tasks)
    df = pd.DataFrame([r for rows in out for r in rows])
    df.to_csv("/work/results/e3b_misfit%s.csv" % ("_quick" if "--quick" in sys.argv else ""), index=False)
    print("done", time.time() - t0)
