"""Shared helpers to load results and compute summary statistics with uncertainty."""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "paper", "figs")
TAB = os.path.join(ROOT, "paper", "tabs")
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)
RNG = np.random.default_rng(12345)


def load(exp):
    scen = pd.read_csv(os.path.join(RES, f"{exp}_scen.csv"))
    raw = pd.read_csv(os.path.join(RES, f"{exp}_raw.csv.gz"))
    p2 = os.path.join(RES, f"{exp}_pred2.csv")
    if os.path.exists(p2):  # first-order theory (bias, noise variance, design variance)
        pred = pd.read_csv(p2).rename(columns={"bias": "bias_pred", "var_noise": "var_pred_noise",
                                               "var_design": "var_pred_design"})
        pred["var_pred_total"] = pred["var_pred_noise"] + pred["var_pred_design"]
    else:
        pred = pd.read_csv(os.path.join(RES, f"{exp}_pred.csv"))
        pred["var_pred_design"] = 0.0  # old-style (noise-only + iid residual) predictions
    df = raw.merge(scen, on="sid")
    df["err"] = df["estimate"] - df["gate"]
    df["cover_hc"] = (np.abs(df["err"]) <= 1.96 * df["se_hc"]).where(df["se_hc"].notna())
    df["cover_cl"] = (np.abs(df["err"]) <= 1.96 * df["se_cl"]).where(df["se_cl"].notna())
    return scen, df, pred


def boot_ci(x, fn, B=400, alpha=0.05):
    x = np.asarray(x)
    x = x[~np.isnan(x)]
    if len(x) < 5:
        return (np.nan, np.nan)
    idx = RNG.integers(0, len(x), (B, len(x)))
    v = np.array([fn(x[i]) for i in idx])
    return tuple(np.quantile(v, [alpha / 2, 1 - alpha / 2]))


def summarize(df, by, ci=True):
    """Pooled bias / sd / rmse (+ bootstrap CI for rmse and SE for bias), validity rate, coverage."""
    rows = []
    for key, g in df.groupby(by, dropna=False):
        e = g["err"].to_numpy()
        valid = ~np.isnan(e)
        ev = e[valid]
        r = dict(zip(by if isinstance(by, list) else [by], key if isinstance(key, tuple) else (key,)))
        r["n_obs"] = len(e)
        r["valid"] = valid.mean()
        if len(ev) >= 2:
            r["bias"] = ev.mean()
            r["bias_se"] = ev.std(ddof=1) / np.sqrt(len(ev))
            # within-scenario sd (pooled), excludes between-graph-instance bias differences
            w = g[valid].groupby("sid")["err"].var(ddof=1).dropna()
            r["sd"] = np.sqrt(w.mean()) if len(w) else np.nan
            r["rmse"] = np.sqrt(np.mean(ev ** 2))
            if ci:
                lo, hi = boot_ci(ev, lambda a: np.sqrt(np.mean(a ** 2)))
                r["rmse_lo"], r["rmse_hi"] = lo, hi
            for c in ["cover_hc", "cover_cl"]:
                cv = g[c].dropna()
                r[c] = cv.mean() if len(cv) else np.nan
                r[c + "_n"] = len(cv)
            r["se_hc_mean"] = g["se_hc"].mean()
            r["se_cl_mean"] = g["se_cl"].mean()
        rows.append(r)
    return pd.DataFrame(rows)


def attach_pred(summ_df, df, pred, by):
    """Add predicted bias / sd (mean over scenarios in the group) from population-OLS theory."""
    sc = df[["sid"] + [b for b in by if b != "est"]].drop_duplicates("sid")
    p = pred.merge(sc, on="sid")
    keys = by
    gp = p.groupby(keys).agg(bias_pred=("bias_pred", "mean"),
                              sd_pred_noise=("var_pred_noise", lambda v: np.sqrt(np.mean(v))),
                              sd_pred_total=("var_pred_total", lambda v: np.sqrt(np.mean(v))),
                              dMd=("dMd", "mean")).reset_index()
    return summ_df.merge(gp, on=keys, how="left")


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h
