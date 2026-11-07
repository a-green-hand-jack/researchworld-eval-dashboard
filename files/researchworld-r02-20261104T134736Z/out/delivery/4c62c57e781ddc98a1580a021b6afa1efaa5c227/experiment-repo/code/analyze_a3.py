"""A3: reliability of the evaluation estimators themselves (RQ3), from the A1 replications.
 (a) bias/RMSE of estimated vs true worst-stratum coverage at finite n_te
 (b) closed-form-by-simulation prediction of that bias (expected min of independent binomials, cell size n_te/ns)
 (c) ranking stability across disjoint blocks of R replications and of a single split vs the truth
 (d) paired vs unpaired uncertainty for method differences
Outputs results/tables/A3_*.csv*"""
import glob, re
import numpy as np, pandas as pd
from scipy.stats import kendalltau, binom

MU = {5: 1.162964, 10: 1.538753, 20: 1.867475}   # E[max of G iid N(0,1)]

rng = np.random.default_rng(1)
rng_rank = np.random.default_rng(2)       # block-pair draws of (c) use their own stream
files = sorted(glob.glob("results/raw/A1_*.csv*"))
NN = (500, 2000, 10000)
bias_rows, pred_rows, rank_rows, single_rows, pair_rows = [], [], [], [], []


def tau(a, b):
    return kendalltau(a, b)[0]


for f in files:
    d = pd.read_csv(f)
    cfg = d.config.iloc[0]
    meths = list(d.method.unique())
    alpha = d.alpha.iloc[0] if "alpha" in d else 0.1
    # (a) bias
    for name, ns in [("x0_5", 5), ("x0_10", 10), ("x0_20", 20), ("bd_10", 10)]:
        for nn in NN:
            col = f"est_{name}_min_{nn}"
            if col not in d:
                continue
            e = d[col] - d[f"true_{name}_min"]
            for m, g in e.groupby(d.method):
                rows = dict(config=cfg, method=m, strat=name, n_te=nn, ns=ns, bias=g.mean(), bias_se=g.std() / np.sqrt(len(g)),
                            sd=g.std(), rmse=np.sqrt((g ** 2).mean()), reps=len(g))
                bias_rows.append(rows)
    # (b) predicted worst-cell estimate given the replicate's true cell coverages c_g (grid; G=10, and G=5 by merging pairs).
    #     exact: E[min_g chat_g] = (1/m) sum_{j=1..m} prod_g P{Bin(m,c_g) >= j}, m = n_te/G  (Prop. 2, equal cell sizes)
    #     mc: Monte-Carlo of the same; normal: cbar - sqrt(cbar(1-cbar)/m) * mu_G
    sl = [f"slab{j}" for j in range(10)]
    C10 = d[sl].values
    for G, name in [(10, "x0_10"), (5, "x0_5")]:
        CG = C10 if G == 10 else C10.reshape(len(d), 5, 2).mean(2)
        for nn in NN:
            col = f"est_{name}_min_{nn}"
            if col not in d:
                continue
            m = nn // G
            jj = np.arange(1, m + 1)
            ex = np.empty(len(d)); mc = np.empty(len(d)); nrm = np.empty(len(d))
            for i, c in enumerate(CG):
                c = np.clip(c, 1e-9, 1 - 1e-9)
                sf = np.stack([binom.sf(jj - 1, m, cg) for cg in c])          # P{Bin>=j}, (G, m)
                ex[i] = sf.prod(0).sum() / m
                mc[i] = (rng.binomial(m, c, size=(400, G)) / m).min(1).mean()
                cb = c.mean(); nrm[i] = cb - np.sqrt(cb * (1 - cb) / m) * MU[G]
            tcol = f"true_{name}_min"
            dd = d.assign(ex=ex, mc=mc, nrm=nrm)
            for mth, g in dd.groupby("method"):
                pred_rows.append(dict(config=cfg, method=mth, strat=name, G=G, n_te=nn, obs_mean=g[col].mean(),
                                      obs_se=g[col].std() / np.sqrt(len(g)), pred_exact=g.ex.mean(), pred_mc=g.mc.mean(),
                                      pred_normal=g.nrm.mean(), true_mean=g[tcol].mean(), reps=len(g),
                                      note="pred uses each replicate's true cell coverages c_g, equal cell size n_te/G"))
    # (c) ranking stability
    seeds = np.sort(d.seed.unique()); nrep = len(seeds)
    metrics = ["true_x0_10_min", "true_bd_10_min", "true_x0_10_dev"] + (["log_vol_ratio"] if d.log_vol_ratio.notna().any() else []) \
        + [f"est_x0_10_min_{nn}" for nn in NN] + ["marg_cov_gap"]
    d = d.assign(marg_cov_gap=(d.marg_cov - (1 - alpha)).abs())
    W = {m: d.pivot(index="seed", columns="method", values=m).loc[seeds, meths].values for m in metrics}   # (rep, method)
    for m in metrics:
        for R in (5, 10, 25, 50, 100):
            if 4 * R > nrep:       # two disjoint blocks that partition (or nearly exhaust) the pool are anticorrelated by construction
                continue
            ts, t1 = [], []
            for _ in range(200):
                p = rng_rank.permutation(nrep); A, Bb = W[m][p[:R]].mean(0), W[m][p[R:2 * R]].mean(0)
                ts.append(tau(A, Bb)); t1.append(float(np.argmax(A) == np.argmax(Bb)) if "dev" not in m and "gap" not in m and "vol" not in m
                                                  else float(np.argmin(A) == np.argmin(Bb)))
            rank_rows.append(dict(config=cfg, metric=m, R=R, nrep=nrep, tau_mean=np.nanmean(ts), tau_lo=np.nanquantile(ts, .025), top1=np.mean(t1)))
    # single split: ranking by one replication's estimated metric vs ranking by the true (all-rep) metric
    truth = W["true_x0_10_min"].mean(0)
    for nn in NN:
        E = W[f"est_x0_10_min_{nn}"]
        ts = [tau(E[i], truth) for i in range(nrep)]
        t1 = [float(np.argmax(E[i]) == np.argmax(truth)) for i in range(nrep)]
        single_rows.append(dict(config=cfg, n_te=nn, tau_single_vs_truth=np.nanmean(ts), tau_lo=np.nanquantile(ts, .025), top1=np.mean(t1)))
    # (d) paired vs unpaired for the difference between each method and euc
    j0 = meths.index("euc")
    for m in ["true_x0_10_min", "log_vol_ratio"]:
        if m not in W:
            continue
        for k, mt in enumerate(meths):
            if mt == "euc":
                continue
            paired = (W[m][:, k] - W[m][:, j0]).std(ddof=1) / np.sqrt(nrep)
            unpaired = np.sqrt(W[m][:, k].var(ddof=1) / nrep + W[m][:, j0].var(ddof=1) / nrep)
            pair_rows.append(dict(config=cfg, metric=m, method=mt, diff=np.mean(W[m][:, k] - W[m][:, j0]), se_paired=paired,
                                  se_unpaired=unpaired, ratio=unpaired / paired))

for name, rows in [("A3_bias", bias_rows), ("A3_pred_bias", pred_rows), ("A3_rank_blocks", rank_rows),
                   ("A3_rank_single", single_rows), ("A3_paired_unpaired", pair_rows)]:
    pd.DataFrame(rows).to_csv(f"results/tables/{name}.csv", index=False)
pd.set_option("display.width", 250)
B_ = pd.DataFrame(bias_rows)
print(B_.groupby(["strat", "n_te"])[["bias", "rmse", "sd"]].mean().round(4))
P_ = pd.DataFrame(pred_rows)
print(P_.groupby(["G", "n_te"])[["obs_mean", "pred_exact", "pred_mc", "pred_normal", "true_mean"]].mean().round(4))
print((P_.obs_mean - P_.pred_exact).abs().describe().round(4))
R_ = pd.DataFrame(rank_rows)
print(R_.groupby(["metric", "R"])[["tau_mean", "top1"]].mean().round(2).unstack(0).to_string())
print(pd.DataFrame(single_rows).groupby("n_te")[["tau_single_vs_truth", "top1"]].mean().round(3))
print(pd.DataFrame(pair_rows).groupby("metric").ratio.describe().round(2))
