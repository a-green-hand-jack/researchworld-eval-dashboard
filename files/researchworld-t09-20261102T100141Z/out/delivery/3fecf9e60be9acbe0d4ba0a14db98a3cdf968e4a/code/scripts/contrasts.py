"""Paired contrasts between estimators on identical (z, y) draws.
For each cell and pair (A, B): MSE ratio MSE_A/MSE_B with a two-level bootstrap CI (graph draws, then replicates within), and the
win rate P(|err_A| < |err_B|).  Usage: contrasts.py EXP [EXP...] -> results/contrasts.csv"""
import os, sys
import numpy as np, pandas as pd
R = os.path.join(os.path.dirname(__file__), "..", "..", "results")
PAIRS = [("ols_f", "dm"), ("ols_f", "hajek_q0.75"), ("ols_f", "ols_poly"), ("ols_f", "ols_f_adj"), ("ols_f2", "ols_f"), ("ridge_rich", "ols_f"), ("gbm", "ols_f")]
rep = pd.read_parquet(os.path.join(R, "replicates.parquet"))
rep = rep[(rep.fit_data == "observed") & rep.experiment.isin(sys.argv[1:] or ["MAIN"])]
rng = np.random.default_rng(1)
rows = []
for (e, tag), c in rep.groupby(["experiment", "tag"], sort=False):
    w = c.pivot_table(index=["graph_id", "rep"], columns="estimator", values="tau_hat")
    gate = c.groupby(["graph_id", "rep"]).tau_true.first()
    for a, b in PAIRS:
        if a not in w or b not in w:
            continue
        ea, eb = (w[a] - gate) ** 2, (w[b] - gate) ** 2
        ok = ea.notna() & eb.notna()
        if ok.sum() < 20:
            continue
        ea, eb = ea[ok], eb[ok]
        gid = ea.index.get_level_values(0).values
        groups = [np.where(gid == g)[0] for g in np.unique(gid)]
        vals = []
        for _ in range(300):
            pick = rng.integers(0, len(groups), len(groups))
            idx = np.concatenate([rng.choice(groups[k], len(groups[k])) for k in pick])
            vals.append(np.log(ea.values[idx].mean() / eb.values[idx].mean()))
        rows.append(dict(experiment=e, tag=tag, A=a, B=b, n_pairs=int(ok.sum()), mse_ratio=ea.mean() / eb.mean(),
                         ratio_lo=np.exp(np.quantile(vals, .025)), ratio_hi=np.exp(np.quantile(vals, .975)),
                         win_rate=float((np.sqrt(ea) < np.sqrt(eb)).mean())))
out = pd.DataFrame(rows)
out.to_csv(os.path.join(R, "contrasts.csv"), index=False)
print(out[out.A.eq("ols_f") & out.B.eq("dm")].assign(sig=lambda d: np.where(d.ratio_hi < 1, "A better", np.where(d.ratio_lo > 1, "B better", "tie"))).sig.value_counts())
