"""Aggregate raw CI results into coverage / width tables.

Coverage uses the Wald-CI indicator per replication; its Monte Carlo SE is sqrt(p(1-p)/R).
Width ratios are computed as mean(width_method) / mean(width_ppi_pp) over the same replications
(the same labeled and unlabeled samples are used for every method within a cell).

Usage: python summarize.py RAW.csv OUT_PREFIX [--group-cols ...]
"""
import sys
import numpy as np
import pandas as pd


def summarize(df, keys):
    g = df.groupby(keys + ["method"])
    s = g.agg(R=("covered", "size"), coverage=("covered", "mean"),
              mean_width=("width", "mean"), sd_est=("est", "std"),
              mean_truth=("truth", "mean")).reset_index()
    s["cov_se"] = np.sqrt(s.coverage * (1 - s.coverage) / s.R)
    # width ratio versus PPI++ within the same cell (paired by replication)
    base = df[df.method == "ppi_pp"].groupby(keys + ["rep"]).width.mean().rename("w_pp").reset_index()
    m = df.merge(base, on=keys + ["rep"])
    m["wratio"] = m.width / m.w_pp
    r = m.groupby(keys + ["method"]).wratio.mean().rename("width_ratio_vs_ppi_pp").reset_index()
    s = s.merge(r, on=keys + ["method"])
    return s


if __name__ == "__main__":
    raw, out = sys.argv[1], sys.argv[2]
    df = pd.read_csv(raw)
    keys = ["scenario"] if "scenario" in df.columns else ["dataset", "regime"]
    keys = keys + ["n", "ratio"]
    s = summarize(df, keys)
    s.to_csv(out + "_summary.csv", index=False)
    print(s.groupby("method")[["coverage", "width_ratio_vs_ppi_pp"]].mean().round(4))
