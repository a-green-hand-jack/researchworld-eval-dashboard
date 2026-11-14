"""A3: plug-in version of Prop. 2 (expected bias of the worst-cell coverage estimate), from results/raw/A3pi_*.csv
(the A3hs configurations re-run with the same seeds, saving per-cell estimated coverage chat_g and cell size m_g).
For a replication, score, stratification (x0_10: deciles of x_0, bd_10: bins of the smallest predicted component) and n_te:
  pred(p) = E[ min_g Bin(m_g, p_g)/m_g ]  (independent cells, exact, unequal m_g; integral of P{min >= t} on a fine grid)
  oracle  p_g = true cell coverage c_g (grid)          -> as A3_pred_bias.csv, but with the actual (unequal) cell sizes
  plugin  p_g = chat_g (the cell estimates of the same test set)
  shrunk  p_g = cbar + lambda (chat_g - cbar), lambda = max(0, 1 - mean_g[chat_g(1-chat_g)/m_g] / var_g(chat_g))   (empirical-Bayes shrinkage)
Bias given p:  bias(p) = pred(p) - min_g p_g.  oracle: bias(c) (the formula's bias at the true cell coverages, A3_pred_bias.csv layout);
plugin: bhat = pred(chat) - min chat (parametric-bootstrap bias estimate); shrunk: bias at the shrunk p. Corrected estimate = min chat - bhat
(plugin, shrunk); the oracle version uses the unknown truth and is reported as a bound only.
Reported per config / score / stratification / n_te: mean observed bias (min chat - true min), mean bhat (oracle, plugin, shrunk), bias and RMSE
of the naive and corrected estimates against the true worst-cell coverage, and the Kendall tau (single replication vs the all-replication true
mean) of naive and corrected rankings of the scores.
Outputs results/tables/A3pi_pred_bias.csv (per config/score), A3pi_summary.csv (means over configs), A3pi_rank.csv"""
import glob, sys
import numpy as np, pandas as pd
from scipy.stats import binom, kendalltau
from multiprocessing import Pool

NN = (500, 2000, 10000)
G = 10
TG = 400


def emin(p, m):
    """E[min_g Bin(m_g,p_g)/m_g], independent cells."""
    p = np.clip(p, 1e-9, 1 - 1e-9); m = m.astype(float)
    sig = np.sqrt(0.25 / m.min())
    lo = max(0.0, p.min() - 7 * sig); hi = min(1.0, p.min() + 7 * sig)
    t = lo + (np.arange(TG) + 0.5) * (hi - lo) / TG                      # midpoints of TG intervals on [lo,hi]
    k = np.ceil(t[None, :] * m[:, None] - 1e-12)                          # need Bin >= k  for  Bin/m >= t
    pm = binom.sf(k - 1, m[:, None], p[:, None]).prod(0)                  # P{min >= t}
    return lo + pm.sum() * (hi - lo) / TG


def shrink(c, m):
    v = np.mean(c * (1 - c) / m); s2 = np.var(c, ddof=1)
    lam = max(0.0, 1 - v / s2) if s2 > 0 else 0.0
    return c.mean() + lam * (c - c.mean())


def one(f):
    d = pd.read_csv(f); cfg = d.config.iloc[0]
    out = []
    for st in ("x0_10", "bd_10"):
        for nn in NN:
            C = d[[f"cell_{st}_{nn}_{j}" for j in range(G)]].values
            M = d[[f"cnt_{st}_{nn}_{j}" for j in range(G)]].values
            Tc = d[[f"truecell_{st}_{j}" for j in range(G)]].values
            n = len(d); po = np.full(n, np.nan); pp = po.copy(); ps = po.copy(); mo = po.copy(); mp = po.copy(); mss = po.copy()
            for i in range(n):
                if (M[i] == 0).any() or np.isnan(C[i]).any():
                    continue
                sh = shrink(C[i], M[i])
                po[i], pp[i], ps[i] = emin(Tc[i], M[i]), emin(C[i], M[i]), emin(sh, M[i])
                mo[i], mp[i], mss[i] = Tc[i].min(), C[i].min(), sh.min()
            mn = d[f"est_{st}_min_{nn}"].values; tr = d[f"true_{st}_min"].values
            e = d.assign(mn=mn, tr=tr, po=po, pp=pp, ps=ps, mo=mo, mp=mp, mss=mss, st=st, nn=nn)
            e["seed"] = d.seed
            out.append(e[["method", "seed", "st", "nn", "mn", "tr", "po", "pp", "ps", "mo", "mp", "mss"]].assign(config=cfg))
    return pd.concat(out)


if __name__ == "__main__":
    files = sorted(glob.glob("results/raw/A3pi_*.csv*"))
    with Pool(2) as P:
        D = pd.concat(P.map(one, files), ignore_index=True)
    D["b_obs"] = D.mn - D.tr
    for k, c, mc in (("oracle", "po", "mo"), ("plugin", "pp", "mp"), ("shrunk", "ps", "mss")):
        D[f"bhat_{k}"] = D[c] - D[mc]
        D[f"corr_{k}"] = D.mn - D[f"bhat_{k}"]
    g = D.groupby(["config", "method", "st", "nn"])
    R = g.agg(reps=("b_obs", "count"), obs_bias=("b_obs", "mean"), obs_bias_se=("b_obs", lambda x: x.std() / np.sqrt(len(x))),
              pred_bias_oracle=("bhat_oracle", "mean"), pred_bias_plugin=("bhat_plugin", "mean"), pred_bias_shrunk=("bhat_shrunk", "mean"),
              mean_est=("mn", "mean"), mean_true=("tr", "mean")).reset_index()
    for k in ("oracle", "plugin", "shrunk"):
        R[f"bias_corr_{k}"] = g.apply(lambda x, k=k: (x[f"corr_{k}"] - x.tr).mean(), include_groups=False).values
        R[f"rmse_corr_{k}"] = g.apply(lambda x, k=k: np.sqrt(((x[f"corr_{k}"] - x.tr) ** 2).mean()), include_groups=False).values
    R["rmse_naive"] = g.apply(lambda x: np.sqrt(((x.mn - x.tr) ** 2).mean()), include_groups=False).values
    R.to_csv("results/tables/A3pi_pred_bias.csv", index=False)
    S = R.groupby(["st", "nn"])[["obs_bias", "pred_bias_oracle", "pred_bias_plugin", "pred_bias_shrunk", "bias_corr_oracle", "bias_corr_plugin",
                                  "bias_corr_shrunk", "rmse_naive", "rmse_corr_plugin", "rmse_corr_shrunk"]].mean().reset_index()
    S["n_configs"] = R.groupby(["st", "nn"]).config.nunique().values
    # per-method spread: correlation across scores between the observed bias and the predicted bias (does the formula explain method-dependent bias?)
    sp = []
    for (c, st, nn), x in R.groupby(["config", "st", "nn"]):
        sp.append(dict(config=c, st=st, nn=nn, range_obs=np.ptp(x.obs_bias), range_plugin=np.ptp(x.pred_bias_plugin), range_oracle=np.ptp(x.pred_bias_oracle),
                       r_plugin=np.corrcoef(x.obs_bias, x.pred_bias_plugin)[0, 1], r_oracle=np.corrcoef(x.obs_bias, x.pred_bias_oracle)[0, 1]))
    SP = pd.DataFrame(sp)
    S = S.merge(SP.groupby(["st", "nn"])[["range_obs", "range_plugin", "range_oracle", "r_plugin", "r_oracle"]].mean().reset_index(), on=["st", "nn"])
    S.to_csv("results/tables/A3pi_summary.csv", index=False)
    # ranking: single replication, corrected vs naive vs truth
    rk = []
    for (c, st, nn), x in D.groupby(["config", "st", "nn"]):
        ms = sorted(x.method.unique())
        W = {k: x.pivot(index="seed", columns="method", values=k)[ms].values for k in ("mn", "tr", "corr_plugin", "corr_shrunk", "corr_oracle")}
        truth = np.nanmean(W["tr"], 0)
        for k, lab in (("mn", "naive"), ("corr_plugin", "plugin"), ("corr_shrunk", "shrunk"), ("corr_oracle", "oracle")):
            ts = [kendalltau(W[k][i], truth)[0] for i in range(len(W[k]))]
            rk.append(dict(config=c, st=st, n_te=nn, estimator=lab, tau_single=np.nanmean(ts)))
    RK = pd.DataFrame(rk); RK.to_csv("results/tables/A3pi_rank.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(S.round(4).to_string())
    print(RK.groupby(["st", "n_te", "estimator"]).tau_single.mean().unstack().round(3))
