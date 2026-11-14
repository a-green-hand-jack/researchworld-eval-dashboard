"""Aggregate Monte-Carlo output into tables (results/*.csv) and figures (figs/*.pdf).
usage: python analysis.py
"""
import numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "../results/"; FG = "../figs/"
Z = stats.norm.ppf(0.975)
METH = ["classical", "ppi", "ppi++", "aipw-lin", "aipw-iso", "aipw-linX", "aipw-gbm", "aipw-auto", "aipw-auto-Uonly"]
rng = np.random.default_rng(0)


def load(f):
    d = pd.read_csv(R + f)
    q = stats.t.ppf(0.975, d["df"])
    d["w_z"] = 2 * Z * d.se
    d["w_t"] = 2 * q * d.se
    d["cov_z"] = (np.abs(d.est - d.truth) <= Z * d.se).astype(float)
    d["cov_t"] = (np.abs(d.est - d.truth) <= q * d.se).astype(float)
    return d


def summarize(d, nboot=300):
    """Per (dataset,n,N,method): coverage (z,t) with MC s.e., mean widths, paired width ratio vs PPI++ with bootstrap CI."""
    rows = []
    for (ds, n, N), g in d.groupby(["dataset", "n", "N"]):
        P = g.pivot(index="rep", columns="method", values="w_z")
        Pt = g.pivot(index="rep", columns="method", values="w_t")
        C = g.pivot(index="rep", columns="method", values="cov_z")
        Ct = g.pivot(index="rep", columns="method", values="cov_t")
        R_ = len(P)
        idx = rng.integers(0, R_, (nboot, R_))
        base = P["ppi++"].values
        for m in P.columns:
            w = P[m].values
            ratios = w[idx].mean(1) / base[idx].mean(1)
            rows.append(dict(dataset=ds, n=n, N=N, method=m, reps=R_,
                             cov_z=C[m].mean(), cov_z_se=np.sqrt(C[m].mean() * (1 - C[m].mean()) / R_),
                             cov_t=Ct[m].mean(), width_z=w.mean(), width_t=Pt[m].mean(),
                             ratio=w.mean() / base.mean(), ratio_lo=np.quantile(ratios, .025), ratio_hi=np.quantile(ratios, .975)))
    return pd.DataFrame(rows)


def theory_variances(pop, n, N):
    """Asymptotic variances (see theory.py)."""
    vy, vf, c = pop.varY, pop.varF, pop["cov"]
    lam = np.clip(c / (vf * (1 + n / N)), 0, 1)
    V = dict(classical=vy / n,
             ppi=(vy - 2 * c + vf) / n + vf / N,
             **{"ppi++": (vy - 2 * lam * c + lam ** 2 * vf) / n + lam ** 2 * vf / N})
    mse_lin = vy - c ** 2 / vf
    cands = [pop[k] for k in ["mse_lin", "mse_iso", "mse_linX", "mse_gbm"] if k in pop.index and not np.isnan(pop[k])]
    mse_opt = min(cands)
    var_mu = vy - mse_opt
    var_m_lin = max(mse_lin - mse_opt, 0)
    V["aipw-lin"] = var_mu / (n + N) + var_m_lin * N / (n * (n + N)) + mse_opt / n
    V["aipw-opt"] = var_mu / (n + N) + mse_opt / n
    return V


if __name__ == "__main__":
    out = {}
    for tag, f in [("real", "real.csv.gz"), ("synth", "synth.csv.gz")]:
        d = load(f)
        s = summarize(d)
        s.to_csv(R + f"summary_{tag}.csv", index=False)
        out[tag] = s
        ch = d[d.method == "aipw-auto"].groupby(["dataset", "n", "N"]).choice.agg(lambda x: x.value_counts(normalize=True).to_dict())
        ch.to_csv(R + f"auto_choice_{tag}.csv")
    th = pd.read_csv(R + "theory_pop.csv").set_index("dataset")
    # predicted vs observed width ratio
    rows = []
    for tag in out:
        s = out[tag]
        for (ds, n, N), g in s.groupby(["dataset", "n", "N"]):
            V = theory_variances(th.loc[ds], n, N)
            for m, key in [("aipw-lin", "aipw-lin"), ("aipw-auto", "aipw-opt"), ("classical", "classical"), ("ppi", "ppi")]:
                obs = g[g.method == m].iloc[0]
                rows.append(dict(suite=tag, dataset=ds, n=n, N=N, method=m, pred_ratio=np.sqrt(V[key] / V["ppi++"]),
                                 obs_ratio=obs.ratio, obs_lo=obs.ratio_lo, obs_hi=obs.ratio_hi))
    pr = pd.DataFrame(rows); pr.to_csv(R + "pred_vs_obs.csv", index=False)
    print("saved summaries")
