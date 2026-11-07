"""[reads] results/summary_validity_real.csv  [writes] figures/fig_validity.{pdf,png}  (run via run_all.sh)
Fig (claim C0): empirical coverage of Wald / t / studentised-bootstrap intervals vs labeled size n, real pools.
Input: data_in/summary_validity_real.csv (experiment-repo; 2000 replicates per cell, i.i.d. with replacement from the pool,
N = min(pool, 20000)).  Error bars: Wilson 95% interval of the coverage (cov_lo, cov_hi)."""
import sys, numpy as np, pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, __file__.rsplit("/", 1)[0]); import style; style.setup()
v = pd.read_csv("data_in/summary_validity_real.csv")
order = ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare", "census_education"]
spec = [("classical", "classical, Wald", "#555555", "x", "-"), ("ppi", "PPI, Wald", "#E69F00", "s", "-"),
        ("ppi++", "PPI++, Wald", "#000000", "o", "-"), ("ppi++_t", "PPI++, $t$", "#0072B2", "^", "-"),
        ("ppi++_boot", "PPI++, studentised boot.", "#D55E00", "D", "-")]
fig, axs = plt.subplots(2, 4, figsize=(style.TEXT_W * 1.2, 3.6), sharex=True, sharey=True)
for ax, d in zip(axs.flat, order):
    ax.axhline(0.95, color="k", lw=0.8)
    for k, (m, lab, c, mk, ls) in enumerate(spec):
        s = v[(v.dataset == d) & (v.method == m)].sort_values("n")
        x = s.n * (1 + 0.03 * (k - 2))      # small horizontal offset so Wilson bars do not overlap
        ax.errorbar(x, s.coverage, yerr=[s.coverage - s.cov_lo, s.cov_hi - s.coverage], color=c, marker=mk, ms=3, lw=0.8,
                    elinewidth=0.6, capsize=0, label=lab)
    ax.set_xscale("log"); ax.set_title(style.DATASET_LABEL[d]); ax.minorticks_off()
    ax.set_xticks([15, 50, 200, 500]); ax.set_xticklabels(["15", "50", "200", "500"])
for ax in axs[1]: ax.set_xlabel("labeled size $n$")
for ax in axs[:, 0]: ax.set_ylabel("coverage")
axs.flat[0].set_ylim(0.62, 1.0)
axs.flat[-1].axis("off")
h, l = axs.flat[0].get_legend_handles_labels()
axs.flat[-1].legend(h, l, loc="center", frameon=False, fontsize=6.5)
fig.tight_layout()
fig.savefig("figures/fig_validity.pdf"); fig.savefig("figures/fig_validity.png", dpi=200)
