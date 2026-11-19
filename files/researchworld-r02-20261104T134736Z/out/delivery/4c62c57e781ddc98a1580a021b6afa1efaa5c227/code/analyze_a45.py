"""A4 (shift) and A5 (split vs CV+/jackknife+) summaries with bootstrap CIs over replications.
Outputs results/tables/A4_summary.csv, A5_summary.csv, A5_paired_vs_split.csv"""
import glob
import numpy as np, pandas as pd
from scipy.stats import beta

rng = np.random.default_rng(0)


def boot(x, B=2000):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 2: return np.nan, np.nan
    m = x[rng.integers(0, len(x), (B, len(x)))].mean(1)
    return np.quantile(m, .025), np.quantile(m, .975)


frames = [pd.read_csv(f) for f in sorted(glob.glob("results/raw/A4_*.csv*"))]
if frames:
    D = pd.concat(frames); rows = []
    for (k, dl, m), g in D.groupby(["kind", "delta", "method"]):
        r = dict(kind=k, delta=dl, method=m, reps=len(g), ess=g.ess.mean())
        for c in ["cov_unweighted", "cov_weighted"]:
            lo, hi = boot(g[c]); r.update({c: g[c].mean(), c + "_lo": lo, c + "_hi": hi})
        r["inf_frac_w"] = g.inf_frac_w.mean()
        rows.append(r)
    A4 = pd.DataFrame(rows); A4.to_csv("results/tables/A4_summary.csv", index=False)
    print(A4.round(3).to_string())
frames = [pd.read_csv(f) for f in sorted(glob.glob("results/raw/A5_*.csv*"))]
if frames:
    D = pd.concat(frames); rows = []; prow = []
    for (k, n, mode, m), g in D.groupby(["kind", "n", "mode", "method"]):
        r = dict(kind=k, n=n, mode=mode, method=m, reps=len(g), secs=g.secs.mean())
        for c in ["cov", "true_marg_cov", "true_x0_10_min", "true_x0_10_dev", "log_vol_ratio"]:
            lo, hi = boot(g[c]); r.update({c: g[c].mean(), c + "_lo": lo, c + "_hi": hi})
        rows.append(r)
    A5 = pd.DataFrame(rows); A5.to_csv("results/tables/A5_summary.csv", index=False)
    for (k, n, m), g in D.groupby(["kind", "n", "method"]):
        base = g[g["mode"] == "split"].set_index("seed")
        for mode in ("cv+", "jackknife+"):
            o = g[g["mode"] == mode].set_index("seed")
            if len(o) == 0: continue
            for c in ["true_marg_cov", "true_x0_10_min", "log_vol_ratio"]:
                dlt = (o[c] - base[c]).dropna().values; lo, hi = boot(dlt)
                prow.append(dict(kind=k, n=n, method=m, mode=mode, metric=c, diff_vs_split=dlt.mean(), lo=lo, hi=hi, reps=len(dlt)))
    pd.DataFrame(prow).to_csv("results/tables/A5_paired_vs_split.csv", index=False)
    print(A5[["kind", "n", "mode", "method", "cov", "true_marg_cov", "true_x0_10_min", "log_vol_ratio"]].round(3).to_string())
