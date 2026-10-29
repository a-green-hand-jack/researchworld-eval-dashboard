"""Fit and evaluate log-linear cover-time predictors from cheap graph statistics.

Reads ../results/cover.csv; writes ../results/summary.txt, ../results/table_*.tex,
../results/fig_pred.pdf. Run with: python analyze.py
"""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "../results/"
rows = list(csv.DictReader(open(R + "cover.csv")))
fam = np.array([r["family"] for r in rows])
n = np.array([float(r["n"]) for r in rows])
m = np.array([float(r["m"]) for r in rows])
dmax = np.array([float(r["max_deg"]) for r in rows])
diam = np.array([float(r["diam"]) for r in rows])
cov = np.array([float(r["cover_mean"]) for r in rows])
se = np.array([float(r["cover_se"]) for r in rows])
y = np.log(cov)
bound = 2 * m * (n - 1)  # Aleliunas et al. (1979) upper bound on expected cover time

FEATS = {
    "log n": [np.log(n)],
    "log n, log m": [np.log(n), np.log(m)],
    "log n, log m, log dmax, log diam": [np.log(n), np.log(m), np.log(dmax), np.log(diam)],
}


def design(cols):
    return np.column_stack([np.ones_like(n)] + cols)


def fit(X, t):
    beta, *_ = np.linalg.lstsq(X, t, rcond=None)
    return beta


def lofo(cols):
    """Leave-one-family-out predictions for each graph."""
    X = design(cols)
    pred = np.empty_like(y)
    for f in np.unique(fam):
        tr, te = fam != f, fam == f
        pred[te] = X[te] @ fit(X[tr], y[tr])
    return pred


def stats(err):
    a = np.abs(err)
    return np.median(a), np.quantile(a, 0.9), np.max(a)


def boot_ci(err, B=2000, seed=0):
    rng = np.random.default_rng(seed)
    a = np.abs(err)
    med = [np.median(a[rng.integers(0, a.size, a.size)]) for _ in range(B)]
    return np.quantile(med, [0.025, 0.975])


out = []
P = lambda *s: out.append(" ".join(str(x) for x in s))
P(f"graphs={len(rows)} families={len(np.unique(fam))} n_range=[{n.min():.0f},{n.max():.0f}] walks=2000")
P(f"median MC relative SE of cover time: {np.median(se / cov):.4f}; max: {np.max(se / cov):.4f}")
P(f"bound 2m(n-1) / measured cover: median ratio {np.median(bound / cov):.2f}, "
  f"min {np.min(bound / cov):.2f}, max {np.max(bound / cov):.2f}")

res = {}
for name, cols in FEATS.items():
    X = design(cols)
    beta = fit(X, y)
    ins = y - X @ beta
    loo = y - lofo(cols)
    res[name] = (beta, ins, loo)
    P(f"\n[{name}] in-sample coef {np.round(beta, 3).tolist()}")
    m1, p1, x1 = stats(ins)
    m2, p2, x2 = stats(loo)
    lo, hi = boot_ci(loo)
    P(f"  in-sample |log err|: median {m1:.3f} (x{np.exp(m1):.2f}), p90 {p1:.3f}, max {x1:.3f}")
    P(f"  LOFO |log err|:      median {m2:.3f} (x{np.exp(m2):.2f}) 95% CI [{lo:.3f},{hi:.3f}], p90 {p2:.3f}, max {x2:.3f}")

# bound-only "predictor"
be = np.log(bound) - y
m3, p3, x3 = stats(be)
P(f"\n[bound 2m(n-1)] |log err|: median {m3:.3f} (x{np.exp(m3):.2f}), p90 {p3:.3f}, max {x3:.3f}")
P(f"  signed median log(bound/true) = {np.median(be):.3f}")

# per-family LOFO errors for the 4-feature model
_, _, loo4 = res["log n, log m, log dmax, log diam"]
P("\nPer-family LOFO (4-feature model) median |log err| and mean signed log err, and bound ratio:")
tab = []
for f in np.unique(fam):
    k = fam == f
    tab.append((f, k.sum(), np.median(np.abs(loo4[k])), np.mean(loo4[k]), np.median(bound[k] / cov[k])))
for t in sorted(tab, key=lambda t: -t[2]):
    P(f"  {t[0]:12s} N={t[1]:3d}  med|err|={t[2]:.3f}  mean_signed={t[3]:+.3f}  bound_ratio={t[4]:.2f}")

with open(R + "summary.txt", "w") as f:
    f.write("\n".join(out) + "\n")
print("\n".join(out))

# LaTeX table of per-family results
with open(R + "table_families.tex", "w") as f:
    f.write("\\begin{tabular}{lrrrr}\n\\toprule\nFamily & $N$ & med.\\ $|\\mathrm{err}|$ & bias & bound/true \\\\\n\\midrule\n")
    for t in sorted(tab, key=lambda t: -t[2]):
        f.write(f"{t[0].replace('_', chr(92) + '_')} & {t[1]} & {t[2]:.3f} & {t[3]:+.3f} & {t[4]:.1f} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# figure: LOFO predicted vs measured log cover time
fig, ax = plt.subplots(figsize=(4.2, 3.4))
cats = np.unique(fam)
cmap = plt.get_cmap("tab10")
for i, c in enumerate(cats):
    k = fam == c
    ax.scatter(y[k], y[k] - loo4[k], s=10, color=cmap(i), label=c, alpha=0.8)
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel(r"$\log$ measured cover time")
ax.set_ylabel(r"$\log$ measured $-$ $\log$ predicted (LOFO)")
ax.legend(fontsize=5.5, ncol=2, frameon=False)
fig.tight_layout()
fig.savefig(R + "fig_pred.pdf")
