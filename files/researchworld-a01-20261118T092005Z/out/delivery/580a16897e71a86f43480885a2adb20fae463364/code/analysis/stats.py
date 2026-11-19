"""Shared statistics for the analyses: cluster bootstrap, Kendall tau, held-out R^2."""
import numpy as np, pandas as pd

NBOOT = 2000
MIN_CLUSTERS = 5   # a clustering scheme with fewer clusters than this (e.g. an incumbent that is the same model for all but one target) is dropped from the union when another scheme has enough; with one scheme the CI is kept and n_clusters reports how few there are


def clusters_of(df, cols):
    """Integer cluster label per row for the (first) clustering column(s)."""
    return pd.factorize(df[cols[0]] if len(cols) == 1 else df[cols].astype(str).agg("|".join, axis=1))[0]


def cluster_ci(df, stat, cluster_cols=("family", "incumbent_id"), nboot=NBOOT, seed=0, alpha=0.05):
    """Percentile CI of stat(sub_df) under a cluster bootstrap. One bootstrap per clustering column (family of the target; identity of the incumbent it is
    compared with); the reported interval is the union (widest) of the per-scheme intervals. Returns (estimate, lo, hi, n_clusters_min)."""
    est = stat(df); los, his, ncl = [], [], []
    rng = np.random.default_rng(seed)
    for col in cluster_cols:
        if col not in df or df[col].isna().all(): continue
        lab = pd.factorize(df[col])[0]; k = lab.max() + 1; ncl.append(k)
        groups = [np.flatnonzero(lab == c) for c in range(k)]
        vals = []
        for _ in range(nboot):
            pick = rng.integers(0, k, k)
            vals.append(stat(df.iloc[np.concatenate([groups[c] for c in pick])]))
        vals = np.array(vals, float)
        los.append(np.nanpercentile(vals, 100 * alpha / 2)); his.append(np.nanpercentile(vals, 100 * (1 - alpha / 2)))
    if not los: return est, np.nan, np.nan, 0
    use = [i for i, k in enumerate(ncl) if k >= MIN_CLUSTERS] or list(range(len(ncl)))
    return est, min(los[i] for i in use), max(his[i] for i in use), min(ncl[i] for i in use)


def kendall_tau(a, b):
    """Kendall tau-b between two score vectors (ties handled)."""
    from scipy.stats import kendalltau
    t = kendalltau(a, b).statistic
    return float(t) if np.isfinite(t) else np.nan


def r2_heldout(y_true, y_pred):
    y_true = np.asarray(y_true, float); y_pred = np.asarray(y_pred, float)
    sst = ((y_true - y_true.mean()) ** 2).sum()
    return float(1 - ((y_true - y_pred) ** 2).sum() / sst) if sst > 0 else np.nan


def cluster_mean_ci(values, labels, nboot=NBOOT, seed=0, alpha=0.05):
    """Fast cluster bootstrap of a mean. `labels`: list of label arrays, one per clustering scheme; the interval is the union over schemes.
    Returns (mean, lo, hi, smallest number of clusters over the schemes used)."""
    v = np.asarray(values, float); ok = np.isfinite(v); est = float(v[ok].mean()) if ok.any() else np.nan
    rng = np.random.default_rng(seed); los, his, ncl = [], [], []
    for lab in labels:
        lab = pd.factorize(np.asarray(lab)[ok])[0]; k = lab.max() + 1 if len(lab) else 0
        if k < 2: continue
        s_ = np.bincount(lab, weights=v[ok], minlength=k); n_ = np.bincount(lab, minlength=k).astype(float)
        pick = rng.integers(0, k, (nboot, k))
        b = s_[pick].sum(1) / n_[pick].sum(1)
        los.append(np.percentile(b, 100 * alpha / 2)); his.append(np.percentile(b, 100 * (1 - alpha / 2))); ncl.append(k)
    if not los: return est, np.nan, np.nan, 0
    use = [i for i, k in enumerate(ncl) if k >= MIN_CLUSTERS] or list(range(len(ncl)))
    return est, min(los[i] for i in use), max(his[i] for i in use), min(ncl[i] for i in use)
