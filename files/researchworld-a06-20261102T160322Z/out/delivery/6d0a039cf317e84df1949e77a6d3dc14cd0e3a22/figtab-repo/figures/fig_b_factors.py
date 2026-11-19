"""Fig B (Q1b): what drives the optimism, T0. Reference cell n=200, K=50 (a-c) / K=24 (d); mean ± 95% CI over replicates.
(a) search procedure x tau; (b) between-config correlation rho; (c) baseline accuracy; (d) few-shot demos drawn from the search set (leakage) vs n.
Reads results/runs_t0.parquet. Writes figures/fig_b_factors.pdf"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import style, common

style.apply()
r = common.main_grid(pd.read_parquet(common.path("runs_t0.parquet")))
base = dict(rho=0.6, base_acc=0.3, leakage=0)
fig, axs = plt.subplots(1, 4, figsize=(style.TEXT_WIDTH_IN, 2.1), sharey=True)
TC = {0.0: "#000000", 0.1: "#D55E00"}
# (a) procedure x tau, K=50 n=200
d = r[(r.n == 200) & (r.K == 50) & (r.rho == 0.6) & (r.base_acc == 0.3) & (r.leakage == 0)]
g = common.gap_table(d, ["procedure", "tau"]); procs = ["exhaustive", "halving", "greedy"]; ax = axs[0]
for tau, off in zip([0.0, 0.1, 0.2], [-0.2, 0, 0.2]):
    for i, p in enumerate(procs):
        x = g[(g.procedure == p) & (g.tau == tau)]
        if len(x): ax.errorbar(i + off, x["mean"], yerr=[x["mean"] - x.lo, x.hi - x["mean"]], fmt="o", ms=3, capsize=1.5, color=plt.cm.viridis({0.0: .1, .1: .5, .2: .85}[tau]), label=rf"$\tau$={tau:g}" if i == 0 else None)
ax.set_xticks(range(3)); ax.set_xticklabels(procs, rotation=40, ha="right"); ax.set_title("(a) procedure"); ax.legend(frameon=False, fontsize=6)
ax.set_ylabel("reported − fresh accuracy (points)")
# (b) rho, (c) base_acc: exhaustive K=50 n=200 tau in {0, 0.1}
for ax, col, title, xl in [(axs[1], "rho", "(b) correlation", r"latent correlation $\rho$"), (axs[2], "base_acc", "(c) baseline acc.", "baseline accuracy")]:
    other = {"rho": ("base_acc", 0.3), "base_acc": ("rho", 0.6)}[col]
    d = r[(r.n == 200) & (r.K == 50) & (r.procedure == "exhaustive") & (r.leakage == 0) & (r[other[0]] == other[1])]
    g = common.gap_table(d, [col, "tau"])
    for tau in (0.0, 0.1):
        x = g[g.tau == tau].sort_values(col)
        ax.errorbar(x[col], x["mean"], yerr=[x["mean"] - x.lo, x.hi - x["mean"]], color=TC[tau], marker="o", ms=3, lw=1, capsize=1.5, label=rf"$\tau$={tau:g}")
    ax.set_title(title); ax.set_xlabel(xl); ax.set_xticks(sorted(g[col].unique()))
axs[1].legend(frameon=False, fontsize=6)
# (d) leakage K=24
d = r[(r.K == 24) & (r.procedure == "exhaustive") & (r.rho == 0.6) & (r.base_acc == 0.3)]
g = common.gap_table(d, ["leakage", "tau", "n"]); ax = axs[3]
for tau in (0.0, 0.1):
    for lk, ls in [(0, "-"), (1, "--")]:
        x = g[(g.tau == tau) & (g.leakage == lk)].sort_values("n")
        ax.errorbar(x.n, x["mean"], yerr=[x["mean"] - x.lo, x.hi - x["mean"]], color=TC[tau], ls=ls, marker="o", ms=3, lw=1, capsize=1.5, label=(rf"$\tau$={tau:g}" if not lk else None))
ax.set_xscale("log"); ax.set_xticks([50, 100, 200, 500]); ax.set_xticklabels([50, 100, 200, 500]); ax.minorticks_off()
ax.set_title("(d) leakage, K=24"); ax.set_xlabel("search-set size $n$")
ax.legend([Line2D([], [], color="0.3", ls="-"), Line2D([], [], color="0.3", ls="--")], ["no leakage", "leakage"], frameon=False, fontsize=6, loc="upper right", handlelength=1.6)  # colours as in (b)
for a in axs: a.axhline(0, color="0.5", lw=0.6)
fig.tight_layout()
fig.savefig(f"{common.OUT}/fig_b_factors.pdf")
print("min reps per point:", int(g.reps.min()))
