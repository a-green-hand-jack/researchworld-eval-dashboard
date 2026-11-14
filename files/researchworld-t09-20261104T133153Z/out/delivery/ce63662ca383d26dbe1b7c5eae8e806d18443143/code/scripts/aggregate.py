#!/usr/bin/env python3
"""Aggregate raw per-replicate results into per-(cell, estimator) summaries: results/summary/<exp>.csv.
bias/sd/rmse of (est - GATE); rel_rmse = rmse/|GATE|; coverage of 95% normal CIs from HC0 and cluster-robust SEs;
bias_se = max(replicate-level SE, between-world SE of per-world mean error) as a Monte-Carlo standard error."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import glob, os, sys
import numpy as np, pandas as pd

ROOT = results_dir()
META = ["exp", "cell", "graph", "design", "tag"]


COLS = ["bias", "sd", "rmse", "rel_rmse", "bias_se", "cov_hc", "mean_se", "cov_cl", "mean_se_cl", "cov_hac1", "mean_se_hac1", "cov_hac2", "mean_se_hac2", "f1_sd", "supp_hi", "supp_lo"]


BOOT_COLS = ["cov_boot_pct", "cov_boot_sd", "mean_se_boot"]  # only in grids that carry the block bootstrap (e15)


def summarize(g):
    has_boot = "se_boot" in g.columns
    cols = COLS + (BOOT_COLS if has_boot else [])
    ok = g.est.notna()
    e = (g.est - g.gate)[ok]
    out = {"n": g.n.mean(), "mean_deg": g.mean_deg.mean(), "n_rep": int(ok.sum()), "n_nan": int((~ok).sum()), "gate": g.gate.mean()}
    for k in cols:
        out.setdefault(k, np.nan)
    if ok.sum() < 5:
        return pd.Series(out)[["n", "mean_deg", "n_rep", "n_nan", "gate"] + cols]
    out.update(bias=e.mean(), sd=e.std(), rmse=np.sqrt((e**2).mean()))
    out["rel_rmse"] = out["rmse"] / abs(out["gate"]) if out["gate"] else np.nan
    wm = e.groupby(g.world[ok]).mean()
    out["bias_se"] = max(e.std() / np.sqrt(len(e)), wm.std() / np.sqrt(len(wm)) if len(wm) > 1 else 0)
    for col, nm in (("se", "cov_hc"), ("se_cl", "cov_cl"), ("se_hac1", "cov_hac1"), ("se_hac2", "cov_hac2")):
        s = g[col][ok]
        if s.notna().all() and len(s):
            out[nm] = float((e.abs() <= 1.96 * s).mean())
            out["mean_" + col] = float(s.mean())
    out["f1_sd"] = g.f1_sd.mean(); out["supp_hi"] = g.supp_hi.mean(); out["supp_lo"] = g.supp_lo.mean()
    if has_boot and g.se_boot[ok].notna().all() and ok.sum():
        out["cov_boot_sd"] = float((e.abs() <= 1.96 * g.se_boot[ok]).mean()); out["mean_se_boot"] = float(g.se_boot[ok].mean())
        out["cov_boot_pct"] = float(((g.boot_lo[ok] <= g.gate[ok]) & (g.gate[ok] <= g.boot_hi[ok])).mean())
    return pd.Series(out)[["n", "mean_deg", "n_rep", "n_nan", "gate"] + cols]


def summarize_frame(df):
    params = [c for c in df.columns if c.startswith("o_")]
    keys = META + params + ["est_name"]
    for c in keys:  # categorical columns (compact files): plain strings, so the groups sort as in the csv path
        if str(df[c].dtype) == "category":
            df[c] = df[c].astype(object)
    return df.groupby(keys, dropna=False).apply(summarize, include_groups=False).reset_index()


def main(exps, compact=False):
    os.makedirs(os.path.join(ROOT, "summary"), exist_ok=True)
    for exp in exps:
        if compact:  # results/compact/<exp>.parquet instead of the raw csv.gz (float32 storage: summaries agree to ~1e-6 relative)
            path = os.path.join(ROOT, "compact", f"{exp}.parquet")
            if not os.path.exists(path):
                continue
            S = summarize_frame(pd.read_parquet(path)); n = path
        else:
            files = sorted(glob.glob(os.path.join(ROOT, "raw", exp, "*.csv.gz")))
            if not files:
                continue
            S = summarize_frame(pd.concat((pd.read_csv(f) for f in files), ignore_index=True)); n = len(files)
        S.to_csv(os.path.join(ROOT, "summary", f"{exp}.csv"), index=False)
        print(exp, n, "cells ->", S.shape)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--compact"]
    main(args or ["e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8", "e9", "e10", "e11", "e12", "e13", "e14", "e15", "e16", "e17", "e18", "e19", "e20", "e21"], compact="--compact" in sys.argv)
