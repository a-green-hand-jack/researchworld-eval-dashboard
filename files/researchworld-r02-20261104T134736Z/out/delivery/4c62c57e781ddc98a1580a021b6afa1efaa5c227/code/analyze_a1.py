"""A1 summary: per config x method means with CIs over replications, and paired differences to the
Euclidean baseline.  Output: results/tables/A1_summary.csv, A1_paired_vs_euc.csv"""
import glob, sys
import numpy as np, pandas as pd

METRICS = ["log_vol_ratio", "true_x0_10_min", "true_x0_10_dev", "true_bd_10_min", "true_bd_10_dev", "marg_cov", "true_marg_cov"]
rng = np.random.default_rng(0)
B = 2000


def boot_ci(x):
    x = np.asarray(x); x = x[~np.isnan(x)]
    n = len(x)
    if n < 2:
        return np.nan, np.nan
    idx = rng.integers(0, n, (B, n))
    m = x[idx].mean(1)
    return np.quantile(m, 0.025), np.quantile(m, 0.975)


PFX = sys.argv[1] if len(sys.argv) > 1 else "A1"   # "A1m": Mahalanobis add-on files
files = sorted(glob.glob(f"results/raw/{PFX}_*.csv*"))
summ, paired = [], []
for f in files:
    d = pd.read_csv(f)
    cfg = d.config.iloc[0]
    P = {m: d.pivot(index="seed", columns="method", values=m) for m in METRICS}
    for meth in d.method.unique():
        row = dict(config=cfg, method=meth, reps=len(P["marg_cov"]), kind=d.kind.iloc[0], K=d.K.iloc[0], hetero=d.hetero.iloc[0],
                   form=d.form.iloc[0], nl=d.nl.iloc[0] if "nl" in d else 0.0, a=d.a.iloc[0], s=d.s.iloc[0], digits=d.digits.iloc[0] if "digits" in d else np.nan)
        for m in METRICS:
            x = P[m][meth].values
            lo, hi = boot_ci(x)
            row.update({f"{m}": np.nanmean(x), f"{m}_lo": lo, f"{m}_hi": hi})
        summ.append(row)
        if meth != "euc":
            for m in ["log_vol_ratio", "true_x0_10_min", "true_bd_10_min", "true_x0_10_dev"]:
                diff = (P[m][meth] - P[m]["euc"]).values
                lo, hi = boot_ci(diff)
                paired.append(dict(config=cfg, method=meth, metric=m, diff_vs_euc=np.nanmean(diff), lo=lo, hi=hi,
                                   win_rate=np.nanmean((diff < 0) if m in ("log_vol_ratio", "true_x0_10_dev") else (diff > 0))))
S = pd.DataFrame(summ); Pd = pd.DataFrame(paired)
S.to_csv(f"results/tables/{PFX}_summary.csv", index=False); Pd.to_csv(f"results/tables/{PFX}_paired_vs_euc.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
for cfg, g in S.groupby("config"):
    print(cfg, g.reps.iloc[0])
    print(g.set_index("method")[["log_vol_ratio", "true_x0_10_min", "true_bd_10_min", "true_x0_10_dev"]].round(3).sort_values("log_vol_ratio").to_string())
