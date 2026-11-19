"""Scale-law check. For y|x ~ Dirichlet(kappa*m): E||y-m||_2^2 = (1-||m||^2)/(kappa+1) exactly (sum of Dirichlet variances).
(i) verify the exact second-moment identity with the TRUE mean m(x) (ratio of means of realised and predicted squared l2 error);
(ii) the l2-score scale is sigma(x)=sqrt((1-||m||^2)/(kappa(x)+1)) up to an x-independent-in-first-order shape factor. Compare the OLS slope of
     log s on x1 (oracle-mean score; fitted-predictor score) with the OLS slope of log sigma(x) on x1 ("slope_sigma"), and with the crude
     prediction that ignores the x1-dependence of m ("slope_kappa_only" = mean of -(h/2) kappa/(kappa+1)).
Usage: python code/exp_scale.py -> results/scale_law.csv"""
import sys, numpy as np, pandas as pd
from scipy.special import softmax
sys.path.insert(0, "code")
import cp
rows = []; N = 200000
for K in [3, 10]:
    for k0 in [3, 30, 300]:
        h = 1.0; rng = np.random.default_rng([5, K, k0]); B, C = cp.scenario_params(K)
        x, y, kap = cp.gen_data(rng, N, K, k0, h, 0, B=B, C=C)
        m = softmax(x @ B, axis=1)
        s2 = ((y - m) ** 2).sum(1); pred_s2 = (1 - (m ** 2).sum(1)) / (kap + 1)
        out = dict(K=K, kappa0=k0, moment_ratio=s2.mean() / pred_s2.mean())
        xt, yt, _ = cp.gen_data(rng, 1000, K, k0, h, 0, B=B, C=C); P = cp.fit_softmax_reg(xt, yt)(x)
        X = np.stack([np.ones(N), x[:, 0]], 1)
        slope = lambda v: np.linalg.lstsq(X, v, rcond=None)[0][1]
        out["slope_oracle"] = slope(np.log(np.sqrt(s2)))
        out["slope_fitted"] = slope(np.log(np.sqrt(((y - P) ** 2).sum(1))))
        out["slope_sigma"] = slope(0.5 * np.log(pred_s2))
        out["slope_kappa_only"] = np.mean(-(h / 2) * kap / (kap + 1))
        rows.append(out)
d = pd.DataFrame(rows).round(4); d.to_csv("results/scale_law.csv", index=False); print(d.to_string())
