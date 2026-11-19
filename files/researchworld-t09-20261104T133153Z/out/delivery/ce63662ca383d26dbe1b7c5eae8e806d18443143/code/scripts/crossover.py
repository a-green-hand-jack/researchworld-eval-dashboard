#!/usr/bin/env python3
"""experiment-repo#14(1): crossover strength gamma* (DM vs OLS_f, linear truth, Bernoulli 0.5) over n x mean degree x sigma (grid e17), and whether the
variance ratio SD(OLS_f)/SD(DM) at gamma = 0 depends on them.
gamma* is read two ways: (i) model-based, RMSE_DM(g)^2 = V_DM + (b g)^2 with b the fitted DM bias slope, OLS_f unbiased with MSE = mean over g
(gamma* = sqrt(MSE_OLS - V_DM)/|b|); (ii) linear interpolation of the observed RMSE difference over the five gammas. Writes t21_crossover.csv, t21b_crossover_scaling.csv."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import numpy as np, pandas as pd

R = str(results_dir())
d = pd.read_csv(R + "/summary/e17.csv")
rows = []
for tag, t in d.groupby("tag"):
    dm, ols = t[t.est_name == "DM"].sort_values("o_gamma"), t[t.est_name == "OLS_f"].sort_values("o_gamma")
    g = dm.o_gamma.values
    b = np.polyfit(g, dm.bias.values, 1)[0]
    v0 = dm.sd.values[0] ** 2
    mse_ols = (ols.rmse.values ** 2).mean()
    gstar = np.sqrt(max(mse_ols - v0, 0)) / abs(b)
    diff = ols.rmse.values - dm.rmse.values            # >0: DM better
    obs = np.nan
    for i in range(len(g) - 1):
        if diff[i] > 0 and diff[i + 1] <= 0:
            obs = g[i] + (g[i + 1] - g[i]) * diff[i] / (diff[i] - diff[i + 1]); break
    if diff[0] <= 0: obs = 0.0
    if np.isnan(obs) and (diff > 0).all(): obs = np.inf
    rows.append(dict(tag=tag, n=int(dm.n.iloc[0]), mean_deg=dm.mean_deg.mean(), sigma=float(dm.o_sigma.iloc[0]), dm_bias_slope=b,
                     sd_dm_g0=np.sqrt(v0), sd_ols_g0=ols.sd.values[0], sd_ratio_g0=ols.sd.values[0] / np.sqrt(v0),
                     ols_rmse_mean=np.sqrt(mse_ols), ols_rmse_min=ols.rmse.min(), ols_rmse_max=ols.rmse.max(),
                     gamma_star_model=gstar, gamma_star_interp=obs, gamma_star_over_sigma=gstar / float(dm.o_sigma.iloc[0])))
T = pd.DataFrame(rows).sort_values(["n", "mean_deg", "sigma"])
T["d_nom"] = T.tag.str.extract(r"d(\d+)\|").astype(int)
T.to_csv(R + "/tables/" + "t21_crossover.csv", index=False)
print(T[["tag", "dm_bias_slope", "sd_ratio_g0", "ols_rmse_min", "ols_rmse_max", "gamma_star_model", "gamma_star_interp"]].round(3).to_string())

# scaling: log-log regression on log n, log d, log sigma
out = []
X = np.column_stack([np.ones(len(T)), np.log(T.n), np.log(T.d_nom), np.log(T.sigma)])
for y, nm in (("sd_ratio_g0", "SD(OLS_f)/SD(DM) at gamma=0"), ("gamma_star_model", "gamma* (model)"), ("sd_ols_g0", "SD(OLS_f) at gamma=0"), ("sd_dm_g0", "SD(DM) at gamma=0")):
    Y = np.log(T[y].values)
    beta, res, *_ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ beta
    s2 = resid @ resid / (len(Y) - 4)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    r2 = 1 - resid @ resid / ((Y - Y.mean()) ** 2).sum()
    out.append(dict(quantity=nm, exp_n=beta[1], se_n=se[1], exp_d=beta[2], se_d=se[2], exp_sigma=beta[3], se_sigma=se[3], r2=r2,
                    min=T[y].min(), median=T[y].median(), max=T[y].max()))
O = pd.DataFrame(out)
O.to_csv(R + "/tables/" + "t21b_crossover_scaling.csv", index=False)
print(O.round(3).to_string())
