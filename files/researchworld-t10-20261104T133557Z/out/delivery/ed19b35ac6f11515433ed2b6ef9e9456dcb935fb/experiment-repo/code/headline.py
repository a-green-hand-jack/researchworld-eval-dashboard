"""headline.py  -- compact like-for-like tables (width ratio vs PPI++ of the same calibration, coverage) from the summaries.
usage: headline.py RESULTS_DIR     writes headline_{mean_real,synth,ols_real}.csv into RESULTS_DIR"""
import sys, os, pandas as pd
R = sys.argv[1] if len(sys.argv) > 1 else "../results"
CF = ["cf_lin_f", "cf_iso_f", "cf_poly_f", "cf_gbm_f", "cf_lin_fX", "cf_gbm_fX"]

def wide(df, keys, methods, val):
    d = df[df.method.isin(methods)]
    return d.pivot_table(index=keys, columns="method", values=val).reindex(columns=[m for m in methods if m in set(d.method)])

def tab(df, keys, methods):
    r = wide(df, keys, methods, "ratio_lfl").add_prefix("ratio_lfl:")
    c = wide(df, keys, methods + ["ppi++", "classical"], "coverage").add_prefix("cov:")
    return r.join(c)

m = pd.read_csv(f"{R}/summary_mean_real.csv")
tab(m, ["dataset", "n"], CF).round(4).to_csv(f"{R}/headline_mean_real.csv")
s = pd.read_csv(f"{R}/summary_synth.csv")
tab(s, ["scenario", "rho", "n"], CF + ["oracle"]).round(4).to_csv(f"{R}/headline_synth.csv")
if os.path.exists(f"{R}/summary_ols_real.csv"):
    o = pd.read_csv(f"{R}/summary_ols_real.csv")
    om = ["cv_f_coord", "cv_f_full", "cv_cf_lin_fX_full", "cv_cf_gbm_fX_full", "classical", "ppi_lib"]
    # `ratio` in the OLS summary is the width relative to ppi++_lib (the baseline)
    r = wide(o, ["n", "coord"], om, "ratio").add_prefix("ratio_vs_ppi++:")
    c = wide(o, ["n", "coord"], om + ["ppi++_lib"], "coverage").add_prefix("cov:")
    r.join(c).round(4).to_csv(f"{R}/headline_ols_real.csv")
