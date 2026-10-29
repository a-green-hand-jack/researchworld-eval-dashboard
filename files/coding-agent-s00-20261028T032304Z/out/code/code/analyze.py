"""Fit and evaluate cover-time predictors from cheap graph statistics.

Reads ../results/cover.csv (from cover.py), writes ../results/summary.txt,
../results/lofo_by_family.csv and ../figs/*.pdf.
"""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "../results/"
rows = list(csv.DictReader(open(R + "cover.csv")))
fam = np.array([r["family"] for r in rows])
f = lambda k: np.array([float(r[k]) for r in rows])
n, m, dmax, diam, C, se, bound = f("n"), f("m"), f("max_deg"), f("diam"), f("cover_mean"), f("cover_se"), f("bound_2m_n1")
y = np.log(C)
rel_se = se / C
rng = np.random.default_rng(0)

# ---- predictors: each returns a function fit(train_idx) -> predict(test_idx) ----
def design(idx, feats):
    cols = [np.ones(len(idx))] + [feats[k][idx] for k in feats]
    return np.column_stack(cols)

FEATS = {
    "bound_only": {},                                  # kappa * 2m(n-1)
    "n_m": {"log n": np.log(n), "log m": np.log(m)},
    "n_m_diam": {"log n": np.log(n), "log m": np.log(m), "log diam": np.log(diam)},
    "n_m_diam_dmax": {"log n": np.log(n), "log m": np.log(m), "log diam": np.log(diam), "log dmax": np.log(dmax)},
}
LOG_BOUND = np.log(bound)

def fit_predict(name, tr, te):
    if name == "bound_only":
        kappa = np.mean(y[tr] - LOG_BOUND[tr])
        return kappa + LOG_BOUND[te]
    F = FEATS[name]
    X_tr, X_te = design(tr, F), design(te, F)
    beta, *_ = np.linalg.lstsq(X_tr, y[tr], rcond=None)
    return X_te @ beta

MODELS = list(FEATS)
out = []
def P(s=""):
    out.append(s); print(s)

P(f"graphs: {len(rows)}, families: {len(set(fam))}, n in [{n.min():.0f},{n.max():.0f}]")
P(f"median relative MC standard error of C: {np.median(rel_se):.4f} (max {rel_se.max():.4f})")
P(f"ratio C / (2m(n-1)): median {np.median(C / bound):.3f}, min {np.min(C / bound):.3f}, max {np.max(C / bound):.3f}")
P()
P("== In-sample fit (all graphs), log-scale errors ==")
P("model            RMSE(log)  MAE(log)  median|ratio-1|")
allidx = np.arange(len(rows))
for mname in MODELS:
    pred = fit_predict(mname, allidx, allidx)
    e = pred - y
    P(f"{mname:16s} {np.sqrt(np.mean(e**2)):8.3f}  {np.mean(np.abs(e)):8.3f}  {np.median(np.abs(np.exp(e)-1)):8.3f}")
P()

# ---- leave-one-family-out CV ----
P("== Leave-one-family-out CV (predict an unseen graph family) ==")
P("model            MAE(log)  median|ratio-1|  90th pct|ratio-1|  bootstrap 95% CI of MAE")
lofo_err = {}
for mname in MODELS:
    pred = np.empty(len(rows))
    for F_ in set(fam):
        te = np.where(fam == F_)[0]
        tr = np.where(fam != F_)[0]
        pred[te] = fit_predict(mname, tr, te)
    e = pred - y
    lofo_err[mname] = (pred, e)
    ae = np.abs(e)
    bs = [ae[rng.integers(0, len(ae), len(ae))].mean() for _ in range(2000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    P(f"{mname:16s} {ae.mean():8.3f}  {np.median(np.abs(np.exp(e)-1)):14.3f}  {np.percentile(np.abs(np.exp(e)-1), 90):16.3f}  [{lo:.3f}, {hi:.3f}]")
P()

# ---- per-family breakdown (LOFO) ----
P("== Per-family LOFO median |ratio-1| and bound ratio ==")
P(f"{'family':14s} {'k':>3s} {'bound_only':>11s} {'n_m':>8s} {'n_m_diam':>9s} {'+dmax':>7s} {'C/(2m(n-1))':>12s}")
fam_rows = []
for F_ in sorted(set(fam)):
    idx = fam == F_
    vals = [np.median(np.abs(np.exp(lofo_err[mm][1][idx]) - 1)) for mm in MODELS]
    ratio = np.median(C[idx] / bound[idx])
    P(f"{F_:14s} {idx.sum():3d} {vals[0]:11.3f} {vals[1]:8.3f} {vals[2]:9.3f} {vals[3]:7.3f} {ratio:12.3f}")
    fam_rows.append(dict(family=F_, k=int(idx.sum()), **{mm: v for mm, v in zip(MODELS, vals)}, bound_ratio=ratio))
with open(R + "lofo_by_family.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(fam_rows[0].keys())); w.writeheader(); w.writerows(fam_rows)

# ---- fitted coefficients on all data (for reporting) ----
P()
P("== Coefficients, fitted on all graphs (n_m_diam_dmax) ==")
F = FEATS["n_m_diam_dmax"]
beta, *_ = np.linalg.lstsq(design(allidx, F), y, rcond=None)
for k, b in zip(["intercept"] + list(F), beta):
    P(f"{k:12s} {b:+.3f}")
open(R + "summary.txt", "w").write("\n".join(out) + "\n")

# ---- figures ----
import matplotlib.cm as cm
fams = sorted(set(fam))
cmap = plt.get_cmap("tab20")
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
for i, F_ in enumerate(fams):
    idx = fam == F_
    ax[0].scatter(bound[idx], C[idx], s=12, color=cmap(i), label=F_)
lim = [C.min() * 0.7, bound.max() * 1.3]
ax[0].plot(lim, lim, "k--", lw=0.8, label="C = bound")
ax[0].set_xscale("log"); ax[0].set_yscale("log")
ax[0].set_xlabel(r"$2m(n-1)$ (universal bound)"); ax[0].set_ylabel("estimated cover time $C$")
ax[0].legend(fontsize=5, ncol=2, frameon=False)
ax[1].scatter(np.exp(lofo_err["n_m_diam_dmax"][0]), C, s=12, c="tab:blue", label="LOFO n,m,diam,dmax")
ax[1].scatter(np.exp(lofo_err["bound_only"][0]), C, s=12, c="tab:orange", marker="x", label="LOFO bound only")
ax[1].plot(lim, lim, "k--", lw=0.8)
ax[1].set_xscale("log"); ax[1].set_yscale("log")
ax[1].set_xlabel("predicted $C$ (held-out family)"); ax[1].set_ylabel("estimated $C$")
ax[1].legend(fontsize=7, frameon=False)
plt.tight_layout(); plt.savefig("../figs/scatter.pdf")

fig, ax = plt.subplots(figsize=(7, 3.2))
ratios = [np.median(np.abs(np.exp(lofo_err["n_m_diam_dmax"][1][fam == F_]) - 1)) for F_ in fams]
ax.bar(range(len(fams)), ratios, color="tab:blue")
ax.set_xticks(range(len(fams))); ax.set_xticklabels(fams, rotation=45, ha="right", fontsize=7)
ax.set_ylabel("median |pred/C - 1| (LOFO)")
plt.tight_layout(); plt.savefig("../figs/per_family.pdf")
