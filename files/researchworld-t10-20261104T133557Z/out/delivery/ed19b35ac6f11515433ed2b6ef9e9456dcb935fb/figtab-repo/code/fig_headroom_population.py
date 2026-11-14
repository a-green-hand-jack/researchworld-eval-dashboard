"""[reads] results/headroom_population.csv, results/datasets.csv  [writes] figures/fig_headroom_population.{pdf,png}  (run via run_all.sh)
Fig (claim C1/C5): asymptotic width ratio of the best control variate in each class vs power-tuned PPI++, real pools.
Input: data_in/headroom_population.csv (experiment-repo results/headroom_population.csv, long format; commit in
data_in/PROVENANCE_experiment_repo_commit.txt) and data_in/datasets.csv.  rho = n/N = 0 (N -> infinity) shown.
Error bars: SD over 10 random 2-fold splits used for cross-fitting on the full pool; they reflect split noise only,
not sampling variability of the pool."""
import sys, numpy as np, pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, __file__.rsplit("/", 1)[0]); import style; style.setup()
h = pd.read_csv("data_in/headroom_population.csv"); h = h[h.rho == 0]
ds = pd.read_csv("data_in/datasets.csv").set_index("dataset")
order = ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare", "census_education"]
methods = ["ppi", "cf_lin_f", "cf_iso_f", "cf_gbm_f", "cf_lin_fX", "cf_gbm_fX"]
fig, ax = plt.subplots(figsize=(style.TEXT_W, 2.7))
ax.axhline(1, color="k", lw=0.8); ax.axhspan(0.99, 1.01, color="#eeeeee", zorder=0)
w = 0.8 / len(methods)
for j, m in enumerate(methods):
    lab, colr, mk = style.style_of(m)
    d = h[h.method == m].set_index("dataset").reindex(order)
    xs = np.arange(len(order)) + (j - (len(methods) - 1) / 2) * w
    ok = d.width_ratio.notna().values
    ax.errorbar(xs[ok], d.width_ratio.values[ok], yerr=d.width_ratio_sd_splits.values[ok], fmt=mk, color=colr, ms=4.5,
                mec="white", mew=0.4, elinewidth=0.8, capsize=1.2, label=lab)
ax.set_xticks(range(len(order)))
ax.set_xticklabels([style.DATASET_LABEL[d].replace(" ", "\n") + f"\n$r$={ds.loc[d, 'corr_y_yhat']:.2f}" for d in order])
ax.tick_params(axis="x", labelsize=6.5)
ax.set_yscale("log"); ax.minorticks_off()
ticks = [0.98, 0.99, 1, 1.02, 1.05, 1.1]; ax.set_yticks(ticks); ax.set_yticklabels([f"{t:g}" for t in ticks])
ax.set_ylim(0.975, 1.2)
ax.set_ylabel("asymptotic width / PPI++ width")
ax.legend(ncol=3, loc="upper left", frameon=False, handletextpad=0.2, columnspacing=1.0)
fig.savefig("figures/fig_headroom_population.pdf"); fig.savefig("figures/fig_headroom_population.png", dpi=200)
