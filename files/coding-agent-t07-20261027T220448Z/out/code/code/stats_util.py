"""Aggregation utilities: relative RMSE vs random sampling with hierarchical (benchmark -> seed) bootstrap CIs."""
import numpy as np, pandas as pd

BASE = "rand/mean"


def tensor(df, methods, protocol, n, col="mse"):
    """-> array [method, bench, seed] of `col` (and list of benches)."""
    s = df[(df.protocol == protocol) & (df.n == n) & df.method.isin(methods)]
    piv = s.pivot_table(index=["bench", "seed"], columns="method", values=col, aggfunc="first")
    benches = sorted(piv.index.get_level_values(0).unique())
    seeds = sorted(piv.index.get_level_values(1).unique())
    arr = np.full((len(methods), len(benches), len(seeds)), np.nan)
    for (b, sd), row in piv.iterrows():
        for mi, m in enumerate(methods):
            arr[mi, benches.index(b), seeds.index(sd)] = row.get(m, np.nan)
    return arr, benches


def rel_rmse(arr, base_idx, bi, si):
    """arr [M,B,S]; bi benches idx (list), si [len(bi), S] seed idx -> relative RMSE [M] (geomean over benches of
    sqrt(mean mse / mean base mse))."""
    out = np.zeros((arr.shape[0], len(bi)))
    for k, b in enumerate(bi):
        a = arr[:, b, :][:, si[k]]
        out[:, k] = np.sqrt(np.nanmean(a, 1) / np.nanmean(a[base_idx]))
    return np.exp(np.log(out).mean(1))


def boot_rel(arr, base_idx, B=1000, seed=0, diff_pairs=()):
    """point estimate and 95% CI per method, plus CI of log ratios for (i,j) pairs (log rel_i - log rel_j)."""
    M, nb, ns = arr.shape
    rng = np.random.default_rng(seed)
    pt = rel_rmse(arr, base_idx, list(range(nb)), np.tile(np.arange(ns), (nb, 1)))
    reps = np.zeros((B, M))
    for r in range(B):
        bi = rng.integers(0, nb, nb)
        si = rng.integers(0, ns, (nb, ns))
        reps[r] = rel_rmse(arr, base_idx, list(bi), si)
    lo, hi = np.percentile(reps, [2.5, 97.5], axis=0)
    diffs = {}
    for i, j in diff_pairs:
        d = np.log(reps[:, i]) - np.log(reps[:, j])
        diffs[(i, j)] = (float(np.log(pt[i]) - np.log(pt[j])), *np.percentile(d, [2.5, 97.5]))
    return pt, lo, hi, diffs


def boot_mean_diff(arr, base_idx, B=1000, seed=0):
    """Mean over (bench, seed) of metric difference to baseline with hierarchical bootstrap CI. arr [M,B,S] of a metric
    (higher=better, e.g. Spearman)."""
    M, nb, ns = arr.shape
    rng = np.random.default_rng(seed)
    d = arr - arr[base_idx][None]
    bm = np.nanmean(d, 2)  # [M,nb]
    pt = bm.mean(1)
    reps = np.zeros((B, M))
    for r in range(B):
        bi = rng.integers(0, nb, nb)
        si = rng.integers(0, ns, (nb, ns))
        reps[r] = np.mean([np.nanmean(d[:, b, :][:, si[k]], 1) for k, b in enumerate(bi)], 0)
    lo, hi = np.percentile(reps, [2.5, 97.5], axis=0)
    return pt, lo, hi
