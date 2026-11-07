"""Fig A (Q1a, Q1b): optimism = reported - fresh accuracy of the selected configuration vs search-set size n, by K.
T0 = synthetic world with known truth, panels by true spread tau. Dashed = extreme-value theory curve from results/theory_curve_t0.csv.
Reads results/runs_t0.parquet, results/theory_curve_t0.csv. Writes figures/fig_a_optimism.pdf"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import style, common

style.apply()
runs = pd.read_parquet(common.path("runs_t0.parquet"))
th = pd.read_csv(common.path("theory_curve_t0.csv"))
runs = common.main_grid(runs)
runs = runs[(runs.procedure == "exhaustive") & (runs.leakage == 0) & (runs.rho == 0.6) & (runs.base_acc == 0.3)]
g = common.gap_table(runs, ["tau", "K", "n"])
th = th[th.cell_id.isin(runs.cell_id.unique())]
taus = sorted(g.tau.unique()); Ks = sorted(g.K.unique())
cols = plt.cm.viridis(np.linspace(0.05, 0.9, len(Ks)))
fig, axs = plt.subplots(1, len(taus), figsize=(style.TEXT_WIDTH_IN, 2.1), sharey=True)
for ax, tau in zip(np.atleast_1d(axs), taus):
    for c, K in zip(cols, Ks):
        d = g[(g.tau == tau) & (g.K == K)].sort_values("n")
        ax.errorbar(d.n, d["mean"], yerr=[d["mean"] - d.lo, d.hi - d["mean"]], color=c, marker="o", ms=3, lw=1, capsize=1.5, label=f"K={K}")
        t = th[(th.tau == tau) & (th.K == K)].sort_values("n")
        ax.plot(t.n, 100 * t.gap_theory, color=c, ls="--", lw=0.8)
    ax.axhline(0, color="0.5", lw=0.6)
    ax.set_xscale("log"); ax.set_xticks(sorted(g.n.unique())); ax.set_xticklabels(sorted(g.n.unique()), rotation=45)
    ax.minorticks_off(); ax.set_title(rf"true spread $\tau$={tau:g}"); ax.set_xlabel("search-set size $n$")
np.atleast_1d(axs)[0].set_ylabel("reported − fresh accuracy (points)")
np.atleast_1d(axs)[-1].legend(title="candidates", frameon=False, loc="upper right")
fig.savefig(f"{common.OUT}/fig_a_optimism.pdf")
print("reps per cell:", int(g.reps.min()), "-", int(g.reps.max()))
