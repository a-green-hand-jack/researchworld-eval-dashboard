#!/usr/bin/env python3
"""Claim-level tables from results/summary/*.csv -> results/tables/*.csv (and a printed digest).
Each table is tied to a hypothesis (H1..H8) / claim (C1..C6) of story-repo's plan."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import os, re, sys
import numpy as np, pandas as pd

R = results_dir()
OUT = os.path.join(R, "tables"); os.makedirs(OUT, exist_ok=True)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)


def load(e):
    p = os.path.join(R, "summary", f"{e}.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p)
    d["fam"] = d.graph.str.split(":").str[0].replace({"stanford3": "stanford3"})
    d["gname"] = d.graph.map(lambda s: {"sbm:5000,50,20,0.8": "SBM", "ba:5000,10": "BA", "ws:5000,20,0.1": "WS", "er:5000,20": "ER",
                                         "stanford3": "Stanford3", "ego": "ego-FB"}.get(s, s))
    return d


def save(df, name):
    df.to_csv(os.path.join(OUT, name + ".csv"), index=False)
    print(f"\n== {name} ==")
    print(df.round(3).to_string(index=False))


def nominal(d):
    """nominal n, mean degree, p from the graph/design strings."""
    d = d.copy()
    a = d.graph.str.extract(r"^(\w+):(\d+),(?:\d+,)?(\d+)")
    d["n_nom"] = a[1].astype(float); d["d_nom"] = a[2].astype(float)
    d["p"] = d.design.str.extract(r"bern:([\d.]+)")[0].astype(float)
    return d


def main():
    e1, e2, e3, e4, e5, e6, e7, e8, e9, e10 = [load(f"e{i}") for i in range(1, 11)]
    EST = ["DM", "HajekFull", "OLS_f", "OLS_zf", "OLS_fd", "OLS_f2", "OLS_quad", "OLS_big", "ORACLE_D"]

    # ---- C2/H6: accuracy by interference strength (linear-in-means truth)
    if e1 is not None:
        t = e1[e1.est_name.isin(["DM", "HajekFull", "OLS_f", "OLS_big", "ORACLE_D"])]
        save(t[["gname", "design", "o_gamma", "est_name", "gate", "bias", "bias_se", "sd", "rmse", "rel_rmse", "cov_hc", "cov_cl", "n_nan"]]
             .sort_values(["gname", "design", "o_gamma", "est_name"]), "t1_strength")
        # DM bias slope vs gamma, and smallest gamma at which DM RMSE exceeds OLS_f RMSE
        rows = []
        for (g, des), d in e1.groupby(["gname", "design"]):
            dm = d[d.est_name == "DM"].set_index("o_gamma"); ols = d[d.est_name == "OLS_f"].set_index("o_gamma")
            slope = np.polyfit(dm.index, dm.bias, 1)[0]
            cross = [gm for gm in sorted(dm.index) if dm.rmse[gm] > ols.rmse[gm]]
            rows.append({"graph": g, "design": des, "dm_bias_slope_per_gamma": slope, "dm_bias_at_gamma0": dm.bias[0.0],
                         "ols_f_bias_at_gamma4": ols.bias[4.0], "ols_f_rmse_g0": ols.rmse[0.0], "dm_rmse_g0": dm.rmse[0.0],
                         "first_gamma_dm_worse": cross[0] if cross else np.nan})
        save(pd.DataFrame(rows), "t1b_dm_vs_regression")

    # ---- H1/H2/C1: noiseless bias
    if e8 is not None:
        t = e8[e8.est_name.isin(["ORACLE", "ORACLE_D", "OLS_f", "OLS_zf", "OLS_quad", "OLS_cubic", "OLS_cnt", "GBM", "DM", "HajekFull"])]
        save(t[["gname", "o_kind", "design", "est_name", "gate", "bias", "sd", "rel_rmse"]].assign(rel_bias=t.bias / t.gate)
             .sort_values(["o_kind", "gname", "design", "est_name"]), "t2_noiseless_bias")
        o = e8[e8.est_name == "ORACLE"]
        print("\nH1 noiseless ORACLE: max |bias| =", o.bias.abs().max(), "over", len(o), "cells")
    p = os.path.join(R, "summary", "theory_vs_sim_e9.csv")
    if os.path.exists(p):
        T = pd.read_csv(p)
        T["gname"] = T.graph.map({"sbm:5000,50,20,0.8": "SBM", "ba:5000,10": "BA", "stanford3": "Stanford3"})
        s = T.groupby(["gname", "o_kind"]).apply(lambda d: pd.Series({
            "cells": len(d), "corr": np.corrcoef(d.bias, d.pred_exact)[0, 1], "mae_exact": (d.bias - d.pred_exact).abs().mean(),
            "max_abs_dev_exact": (d.bias - d.pred_exact).abs().max(), "mae_largedeg": (d.bias - d.pred_largedeg).abs().mean(),
            "max_abs_bias": d.bias.abs().max()}), include_groups=False).reset_index()
        save(s, "t3_theory_vs_sim")

    # ---- H3: bias vs n
    if e10 is not None:
        d = nominal(e10)
        save(d[["n_nom", "o_kind", "design", "est_name", "gate", "bias", "bias_se", "sd", "rmse"]].sort_values(["o_kind", "design", "est_name", "n_nom"]), "t4_bias_vs_n")

    # ---- H4: variance scaling
    if e3 is not None:
        d = nominal(e3); d = d[d.fam.isin(["er"])]
        rows = []
        for est in ["OLS_f", "ORACLE", "OLS_fd", "OLS_big"]:
            x = d[d.est_name == est]
            if len(x) < 6: continue
            X = np.column_stack([np.ones(len(x)), np.log(x.n_nom), np.log(x.d_nom)])
            b, *_ = np.linalg.lstsq(X, np.log(x.sd), rcond=None)
            res = np.log(x.sd) - X @ b
            cov = np.linalg.inv(X.T @ X) * res.var(ddof=3)
            rows.append({"estimator": est, "cells": len(x), "exp_n": b[1], "se_n": np.sqrt(cov[1, 1]), "exp_d": b[2], "se_d": np.sqrt(cov[2, 2]), "pred_n": -0.5, "pred_d": 0.5})
        save(pd.DataFrame(rows), "t5_scaling_exponents")
        save(d[d.est_name == "OLS_f"][["n_nom", "d_nom", "sd", "bias", "cov_hc", "cov_cl", "cov_hac1", "cov_hac2"]].sort_values(["d_nom", "n_nom"]), "t5b_sd_grid_er")
    # p-dependence from e4
    if e4 is not None:
        d = nominal(e4[(e4.tag.str.contains("bern_p")) & (e4.o_kind == "linear")])
        t = d[d.est_name.isin(["OLS_f", "ORACLE_D"])][["gname", "p", "est_name", "sd", "bias", "bias_se", "rmse", "cov_cl"]].copy()
        t["pred_rel_sd"] = np.sqrt(1 / (t.p * (1 - t.p)))
        t["sd_ratio_to_p0.5"] = t.sd / t.groupby(["gname", "est_name"]).sd.transform(lambda s: s[t.loc[s.index, "p"] == 0.5].iloc[0] if (t.loc[s.index, "p"] == 0.5).any() else np.nan)
        t["pred_ratio_to_p0.5"] = t.pred_rel_sd / np.sqrt(1 / 0.25)
        save(t.sort_values(["gname", "est_name", "p"]), "t5c_p_dependence")

    # ---- H5/C4: cluster quality
    if e4 is not None:
        d = e4[e4.est_name.isin(["OLS_f", "OLS_quad", "ORACLE_D", "DM"])]
        d = d[d.tag.str.contains("louv_res|rand_res")]
        d = d.assign(clus=d.tag.str.split("|").str[1].str.replace("_res", ""), res=d.design.str.extract(r":([\d.]+),")[0].astype(float))
        save(d[["gname", "o_kind", "clus", "res", "est_name", "gate", "bias", "bias_se", "sd", "rmse", "cov_cl"]].sort_values(["gname", "o_kind", "est_name", "res", "clus"]), "t6_cluster_quality")
        d2 = e4[e4.tag.str.startswith("sbm_f")]
        d2 = d2[d2.est_name.isin(["OLS_f", "ORACLE_D", "DM"])]
        save(d2[["tag", "o_kind", "design", "est_name", "bias", "bias_se", "sd", "rmse", "cov_cl"]].sort_values(["o_kind", "est_name", "tag", "design"]), "t6b_planted_blocks")

    # ---- misspecification x design (C2/C3)
    if e2 is not None:
        d = e2[e2.est_name.isin(["DM", "HajekFull", "OLS_f", "OLS_zf", "OLS_quad", "OLS_cubic", "OLS_big", "GBM", "ORACLE_D"])]
        save(d[["gname", "o_kind", "design", "est_name", "gate", "bias", "bias_se", "sd", "rmse", "rel_rmse", "cov_cl", "cov_hac2"]]
             .sort_values(["gname", "o_kind", "design", "est_name"]), "t7_misspecification")

    # ---- H7/C5: coverage
    if e6 is not None:
        d = e6[e6.est_name.isin(["OLS_f", "OLS_fd", "OLS_quad", "ORACLE_D"])]
        save(d[["gname", "o_kind", "design", "tag", "est_name", "bias", "sd", "mean_se", "cov_hc", "mean_se_cl", "cov_cl", "mean_se_hac1", "cov_hac1", "mean_se_hac2", "cov_hac2"]]
             .sort_values(["gname", "o_kind", "design", "tag", "est_name"]), "t8_coverage")

    # ---- other mechanisms (C6/H8)
    if e7 is not None:
        d = e7.copy(); d["mech"] = d.o_mech + d.o_rho.map(lambda r: "" if pd.isna(r) else f"(rho={r})")
        save(d[["gname", "mech", "design", "est_name", "gate", "bias", "bias_se", "sd", "rmse", "rel_rmse", "cov_cl"]]
             .sort_values(["mech", "gname", "design", "est_name"]), "t9_mechanisms")

    # ---- noise/baseline
    if e5 is not None:
        save(e5[["gname", "design", "o_sigma", "o_alpha_graph", "est_name", "bias", "sd", "rmse", "cov_cl"]]
             .sort_values(["gname", "design", "o_sigma", "o_alpha_graph", "est_name"]), "t10_noise_baseline")


if __name__ == "__main__":
    main()
