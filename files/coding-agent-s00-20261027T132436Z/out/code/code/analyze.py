"""Fit and evaluate cover-time predictors on results/data.csv.
Writes results/summary.json, results/family_table.md, results/fig_pred.pdf.
Usage: python analyze.py"""
import json, os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
rng = np.random.default_rng(12345)
df = pd.read_csv(os.path.join(RES, "data.csv"))
df["logT"] = np.log(df.cover_time)
df["logB"] = np.log(df.bound_2m_n1)
df["logn"], df["logm"] = np.log(df.n), np.log(df.m)
df["logD"], df["logDelta"] = np.log(df["diameter"]), np.log(df.max_deg)
df["ratio_B"] = df.cover_time / df.bound_2m_n1
X_FEATS = {"M1 (log n, log m, log Δ, log D)": ["logn", "logm", "logDelta", "logD"]}

def fit_ols(X, y):
    A = np.column_stack([np.ones(len(X)), X])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return coef

def predict_ols(coef, X):
    return np.column_stack([np.ones(len(X)), X]) @ coef

def fit_scaled_bound(d):
    # M0: T = c * 2m(n-1), c fitted in log space (geometric mean of ratios)
    return np.mean(d.logT - d.logB)

def predict_scaled_bound(c, d):
    return d.logB.values + c

def predict(model, train, test):
    if model == "M0 scaled bound":
        c = fit_scaled_bound(train)
        return predict_scaled_bound(c, test)
    feats = X_FEATS[model]
    coef = fit_ols(train[feats].values, train.logT.values)
    return predict_ols(coef, test[feats].values)

MODELS = ["M0 scaled bound"] + list(X_FEATS)
summary = {"n_graphs": int(len(df)), "n_range": [int(df.n.min()), int(df.n.max())],
           "bound_holds_fraction": float((df.cover_time <= df.bound_2m_n1).mean()),
           "ratio_B_median": float(df.ratio_B.median()), "ratio_B_max": float(df.ratio_B.max()),
           "median_rel_mc_se": float((df.cover_se / df.cover_time).median()),
           "max_rel_mc_se": float((df.cover_se / df.cover_time).max())}

# --- 10-fold CV on random splits (repeated 20x) ---
def cv_errors(model, reps=20, k=10):
    errs = []
    for _ in range(reps):
        idx = rng.permutation(len(df)); folds = np.array_split(idx, k)
        pred = np.empty(len(df))
        for f in folds:
            tr = df.drop(df.index[f]); te = df.iloc[f]
            pred[f] = predict(model, tr, te)
        errs.append(pred - df.logT.values)
    return np.array(errs)  # reps x N (log errors)

summary["cv"] = {}
for mdl in MODELS:
    E = cv_errors(mdl)
    ae = np.abs(E)
    summary["cv"][mdl] = {
        "median_abs_log_err": float(np.median(ae)),
        "median_abs_log_err_CI95": [float(np.percentile(np.median(ae, 1), 2.5)), float(np.percentile(np.median(ae, 1), 97.5))],
        "median_APE_pct": float(100 * (np.exp(np.median(ae)) - 1)),
        "frac_within_1.25x": float((ae < np.log(1.25)).mean()),
        "frac_within_1.5x": float((ae < np.log(1.5)).mean()),
    }

# --- leave-one-family-out ---
lofo = {}
for fam in df.family.unique():
    te = df[df.family == fam]; tr = df[df.family != fam]
    if len(tr) < 20:
        continue
    lofo[fam] = {"n_graphs": int(len(te))}
    for mdl in MODELS:
        p = predict(mdl, tr, te)
        lofo[fam][mdl] = float(np.median(np.abs(p - te.logT.values)))
summary["lofo_median_abs_log_err"] = lofo

# --- per-family table on full-data fit (in-sample, for description) ---
rows = []
for fam, g in df.groupby("family"):
    rows.append({"family": fam, "n_graphs": len(g), "n_range": f"{g.n.min()}–{g.n.max()}",
                 "median T/B": round(g.ratio_B.median(), 3),
                 "max T/B": round(g.ratio_B.max(), 3),
                 "median LOFO err M0 (%)": round(100 * (np.exp(lofo.get(fam, {}).get("M0 scaled bound", np.nan)) - 1), 1),
                 "median LOFO err M1 (%)": round(100 * (np.exp(lofo.get(fam, {}).get("M1 (log n, log m, log Δ, log D)", np.nan)) - 1), 1)})
tab = pd.DataFrame(rows).sort_values("median T/B")
with open(os.path.join(RES, "family_table.md"), "w") as f:
    f.write(tab.to_markdown(index=False))

# --- full-data coefficients of M1 and scaled-bound constant ---
coef = fit_ols(df[X_FEATS["M1 (log n, log m, log Δ, log D)"]].values, df.logT.values)
summary["M1_coef_intercept_logn_logm_logDelta_logD"] = [float(c) for c in coef]
summary["M0_c"] = float(np.exp(fit_scaled_bound(df)))

# bootstrap CI for M1 coefficients
B = []
for _ in range(1000):
    b = df.sample(len(df), replace=True, random_state=int(rng.integers(1e9)))
    B.append(fit_ols(b[X_FEATS["M1 (log n, log m, log Δ, log D)"]].values, b.logT.values))
B = np.array(B)
summary["M1_coef_bootstrap95"] = [[float(a), float(b)] for a, b in zip(np.percentile(B, 2.5, 0), np.percentile(B, 97.5, 0))]

with open(os.path.join(RES, "summary.json"), "w") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(json.dumps({k: v for k, v in summary.items() if k not in ("lofo_median_abs_log_err",)}, indent=2, ensure_ascii=False))
print(tab.to_string(index=False))

# --- figure: predicted vs observed (CV predictions from one 10-fold run) ---
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))
for ax, mdl in zip(axes, MODELS):
    E = cv_errors(mdl, reps=1)[0]
    pred = df.logT.values + E
    for fam, g in df.groupby("family"):
        ax.scatter(np.exp(g.logT), np.exp(pred[g.index]), s=6, label=fam, alpha=0.7)
    lo, hi = df.cover_time.min() * 0.8, df.bound_2m_n1.max() * 1.1
    ax.plot([lo, hi], [lo, hi], "k--", lw=0.8)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("MC cover time"); ax.set_ylabel("predicted (CV)")
    ax.set_title(mdl, fontsize=8)
axes[1].legend(fontsize=4.5, ncol=2, frameon=False, loc="upper left")
plt.tight_layout(); plt.savefig(os.path.join(RES, "fig_pred.pdf"))
