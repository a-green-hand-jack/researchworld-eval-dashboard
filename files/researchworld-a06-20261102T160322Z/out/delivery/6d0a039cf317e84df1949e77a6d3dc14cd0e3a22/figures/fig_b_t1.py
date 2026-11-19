"""Fig B-T1 (Q1b): does the search procedure change the optimism on the real MMLU-Pro matrix?
Reported - fresh accuracy (points) vs n; left K=24 (exhaustive, successive halving, greedy), right K in {100, 300} (exhaustive vs halving).
Bars: mean ± 1.96 x delete-a-block SE (10 blocks). Reads results/runs_t1.parquet. Writes figures/fig_b_t1.pdf"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import style, common

style.apply()
runs = pd.read_parquet(common.path("runs_t1.parquet"))
runs = runs[~runs.cell_id.str.contains("|m3", regex=False)]
g = common.block_gap_table(runs, ["procedure", "K", "n"])
PC = {"exhaustive": style.OKABE_ITO[5], "halving": style.OKABE_ITO[1], "greedy": style.OKABE_ITO[3]}
LS = {"exhaustive": "-", "halving": "--", "greedy": ":"}
fig, axs = plt.subplots(1, 3, figsize=(style.TEXT_WIDTH_IN, 1.9), sharey=True)
for ax, K in zip(axs, [24, 100, 300]):
    for p in ["exhaustive", "halving", "greedy"]:
        d = g[(g.procedure == p) & (g.K == K)].sort_values("n")
        if d.empty:
            continue
        ax.errorbar(d.n, d["mean"], yerr=1.96 * d.se, color=PC[p], ls=LS[p], marker="o", ms=3, lw=1, capsize=1.5, label=p)
    ax.axhline(0, color="0.5", lw=0.6)
    ax.set_xscale("log"); ax.set_xticks([50, 100, 200, 500]); ax.set_xticklabels([50, 100, 200, 500]); ax.minorticks_off()
    ax.set_title(f"K={K}", fontsize=8); ax.set_xlabel("search-set size $n$")
axs[0].set_ylabel("reported − fresh accuracy (points)")
axs[0].legend(frameon=False, loc="upper right")
fig.tight_layout(pad=0.4)
fig.savefig(f"{common.OUT}/fig_b_t1.pdf")
print(g[g.K.isin([24, 100, 300]) & g.n.isin([100, 500])].round(2).to_string())
