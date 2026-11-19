#!/usr/bin/env python3
"""experiment-repo#11 (H8): matched heavy-tail experiment e14. Per graph: realised mean degree, harmonic-mean degree d_h, clustering-free summary of
OLS_f / OLS_fd / ORACLE_D bias, SD, RMSE, and the variance-law prediction sigma_r^2 (1 + d_h) / (n p (1-p)). Writes t23_heavy_tail.csv."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
from netgate.paths import results_dir
from netgate.experiments import EXPERIMENTS
from variance_law import world_stats, predicted_sd
import numpy as np, pandas as pd

R = str(results_dir())
S = pd.read_csv(R + "/summary/e14.csv")
cells = EXPERIMENTS["e14"]()
rows = []
for i, c in enumerate(cells):
    n, d, dh, sig2 = world_stats(c)
    s = S[S.cell == i]
    for _, r in s.iterrows():
        rows.append(dict(graph=c["tag"], kind=c["outcome"]["kind"], gamma=c["outcome"]["gamma"], est_name=r.est_name, n=n, mean_deg=d, d_harm=dh,
                         bias=r.bias, bias_se=r.bias_se, sd=r.sd, rmse=r.rmse, n_rep=r.n_rep, n_nan=r.n_nan,
                         sd_pred_dh=predicted_sd(sig2, n, dh) if r.est_name == "OLS_f" else np.nan))
T = pd.DataFrame(rows)
T["sd_obs_over_pred_dh"] = T.sd / T.sd_pred_dh
T.to_csv(R + "/tables/t23_heavy_tail.csv", index=False)
pd.set_option("display.width", 250)
print(T[(T.est_name == "OLS_f") & (T.kind == "linear") & (T.gamma == 0)].round(3).to_string(index=False))
print(T[(T.est_name == "OLS_f") & (T.kind == "concave") & (T.gamma == 2)][["graph", "d_harm", "bias", "bias_se", "sd", "rmse"]].round(3).to_string(index=False))
