"""Censoring-aware summaries used by all analyses (see code/SPEC.md)."""
import numpy as np
import pandas as pd
from scipy import stats

RNG = np.random.RandomState(0)


def km_median(t, event):
    """Kaplan-Meier median; np.inf if the survival curve never drops to <=0.5 (median > observed range)."""
    t, event = np.asarray(t, float), np.asarray(event, bool)
    order = np.argsort(t, kind="stable"); t, event = t[order], event[order]
    n, s = len(t), 1.0
    for i, (ti, ei) in enumerate(zip(t, event)):
        if ei:
            s *= 1 - 1 / (n - i)
            if s <= 0.5:
                return ti
    return np.inf


def boot_ci(x, fn, B=5000, alpha=0.05):
    """Percentile bootstrap CI of fn over rows resampled with replacement. x: array or tuple of arrays."""
    arrs = x if isinstance(x, tuple) else (x,)
    arrs = [np.asarray(a) for a in arrs]
    n = len(arrs[0]); vals = []
    for _ in range(B):
        idx = RNG.randint(0, n, n)
        vals.append(fn(*[a[idx] for a in arrs]))
    vals = np.array(vals, float)
    return tuple(np.nanpercentile(vals, [100 * alpha / 2, 100 * (1 - alpha / 2)]))


def add_censor_columns(df, thr="99"):
    """t_gen_c: generalisation time, censored at steps_run; ev_gen: event indicator. Likewise for fit."""
    df = df.copy()
    df["t_fit_c"] = df["t_fit" + thr].fillna(df.steps_run); df["ev_fit"] = df["t_fit" + thr].notna()
    df["t_gen_c"] = df["t_gen" + thr].fillna(df.steps_run); df["ev_gen"] = df["t_gen" + thr].notna()
    df["delay_c"] = df.t_gen_c - df.t_fit_c            # censored at steps_run - t_fit when no t_gen
    return df


def perm_spearman(x, y, B=10000):
    r = stats.spearmanr(x, y)[0]
    xs = np.asarray(x); ys = np.asarray(y); cnt = 0
    for _ in range(B):
        if abs(stats.spearmanr(xs, RNG.permutation(ys))[0]) >= abs(r) - 1e-12:
            cnt += 1
    return r, (cnt + 1) / (B + 1)


def loglog_slope(width, y, B=5000):
    """OLS slope of log y on log width with bootstrap CI (resampling runs)."""
    lx, ly = np.log(width), np.log(y)
    f = lambda a, b: np.polyfit(a, b, 1)[0]
    return f(lx, ly), boot_ci((lx, ly), f, B)


def cell_summary(g):
    """One row per cell (a DataFrame group): n, censoring, medians with bootstrap CIs."""
    g = add_censor_columns(g)
    out = dict(n=len(g), n_fit_cens=int((~g.ev_fit).sum()), n_gen_cens=int((~g.ev_gen).sum()), n_params=int(g.n_params.iloc[0]))
    out["t_fit_med"] = np.median(g.t_fit_c); out["t_fit_ci"] = boot_ci(g.t_fit_c.values, np.median, 2000)
    kmf = lambda t, e: km_median(t, e)
    out["t_gen_km_med"] = km_median(g.t_gen_c, g.ev_gen)
    out["t_gen_km_ci"] = boot_ci((g.t_gen_c.values, g.ev_gen.values), kmf, 2000)
    d = g[g.ev_fit]
    out["delay_km_med"] = km_median(d.delay_c, d.ev_gen) if len(d) else np.nan
    out["delay_km_ci"] = boot_ci((d.delay_c.values, d.ev_gen.values), kmf, 2000) if len(d) else (np.nan, np.nan)
    return pd.Series(out)


def tobit_slope(width, t, event, B=1000):
    """Lognormal right-censored (Tobit) regression log t = a + b log width + s*eps; returns slope b and bootstrap CI.
    t is the observed time or the censoring time, event False when censored."""
    from scipy.optimize import minimize
    from scipy.stats import norm
    lx = np.log(np.asarray(width, float)); ly = np.log(np.asarray(t, float)); ev = np.asarray(event, bool)

    def fit(lx, ly, ev):
        def nll(th):
            a, b, ls = th; s = np.exp(ls); mu = a + b * lx; z = (ly - mu) / s
            ll = np.where(ev, norm.logpdf(z) - ls, norm.logsf(z))
            return -ll.sum()
        r = minimize(nll, [ly.mean(), 0.0, np.log(ly.std() + 1e-3)], method="Nelder-Mead", options=dict(xatol=1e-5, fatol=1e-8, maxiter=4000))
        return r.x[1]
    b = fit(lx, ly, ev)
    n = len(lx); bs = []
    for _ in range(B):
        i = RNG.randint(0, n, n)
        if ev[i].sum() >= 3 and len(np.unique(lx[i])) > 1:
            bs.append(fit(lx[i], ly[i], ev[i]))
    return b, tuple(np.percentile(bs, [2.5, 97.5]))
