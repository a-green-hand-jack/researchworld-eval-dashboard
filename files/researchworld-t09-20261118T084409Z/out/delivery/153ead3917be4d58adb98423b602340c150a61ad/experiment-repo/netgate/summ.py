"""Cell-level summaries with Monte-Carlo uncertainty."""
import numpy as np
import pandas as pd

CELL = ["graph.kind", "graph.n", "graph.d", "out.kind", "out.kappa", "out.shape", "out.w2", "out.sigma", "out.sigma_alpha",
        "out.gamma", "out.beta", "out.het_beta", "out.het_gamma", "design.kind", "design.p", "design.res", "design.labels", "graph.kw.mu", "graph.kw.rewire", "graph.q", "out.theta", "stag.T", "obs.q", "tag"]


def cell_cols(df):
    return [c for c in CELL if c in df.columns and df[c].nunique(dropna=False) >= 1]


def boot_ci(x, f, B=300, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x)
    idx = rng.integers(0, len(x), (B, len(x)))
    v = np.array([f(x[i]) for i in idx])
    return float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))


def est_stats(err):
    err = np.asarray(err, float)
    ok = ~np.isnan(err)
    e = err[ok]
    n = len(e)
    rmse = float(np.sqrt(np.mean(e ** 2)))
    lo, hi = boot_ci(e, lambda v: np.sqrt(np.mean(v ** 2)), B=200)
    return dict(n=n, bias=float(e.mean()), bias_se=float(e.std(ddof=1) / np.sqrt(n)), sd=float(e.std(ddof=1)),
                rmse=rmse, rmse_lo=lo, rmse_hi=hi, n_nan=int((~ok).sum()))


def summarize(df, ests, extra_mean=(), by=None):
    by = by or cell_cols(df)
    out = []
    for key, g in df.groupby(by, dropna=False):
        base = dict(zip(by, key if isinstance(key, tuple) else (key,)))
        for c in extra_mean:
            if c in g:
                base[c] = float(g[c].mean())
        for nm in ests:
            if nm in g:
                out.append(dict(base, est=nm, **est_stats(g[nm] - g["tau"])))
        if "HT_var_exact" in g:
            v = g["HT_var_exact"].to_numpy()
            lo, hi = boot_ci(v, lambda x: np.sqrt(np.mean(x)), B=200)
            out.append(dict(base, est="HT-exact", n=len(v), bias=0.0, bias_se=0.0, sd=float(np.sqrt(v.mean())),
                            rmse=float(np.sqrt(v.mean())), rmse_lo=lo, rmse_hi=hi, n_nan=0))
    return pd.DataFrame(out)


def load_partial(grid, work="work"):
    """Concatenate the cell caches of a (possibly unfinished) grid run."""
    import glob
    import pickle
    rows = []
    for f in glob.glob(f"{work}/{grid}/*.pkl"):
        rows += pickle.load(open(f, "rb"))
    return pd.DataFrame(rows)
