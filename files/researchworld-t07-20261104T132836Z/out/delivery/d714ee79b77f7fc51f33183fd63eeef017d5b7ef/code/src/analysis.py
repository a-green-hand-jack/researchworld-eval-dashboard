"""Aggregate raw per-target predictions into tables with bootstrap CIs and paired comparisons.

Resampling unit: `extrap` (one fixed target set) -> target models (reps are item-selection seeds, averaged);
`random` (new target set per rep) -> reps. Paired differences use the same resample for both methods.
"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr, kendalltau, wilcoxon

sys.path.insert(0, os.path.dirname(__file__))
METRICS = ["mae", "rmse", "spearman", "kendall"]


def load(dirs):
    fs = [f for d in dirs for f in glob.glob(f"{d}/*.parquet")]
    df = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    df["method"] = df.method.replace({"null": "sources_only"})  # runs before the rename used the label `null` (read as NaN by pandas)
    return df.drop_duplicates(["bench", "protocol", "rep", "method", "n", "model"])


def _rank_corr(t, p):
    if np.std(p) == 0:
        return 0.0, 0.0
    return spearmanr(t, p)[0], kendalltau(t, p)[0]


def rep_metrics(g):
    """g: DataFrame for one (bench, protocol, method, n, rep). Returns dict of metrics."""
    t, p = g.true.values, g.pred.values
    e = p - t
    s, k = _rank_corr(t, p)
    return dict(mae=np.abs(e).mean(), rmse=np.sqrt((e ** 2).mean()), bias=e.mean(), spearman=s, kendall=k)


def per_rep(df):
    rows = []
    for k, g in df.groupby(["bench", "protocol", "method", "n", "rep"], sort=False):
        rows.append(dict(zip(["bench", "protocol", "method", "n", "rep"], k)) | rep_metrics(g))
    return pd.DataFrame(rows)


def boot_cell(df_cell_methods, methods, B=500, seed=0):
    """df_cell_methods: raw rows of one (bench, protocol, n) for the given methods.
    Returns {method: array(B, 4)} of bootstrap metric values (MAE, RMSE, Spearman, Kendall) with common resamples."""
    rng = np.random.default_rng(seed)
    proto = df_cell_methods.protocol.iloc[0]
    out = {m: np.zeros((B, 4)) for m in methods}
    piv = {m: df_cell_methods[df_cell_methods.method == m] for m in methods}
    if proto.startswith("extrap"):
        models = np.sort(df_cell_methods.model.unique())
        reps = np.sort(df_cell_methods.rep.unique())
        # arrays (rep, model)
        arr = {}
        for m in methods:
            a = piv[m].pivot(index="rep", columns="model", values="pred").loc[reps, models].values
            arr[m] = a
        tr = piv[methods[0]].drop_duplicates("model").set_index("model").loc[models, "true"].values
        for b in range(B):
            ix = rng.integers(0, len(models), len(models))
            for m in methods:
                a = arr[m][:, ix]
                e = a - tr[ix]
                sp = [_rank_corr(tr[ix], a[r]) for r in range(a.shape[0])]
                out[m][b] = [np.abs(e).mean(), np.sqrt((e ** 2).mean(1)).mean(), np.mean([x[0] for x in sp]), np.mean([x[1] for x in sp])]
    else:
        reps = np.sort(df_cell_methods.rep.unique())
        pr = {m: per_rep(piv[m]).set_index("rep").loc[reps, METRICS].values for m in methods}
        for b in range(B):
            ix = rng.integers(0, len(reps), len(reps))
            for m in methods:
                out[m][b] = pr[m][ix].mean(0)
    return out


def point(df):
    pr = per_rep(df)
    return pr.groupby(["bench", "protocol", "method", "n"])[METRICS + ["bias"]].mean().reset_index()
