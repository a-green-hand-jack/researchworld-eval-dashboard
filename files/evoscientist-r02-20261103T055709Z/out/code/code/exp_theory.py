"""Theory check: finite-sample distribution of conditional coverage of split conformal on simplex data.

Theory (continuous scores, exchangeable): with n calibration points and l = floor((n+1)*alpha),
  C = P(S_test <= q_hat | calibration) ~ Beta(n + 1 - l, l),  E[C] = (n+1-l)/(n+1) >= 1-alpha.
Mondrian (group-conditional) version: within a group with n_g calibration points the same holds with n_g.
We fix one trained predictor (Dirichlet data, K=3, kappa0=30, hetero=0, correctly specified), draw many calibration
sets of size n from fresh data, and estimate C by a large test pool (1e6 points, so that the offset shared by all repetitions is <=5e-4).
Usage: python code/exp_theory.py   -> results/theory.csv, results/theory_summary.csv
"""
import sys, numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import cp

ALPHA = 0.1; K = 3; NTEST = 1000000; REPS = 3000
rng = np.random.default_rng(2024)
B, C = cp.scenario_params(K)
x, y, _ = cp.gen_data(rng, 3000, K, 30, 0, 0, B=B, C=C)
pred = cp.fit_softmax_reg(x, y)
xt, yt, _ = cp.gen_data(rng, NTEST, K, 30, 0, 0, B=B, C=C)
Pt = pred(xt)
rows = []
for sc in ["l2", "kl", "aitch"]:
    f = cp.make_score(sc)
    st = np.sort(f(yt, Pt))
    for n in [20, 50, 100, 500, 2000]:
        l = int(np.floor((n + 1) * ALPHA))
        covs = np.empty(REPS)
        for r in range(REPS):
            xc, yc, _ = cp.gen_data(rng, n, K, 30, 0, 0, B=B, C=C)
            q = cp.conf_quantile(f(yc, pred(xc)), ALPHA)
            covs[r] = np.searchsorted(st, q, side="right") / NTEST
        # reference: exact Beta law; the shared test-pool offset has SD <= 5e-4 with 1e6 pool points
        ref = rng.beta(n + 1 - l, l, REPS)
        ks = stats.ks_2samp(covs, ref)
        rows.append(dict(score=sc, n=n, l=l, emp_mean=covs.mean(), emp_mean_se=covs.std(ddof=1) / np.sqrt(REPS),
                         beta_mean=(n + 1 - l) / (n + 1), emp_sd=covs.std(ddof=1),
                         beta_sd=np.sqrt((n + 1 - l) * l / ((n + 1) ** 2 * (n + 2))),
                         emp_q05=np.quantile(covs, .05), beta_q05=stats.beta.ppf(.05, n + 1 - l, l),
                         emp_q95=np.quantile(covs, .95), beta_q95=stats.beta.ppf(.95, n + 1 - l, l),
                         ks_stat=ks.statistic, ks_p=ks.pvalue,
                         p_below_90=(covs < 0.9).mean(), beta_p_below_90=stats.beta.cdf(0.9, n + 1 - l, l)))
        print(rows[-1], flush=True)
d = pd.DataFrame(rows)
d.to_csv("results/theory.csv", index=False)
