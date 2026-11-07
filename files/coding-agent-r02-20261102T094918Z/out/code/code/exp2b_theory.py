"""E2b: check the asymptotic (kappa -> infinity) theory for Dirichlet noise.
For each score we compare the conditional coverage (by deciles of max(mu)) obtained from exact Dirichlet simulation
(radius = exact marginal quantile) with the prediction from the Gaussian/linearised limit.
Writes results/e2b_theory.csv"""
import numpy as np, pandas as pd
from ccp.geometry import SCORES, softmax
from ccp.synth import SynthProblem
from ccp.evalkit import quantile_bins

ALPHA, N_BINS = 0.1, 10
M = 400000


def linearised_scores(mu, kappa, rng):
    """Scores of the Gaussian limit: eps ~ N(0, (diag(mu)-mu mu^T)/kappa), s evaluated to leading order."""
    z = rng.normal(size=mu.shape)
    sq = np.sqrt(mu)
    eps = (sq * z - mu * (sq * z).sum(-1, keepdims=True)) / np.sqrt(kappa)
    P = lambda v: v - v.mean(-1, keepdims=True)
    return {
        "euclid": np.sqrt((eps ** 2).sum(-1)),
        "tv": 0.5 * np.abs(eps).sum(-1),
        "hellinger": 0.5 * np.sqrt((eps ** 2 / mu).sum(-1)),
        "chi2": np.sqrt((eps ** 2 / mu).sum(-1)),
        "kl": np.sqrt(0.5 * (eps ** 2 / mu).sum(-1)),
        "aitchison": np.sqrt((P(eps / mu) ** 2).sum(-1)),
    }


rows = []
curves = []
for D in (3, 5, 10):
    for kappa in (30, 100, 300, 1000, 3000, 10000):
        pr = SynthProblem(D=D, family="dirichlet", kappa=kappa, tau=1.5, seed=1)
        rng = np.random.default_rng(11)
        _, mu, y = pr.sample(M, rng)
        conf = mu.max(-1)
        b, _ = quantile_bins(conf, N_BINS)
        # exact simulation
        S = {n: f(y, mu) for n, f in SCORES.items()}
        L = linearised_scores(mu, kappa, rng)
        for n in SCORES:
            r_exact = np.quantile(S[n], 1 - ALPHA)
            r_lin = np.quantile(L[n], 1 - ALPHA)
            cov_exact = np.array([np.mean(S[n][b == i] <= r_exact) for i in range(N_BINS)])
            cov_pred = np.array([np.mean(L[n][b == i] <= r_lin) for i in range(N_BINS)])
            rows.append(dict(D=D, kappa=kappa, score=n, r_exact=r_exact, r_lin=r_lin,
                             max_dev_exact=np.abs(cov_exact - 0.9).max(), max_dev_pred=np.abs(cov_pred - 0.9).max(),
                             max_abs_pred_vs_exact=np.abs(cov_pred - cov_exact).max(),
                             kappa_mu_min_median=kappa * np.median(mu.min(-1))))
            if D == 3 and kappa in (100, 1000):
                for i in range(N_BINS):
                    curves.append(dict(D=D, kappa=kappa, score=n, bin=i, conf_mid=conf[b == i].mean(),
                                       cov_exact=cov_exact[i], cov_pred=cov_pred[i]))
df = pd.DataFrame(rows)
df.to_csv("/work/results/e2b_theory.csv", index=False)
pd.DataFrame(curves).to_csv("/work/results/e2b_curves.csv", index=False)
pd.set_option("display.width", 200)
print(df.pivot_table(index=["D", "kappa"], columns="score", values="max_abs_pred_vs_exact").round(3))
print(df.pivot_table(index=["D", "kappa"], columns="score", values="max_dev_exact").round(3))
