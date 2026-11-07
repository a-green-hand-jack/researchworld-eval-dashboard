#!/usr/bin/env python3
"""experiment-repo#13: scope of the estimator (e16, the Bernoulli cells of e2 re-run with the same seeds).
Pairing check: OLS_f / OLS_zf / OLS_big / GBM of e16 must equal e2's (same worlds and assignments). Table t25_estimator_scope.csv: per estimator over the
cells: median and mean RMSE ratio to OLS_f, share of cells with lower RMSE than OLS_f, per truth shape x p; t25b: per-cell values."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
from netgate.experiments import EXPERIMENTS
import numpy as np, pandas as pd
R = str(results_dir())
e2, e16 = pd.read_csv(R + "/summary/e2.csv"), pd.read_csv(R + "/summary/e16.csv")
idx2 = [i for i, c in enumerate(EXPERIMENTS["e2"]()) if c["design"].startswith("bern")]
m = {j: i for j, i in enumerate(idx2)}
e16["cell2"] = e16.cell.map(m)
chk = e16[e16.est_name.isin(["OLS_f", "OLS_zf", "OLS_big", "GBM"])].merge(e2[["cell", "est_name", "bias", "rmse"]], left_on=["cell2", "est_name"], right_on=["cell", "est_name"], suffixes=("", "_e2"))
print("pairing with e2: max |rmse - rmse_e2| =", float((chk.rmse - chk.rmse_e2).abs().max()), "max |bias diff| =", float((chk.bias - chk.bias_e2).abs().max()), "n =", len(chk))
e16["p"] = e16.design.str.split(":").str[1].astype(float)
piv = e16.pivot_table(index=["cell", "graph", "o_kind", "p"], columns="est_name", values="rmse")
bias = e16.pivot_table(index=["cell", "graph", "o_kind", "p"], columns="est_name", values="bias")
sd = e16.pivot_table(index=["cell", "graph", "o_kind", "p"], columns="est_name", values="sd")
piv.reset_index().to_csv(R + "/tables/t25b_estimator_scope_cells.csv", index=False)
rows = []
for est in [c for c in piv.columns if c != "OLS_f"]:
    for (kind, p), g in list(piv.groupby(level=["o_kind", "p"])) + [(("all", "all"), piv)]:
        ok = g[est].notna()
        if not ok.any(): continue
        r = g.loc[ok, est] / g.loc[ok, "OLS_f"]
        gi = g.index[ok]
        rows.append(dict(est_name=est, truth=kind, p=p, n_cells=int(ok.sum()), median_rmse_ratio=r.median(), mean_rmse_ratio=r.mean(),
                         share_better_than_OLS_f=float((r < 1).mean()), median_abs_bias=bias.loc[gi, est].abs().median(), median_sd=sd.loc[gi, est].median(),
                         median_abs_bias_OLS_f=bias.loc[gi, "OLS_f"].abs().median(), median_sd_OLS_f=sd.loc[gi, "OLS_f"].median()))
T = pd.DataFrame(rows); T.to_csv(R + "/tables/t25_estimator_scope.csv", index=False)
pd.set_option("display.width", 250)
print(T[(T.truth == "all")].round(3).to_string(index=False))
print(T[(T.truth != "all")].round(2)[["est_name", "truth", "p", "n_cells", "median_rmse_ratio", "share_better_than_OLS_f"]].to_string(index=False))
