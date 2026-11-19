#!/usr/bin/env python3
"""experiment-repo#14(2): variance decomposition of log RMSE (and log SD) of OLS_f / DM / ORACLE_D over the full factorial e20
(SBM; n x mean degree x p x sigma x graph-smooth baseline x spillover shape; gamma = 2). The factorial is balanced, so the sum of squares of log RMSE splits exactly
into main effects and interactions: first-order share S_i = SS_i / SS_total, total share ST_i = sum of the shares of all effects that involve i
(Sobol indices of the cell-mean function, uniform weights over the tested levels). Intervals: parametric bootstrap of the cell values, log-RMSE noise
sd = 1/sqrt(2 N_eff) with N_eff = 400 replicates (no between-world variance for these cells, ICC ~ 0 in t20) - sd 0.035, and 0.05 for the world-level
inflation checked on e18; the point estimate and 2.5-97.5% over B = 1000. Writes t22_factor_anova.csv (shares) and t22b_factor_anova_interactions.csv (top interactions)."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import itertools, numpy as np, pandas as pd

R = str(results_dir())
d = pd.read_csv(R + "/summary/e20.csv")
d["n_f"] = d.n.round(-2); d["p"] = d.design.str.split(":").str[1].astype(float); d["d_nom"] = d.tag.str.extract(r"d(\d+)\|")[0].astype(int)
d = d.rename(columns={"o_sigma": "sigma", "o_alpha_graph": "graph_smooth_sd", "o_kind": "shape"})
FACT = ["n_f", "d_nom", "p", "sigma", "graph_smooth_sd", "shape"]
LAB = {"n_f": "n", "d_nom": "mean degree", "p": "treated share p", "sigma": "noise sigma", "graph_smooth_sd": "graph-smooth baseline", "shape": "spillover shape"}


def shares(Y):
    """Y: ndarray with one axis per factor (balanced). Returns {frozenset(factor idx): SS share}."""
    k = Y.ndim; mu = Y.mean(); out = {}; sst = ((Y - mu) ** 2).sum()
    for r in range(1, k + 1):
        for S in itertools.combinations(range(k), r):
            # effect of S = sum over subsets T of S of (-1)^{|S|-|T|} mean over axes not in T
            eff = np.zeros_like(Y)
            for t in range(0, r + 1):
                for T in itertools.combinations(S, t):
                    m = Y.mean(axis=tuple(a for a in range(k) if a not in T), keepdims=True) if len(T) < k else Y
                    eff = eff + (-1) ** (r - t) * m
            out[S] = (eff ** 2).sum() / sst
    return out


def tensor(sub, col):
    s = sub.sort_values(FACT)
    return np.log(s[col].values).reshape([s[f].nunique() for f in FACT])


rng = np.random.default_rng(7)
rows, inter = [], []
for est in ["OLS_f", "DM", "ORACLE_D"]:
    sub = d[d.est_name == est]
    for col in ["rmse", "sd"]:
        Y = tensor(sub, col)
        sh = shares(Y)
        first = {i: sh[(i,)] for i in range(6)}
        tot = {i: sum(v for S, v in sh.items() if i in S) for i in range(6)}
        bs_first, bs_tot = [], []
        for b in range(1000):
            Yb = Y + rng.normal(0, 0.05, Y.shape)
            s2 = shares(Yb); bs_first.append([s2[(i,)] for i in range(6)]); bs_tot.append([sum(v for S, v in s2.items() if i in S) for i in range(6)])
        bf, bt = np.array(bs_first), np.array(bs_tot)
        # range of the response over the factor: max-min of the factor's marginal means (ratio on original scale)
        for i, f in enumerate(FACT):
            marg = np.exp(Y.mean(axis=tuple(a for a in range(6) if a != i)))
            rows.append(dict(est_name=est, response=col, factor=LAB[f], levels=" / ".join(str(x) for x in sorted(sub[f].unique())),
                             first_order=first[i], first_lo=np.percentile(bf[:, i], 2.5), first_hi=np.percentile(bf[:, i], 97.5),
                             total=tot[i], total_lo=np.percentile(bt[:, i], 2.5), total_hi=np.percentile(bt[:, i], 97.5),
                             marginal_max_over_min=marg.max() / marg.min()))
        resid = 1 - sum(sh.values())
        top = sorted(((v, S) for S, v in sh.items() if len(S) >= 2), reverse=True)[:6]
        for v, S in top:
            inter.append(dict(est_name=est, response=col, interaction=" x ".join(LAB[FACT[a]] for a in S), share=v))
T = pd.DataFrame(rows); T.to_csv(R + "/tables/t22_factor_anova.csv", index=False)
pd.DataFrame(inter).to_csv(R + "/tables/t22b_factor_anova_interactions.csv", index=False)
pd.set_option("display.width", 200)
print(T[(T.est_name == "OLS_f")].round(3).to_string())
print(T[(T.est_name != "OLS_f") & (T.response == "rmse")].round(3)[["est_name", "factor", "first_order", "total", "marginal_max_over_min"]].to_string())
print(pd.DataFrame(inter).query("est_name=='OLS_f'").round(3).to_string())
