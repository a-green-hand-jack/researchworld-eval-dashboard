"""Aggregate replication-level results into summary metrics and paper tables.

Reads /work/results/reps_E{1..4}.csv (written by run_sim.py) and writes
/work/results/summary_E{k}.csv plus LaTeX tables in /work/paper/tables/.
Metrics per (setting, estimator):
  bias, mcse_bias (Monte Carlo s.e. of the bias), sd (across replications),
  rmse, cov_hc1 / cov_cr1 (coverage of nominal 95% t intervals),
  se_hc1 / se_cr1 (mean estimated s.e.), width_cr1 (mean CI width), ratio_cr1 (mean se / sd).
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "/work/code")
from gate import dgp  # noqa: E402

RES = "/work/results"
TAB = "/work/paper/tables"
KEYS = ["exp", "setting", "graph", "n", "n_clusters", "mean_deg", "mech", "design", "p", "estimator", "truth"]
NAMES = {"dim": "DiM", "r1": "OLS $z$", "r2": "OLS $z,f_1$", "r3": "OLS $z,f_1,f_2$",
         "r4": "OLS $z,f_1,f_1^2$", "r5": "GBM"}


def _ci(est, se, df, level=0.975):
    t = stats.t.ppf(level, df)
    return est - t * se, est + t * se


def add_coverage(df):
    for v in ["hc1", "cr1"]:
        lo, hi = _ci(df["est"], df[f"se_{v}"], df[f"df_{v}"])
        df[f"cov_{v}"] = ((lo <= df["truth"]) & (df["truth"] <= hi)).astype(float)
        df.loc[~np.isfinite(df[f"se_{v}"]), f"cov_{v}"] = np.nan
        df[f"width_{v}"] = hi - lo
    return df


def summarize(df):
    df = add_coverage(df.copy())
    df["err"] = df["est"] - df["truth"]
    keys = ["exp", "setting", "graph", "n", "n_clusters", "mean_deg", "mech", "design", "p", "estimator", "truth"]
    g = df.groupby(keys, dropna=False)
    out = g.agg(R=("err", "size"), bias=("err", "mean"), sd=("est", "std"),
                rmse=("err", lambda e: float(np.sqrt(np.mean(e**2)))),
                se_hc1=("se_hc1", "mean"), se_cr1=("se_cr1", "mean"),
                cov_hc1=("cov_hc1", "mean"), cov_cr1=("cov_cr1", "mean"),
                width_cr1=("width_cr1", "mean"), width_hc1=("width_hc1", "mean")).reset_index()
    out["mcse_bias"] = out["sd"] / np.sqrt(out["R"])
    out["rel_bias"] = out["bias"] / out["truth"].abs()
    out["ratio_cr1"] = out["se_cr1"] / out["sd"]
    out["ratio_hc1"] = out["se_hc1"] / out["sd"]
    return out


def load_raw(exp):
    """Concatenate the per-setting replication files for one experiment."""
    d = os.path.join(RES, "raw")
    files = sorted(f for f in os.listdir(d) if f.startswith(exp + "__") and f.endswith("__R500.csv"))
    if not files:
        return None, 0
    return pd.concat([pd.read_csv(os.path.join(d, f)) for f in files], ignore_index=True), len(files)


def main():
    for exp in ["E1", "E2", "E3", "E4"]:
        df, nfiles = load_raw(exp)
        if nfiles == 0:
            print("no results yet for", exp)
            continue
        s = summarize(df)
        s.to_csv(os.path.join(RES, f"summary_{exp}.csv"), index=False)
        print(exp, nfiles, "settings,", len(s), "setting-estimator rows")


if __name__ == "__main__":
    main()
