"""A3 corrected estimator: naive min-over-cells vs half-split (select the apparent worst cell on one half of the test set, measure it on
the other, average both directions), from results/raw/A3hs_*.csv. Per config, stratification and n_te:
 bias / RMSE of each estimator against the true worst-cell coverage (min over cells on the ground-truth grid); the half-split estimator
 targets the coverage of the *selected* cell (true_*_hssel), so its bias against that is reported too;
 ranking quality: Kendall tau and top-1 agreement between the ranking of methods by one replication's estimate (or the mean over R=10
 replications) and by the true (all-replication mean) worst-cell coverage.
Also A3hs_rank_blocks.csv: Kendall tau / top-1 agreement between the rankings of two disjoint random blocks of R replications (R up to 100 from
the 1000-replication pool), for the true worst cell, the estimated worst cell, the marginal coverage gap, per config.
Outputs results/tables/A3hs_bias.csv, A3hs_rank.csv, A3hs_rank_blocks.csv"""
import glob
import numpy as np, pandas as pd
from scipy.stats import kendalltau

rng = np.random.default_rng(2)
rng_blk = np.random.default_rng(3)      # block-pair draws use their own stream, so A3hs_rank.csv does not depend on them
NN = (500, 2000, 10000)
brow, rrow, krow = [], [], []
for f in sorted(glob.glob("results/raw/A3hs_*.csv*")):
    d = pd.read_csv(f); cfg = d.config.iloc[0]
    meths = list(d.method.unique()); seeds = np.sort(d.seed.unique())
    for st in ("x0_10", "bd_10"):
        tm = d.pivot(index="seed", columns="method", values=f"true_{st}_min").loc[seeds, meths].values
        truth = np.nanmean(tm, 0)
        for nn in NN:
            nv = d.pivot(index="seed", columns="method", values=f"est_{st}_min_{nn}").loc[seeds, meths].values
            hs = d.pivot(index="seed", columns="method", values=f"est_{st}_hs_{nn}").loc[seeds, meths].values
            sel = d.pivot(index="seed", columns="method", values=f"true_{st}_hssel_{nn}").loc[seeds, meths].values
            for kind, E in (("naive", nv), ("halfsplit", hs)):
                err = E - tm
                brow.append(dict(config=cfg, strat=st, n_te=nn, estimator=kind, reps=len(seeds),
                                 bias_vs_true_min=np.nanmean(err), rmse_vs_true_min=np.sqrt(np.nanmean(err ** 2)),
                                 bias_vs_selected_cell=np.nanmean(E - sel) if kind == "halfsplit" else np.nan,
                                 bias_range_across_methods=np.ptp(np.nanmean(err, 0))))
                ts = [kendalltau(E[i], truth)[0] for i in range(len(seeds))]
                t1 = [float(np.nanargmax(E[i]) == np.nanargmax(truth)) for i in range(len(seeds))]
                ts10 = []
                for _ in range(300):
                    p = rng.choice(len(seeds), 10, replace=False); ts10.append(kendalltau(np.nanmean(E[p], 0), truth)[0])
                rrow.append(dict(config=cfg, strat=st, n_te=nn, estimator=kind, tau_single=np.nanmean(ts), top1_single=np.mean(t1),
                                 tau_R10=np.nanmean(ts10), n_methods=len(meths)))
    # ranking agreement between disjoint blocks of R replications
    d = d.assign(marg_cov_gap=(d.marg_cov - 0.9).abs())
    W = {m: d.pivot(index="seed", columns="method", values=m).loc[seeds, meths].values
         for m in ["true_x0_10_min", "true_bd_10_min", "est_x0_10_min_500", "est_x0_10_min_2000", "est_x0_10_min_10000", "marg_cov_gap"]}
    for m, X in W.items():
        for Rb in (5, 10, 25, 50, 100):
            ts, t1 = [], []
            for _ in range(300):
                pp = rng_blk.permutation(len(seeds)); A, Bb = X[pp[:Rb]].mean(0), X[pp[Rb:2 * Rb]].mean(0)
                ts.append(kendalltau(A, Bb)[0])
                t1.append(float(np.argmin(A) == np.argmin(Bb)) if "gap" in m else float(np.argmax(A) == np.argmax(Bb)))
            krow.append(dict(config=cfg, metric=m, R=Rb, nrep=len(seeds), tau_mean=np.nanmean(ts), tau_lo=np.nanquantile(ts, .025), top1=np.mean(t1)))
B = pd.DataFrame(brow); R = pd.DataFrame(rrow)
B.to_csv("results/tables/A3hs_bias.csv", index=False); R.to_csv("results/tables/A3hs_rank.csv", index=False)
K = pd.DataFrame(krow); K.to_csv("results/tables/A3hs_rank_blocks.csv", index=False)
pd.set_option("display.width", 200)
print(B.groupby(["strat", "n_te", "estimator"])[["bias_vs_true_min", "rmse_vs_true_min", "bias_vs_selected_cell", "bias_range_across_methods"]].mean().round(4))
print(R.groupby(["strat", "n_te", "estimator"])[["tau_single", "top1_single", "tau_R10"]].mean().round(3))

print(K.groupby(["metric", "R"])[["tau_mean", "top1"]].mean().round(2).unstack(0).to_string())
