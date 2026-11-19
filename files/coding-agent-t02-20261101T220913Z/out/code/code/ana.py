"""Shared analysis helpers: load runs, derive t_fit / t_gen / regime labels, bootstrap CIs."""
import json, os, sys
import numpy as np
import pandas as pd

FIT_THR, GEN_THR = 0.99, 0.99


def sustained(steps, vals, thr, k=3):
    for i in range(len(steps)):
        if vals[i] >= thr and all(v >= thr * 0.97 for v in vals[i:i + k]):
            return steps[i]
    return np.nan


def load(outdir, **extra):
    rows = []
    for fn in sorted(os.listdir(outdir)):
        if not fn.endswith(".json"):
            continue
        o = json.load(open(os.path.join(outdir, fn)))
        c, cv = o["cfg"], o["curves"]
        s = cv["step"]
        t_fit = sustained(s, cv["tr_acc"], FIT_THR)
        t_gen = sustained(s, cv["va_acc"], GEN_THR)
        t_gen90 = sustained(s, cv["va_acc"], 0.90)
        t_gen50 = sustained(s, cv["va_acc"], 0.50)
        va_fit = cv["va_acc"][s.index(int(t_fit))] if t_fit == t_fit else np.nan
        # peak "memorisation gap": min val acc over steps from t_fit on
        row = dict(c, P=o["n_params"], N=o["n_train"], t_fit=t_fit, t_gen=t_gen, t_gen90=t_gen90, t_gen50=t_gen50,
                   va_fit=va_fit, fin_tr=cv["tr_acc"][-1], fin_va=cv["va_acc"][-1], max_va=max(cv["va_acc"]),
                   last=s[-1], wall=o["wall"], fn=fn)
        row["fit"] = t_fit == t_fit
        row["gen"] = t_gen == t_gen
        row["mem_first"] = bool(row["fit"] and va_fit < 0.5)
        rows.append(row)
    return pd.DataFrame(rows)


def censored_median(x, cens_value):
    """median with NaN (never reached within budget) treated as +inf; returns (median, is_censored)"""
    x = np.where(np.isnan(x), np.inf, x)
    m = np.median(x)
    return (m, False) if np.isfinite(m) else (cens_value, True)


def boot_ci(vals, fn=np.median, n=2000, seed=0, alpha=0.05):
    rng = np.random.default_rng(seed)
    vals = np.asarray(vals, float)
    b = [fn(vals[rng.integers(0, len(vals), len(vals))]) for _ in range(n)]
    return np.percentile(b, [100 * alpha / 2, 100 * (1 - alpha / 2)])
