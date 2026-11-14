"""Shared helpers for analysis scripts."""
import numpy as np, pandas as pd
from scipy import stats

NAMES = {"l2": r"$\ell_2$", "l1": r"TV", "linf": r"$\ell_\infty$", "hell": "Hellinger", "kl": "KL",
         "ait": "Aitchison", "mah": "Mahal.-ilr", "l2n": r"$\ell_2/\hat\sigma$", "l2_mond": r"$\ell_2$-Mond.",
         "ait_mond": "Ait.-Mond."}
PLAIN = {"l2": "L2", "l1": "TV", "linf": "Linf", "hell": "Hellinger", "kl": "KL", "ait": "Aitchison",
         "mah": "Mahal-ilr", "l2n": "L2/sigma", "l2_mond": "L2-Mond", "ait_mond": "Ait-Mond"}
ORDER = ["l2", "l1", "linf", "hell", "kl", "ait", "mah", "l2n", "l2_mond", "ait_mond"]
DGPN = {"ln": "LN-homo", "ln_het": "LN-hetero", "dir": "Dirichlet", "mult": "Multinom."}
ALPHA = 0.1


def mean_ci(x):
    x = np.asarray(x, float)
    n = len(x)
    m = x.mean()
    hw = 1.96 * x.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
    return m, hw


def agg(df, keys, vals):
    rows = []
    for k, g in df.groupby(keys):
        k = k if isinstance(k, tuple) else (k,)
        r = dict(zip(keys, k))
        for v in vals:
            m, hw = mean_ci(g[v].dropna()) if g[v].notna().any() else (np.nan, np.nan)
            r[v], r[v + "_hw"] = m, hw
        r["R"] = len(g)
        rows.append(r)
    return pd.DataFrame(rows)


def group_gap(g, prefix, ngr, alpha=ALPHA, min_n=1, B=300, seed=0):
    """worst-group |coverage - (1-alpha)| over groups from pooled counts; bootstrap CI over replicates."""
    C = np.stack([g[f"g_{prefix}{j}_c"].to_numpy() for j in range(ngr)], 1).astype(float)
    N = np.stack([g[f"g_{prefix}{j}_n"].to_numpy() for j in range(ngr)], 1).astype(float)
    R = len(g)
    def stat_from(c, n):
        ok = n >= min_n
        cov = c / np.maximum(n, 1)
        dev = np.where(ok, np.abs(cov - (1 - alpha)), 0.0)
        return dev.max(-1), cov
    est, cov = stat_from(C.sum(0), N.sum(0))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, R, (B, R))
    bs, _ = stat_from(C[idx].sum(1), N[idx].sum(1))
    return float(est), np.quantile(bs, 0.025), np.quantile(bs, 0.975), cov


def holm(p):
    p = np.asarray(p); o = np.argsort(p); m = len(p)
    adj = np.empty(m); run = 0
    for i, j in enumerate(o):
        run = max(run, (m - i) * p[j]); adj[j] = min(1, run)
    return adj


def paired_diff(df, a, b, col, keys):
    """paired difference (a - b) of `col` per replicate within each cell; returns mean, hw, p."""
    rows = []
    for k, g in df.groupby(keys):
        k = k if isinstance(k, tuple) else (k,)
        pa = g[g.method == a].set_index("rep")[col]; pb = g[g.method == b].set_index("rep")[col]
        d = (pa - pb).dropna().to_numpy()
        if len(d) < 2: continue
        t = stats.ttest_1samp(d, 0.0)
        rows.append(dict(zip(keys, k), a=a, b=b, diff=d.mean(), hw=1.96 * d.std(ddof=1) / np.sqrt(len(d)), p=t.pvalue,
                         rel=d.mean() / pb.mean()))
    return pd.DataFrame(rows)
