"""A3 (e): does method-dependent bias of the finite-test worst-cell estimate mis-rank methods?
Noise-free version: rank methods by the replication-mean of the estimated worst-cell coverage vs by the replication-mean of the
true worst-cell coverage, within each config. Uses results/tables/A3_pred_bias.csv. Output results/tables/A3_bias_rank.csv"""
import pandas as pd, numpy as np
from scipy.stats import kendalltau
P = pd.read_csv("results/tables/A3_pred_bias.csv")
rows = []
for (c, s, nn), g in P.groupby(["config", "strat", "n_te"]):
    b = g.obs_mean.values - g.true_mean.values
    rows.append(dict(config=c, strat=s, G=g.G.iloc[0], n_te=nn, methods=len(g),
                     tau_est_vs_true=kendalltau(g.obs_mean, g.true_mean)[0],
                     tau_formula_vs_true=kendalltau(g.pred_exact, g.true_mean)[0],
                     top1_agree=float(g.obs_mean.values.argmax() == g.true_mean.values.argmax()),
                     bias_mean=b.mean(), bias_sd_across_methods=b.std(ddof=1), bias_range=b.max() - b.min(),
                     true_spread=g.true_mean.max() - g.true_mean.min()))
R = pd.DataFrame(rows); R.to_csv("results/tables/A3_bias_rank.csv", index=False)
pd.set_option("display.width", 200)
print(R.groupby(["strat", "n_te"])[["tau_est_vs_true", "tau_formula_vs_true", "top1_agree", "bias_mean", "bias_sd_across_methods", "bias_range", "true_spread"]].mean().round(3))
