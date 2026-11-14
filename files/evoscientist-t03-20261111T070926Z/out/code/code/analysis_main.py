"""Aggregate E1 instance-level metrics -> tables / figures (results/tables, results/figs)."""
import os, sys
import numpy as np, pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from data import RESULTS

suffix = "_quick" if "--quick" in sys.argv else ""
TAB = os.path.join(RESULTS, "tables"); FIG = os.path.join(RESULTS, "figs")
os.makedirs(TAB, exist_ok=True); os.makedirs(FIG, exist_ok=True)
rng = np.random.default_rng(11)
THR = 0.9
DSN = {"pima": "Pima", "gmsc": "GMSC", "acsincome": "ACSIncome", "german": "German"}
MODELS = ["lr", "xgb", "rf", "mlp"]
MCOL = {"lr": "tab:blue", "xgb": "tab:orange", "rf": "tab:green", "mlp": "tab:red"}


def boot(v, fn=np.mean, B=2000):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return (np.nan, np.nan, np.nan)
    idx = rng.integers(0, len(v), (B, len(v)))
    bs = fn(v[idx], axis=1)
    return fn(v, axis=None), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


df = pd.read_csv(os.path.join(RESULTS, f"core_metrics{suffix}.csv"))
dfp = df[df.scale == "prob"].copy()
dfp["pass1"] = (dfp.top1 >= THR).astype(float)
dfp["pass3"] = (dfp.same3 >= THR).astype(float)
dfp["exact_kernel"] = dfp.exact

# ---- Table A: per (dataset, model, est, budget)
rows = []
for (ds, mo, est, mult), g in dfp.groupby(["dataset", "model", "est", "mult"]):
    r = dict(dataset=ds, model=mo, est=est, mult=mult, budget=int(g.budget.iloc[0]), exact=bool(g.exact.all()), n=len(g))
    for key, col, fn in [("pass1", "pass1", np.mean), ("pass3", "pass3", np.mean), ("top1", "top1", np.median),
                         ("jac3", "jac3", np.median), ("jac5", "jac5", np.median), ("rbo", "rbo", np.median),
                         ("tau", "tau", np.median), ("rel_l2", "rel_l2", np.median),
                         ("ref_rel_err", "ref_rel_err", np.median), ("ref_top1", "ref_top1", np.mean),
                         ("ref_jac3", "ref_jac3", np.mean)]:
        m, lo, hi = boot(g[col].values, fn)
        r[key], r[key + "_lo"], r[key + "_hi"] = m, lo, hi
    rows.append(r)
A = pd.DataFrame(rows)
A.to_csv(os.path.join(TAB, f"tabA_main{suffix}.csv"), index=False)

# ---- Figure 1: pass rates vs budget multiple
fig, axes = plt.subplots(2, 4, figsize=(15, 6.2), sharey=True)
for c, ds in enumerate(["pima", "gmsc", "acsincome", "german"]):
    for r, (col, ttl) in enumerate([("pass1", "top-1 feature"), ("pass3", "top-3 set")]):
        ax = axes[r, c]
        for mo in MODELS:
            for est, ls in [("kernel", "-"), ("perm", "--")]:
                g = A[(A.dataset == ds) & (A.model == mo) & (A.est == est)].sort_values("mult")
                if len(g) == 0:
                    continue
                ax.plot(g.mult, g[col], ls, color=MCOL[mo], marker="o", ms=3, lw=1.3,
                        label=f"{mo}-{est}" if (r == 0 and c == 0) else None)
                ax.fill_between(g.mult, g[col + "_lo"], g[col + "_hi"], color=MCOL[mo], alpha=0.08)
        ax.axhline(0.9, color="gray", lw=0.6, ls=":")
        ax.set_xscale("log", base=2)
        ax.set_title(f"{DSN[ds]} (d={int(dfp[dfp.dataset == ds].d.iloc[0])}) - {ttl}", fontsize=9)
        if r == 1:
            ax.set_xlabel("budget / d  (coalition evaluations per run)")
        if c == 0:
            ax.set_ylabel("fraction of instances with\nrun-pair agreement >= 0.9")
axes[0, 0].legend(fontsize=6, ncol=2)
plt.tight_layout()
plt.savefig(os.path.join(FIG, f"fig_passrate{suffix}.pdf"))
plt.savefig(os.path.join(FIG, f"fig_passrate{suffix}.png"), dpi=70)
plt.close()

# ---- Table B: smallest budget multiple at which >= 90% of instances pass
fr = []
for (ds, mo, est), g in A.groupby(["dataset", "model", "est"]):
    g = g.sort_values("mult")
    row = dict(dataset=ds, model=mo, est=est)
    for col in ("pass1", "pass3"):
        ok = g[g[col] >= 0.9]
        row[col + "_min_mult"] = int(ok.mult.iloc[0]) if len(ok) else np.nan
        # note: monotone? require all larger budgets to also pass
        stable = [m for m in g.mult if (g[(g.mult >= m)][col] >= 0.9).all()]
        row[col + "_min_mult_stable"] = int(stable[0]) if stable else np.nan
    fr.append(row)
FR = pd.DataFrame(fr)
FR.to_csv(os.path.join(TAB, f"tabB_frontier{suffix}.csv"), index=False)

# ---- Heterogeneity / mechanism: Spearman of noise with non-additivity & gaps (table datasets, prob scale)
mech = []
for (ds, mo, est, mult), g in dfp[dfp.d <= 12].groupby(["dataset", "model", "est", "mult"]):
    if g.exact.all():
        continue
    r1 = stats.spearmanr(g.nonadd, g.noise_ratio)
    r2 = stats.spearmanr(g.gap1, g.top1)
    r3 = stats.spearmanr(g.gap3, g.jac3)
    r4 = stats.spearmanr(g.nonadd, g.jac3)
    mech.append(dict(dataset=ds, model=mo, est=est, mult=mult, rho_nonadd_noise=r1[0], p1=r1[1], rho_gap1_top1=r2[0],
                     p2=r2[1], rho_gap3_jac3=r3[0], p3=r3[1], rho_nonadd_jac3=r4[0], p4=r4[1]))
MC = pd.DataFrame(mech)
MC.to_csv(os.path.join(TAB, f"tabC_mechanism{suffix}.csv"), index=False)

# ---- Near-boundary vs confident instances (|p-0.5|<0.2)
dfp["near"] = (np.abs(dfp.px - 0.5) < 0.2)
nb = []
for (ds, est, mult), g in dfp.groupby(["dataset", "est", "mult"]):
    a, b = g[g.near], g[~g.near]
    if len(a) >= 5 and len(b) >= 5:
        u = stats.mannwhitneyu(a.jac3, b.jac3)
        nb.append(dict(dataset=ds, est=est, mult=mult, n_near=len(a), n_far=len(b), jac3_near=a.jac3.median(),
                       jac3_far=b.jac3.median(), p=u.pvalue))
pd.DataFrame(nb).to_csv(os.path.join(TAB, f"tabD_boundary{suffix}.csv"), index=False)

# ---- Kernel vs permutation, paired by instance (Wilcoxon on jac3), Holm over all cells
pr = []
for (ds, mo, mult), g in dfp.groupby(["dataset", "model", "mult"]):
    k = g[g.est == "kernel"].set_index("inst").jac3
    p = g[g.est == "perm"].set_index("inst").jac3
    ex = bool(g[g.est == "kernel"].exact.all())
    if ex or len(k) < 10:
        continue
    dlt = (k - p.loc[k.index]).values
    try:
        w = stats.wilcoxon(dlt) if np.any(dlt != 0) else None
    except ValueError:
        w = None
    pr.append(dict(dataset=ds, model=mo, mult=mult, kernel_minus_perm=dlt.mean(), p=w.pvalue if w else 1.0))
PR = pd.DataFrame(pr)
if len(PR):
    order = np.argsort(PR.p.values)
    m = len(PR)
    holm = np.empty(m)
    run = 0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * PR.p.values[i]))
        holm[i] = run
    PR["p_holm"] = holm
PR.to_csv(os.path.join(TAB, f"tabE_kernel_vs_perm{suffix}.csv"), index=False)
print(A.groupby(["dataset", "est", "mult"])[["pass1", "pass3", "jac3"]].mean().round(2).to_string())
print(FR.to_string())
print(PR.describe().to_string() if len(PR) else "")
