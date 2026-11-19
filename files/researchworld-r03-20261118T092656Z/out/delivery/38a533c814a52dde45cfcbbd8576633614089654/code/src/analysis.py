"""Aggregation, bootstrap CIs over held-out models, paired differences with Holm correction."""
import glob, json
import numpy as np, pandas as pd

KEYS = ['model', 'k', 'selector', 'method']


def load(setting_dir):
    """Raw records of every repetition (results/M/rec_rep*.parquet); if they are absent (the delivered copy ships only the compact
    per-model table written by exp/make_pm.py), the per-model table instead."""
    fs = sorted(glob.glob(f"{setting_dir}/rec_rep*.parquet"))
    if not fs:
        return pd.read_parquet(f"{setting_dir}/per_model.parquet")
    return pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)


def per_model(df):
    """mean over repetitions (cross-fits) per held-out model: the unit of replication."""
    if 'rep' not in df.columns:       # already per-model (compact table)
        return df
    num = [c for c in df.columns if c not in KEYS + ['rep', 'fold']]
    return df.groupby(KEYS)[num].mean().reset_index()


def boot_idx(n, B=4000, seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(0, n, (B, n))


def boot_cluster(V, g, B=4000, seed=0):
    """Family-clustered bootstrap of the mean of V (n, nk) over rows: resample whole groups g (n,) with replacement.
    Returns (B, nk) resampled means (ratio of resampled sums to resampled counts, so unequal group sizes are respected)."""
    g = np.asarray(g); u, inv = np.unique(g, return_inverse=True); G = len(u)
    S = np.zeros((G, V.shape[1])); np.add.at(S, inv, V); n = np.bincount(inv, minlength=G).astype(float)
    rng = np.random.default_rng(seed); W = np.zeros((B, G))
    for b in range(B):
        W[b] = np.bincount(rng.integers(0, G, G), minlength=G)
    return (W @ S) / (W @ n)[:, None]


def pivot(pm, selector, method, metric='mse'):
    """models x k matrix for one (selector, method)."""
    d = pm[(pm.selector == selector) & (pm.method == method)]
    return d.pivot(index='model', columns='k', values=metric)


def curve(pm, selector, method, metric='mse', rmse=True, B=4000, seed=0, groups=None):
    """groups: optional model-index -> family label (array indexed by model); then the bootstrap resamples families."""
    P = pivot(pm, selector, method, metric)
    P = P.dropna()
    V = P.values
    boots = boot_cluster(V, np.asarray(groups)[P.index.values], B, seed) if groups is not None else V[boot_idx(len(P), B, seed)].mean(1)   # (B, nk)
    est = V.mean(0)
    f = np.sqrt if rmse else (lambda x: x)
    lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
    return pd.DataFrame(dict(k=P.columns, est=f(est), lo=f(lo), hi=f(hi), n_models=len(P)))


def paired(pm, a, b, metric='mse', ks=None, B=10000, seed=0, groups=None):
    """a, b = (selector, method). difference a - b (negative: a better for an error metric), per k; rel = diff / mean of b."""
    A = pivot(pm, *a, metric=metric); Bm = pivot(pm, *b, metric=metric)
    common = A.index.intersection(Bm.index); ks = ks or sorted(set(A.columns) & set(Bm.columns))
    D = (A.loc[common, ks] - Bm.loc[common, ks]).dropna()
    V = D.values
    boots = boot_cluster(V, np.asarray(groups)[D.index.values], B, seed) if groups is not None else V[boot_idx(len(D), B, seed)].mean(1)
    est = V.mean(0)
    lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
    p = 2 * np.minimum((boots <= 0).mean(0), (boots >= 0).mean(0)).clip(min=1.0 / B)
    return pd.DataFrame(dict(k=ks, diff=est, lo=lo, hi=hi, p=p, n_models=len(D),
                             rel=est / Bm.loc[common, ks].mean(0).values))


def holm(p):
    p = np.asarray(p); order = np.argsort(p); m = len(p)
    adj = np.empty(m); run = 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * p[i]); adj[i] = min(run, 1.0)
    return adj


def f1_top10(pm, selector, method):
    d = pm[(pm.selector == selector) & (pm.method == method)].groupby('k')[['t10_tp', 't10_fp', 't10_fn']].sum()
    return (2 * d.t10_tp / (2 * d.t10_tp + d.t10_fp + d.t10_fn)).rename('f1_top10')
