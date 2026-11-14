"""Prints the headline numbers quoted in the text (and saves them to paper/tables/headline_numbers.json)."""
import json, numpy as np, pandas as pd
from ac import *
out = {}
# --- E1: leverage prediction
df = load("E1"); df["gl"] = gkey(df)
o = df[(df.estimator == "ols_s") & (df.tag != "er_siga")].copy()
o["pred_raw"] = np.sqrt(o.lev_theory / o.n)
er = o[(o.gl == "ER") & (o.design_type == "bern")]
kappa = float(np.exp(np.mean(np.log(er.rmse / er.pred_raw))))
o["ratio"] = o.rmse / (kappa * o.pred_raw)
b = o[o.design_type == "bern"]; bo = b[b.gl != "ER"]; c = o[o.design_type == "cluster"]
out["kappa"] = kappa; out["n_bern_runs"] = len(b); out["n_bern_out_of_sample"] = len(bo)
out["bern_ratio_median"] = float(b.ratio.median()); out["bern_ratio_range"] = [float(b.ratio.min()), float(b.ratio.max())]
out["bern_oos_within10"] = float(((bo.ratio > 0.9) & (bo.ratio < 1.1)).mean()); out["bern_oos_within15"] = float(((bo.ratio > 0.85) & (bo.ratio < 1.15)).mean())
out["bern_within10"] = float(((b.ratio > 0.9) & (b.ratio < 1.1)).mean())
out["n_cluster_runs"] = len(c); out["cluster_ratio_median"] = float(c.ratio.median()); out["cluster_ratio_iqr"] = [float(c.ratio.quantile(.25)), float(c.ratio.quantile(.75))]
out["cluster_ratio_range"] = [float(c.ratio.min()), float(c.ratio.max())]
out["cluster_ratio_range_ex_fewclusters"] = [float(c[c.n_clusters >= 20].ratio.min()), float(c[c.n_clusters >= 20].ratio.max())]
out["cluster_over_pred_frac"] = float((c.ratio > 1).mean())
# rank correlation across all runs
from scipy.stats import spearmanr
out["spearman_all"] = float(spearmanr(o.pred_raw, o.rmse)[0])
# slope of log rmse vs log(1+d) in ER
er2 = er[er.tag == "er_d"]
out["er_slope_d"] = float(np.polyfit(np.log(er2.graph_d + 1), np.log(er2.rmse), 1)[0])
ern = er[er.tag == "er_n"]
out["er_slope_n"] = float(np.polyfit(np.log(ern.graph_n), np.log(ern.rmse), 1)[0])
# leverage ratios (sim vs theory) bernoulli
out["lev_ratio_bern_range"] = [float((b.lev / b.lev_theory).min()), float((b.lev / b.lev_theory).max())]
# cluster vs Bern on real graphs (K ~ 30 / 40)
for g in ["ego-Facebook", "Stanford3"]:
    s = o[(o.gl == g) & (o.tag == "real")]
    rb = s[s.design_type == "bern"].rmse.mean()
    for K in [10, 30, 100, 300]:
        rc = s[(s.design_type == "cluster") & (s.design_K == K)].rmse.mean()
        out[f"{g}_rmse_bern"] = float(rb); out[f"{g}_rmse_cluster_K{K}"] = float(rc)
        out[f"{g}_cut_K{K}"] = float(s[(s.design_type == "cluster") & (s.design_K == K)].cut_frac.mean())
        out[f"{g}_lev_K{K}"] = float(s[(s.design_type == "cluster") & (s.design_K == K)].lev.mean())
    out[f"{g}_lev_bern"] = float(s[s.design_type == "bern"].lev.mean())
# baselines at real graphs
for g in ["ego-Facebook", "Stanford3"]:
    for des in ["bern", "cluster"]:
        s = df[(df.gl == g) & (df.tag == "real") & (df.design_type == des) & ((df.design_K == 30) | (df.design_type == "bern"))]
        for est in ["ols_s", "dm", "hajek"]:
            t = s[s.estimator == est]
            out[f"{g}_{des}_{est}_rmse"] = float(t.rmse.mean()); out[f"{g}_{des}_{est}_bias"] = float(t.bias.mean())
# Hajek failure rates by degree (ER, Bernoulli, n=4000)
h = df[(df.estimator == "hajek") & (df.tag == "er_d")]
out["hajek_fail_er_d"] = {int(d): float(f) for d, f in h.groupby("graph_d").fail.mean().items()}
# ---- E5: p sweep
e5 = load("E5"); e5["gl"] = gkey(e5)
q = e5[(e5.estimator == "ols_s") & (e5.tag == "p_lin") & (e5.design_type == "bern")].copy()
q["ratio"] = q.rmse / (kappa * np.sqrt(q.lev_theory / q.n))
out["E5_p_lin_bern_ratio_median"] = float(q.ratio.median()); out["E5_p_lin_bern_ratio_range"] = [float(q.ratio.min()), float(q.ratio.max())]
for g in ["SBM", "ego-Facebook", "Stanford3"]:
    t = q[q.gl == g]
    out[f"E5_{g}_rmse_p005_over_p05"] = float(t[t.design_p == 0.05].rmse.mean() / t[t.design_p == 0.5].rmse.mean())
    out[f"E5_{g}_pred_p005_over_p05"] = float(np.sqrt(t[t.design_p == 0.05].lev_theory.mean() / t[t.design_p == 0.5].lev_theory.mean()))
for tg in ["p_pow4", "p_pow05"]:
    t = e5[(e5.estimator == "ols_s") & (e5.tag == tg) & (e5.design_type == "bern")]
    out[f"E5_{tg}_maxabs_bias_minus_theory"] = float((t.bias - t.proj_bias_theory).abs().max())
    out[f"E5_{tg}_median_abs_bias_minus_theory"] = float((t.bias - t.proj_bias_theory).abs().median())
# ---- E4 crossover table
ct = pd.read_csv(f"{TAB}/crossover.csv") if __import__("os").path.exists(f"{TAB}/crossover.csv") else None
if ct is not None:
    out["E4_crossover_ratio_obs_over_pred_range"] = [float((ct.gstar / ct.pred_closed).min()), float((ct.gstar / ct.pred_closed).max())]
    out["E4_crossover_table"] = ct[["d", "n", "gstar", "pred_closed"]].round(3).values.tolist()
json.dump(out, open(f"{TAB}/headline_numbers.json", "w"), indent=1)
for k, v in out.items():
    print(k, v)
