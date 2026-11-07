"""Fig A-T1 (Q1a, Q1b): optimism of the naive report on the real MMLU-Pro outcome matrix (Qwen2.5-1.5B-Instruct, 2000 items),
reported - fresh accuracy (points) vs search-set size n, by candidates K (exhaustive search; main cells, 1000 replicates each).
Bars: 95% CI = mean ± 1.96 x delete-a-block SE (10 blocks): replicates share items, so the plain replicate SE is too small.
Dashed: closed-form prediction fed with the matrix's own sigma, r, tau (`gap_theory_from_matrix`).
Reads results/runs_t1.parquet, results/summary_gap_t1.csv. Writes figures/fig_a_t1.pdf"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import style, common

style.apply()
runs = pd.read_parquet(common.path("runs_t1.parquet"))
runs = runs[(runs.procedure == "exhaustive") & ~runs.cell_id.str.contains("|m3", regex=False)]
th = pd.read_csv(common.path("summary_gap_t1.csv"))
th = th[(th.procedure == "exhaustive") & ~th.cell_id.str.contains("|m3", regex=False)]
Ks = [2, 5, 24, 100, 300]
g = common.block_gap_table(runs, ["K", "n"])
chk = g.merge(th[["K", "n", "gap_block_se"]], on=["K", "n"])
assert np.allclose(chk.se / 100, chk.gap_block_se, rtol=1e-6), "block SE differs from experiment-repo's"
cols = plt.cm.viridis(np.linspace(0.05, 0.9, len(Ks)))
fig, ax = plt.subplots(figsize=(style.TEXT_WIDTH_IN, 2.2))
for c, K in zip(cols, Ks):
    d = g[g.K == K].sort_values("n")
    ax.errorbar(d.n, d["mean"], yerr=1.96 * d.se, color=c, marker="o", ms=3, lw=1, capsize=1.5, label=f"K={K}")
    t = th[th.K == K].sort_values("n")
    ax.plot(t.n, 100 * t.gap_theory_from_matrix, color=c, ls="--", lw=0.8)
ax.axhline(0, color="0.5", lw=0.6)
ax.set_xscale("log"); ax.set_xticks([50, 100, 200, 300, 500]); ax.set_xticklabels([50, 100, 200, 300, 500]); ax.minorticks_off()
ax.set_xlabel("search-set size $n$"); ax.set_ylabel("reported − fresh accuracy (points)")
ax.legend(title="candidates", frameon=False, loc="upper right", ncol=1)
fig.savefig(f"{common.OUT}/fig_a_t1.pdf")
print("reps per cell:", int(g.reps.min()), "-", int(g.reps.max()))
