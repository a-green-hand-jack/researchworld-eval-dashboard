"""Error decomposition (Q4) and pairwise ranking vs score gap (Q6), from per-prediction parquet files.
usage: python analysis_extra.py PRED_DIR OUT_DIR"""
import sys, glob, os
import numpy as np, pandas as pd

pred_dir, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
GAPS = [0, 0.01, 0.02, 0.05, 0.10, 1.01]
q4, q6, q4b = [], [], []
for f in sorted(glob.glob(os.path.join(pred_dir, "*.parquet"))):
    df = pd.read_parquet(f)
    # --- Q4: per target model over seeds: bias and sd of the prediction; MSE = mean(bias^2) + mean(var)
    g = df.assign(err=df.pred - df.true).groupby(["benchmark", "split_type", "n", "method", "target_model"])
    s = g.agg(true=("true", "first"), bias=("err", "mean"), sd=("pred", lambda x: x.std(ddof=0)), cnt=("err", "size"), mse=("err", lambda x: (x ** 2).mean())).reset_index()
    s = s[s.cnt >= 3]
    a = s.groupby(["benchmark", "split_type", "n", "method"]).agg(bias2=("bias", lambda x: (x ** 2).mean()), var=("sd", lambda x: (x ** 2).mean()),
                                                                mse=("mse", "mean"), n_models=("bias", "size")).reset_index()
    q4.append(a)
    # error by true-score tercile within (benchmark, split_type): signed bias and MAE
    s["tercile"] = s.groupby(["benchmark", "split_type", "n", "method"]).true.transform(lambda x: pd.qcut(x.rank(method="first"), 3, labels=False))
    q4b.append(s.groupby(["benchmark", "split_type", "n", "method", "tercile"]).agg(bias=("bias", "mean"), sd=("sd", "mean"), true=("true", "mean")).reset_index())
    # --- Q6: pairwise ordering accuracy by true gap
    for key, r in df.groupby(["benchmark", "split_type", "n", "method", "seed"], sort=False):
        t, p = r["true"].values, r["pred"].values
        iu = np.triu_indices(len(t), 1)
        gap = np.abs(t[:, None] - t[None, :])[iu]
        ok = ((t[:, None] - t[None, :]) * (p[:, None] - p[None, :]))[iu] > 0
        tie = (p[:, None] == p[None, :])[iu]
        ok = ok + 0.5 * tie                                   # tied predictions count half
        b = np.digitize(gap, GAPS) - 1
        for j in range(len(GAPS) - 1):
            m = (b == j) & (gap > 0)
            if m.any():
                q6.append((*key, GAPS[j], GAPS[j + 1], ok[m].sum(), m.sum()))
pd.concat(q4).to_csv(os.path.join(out, "q4_bias_variance.csv"), index=False)
pd.concat(q4b).to_csv(os.path.join(out, "q4_by_true_tercile.csv"), index=False)
q = pd.DataFrame(q6, columns=["benchmark", "split_type", "n", "method", "seed", "gap_lo", "gap_hi", "correct", "pairs"])
q = q.groupby(["benchmark", "split_type", "n", "method", "gap_lo", "gap_hi"]).agg(correct=("correct", "sum"), pairs=("pairs", "sum")).reset_index()
q["pairwise_acc"] = q.correct / q.pairs
q.to_csv(os.path.join(out, "q6_pairwise_by_gap.csv"), index=False)
print("done")
