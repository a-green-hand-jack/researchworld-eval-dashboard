"""Aggregate replicate-level CSVs into summary tables with 95% t-intervals over independent replicates."""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats

METRICS = ["cov05", "cov10", "cov20", "ymax_min", "ymax_max", "ent_min", "ent_max", "scale_min", "scale_max", "bnd_cov",
           "int_cov", "wsc", "vol_med", "vol_mean", "inf_frac", "size05", "size10", "size20", "classcov_min", "classcov_mean",
           "sscv_min", "empty_frac", "conf_min", "conf_max", "ambig_min", "ambig_max", "pool_frac", "maxsize_frac_all", "pool_frac", "or_gap", "or_rmse", "or_q05", "or_q95", "ess"]


def summarise(df, by):
    out = []
    for key, g in df.groupby(by, dropna=False):
        row = dict(zip(by, key if isinstance(key, tuple) else (key,)))
        row["n_rep"] = g["rep"].nunique()
        for m in METRICS:
            if m in g and g[m].notna().sum() > 1:
                v = g[m].dropna().values
                h = stats.t.ppf(0.975, len(v) - 1) * v.std(ddof=1) / np.sqrt(len(v))
                row[m], row[m + "_lo"], row[m + "_hi"] = v.mean(), v.mean() - h, v.mean() + h
        out.append(row)
    return pd.DataFrame(out)


def derived(df):
    """Per-replicate derived reliability measures (computed before averaging so CIs are over replicates)."""
    df = df.copy()
    if "ymax_min" in df:
        df["ymax_gap"] = df["ymax_max"] - df["ymax_min"]
        df["ent_gap"] = df["ent_max"] - df["ent_min"]
        df["cov10_err"] = df["cov10"] - 0.9
    return df


if __name__ == "__main__":
    for tag, pat, by in [("e1_main", "results/e1/main_*.csv", ["family", "D", "hetero", "pred", "method"]),
                         ("e1_sens_eps", "results/e1/sens_eps*.csv", ["family", "D", "hetero", "pred", "eps", "method"]),
                         ("e1_sens_ncal", "results/e1/sens_ncal*.csv", ["family", "D", "hetero", "pred", "n_cal", "method"]),
                         ("e2", "results/e23/e2_*[0-9].csv", ["logits", "T", "n_cal", "method"]),
                         ("e3", "results/e23/e3_*.csv", ["logits", "T", "n_cal", "method"]),
                         ("e4", "results/e4/shift_*.csv", ["family", "delta", "method", "weighted"])]:
        fs = glob.glob(pat)
        if not fs:
            continue
        df = derived(pd.concat([pd.read_csv(f) for f in fs]))
        METRICS.extend([m for m in ["ymax_gap", "ent_gap", "cov10_err"] if m not in METRICS])
        summarise(df, by).to_csv(f"results/{tag}_summary.csv", index=False)
        print(tag, len(fs), "files")
    fs = glob.glob("results/e23/e2_*_ident.csv")
    if fs:
        d = pd.concat([pd.read_csv(f) for f in fs])
        d.groupby(["logits", "T", "n_cal"]).mean(numeric_only=True).reset_index().to_csv("results/e2_ident_summary.csv", index=False)
