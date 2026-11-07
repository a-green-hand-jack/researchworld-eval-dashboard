"""Setting B summaries: per config x method means with bootstrap CIs over replications, paired differences
to LAC, and bias of finite-test-set size-stratified-coverage (SSC) estimates relative to exact SSC.
Outputs results/tables/B_summary.csv, B_paired_vs_lac.csv, B_ssc_bias.csv"""
import glob, sys
import numpy as np, pandas as pd

rng = np.random.default_rng(0)


def boot(x, B=1000):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 2:
        return np.nan, np.nan
    m = x[rng.integers(0, len(x), (B, len(x)))].mean(1)
    return np.quantile(m, .025), np.quantile(m, .975)


frames = []
for f in sorted(glob.glob("results/raw/B_*.csv*")):
    frames.append(pd.read_csv(f))
D = pd.concat(frames, ignore_index=True)
keys = ["config"]
metrics_synth = ["cov_exact", "size", "ssc_exact", "hard_decile_min_exact", "cond_dev_exact", "cc_gap_max"]
metrics_real = ["cov", "size", "ssc_full", "cc_gap_mean", "cc_gap_max"]
summ, paired, bias = [], [], []
for cfg, g in D.groupby("config"):
    synth = g.source.iloc[0] == "synth"
    ms = metrics_synth if synth else metrics_real
    piv = {m: g.pivot(index="seed", columns="method", values=m) for m in ms}
    for meth in g.method.unique():
        r = dict(config=cfg, method=meth, source=g.source.iloc[0], n_cal=g.n_cal.iloc[0], reps=len(piv[ms[0]]))
        for c in ["beta", "tau", "noise", "T"]:
            if c in g and g[c].notna().any(): r[c] = g[c].iloc[0]
        for m in ms:
            x = piv[m][meth].values; lo, hi = boot(x)
            r.update({m: np.nanmean(x), f"{m}_lo": lo, f"{m}_hi": hi})
        summ.append(r)
        if meth != "lac":
            for m in ms:
                dlt = (piv[m][meth] - piv[m]["lac"]).values; lo, hi = boot(dlt)
                paired.append(dict(config=cfg, method=meth, metric=m, diff_vs_lac=np.nanmean(dlt), lo=lo, hi=hi))
        gm = g[g.method == meth]
        ref = gm.ssc_exact if synth else gm.ssc_full
        for nn in (200, 1000, 5000):
            if f"ssc30_est_{nn}" in gm:
                e30 = gm[f"ssc30_est_{nn}"] - gm[f"ssc30_tgt_{nn}"]
                lo, hi = boot(e30)
                bias.append(dict(config=cfg, method=meth, n_te=nn, bias=e30.mean(), lo=lo, hi=hi, sd=e30.std(),
                                 rmse=np.sqrt((e30 ** 2).mean()), ref="cells>=30 vs same cells (full/exact)",
                                 frac_defined=gm[f"ssc30_ncell_{nn}"].gt(0).mean()))
            e = gm[f"ssc_est_{nn}"] - ref
            lo, hi = boot(e)
            bias.append(dict(config=cfg, method=meth, n_te=nn, bias=e.mean(), lo=lo, hi=hi, sd=e.std(), rmse=np.sqrt((e ** 2).mean()),
                             ref="exact" if synth else "full-test"))
for n, rows in [("B_summary", summ), ("B_paired_vs_lac", paired), ("B_ssc_bias", bias)]:
    pd.DataFrame(rows).to_csv(f"results/tables/{n}.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
S = pd.DataFrame(summ); Bv = pd.DataFrame(bias)
print(Bv.groupby(["ref", "n_te", "method"])[["bias", "rmse"]].mean().round(3).unstack("method"))
print(S[S.source == "synth"].groupby(["n_cal", "method"])[["size", "ssc_exact", "cond_dev_exact", "cc_gap_max"]].mean().round(3))
