"""Per-run metrics and aggregation from the per-prediction table.

Input: tidy table with one row per (benchmark, method, n, split_type, seed, target_model):
  benchmark, method, n, split_type, seed, target_model, true, pred
A *run* is one (benchmark, method, n, split_type, seed) group; metrics are computed over its target models.
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau

KEYS = ["benchmark", "split_type", "n", "seed"]


def load(path):
    df = pd.read_parquet(path) if str(path).endswith(".parquet") else pd.read_csv(path)
    need = {"benchmark", "method", "n", "split_type", "seed", "target_model", "true", "pred"}
    miss = need - set(df.columns)
    if miss:
        raise SystemExit(f"results table lacks columns {sorted(miss)}")
    return df


def _run_metrics(g):
    t, p = g["true"].to_numpy(), g["pred"].to_numpy()
    ok = len(t) >= 3 and np.ptp(t) > 0
    const = np.ptp(p) == 0
    return pd.Series(dict(
        mae=np.mean(np.abs(p - t)), rmse=np.sqrt(np.mean((p - t) ** 2)), n_targets=len(t),
        spearman=np.nan if (not ok or const) else spearmanr(t, p)[0],
        kendall=np.nan if (not ok or const) else kendalltau(t, p)[0]))


def per_run(df):
    """One row per run; accuracy-point units: errors are in accuracy points (x100)."""
    r = df.groupby(["method"] + KEYS, sort=False).apply(_run_metrics, include_groups=False).reset_index()
    r["mae"] *= 100
    r["rmse"] *= 100
    return r


def pairwise_by_gap(df, bins):
    """Pairwise ranking accuracy of predicted order vs true order, binned by true score gap (points)."""
    out = []
    for (b, m, n, st, s), g in df.groupby(["benchmark", "method", "n", "split_type", "seed"], sort=False):
        t, p = g["true"].to_numpy() * 100, g["pred"].to_numpy() * 100
        i, j = np.triu_indices(len(t), 1)
        gap = np.abs(t[i] - t[j])
        correct = np.where(p[i] == p[j], 0.5, (np.sign(t[i] - t[j]) == np.sign(p[i] - p[j])).astype(float))
        k = np.digitize(gap, bins) - 1
        for q in range(len(bins) - 1):
            sel = k == q
            if sel.any():
                out.append(dict(benchmark=b, method=m, n=n, split_type=st, seed=s, bin=q, acc=correct[sel].mean(), pairs=int(sel.sum())))
    return pd.DataFrame(out)


def boot_mean(runs, col, by, B=2000, seed=0):
    """Mean of `col` per group `by`, with 95% percentile CI from resampling seeds (runs) within group."""
    rng = np.random.default_rng(seed)
    rows = []
    for key, g in runs.groupby(by, sort=False):
        x = g[col].dropna().to_numpy()
        if len(x) == 0:
            continue
        bs = x[rng.integers(0, len(x), (B, len(x)))].mean(1)
        rows.append(dict(zip(by, key if isinstance(key, tuple) else (key,)), mean=x.mean(),
                         lo=np.quantile(bs, .025), hi=np.quantile(bs, .975), nruns=len(x)))
    return pd.DataFrame(rows)


def macro(runs, col, by_extra, B=2000, seed=0):
    """Macro-average over benchmarks (equal weight) of per-benchmark seed-means; CI resamples seeds within each
    benchmark independently. `by_extra` e.g. ['split_type','n','method']."""
    rng = np.random.default_rng(seed)
    rows = []
    for key, g in runs.groupby(by_extra, sort=False):
        per = [gb[col].dropna().to_numpy() for _, gb in g.groupby("benchmark")]
        per = [x for x in per if len(x)]
        if not per:
            continue
        pt = np.mean([x.mean() for x in per])
        bs = np.mean([x[rng.integers(0, len(x), (B, len(x)))].mean(1) for x in per], axis=0)
        rows.append(dict(zip(by_extra, key if isinstance(key, tuple) else (key,)), mean=pt,
                         lo=np.quantile(bs, .025), hi=np.quantile(bs, .975), nbench=len(per)))
    return pd.DataFrame(rows)


def paired_diff(runs, col, baseline):
    """method - baseline for the same (benchmark, split_type, n, seed) run."""
    b = runs[runs.method == baseline][KEYS + [col]].rename(columns={col: "base"})
    d = runs[runs.method != baseline].merge(b, on=KEYS)
    d["diff"] = d[col] - d["base"]
    return d
