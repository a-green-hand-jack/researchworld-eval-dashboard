"""A2: check the exact finite-sample law of split-conformal coverage.
Given calibration size n and alpha, V = P(Y in C | calibration) ~ Beta(n+1-l, l), l = floor((n+1)alpha),
and the observed test coverage over n_te points is BetaBinomial(n_te, n+1-l, l)/n_te.
Compares mean, SD and randomised-PIT uniformity (KS) across methods."""
import glob, os, re, sys
import numpy as np, pandas as pd
from scipy import stats

rows = []
for f in sorted(glob.glob("results/raw/A2_*.csv*") + glob.glob("results/raw/A2x_*.csv*") + glob.glob("results/raw/A2tie_*.csv*")):
    d = pd.read_csv(f)
    g0 = lambda c, default: d[c].iloc[0] if (c in d and d[c].notna().any()) else default
    kind = g0("kind", "?")
    n = int(g0("n_cal", -1)) if "n_cal" in d else int(re.search(r"_n(\d+)", f).group(1))
    alpha = float(g0("alpha", 0.1)); K = int(g0("K", 3)); digits = g0("digits", np.nan); nte = int(g0("n_te", 2000))
    l = int(np.floor((n + 1) * alpha)); a, b = n + 1 - l, l
    bb = stats.betabinom(nte, a, b)
    rng = np.random.default_rng(0)
    for m, g in d.groupby("method"):
        k = np.rint(g.marg_cov.values * nte).astype(int)
        pit = bb.cdf(k - 1) + rng.uniform(size=len(k)) * bb.pmf(k)
        ks = stats.kstest(pit, "uniform")
        rows.append(dict(file=os.path.basename(f).replace(".gz", ""), kind=kind, K=K, alpha=alpha, digits=digits, n_cal=n, n_te=nte, method=m, reps=len(g),
                         pred_mean=bb.mean() / nte, obs_mean=g.marg_cov.mean(),
                         obs_mean_se=g.marg_cov.std() / np.sqrt(len(g)), pred_sd=bb.std() / nte, obs_sd=g.marg_cov.std(),
                         ks_stat=ks.statistic, ks_p=ks.pvalue, excess=g.marg_cov.mean() - (1 - alpha)))
out = pd.DataFrame(rows)
out.to_csv("results/tables/A2_beta_law.csv", index=False)
pd.set_option("display.width", 220)
print(out[out.method.isin(["euc", "aitch"])].round(4).to_string())
print("KS p<0.01 among continuous (digits NaN) cases: %d / %d" % ((out[out.digits.isna()].ks_p < 0.01).sum(), out.digits.isna().sum()))
