"""Shared analysis helpers: loading, balanced panels, per-model aggregation, bootstrap CIs."""
import numpy as np, pandas as pd

RES = '/work/out/results'
NB = 2000


def load(ds, split):
    d = pd.read_parquet(f'{RES}/{ds}__{split}.parquet')
    d['cell'] = d['fold'].astype(str) + '|' + d['model'].astype(str) + '|' + d['t0'].astype(str)
    return d


def balanced(d, ref=('gauss', 'greedy_var')):
    """Keep only (fold, model, t0) cells for which every k was evaluated, so curves compare the same targets across k."""
    r = d[(d.predictor == ref[0]) & (d.selector == ref[1])]
    ks = sorted(r.k.unique())
    cnt = r.groupby('cell').k.nunique()
    keep = cnt[cnt == len(ks)].index
    return d[d.cell.isin(keep)].copy(), ks


def per_model(d, metric='mse_z'):
    """Average draws, cells and folds -> one value per (predictor, selector, k, model)."""
    g = d.groupby(['predictor', 'selector', 'k', 'model', 'cell'])[metric].mean().reset_index()
    return g.groupby(['predictor', 'selector', 'k', 'model'])[metric].mean().reset_index()


def wide(pm, predictor, selector, metric='mse_z'):
    """-> DataFrame index=model, columns=k."""
    x = pm[(pm.predictor == predictor) & (pm.selector == selector)]
    return x.pivot(index='model', columns='k', values=metric)


def boot_idx(n, rng, nb=NB):
    return rng.integers(0, n, size=(nb, n))


def ci_mean(A, rng_seed=0, nb=NB):
    """A: (n_models, n_k) -> mean, lo, hi per column (percentile bootstrap over models)."""
    A = np.asarray(A, float); n = A.shape[0]
    idx = boot_idx(n, np.random.default_rng(rng_seed), nb)
    bm = A[idx].mean(1)
    return A.mean(0), np.percentile(bm, 2.5, axis=0), np.percentile(bm, 97.5, axis=0)


def ci_ratio(A, B, rng_seed=0, nb=NB):
    """CI for 1 - mean(A)/mean(B) (e.g. R^2 relative to the mean baseline), models resampled jointly."""
    A = np.asarray(A, float); B = np.asarray(B, float); n = A.shape[0]
    idx = boot_idx(n, np.random.default_rng(rng_seed), nb)
    bm = 1 - A[idx].mean(1) / B[idx].mean(1)
    return 1 - A.mean(0) / B.mean(0), np.percentile(bm, 2.5, axis=0), np.percentile(bm, 97.5, axis=0)


def ci_rel_reduction(A, B, rng_seed=0, nb=NB):
    """CI for relative error reduction 1 - mean(A)/mean(B) of method A vs reference B (paired by model)."""
    return ci_ratio(A, B, rng_seed, nb)


def k_to_reach(ks, curve, thresh):
    """smallest k with curve(k) <= thresh (None if never)."""
    for k, v in zip(ks, curve):
        if v <= thresh: return k
    return None
