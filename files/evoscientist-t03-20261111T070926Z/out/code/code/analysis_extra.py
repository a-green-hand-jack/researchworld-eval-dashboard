"""Pooled summaries, mechanism ('margin-to-noise') collapse, and scale (prob vs logit) sensitivity.
Writes results/tables/tabI_pooled.csv, tabJ_auc.csv, tabK_scale.csv and figs/fig_collapse.pdf"""
import os, sys
import numpy as np, pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from data import RESULTS

TAB = os.path.join(RESULTS, "tables"); FIG = os.path.join(RESULTS, "figs")
rng = np.random.default_rng(21)
df = pd.read_csv(os.path.join(RESULTS, "core_metrics.csv"))
df["pass1"] = (df.top1 >= 0.9).astype(float)
df["pass3"] = (df.same3 >= 0.9).astype(float)
P = df[df.scale == "prob"].copy()

# ---- pooled over (dataset, model) cells: mean of cell-level pass rates; min/max across cells
cell = P.groupby(["dataset", "model", "est", "mult"])[["pass1", "pass3", "jac3", "rbo", "tau", "rel_l2"]].agg(
    {"pass1": "mean", "pass3": "mean", "jac3": "median", "rbo": "median", "tau": "median", "rel_l2": "median"}).reset_index()
cell = cell.merge(P.groupby(["dataset", "model", "est", "mult"]).exact.all().reset_index(), on=["dataset", "model", "est", "mult"])
rows = []
for (est, mult), g in cell.groupby(["est", "mult"]):
    # cluster bootstrap over cells
    r = dict(est=est, mult=mult, n_cells=len(g), n_exact=int(g.exact.sum()))
    for c in ("pass1", "pass3", "jac3", "rbo", "tau", "rel_l2"):
        v = g[c].values
        bs = v[rng.integers(0, len(v), (2000, len(v)))].mean(1)
        r[c], r[c + "_lo"], r[c + "_hi"] = v.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
        r[c + "_min"], r[c + "_max"] = v.min(), v.max()
    rows.append(r)
pd.DataFrame(rows).to_csv(os.path.join(TAB, "tabI_pooled.csv"), index=False)

# ---- mechanism: margin-to-noise ratio
NE = P[(~P.exact) & (P.mult >= 4) & (P.d <= 12)].copy()   # table datasets, where nonadd is defined
NE["z1"] = NE.gap1 / NE.noise_ratio
NE["z3"] = NE.gap3 / NE.noise_ratio


def auc(score, y):
    y = np.asarray(y).astype(bool)
    if y.all() or (~y).all():
        return np.nan
    u = stats.mannwhitneyu(score[y], score[~y]).statistic
    return u / (y.sum() * (~y).sum())


rows = []
for est in ("kernel", "perm"):
    g = NE[NE.est == est]
    for tgt, zc, gc in (("pass1", "z1", "gap1"), ("pass3", "z3", "gap3")):
        y = g[tgt].values
        rows.append(dict(est=est, target=tgt, n=len(g), auc_margin_over_noise=auc(g[zc].values, y), auc_gap_only=auc(g[gc].values, y),
                         auc_neg_nonadd=auc(-g.nonadd.values, y), auc_budget_only=auc(g.mult.values.astype(float), y),
                         auc_neg_noise_ratio=auc(-g.noise_ratio.values, y), base_rate=y.mean()))
pd.DataFrame(rows).to_csv(os.path.join(TAB, "tabJ_auc.csv"), index=False)

fig, axes = plt.subplots(1, 2, figsize=(9, 3.3))
for ax, (tgt, zc, ttl) in zip(axes, [("top1", "z1", "top-1 feature"), ("same3", "z3", "top-3 set")]):
    for est, col in (("kernel", "tab:blue"), ("perm", "tab:orange")):
        g = NE[NE.est == est]
        qs = np.unique(np.quantile(g[zc], np.linspace(0, 1, 16)))
        b = np.digitize(g[zc], qs[1:-1])
        xs = [g[zc][b == i].median() for i in range(len(qs) - 1)]
        ys = [g[tgt][b == i].mean() for i in range(len(qs) - 1)]
        ax.plot(xs, ys, "o-", color=col, ms=3, label=est)
    ax.set_xscale("log")
    ax.set_xlabel(r"margin-to-noise ratio  (gap$_k$ / $\|\mathrm{sd}\|$)")
    ax.set_ylabel("mean run-pair agreement")
    ax.set_title(ttl, fontsize=9)
    ax.axhline(0.9, color="gray", ls=":", lw=0.6)
axes[0].legend(fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "fig_collapse.pdf"))

# ---- scale sensitivity (probability vs log-odds value function), table datasets
S = df[df.d <= 12].groupby(["scale", "model", "est", "mult"])[["pass1", "pass3"]].mean().reset_index()
S = S.pivot_table(index=["model", "est", "mult"], columns="scale", values=["pass1", "pass3"]).reset_index()
S.columns = ["_".join([c for c in col if c]) for col in S.columns]
S.to_csv(os.path.join(TAB, "tabK_scale.csv"), index=False)
print(pd.DataFrame(rows).round(3).to_string())
print(S[S.mult.isin([4, 16])].round(2).to_string())
print(pd.read_csv(os.path.join(TAB, "tabI_pooled.csv"))[["est", "mult", "pass1", "pass1_lo", "pass1_hi", "pass3", "pass3_lo", "pass3_hi", "jac3", "rel_l2", "n_exact"]].round(3).to_string())

# ---- sensitivity of the pass criterion to the threshold (pooled over cells)
rows = []
for thr in (0.8, 0.9, 0.95, 0.99):
    for (est, mult), g in P.groupby(["est", "mult"]):
        cells = g.assign(p1=(g.top1 >= thr), p3=(g.same3 >= thr)).groupby(["dataset", "model"])[["p1", "p3"]].mean()
        rows.append(dict(thr=thr, est=est, mult=mult, pass1=cells.p1.mean(), pass3=cells.p3.mean()))
pd.DataFrame(rows).to_csv(os.path.join(TAB, "tabM_threshold.csv"), index=False)
print(pd.DataFrame(rows).pivot_table(index=["est", "mult"], columns="thr", values=["pass1", "pass3"]).round(2).to_string())
