#!/usr/bin/env python3
"""experiment-repo#16(3): design-based baselines under the cluster design at high degree (e19). Writes t24_cluster_hajek.csv: bias, bias_se, sd, rmse,
n_nan per cell and estimator, and RMSE relative to OLS_f."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import pandas as pd
R = str(results_dir())
d = pd.read_csv(R + "/summary/e19.csv")
T = d[["tag", "o_kind", "est_name", "n", "mean_deg", "n_rep", "n_nan", "gate", "bias", "bias_se", "sd", "rmse"]].copy()
ref = d[d.est_name == "OLS_f"].set_index(["tag", "o_kind"]).rmse
T["rmse_over_ols_f"] = [r.rmse / ref[(r.tag, r.o_kind)] for r in T.itertuples()]
T = T.rename(columns={"tag": "graph_resolution", "o_kind": "truth"})
T.to_csv(R + "/tables/t24_cluster_hajek.csv", index=False)
print(T.pivot_table(index=["truth", "graph_resolution"], columns="est_name", values="rmse_over_ols_f").round(2).to_string())
