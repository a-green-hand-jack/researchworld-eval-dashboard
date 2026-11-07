"""Stage 4: figures and LaTeX tables from results/*.csv. Every number in the paper comes from here."""
import os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

FIG = os.path.join(ROOT, "figs"); TAB = os.path.join(ROOT, "paper", "tables")
os.makedirs(FIG, exist_ok=True); os.makedirs(TAB, exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.grid": True, "grid.alpha": .3})
C = pd.read_csv(os.path.join(RES, "cell_summary.csv"))
I = pd.read_csv(os.path.join(RES, "instance_metrics.csv"))
F = pd.read_csv(os.path.join(RES, "floor_metrics.csv"))
P = pd.read_csv(os.path.join(RES, "model_perf.csv"))
rng = np.random.RandomState(5)


def ci(v, n=2000):
    v = np.asarray(v, float); v = v[~np.isnan(v)]
    m = v[rng.randint(0, len(v), (n, len(v)))].mean(1)
    return v.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5)


# Table 1: model performance
t = P.pivot(index="dataset", columns="model", values="auc").round(3)
t.insert(0, "d", P.groupby("dataset").d.first()); t.insert(0, "n_train", P.groupby("dataset").n_train.first())
t.to_latex(os.path.join(TAB, "perf.tex"), escape=False)

# Fig 1: run-to-run J3 vs budget (kernel, perm), per dataset, models as lines
fig, axs = plt.subplots(2, len(DATASETS), figsize=(11, 4.2), sharey="row")
for r, ex in enumerate(["kernel", "perm"]):
    for c, ds in enumerate(DATASETS):
        ax = axs[r, c]
        for m, col in zip(MODELS, ["C0", "C1", "C2", "C3"]):
            g = C[(C.dataset == ds) & (C.model == m) & (C.explainer == ex)].sort_values("B")
            if len(g) == 0: continue
            ax.errorbar(g.B, g.rr_J3, yerr=[g.rr_J3 - g.rr_J3_lo, g.rr_J3_hi - g.rr_J3], marker="o", ms=3, capsize=2, label=m, color=col)
            ax.set_xscale("log")
        ax.axhline(.8, color="k", ls=":", lw=1)
        if r == 0: ax.set_title(f"{ds} (d={int(C[C.dataset==ds].d.iloc[0])})")
        if c == 0: ax.set_ylabel(f"{ex}: run-to-run top-3 Jaccard")
        if r == 1: ax.set_xlabel("budget B (coalitions)")
axs[0, 0].legend(fontsize=6)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig1_rr_j3_vs_budget.pdf")); plt.close()

# Floors summary at the largest budget of KernelSHAP: run-to-run vs floors
rows = []
for (ds, m), g in C[(C.explainer == "kernel")].groupby(["dataset", "model"]):
    gB = g.sort_values("B")
    for tag, b in [("lowB", gB.iloc[0]), ("highB", gB.iloc[-1])]:
        rows.append(dict(dataset=ds, model=m, tag=tag, B=int(b.B), rr_J3=b.rr_J3, lo=b.rr_J3_lo, hi=b.rr_J3_hi,
                         ref_J3=b.get("ref_J3", np.nan), bg=b.get("bg_floor_J3", np.nan), retrain=b.get("retrain_floor_J3", np.nan),
                         between=b.get("between_instance_J3", np.nan), glob=b.get("global_importance_J3", np.nan), cap=int(b.exact_cap)))
T = pd.DataFrame(rows); T.to_csv(os.path.join(RES, "table_main.csv"), index=False)
with open(os.path.join(TAB, "main.tex"), "w") as f:
    f.write("\\begin{tabular}{llrrcccccc}\\toprule\nData & Model & $B$ & cap & run--run $J_3$ [95\\% CI] & vs exact & bg floor & retrain floor & other-inst. & global \\\\\\midrule\n")
    for _, r in T.iterrows():
        fm = lambda x: "--" if pd.isna(x) else f"{x:.2f}"
        f.write(f"{r.dataset} & {r.model} & {r.B} & {'y' if r.cap else ''} & {r.rr_J3:.2f} [{r.lo:.2f},{r.hi:.2f}] & {fm(r.ref_J3)} & {fm(r.bg)} & {fm(r.retrain)} & {fm(r.between)} & {fm(r.glob)} \\\\\n")
    f.write("\\bottomrule\\end{tabular}\n")

# Fig 2: per-instance distribution at the high budget (kernel) -- fraction of instances with J3<1
fig, axs = plt.subplots(1, 2, figsize=(7.5, 2.8))
for ax, which in zip(axs, ["lowB", "highB"]):
    data, labels = [], []
    for ds in DATASETS:
        for m in MODELS:
            g = I[(I.dataset == ds) & (I.model == m) & (I.explainer == "kernel")]
            if len(g) == 0: continue
            B = g.B.min() if which == "lowB" else g.B.max()
            data.append(g[g.B == B].rr_J3.values); labels.append(f"{ds[:4]}-{m}")
    ax.boxplot(data, labels=labels, showfliers=True, flierprops=dict(ms=2))
    ax.set_xticklabels(labels, rotation=90, fontsize=5); ax.set_title(f"KernelSHAP, {which}"); ax.set_ylabel("per-instance run-to-run J3")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig2_instance_dist.pdf")); plt.close()

# Fig 3: instance-level driver: gap between 3rd and 4th |phi| vs J3 (kernel, lowest budget with ref)
g = I[(I.explainer == "kernel") & I.gap34.notna()]
g = g[g.groupby(["dataset", "model"]).B.transform("min") == g.B]
fig, ax = plt.subplots(figsize=(3.4, 2.8))
ax.scatter(g.gap34, g.rr_J3, s=4, alpha=.4)
from scipy.stats import spearmanr
rho = spearmanr(g.gap34, g.rr_J3, nan_policy="omit")
ax.set_xlabel("relative gap |phi|(3rd)-|phi|(4th)"); ax.set_ylabel("run-to-run J3 (lowest B)")
ax.set_title(f"Spearman={rho[0]:.2f}"); plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig3_gap.pdf")); plt.close()
pd.DataFrame([dict(rho=rho[0], p=rho[1], n=len(g))]).to_csv(os.path.join(RES, "gap_spearman.csv"), index=False)

# Fig 4: cost-aware comparison: J3 vs model-evaluation rows (kernel vs kernel_l1 vs perm) averaged over cells, and avg-of-5
fig, ax = plt.subplots(figsize=(3.6, 2.9))
for ex, col in zip(EXPLAINERS, ["C0", "C1", "C2"]):
    g = C[(C.explainer == ex)].copy()
    g["bidx"] = g.groupby(["dataset", "model", "explainer"]).B.rank()
    h = g.groupby("bidx").agg(J=("rr_J3", "mean"))
    ax.plot(h.index, h.J, marker="o", label=ex, color=col)
ax.set_xlabel("budget level (1=lowest .. 4=highest)"); ax.set_ylabel("mean run-to-run J3 (all cells)"); ax.legend()
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig4_explainers.pdf")); plt.close()

# Table: explainer comparison at each budget level (mean over cells, plus per-run time)
C["lvl"] = C.groupby(["dataset", "model", "explainer"]).B.rank().astype(int)
E = C.groupby(["explainer", "lvl"]).agg(rr_J3=("rr_J3", "mean"), rr_top1=("rr_top1", "mean"), rr_rbo=("rr_rbo", "mean"),
                                         ref_J3=("ref_J3", "mean"), avg5=("avg5_J3", "mean"), cells=("rr_J3", "size")).round(3)
E.to_csv(os.path.join(RES, "table_explainers.csv")); E.to_latex(os.path.join(TAB, "explainers.tex"))

# Averaging m=5 runs vs single run vs exact (kernel)
A = C[C.explainer == "kernel"].groupby("lvl").agg(single_vs_ref=("ref_J3", "mean"), avg5_vs_ref=("avg5_J3", "mean")).round(3)
A.to_csv(os.path.join(RES, "table_avg5.csv"))

# Adequacy table: fraction of cells passing absolute and relative rules, by explainer x level
A2 = C.groupby(["explainer", "lvl"]).agg(abs_rule=("adequate_abs", "mean"), rel_rule=("no_worse_than_bg", "mean")).round(2)
A2.to_csv(os.path.join(RES, "table_rules.csv")); A2.to_latex(os.path.join(TAB, "rules.tex"))

# Per-metric disagreement (do conclusions depend on the metric?)
M = C[C.explainer == "kernel"].groupby("lvl")[["rr_J3", "rr_top1", "rr_rbo", "rr_spear", "rr_relL2", "rr_sign3"]].mean().round(3)
M.to_csv(os.path.join(RES, "table_metrics.csv")); M.to_latex(os.path.join(TAB, "metrics.tex"))
print("ok")
