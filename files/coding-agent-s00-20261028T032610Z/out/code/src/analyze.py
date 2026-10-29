"""Fit and evaluate cover-time predictors from simple graph statistics.
Usage: python analyze.py ../data/results.csv ../data"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

path, outdir = sys.argv[1], sys.argv[2]
df = pd.read_csv(path)
df = df[df.cover_mc > 0].reset_index(drop=True)
rng = np.random.default_rng(123)
y = np.log(df.cover_mc.values)
X_feat = np.column_stack([np.ones(len(df)), np.log(df.n), np.log(df.m),
                          np.log(df.max_deg), np.log(df.diameter)])
X_kappa = np.log(df.bound_2m_n1.values)  # log(2m(n-1))


def fit_predict(tr, te, model):
    if model == "2m(n-1) bound":
        return df.bound_2m_n1.values[te]
    if model == "kappa*2m(n-1)":
        c = np.mean(y[tr] - X_kappa[tr])
        return np.exp(X_kappa[te] + c)
    if model == "log-linear(n,m,D,maxdeg)":
        beta, *_ = np.linalg.lstsq(X_feat[tr], y[tr], rcond=None)
        return np.exp(X_feat[te] @ beta)
    if model == "log-linear(n,m)":
        Z = X_feat[:, :3]
        beta, *_ = np.linalg.lstsq(Z[tr], y[tr], rcond=None)
        return np.exp(Z[te] @ beta)
    raise ValueError(model)


MODELS = ["2m(n-1) bound", "kappa*2m(n-1)", "log-linear(n,m)", "log-linear(n,m,D,maxdeg)"]


def cv_predictions(model, folds):
    pred = np.zeros(len(df))
    for te in folds:
        tr = np.setdiff1d(np.arange(len(df)), te)
        pred[te] = fit_predict(tr, te, model)
    return pred


# 5-fold random CV (repeated 5 times) and leave-one-family-out (LOFO).
rel = {}
summary = []
perm_folds = []
for rep in range(5):
    idx = rng.permutation(len(df))
    perm_folds.append(np.array_split(idx, 5))
fams = df.family.unique()
lofo_folds = [np.where(df.family.values == f)[0] for f in fams]

for model in MODELS:
    errs_cv = []
    for folds in perm_folds:
        p = cv_predictions(model, folds)
        errs_cv.append(np.abs(p - df.cover_mc.values) / df.cover_mc.values)
    e = np.mean(errs_cv, axis=0)
    # Bootstrap CI for the median relative error (first repetition's per-graph errors averaged over reps).
    boots = [np.median(e[rng.integers(0, len(e), len(e))]) for _ in range(2000)]
    p_lofo = cv_predictions(model, lofo_folds)
    e_lofo = np.abs(p_lofo - df.cover_mc.values) / df.cover_mc.values
    summary.append(dict(model=model,
                        median_rel_err_cv=np.median(e), ci_lo=np.percentile(boots, 2.5), ci_hi=np.percentile(boots, 97.5),
                        mean_rel_err_cv=np.mean(e), frac_within_20pct_cv=np.mean(e <= 0.2),
                        median_rel_err_lofo=np.median(e_lofo), frac_within_20pct_lofo=np.mean(e_lofo <= 0.2),
                        frac_overpredict_cv=np.nan))
    rel[model] = (e, e_lofo, p_lofo)
    summary_over = None

# Matthews bound (needs hitting times; reference only).
mat = df.matthews.values
e_mat = np.abs(mat - df.cover_mc.values) / df.cover_mc.values
summary.append(dict(model="Matthews bound (oracle, reference)", median_rel_err_cv=np.median(e_mat), ci_lo=np.nan, ci_hi=np.nan,
                    mean_rel_err_cv=np.mean(e_mat), frac_within_20pct_cv=np.mean(e_mat <= 0.2),
                    median_rel_err_lofo=np.nan, frac_within_20pct_lofo=np.nan, frac_overpredict_cv=np.mean(mat > df.cover_mc.values)))
S = pd.DataFrame(summary)
S.to_csv(f"{outdir}/summary.csv", index=False)
pd.set_option("display.width", 200)
print(S.round(3).to_string(index=False))

# Coefficients of the full log-linear model on all data (for interpretation).
beta, *_ = np.linalg.lstsq(X_feat, y, rcond=None)
resid = y - X_feat @ beta
r2 = 1 - resid.var() / y.var()
print("\nlog-linear(n,m,D,maxdeg) coefficients [1, log n, log m, log maxdeg, log D]:", np.round(beta, 3), "R2(log)=", round(r2, 4))
# Bootstrap CIs for coefficients
bs = []
for _ in range(1000):
    i = rng.integers(0, len(df), len(df))
    b, *_ = np.linalg.lstsq(X_feat[i], y[i], rcond=None)
    bs.append(b)
bs = np.array(bs)
coef_ci = np.column_stack([np.percentile(bs, 2.5, axis=0), np.percentile(bs, 97.5, axis=0)])
print("coef 95% bootstrap CI:", np.round(coef_ci, 3).tolist())

# Per-family errors (LOFO predictions of the best simple model vs the 2m(n-1) bound).
fam_rows = []
e_bound_lofo = rel["2m(n-1) bound"][1]
e_fit_lofo = rel["log-linear(n,m,D,maxdeg)"][1]
for f in fams:
    k = df.family.values == f
    fam_rows.append(dict(family=f, graphs=int(k.sum()), n_range=f"{df.n[k].min()}-{df.n[k].max()}",
                         median_rel_err_loglinear_lofo=np.median(e_fit_lofo[k]),
                         median_rel_err_bound=np.median(e_bound_lofo[k]),
                         median_rel_err_matthews=np.median(e_mat[k]),
                         median_mc_se_rel=np.median((df.cover_se / df.cover_mc).values[k])))
F = pd.DataFrame(fam_rows).sort_values("median_rel_err_loglinear_lofo", ascending=False)
F.to_csv(f"{outdir}/per_family.csv", index=False)
print("\n", F.round(3).to_string(index=False))

# Exact-vs-MC validation (n<=8).
v = df.dropna(subset=["cover_exact"])
if len(v):
    print(f"\nexact vs MC on {len(v)} graphs (n<=8): max |MC/exact-1| = {np.max(np.abs(v.cover_mc/v.cover_exact-1)):.4f}, "
          f"median = {np.median(np.abs(v.cover_mc/v.cover_exact-1)):.4f}")

# Figure: predicted vs measured (LOFO for loglinear) and error by family.
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
cmap = plt.get_cmap("tab20")
for i, f in enumerate(fams):
    k = df.family.values == f
    ax[0].scatter(df.cover_mc[k], rel["log-linear(n,m,D,maxdeg)"][2][k], s=8, color=cmap(i % 20), label=f)
lim = [df.cover_mc.min() * 0.8, df.cover_mc.max() * 1.2]
ax[0].plot(lim, lim, "k--", lw=1)
ax[0].set_xscale("log"); ax[0].set_yscale("log")
ax[0].set_xlabel("measured cover time (MC)"); ax[0].set_ylabel("predicted (leave-one-family-out)")
ax[0].set_title("(a) log-linear predictor")
ax[1].scatter(df.cover_mc, df.bound_2m_n1, s=6, c="gray", label="2m(n-1)")
ax[1].scatter(df.cover_mc, df.matthews, s=6, c="tab:red", label="Matthews")
ax[1].plot(lim, lim, "k--", lw=1)
ax[1].set_xscale("log"); ax[1].set_yscale("log")
ax[1].set_xlabel("measured cover time (MC)"); ax[1].set_ylabel("generic upper bound")
ax[1].legend(fontsize=7); ax[1].set_title("(b) generic upper bounds")
plt.tight_layout()
plt.savefig(f"{outdir}/../figs/scatter.pdf")
print("saved")
