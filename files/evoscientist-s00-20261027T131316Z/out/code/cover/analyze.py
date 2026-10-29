"""Fit and evaluate simple cover-time predictors from results.csv (numpy only).
Usage: python3 analyze.py results.csv > analysis.txt
"""
import sys
import numpy as np
import pandas as pd

df = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "results.csv")
rng = np.random.default_rng(12345)
y_all = np.log(df.cover_mc.values)
se_log = df.cover_se.values / df.cover_mc.values

print("N graphs:", len(df), " families:", df.family.nunique())

# ---- 1. validation of MC against exact values (n<=10)
ex = df[df.cover_exact.notna()].copy()
z = (ex.cover_mc - ex.cover_exact) / ex.cover_se
print("\n[Validation] exact vs MC, n<=10: graphs=%d" % len(ex))
print("  mean |MC/exact - 1| = %.4f" % np.mean(np.abs(ex.cover_mc / ex.cover_exact - 1)))
print("  max |z| = %.2f ; fraction |z|<2 = %.3f" % (np.max(np.abs(z)), np.mean(np.abs(z) < 2)))

# ---- 2. ratio to the classic bound 2m(n-1)
ratio = df.cover_mc / df.bound_2m_nm1
print("\n[Classic bound 2m(n-1)] C/bound: median=%.3f, min=%.3f, max=%.3f" %
      (ratio.median(), ratio.min(), ratio.max()))
print("  by family (median C/bound):")
print(df.assign(r=ratio).groupby("family").r.median().sort_values().round(3).to_string())


def feats(d, kind):
    one = np.ones(len(d))
    L = lambda c: np.log(d[c].values.astype(float))
    if kind == "bound_scale":      # log C = log bound + a  (one free constant)
        return np.column_stack([one, L("bound_2m_nm1")])
    if kind == "n_m":              # log C = a + b log n + c log m
        return np.column_stack([one, L("n"), L("m")])
    if kind == "n_m_D":            # + log diameter
        return np.column_stack([one, L("n"), L("m"), L("diam")])
    if kind == "full":             # + log max degree
        return np.column_stack([one, L("n"), L("m"), L("dmax"), L("diam")])
    raise ValueError(kind)


MODELS = ["bound_scale", "n_m", "n_m_D", "full"]


def fit_predict(train, test, kind):
    X = feats(train, kind)
    y = np.log(train.cover_mc.values)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return np.exp(feats(test, kind) @ beta), beta


def rel_err(pred, true):
    return np.abs(pred - true) / true


# ---- 3. in-sample fit and leave-one-family-out (LOFO) CV
print("\n[Predictors] relative error |pred-C|/C over graphs")
print("%-14s %-10s %-10s %-10s %-10s %-10s" % ("model", "in-sample", "LOFO med", "LOFO p90", "LOFO max", "LOFO-CI95(med)"))
results = {}
for kind in MODELS:
    ins_pred, beta = fit_predict(df, df, kind)
    ins = rel_err(ins_pred, df.cover_mc.values)
    preds = np.zeros(len(df))
    for fam in df.family.unique():
        tr = df[df.family != fam]
        te_mask = (df.family == fam).values
        p, _ = fit_predict(tr, df[te_mask], kind)
        preds[te_mask] = p
    lofo = rel_err(preds, df.cover_mc.values)
    # bootstrap CI for LOFO median (resample graphs)
    boots = [np.median(lofo[rng.integers(0, len(lofo), len(lofo))]) for _ in range(2000)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    results[kind] = (preds, lofo)
    print("%-14s %-10.3f %-10.3f %-10.3f %-10.3f [%.3f, %.3f]" %
          (kind, np.median(ins), np.median(lofo), np.percentile(lofo, 90), lofo.max(), lo, hi))
    print("   coefficients (log-space):", np.round(beta, 3))

# ---- 4. per-family LOFO error of the best simple model (n_m_D) and the bound
print("\n[Per-family median relative error, LOFO]")
tab = pd.DataFrame({"family": df.family, "n_m_D": results["n_m_D"][1],
                    "full": results["full"][1], "bound_scale": results["bound_scale"][1]})
print(tab.groupby("family").median().round(3).sort_values("n_m_D").to_string())

# ---- 5. error vs. graph density/structure: correlation of log-residual with log(m/n), diam/n
pred_full = results["n_m_D"][0]
res = np.log(df.cover_mc.values) - np.log(pred_full)
print("\n[Residual (LOFO log-residual) correlations for n_m_D]")
for name, v in [("log(m/n)", np.log(df.m / df.n)), ("diam/n", df.diam / df.n),
                ("log n", np.log(df.n)), ("dmax/n", df.dmax / df.n)]:
    print("  corr(res, %s) = %.3f" % (name, np.corrcoef(res, v)[0, 1]))

# ---- 6. MC uncertainty: median relative SE
print("\n[MC uncertainty] median relative SE = %.4f, max = %.4f" %
      (np.median(se_log), np.max(se_log)))

# ---- 7. power-law exponent sanity check for the fitted model on families
print("\n[Fitted exponents, full-data n_m_D fit] (log C ~ a + b log n + c log m + d log D)")
_, b = fit_predict(df, df, "n_m_D")
print("  b_n=%.3f b_m=%.3f b_diam=%.3f" % (b[1], b[2], b[3]))
