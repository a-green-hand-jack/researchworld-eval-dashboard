"""Fit/evaluate cover-time predictors from easy statistics.
Reads ../results/graphs.csv; writes ../results/*.txt, ../paper/fig_*.pdf.
Usage: python analyze.py"""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "../results/"
rows = list(csv.DictReader(open(R + "graphs.csv")))
fams = sorted({r["family"] for r in rows})
num = lambda k: np.array([float(r[k]) for r in rows])
fam = np.array([r["family"] for r in rows])
n, m, dmin, dmax, diam = num("n"), num("m"), num("dmin"), num("dmax"), num("diam")
C = num("C_mc"); se = num("C_se"); Mt = num("matthews"); B = num("bound_2m_n1")
y = np.log(C)

def X_of(cols):
    cols = [np.ones_like(n)] + cols
    return np.column_stack(cols)

FEATS = {
    "logm,logn": [np.log(m), np.log(n)],
    "logm,logn,logdiam,logdmax": [np.log(m), np.log(n), np.log(diam), np.log(dmax)],
}

def fit_predict(model, tr, te):
    if model == "bound 2m(n-1)":
        return np.log(B[te])
    if model == "scaled bound kappa*2m(n-1)":
        kappa = np.median(y[tr] - np.log(B[tr]))
        return np.log(B[te]) + kappa
    X = X_of(FEATS[model])
    beta, *_ = np.linalg.lstsq(X[tr], y[tr], rcond=None)
    return X[te] @ beta

MODELS = ["bound 2m(n-1)", "scaled bound kappa*2m(n-1)", "logm,logn", "logm,logn,logdiam,logdmax"]

def summarize(err_log):
    """err_log = log(pred) - log(C). Returns median factor, 90% pct factor, frac within +-25%."""
    a = np.abs(err_log)
    return dict(median_factor=float(np.exp(np.median(a))),
                p90_factor=float(np.exp(np.percentile(a, 90))),
                within_25pct=float(np.mean(a <= np.log(1.25))),
                frac_over=float(np.mean(err_log > 0)))

def boot_ci(err_log, B_=2000, seed=0):
    rng = np.random.default_rng(seed)
    a = np.abs(err_log)
    meds = [np.median(a[rng.integers(0, a.size, a.size)]) for _ in range(B_)]
    return float(np.exp(np.percentile(meds, 2.5))), float(np.exp(np.percentile(meds, 97.5)))

out = []
def p(s=""):
    print(s); out.append(s)

N = len(rows)
p(f"# Results ({N} graphs, {len(fams)} families)")
p()
p("## A. Leave-one-family-out (LOFO) generalisation, pooled over held-out predictions")
p("| predictor | median factor [95% CI] | 90th pct factor | within x1.25 | frac over-predicted |")
p("|---|---|---|---|---|")
lofo = {}
for mod in MODELS:
    pred = np.zeros(N)
    for f in fams:
        te = fam == f; tr = ~te
        pred[te] = fit_predict(mod, tr, te)
    e = pred - y
    lofo[mod] = e
    s = summarize(e); lo, hi = boot_ci(e)
    p(f"| {mod} | {s['median_factor']:.2f} [{lo:.2f}, {hi:.2f}] | {s['p90_factor']:.2f} | {s['within_25pct']:.2f} | {s['frac_over']:.2f} |")
# Matthews reference (uses hitting times, not an easy statistic)
e = np.log(Mt) - y
s = summarize(e); lo, hi = boot_ci(e)
p(f"| Matthews h_max*H_(n-1) (reference, needs hitting times) | {s['median_factor']:.2f} [{lo:.2f}, {hi:.2f}] | {s['p90_factor']:.2f} | {s['within_25pct']:.2f} | {s['frac_over']:.2f} |")
p()

p("## B. Random 10-fold CV, repeated 20 times (mean of per-repeat medians)")
p("| predictor | median factor (CV) | within x1.25 |")
p("|---|---|---|")
for mod in MODELS[1:]:
    meds, wins = [], []
    for rep in range(20):
        r = np.random.default_rng(rep)
        perm = r.permutation(N); folds = np.array_split(perm, 10)
        pred = np.zeros(N)
        for te_idx in folds:
            te = np.zeros(N, bool); te[te_idx] = True
            pred[te] = fit_predict(mod, ~te, te)
        e = pred - y
        meds.append(summarize(e)["median_factor"]); wins.append(summarize(e)["within_25pct"])
    p(f"| {mod} | {np.mean(meds):.2f} (sd {np.std(meds):.3f}) | {np.mean(wins):.2f} |")
p()

p("## C. Per-family LOFO median factor (predictor: logm,logn,logdiam,logdmax)")
p("| family | count | median factor | within x1.25 | bound 2m(n-1) median factor | Matthews median factor |")
p("|---|---|---|---|---|---|")
best = "logm,logn,logdiam,logdmax"
fam_err = {}
for f in fams:
    t = fam == f
    e = lofo[best][t]; fam_err[f] = np.median(np.abs(e))
    eb = np.log(B[t]) - y[t]; em = np.log(Mt[t]) - y[t]
    p(f"| {f} | {t.sum()} | {np.exp(np.median(np.abs(e))):.2f} | {np.mean(np.abs(e)<=np.log(1.25)):.2f} | {np.exp(np.median(np.abs(eb))):.2f} | {np.exp(np.median(np.abs(em))):.2f} |")
p()

# Fitted coefficients on all data (for reporting)
X = X_of(FEATS[best]); beta, *_ = np.linalg.lstsq(X, y, rcond=None)
p("## D. Full-data fit, logm,logn,logdiam,logdmax: log C = b0 + b1 log m + b2 log n + b3 log diam + b4 log dmax")
p("coefficients: " + ", ".join(f"{b:.3f}" for b in beta))
resid = y - X @ beta
p(f"in-sample R^2 (log scale): {1 - resid.var() / y.var():.4f}; residual sd {resid.std():.3f}")
p()
p("## E. Where it fails: worst LOFO graphs (top 8 by |log error|)")
idx = np.argsort(-np.abs(lofo[best]))[:8]
p("| family | n | m | diam | dmax | C_mc | predicted | factor |")
p("|---|---|---|---|---|---|---|---|")
for i in idx:
    pr = np.exp(y[i] + lofo[best][i])
    p(f"| {fam[i]} | {int(n[i])} | {int(m[i])} | {int(diam[i])} | {int(dmax[i])} | {C[i]:.1f} | {pr:.1f} | {np.exp(abs(lofo[best][i])):.2f} |")
p()
rel = se / C
p(f"Monte Carlo: median relative SE of C_mc = {np.median(rel)*100:.2f}%, max = {rel.max()*100:.2f}%")
open(R + "results.md", "w").write("\n".join(out) + "\n")

# Figures
pal = plt.cm.tab20(np.linspace(0, 1, len(fams)))
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.2))
pred_all = np.zeros(N)
for f in fams:
    te = fam == f
    pred_all[te] = fit_predict(best, ~te, te)
for k, f in enumerate(fams):
    t = fam == f
    ax[0].scatter(C[t], np.exp(pred_all[t]), s=8, color=pal[k], label=f)
lim = [C.min() * 0.7, max(B.max(), C.max()) * 1.2]
ax[0].plot(lim, lim, "k-", lw=0.8)
ax[0].plot(lim, [l * 1.25 for l in lim], "k:", lw=0.6)
ax[0].plot(lim, [l / 1.25 for l in lim], "k:", lw=0.6)
ax[0].set_xscale("log"); ax[0].set_yscale("log")
ax[0].set_xlabel("MC cover time $\\hat C$"); ax[0].set_ylabel("LOFO prediction")
ax[0].set_title("(a) predicted vs. measured", fontsize=9)
order = sorted(fams, key=lambda f: fam_err[f])
for j, f in enumerate(order):
    t = fam == f
    ax[1].scatter(np.full(t.sum(), j) + np.random.default_rng(j).uniform(-0.2, 0.2, t.sum()),
                  np.abs(lofo[best][t]), s=5, color="0.3")
ax[1].axhline(np.log(1.25), color="r", ls="--", lw=0.8)
ax[1].set_xticks(range(len(order))); ax[1].set_xticklabels(order, rotation=70, fontsize=6)
ax[1].set_ylabel("|log error| (LOFO)"); ax[1].set_title("(b) error by family", fontsize=9)
ax[0].legend(fontsize=5, ncol=2, frameon=False, loc="upper left")
plt.tight_layout(); plt.savefig("../paper/fig_main.pdf")
