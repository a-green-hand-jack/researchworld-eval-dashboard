"""Loading and interval helpers shared by the figure/table scripts. Reads only experiment-repo's results/ files."""
import os
import numpy as np
import pandas as pd

RESULTS = os.environ.get("FIGTAB_RESULTS", "results")
OUT = os.environ.get("FIGTAB_OUT", "figures")
TOUT = os.environ.get("FIGTAB_TOUT", "tables")
os.makedirs(OUT, exist_ok=True)
os.makedirs(TOUT, exist_ok=True)


def path(name):
    return os.path.join(RESULTS, name)


def wilson(k, n, z=1.96):
    """Wilson score interval for k successes in n trials (arrays ok)."""
    k, n = np.asarray(k, float), np.asarray(n, float)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def mean_ci(x, z=1.96):
    x = np.asarray(x, float)
    m, se = x.mean(), x.std(ddof=1) / np.sqrt(len(x))
    return m, m - z * se, m + z * se


def gap_table(runs, by):
    """Mean optimism (reported - fresh accuracy, in points) with 95% CI over replicates, per group `by`."""
    runs = runs.assign(gap=100 * (runs.reported_naive - runs.theta))
    g = runs.groupby(by, dropna=False).gap
    out = g.agg(mean="mean", sd="std", reps="size").reset_index()
    out["se"] = out.sd / np.sqrt(out.reps)
    out["lo"], out["hi"] = out["mean"] - 1.96 * out.se, out["mean"] + 1.96 * out.se
    return out


def main_grid(df):
    """Drop the extra '|m3' cells (300 replicates, the only cells with the M3 bootstrap methods); they are analysed on their own."""
    return df[~df.cell_id.str.contains("|m3", regex=False)]


def reference(df):
    """Main-grid cells of the reference world: rho=0.6, baseline accuracy 0.3, exhaustive search, no leakage."""
    c = df.cell_id
    return df[c.str.contains("rho=0.6|acc=0.3|proc=exhaustive", regex=False) & ~c.str.contains("|leak", regex=False)]


def method_stats(m, keys):
    """Per-cell bias (pts, vs the method's own target), RMSE, coverage with Wilson interval, median width (pts) and item cost.
    `m` is a methods_*.parquet frame; one row of output per group of `keys`.
    With a `block` column (T1: replicates share items) the bias SE and the coverage interval come from the 10 block means
    (delete-a-block, mean +- 1.96 SE, columns bias_se, cov_lo, cov_hi); otherwise from replicates (Wilson for coverage)."""
    m = m.assign(err=100 * (m.estimate - m.theta_target), has=m.lo.notna() | m.hi.notna())
    m["cover"] = ((m.lo <= m.theta_target) & (m.theta_target <= m.hi)).astype(float)
    m["width"] = 100 * (m.hi - m.lo).replace([np.inf, -np.inf], np.nan)
    rows = []
    for k, d in m.groupby(keys):
        k = k if isinstance(k, tuple) else (k,)
        bl = "block" in d
        bse = (lambda x: x.groupby(d.block.loc[x.index]).mean().std() / np.sqrt(d.block.nunique())) if bl else (lambda x: x.std() / np.sqrt(len(x)))
        r = dict(zip(keys, k), reps=len(d), bias=d.err.mean(), bias_se=bse(d.err), rmse=np.sqrt((d.err ** 2).mean()),
                 items_search=d.items_search.mean(), items_report=d.items_report.mean())
        ci = d[d.has]
        if len(ci):
            kk, N = ci.cover.sum(), len(ci)
            lo, hi = wilson(kk, N)
            if bl:
                lo, hi = kk / N - 1.96 * bse(ci.cover), kk / N + 1.96 * bse(ci.cover)
            r.update(cov=kk / N, cov_lo=float(lo), cov_hi=float(hi), width=ci.width.median())
        rows.append(r)
    return pd.DataFrame(rows)


def block_gap_table(runs, by, z=1.96):
    """T1 optimism (points) per group `by` with the delete-a-block SE: SD of the per-block means / sqrt(#blocks).
    Replicates in T1 share items from a fixed pool, so the plain replicate SE is too small."""
    runs = runs.assign(gap=100 * (runs.reported_naive - runs.theta))
    bm = runs.groupby(by + ["block"]).gap.mean().reset_index()
    out = bm.groupby(by).gap.agg(mean="mean", sd="std", blocks="size").reset_index()
    out["se"] = out.sd / np.sqrt(out.blocks)
    out["lo"], out["hi"] = out["mean"] - z * out.se, out["mean"] + z * out.se
    out = out.merge(runs.groupby(by).size().rename("reps").reset_index(), on=by)
    return out
