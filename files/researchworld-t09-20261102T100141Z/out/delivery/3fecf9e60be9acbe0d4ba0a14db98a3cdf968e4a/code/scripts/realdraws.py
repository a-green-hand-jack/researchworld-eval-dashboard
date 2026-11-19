"""Real-graph results over independent baseline draws (MAIN_realdraws: 8 draws x 60 assignments per cell).
Writes results/realdraws_perdraw.csv (rel. RMSE and bias per cell x estimator x baseline draw `graph_id`; relative = / |GATE|) and
results/realdraws_summary.csv (mean, SD, min, max of rel. RMSE across draws; number of draws in which OLS(z,f) beats DM and OLS(z,f)+covariates beats OLS(z,f))."""
import os
import numpy as np, pandas as pd
R = os.path.join(os.path.dirname(__file__), "..", "..", "results")
r = pd.read_parquet(os.path.join(R, "replicates.parquet"))
r = r[(r.experiment == "MAIN_realdraws") & (r.fit_data == "observed")].copy()
r["err"] = r.tau_hat - r.tau_true
key = ["graph", "mechanism", "design", "p"]
pd_ = (r.groupby(key + ["estimator", "graph_id"])
       .apply(lambda c: pd.Series(dict(n_rep=len(c), frac_undefined=c.tau_hat.isna().mean(), gate=c.tau_true.iloc[0], bias=np.nanmean(c.err),
                                       rmse=np.sqrt(np.nanmean(c.err ** 2)) if c.tau_hat.notna().any() else np.nan)), include_groups=False)
       .reset_index())
pd_["rel_rmse"] = pd_.rmse / pd_.gate.abs()
pd_.to_csv(os.path.join(R, "realdraws_perdraw.csv"), index=False)
s = pd_.groupby(key + ["estimator"]).rel_rmse.agg(mean="mean", sd="std", min="min", max="max", n_draws="count").reset_index()
w = pd_.pivot_table(index=key + ["graph_id"], columns="estimator", values="rmse")
wins = pd.DataFrame({"ols_beats_dm": (w.ols_f < w.dm), "adj_beats_ols": (w.ols_f_adj < w.ols_f)}).groupby(key).sum().reset_index()
s = s.merge(wins, on=key, how="left")
s.loc[s.estimator != "ols_f", ["ols_beats_dm", "adj_beats_ols"]] = np.nan
s.to_csv(os.path.join(R, "realdraws_summary.csv"), index=False)
print(len(pd_), "per-draw rows;", len(s), "summary rows")
