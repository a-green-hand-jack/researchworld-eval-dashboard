"""Fig. 4 (H6): coverage of the nominal-95% cluster-robust sandwich CI vs the bias-to-SD ratio of the estimator.
One point per main-grid cell and OLS estimator (95% normal interval from a Louvain-community cluster-robust
variance, results/replicates.parquet ci_lo/ci_hi). Dashed: coverage of an interval whose width is correct
(half-width 1.96 SD) when the estimator has bias b = |bias|/SD: P(|Z + b| <= 1.96).
Error bars: binomial 95% interval over the cell's replicates."""
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import common as C

C.setup_style()
df = C.load_replicates()
df = df[(df.experiment == "MAIN") & df.estimator.isin(["ols_f", "ols_f_deg", "ols_f2", "ols_poly"])]
agg = C.aggregate(df, ["tag", "mechanism", "dsg", "estimator"])
agg["bsd"] = agg.bias.abs() / agg.sd
fig, ax = plt.subplots(figsize=(C.TEXTWIDTH * 0.7, 2.7))
mk = {"bern0.5": "o", "bern0.1": "^", "cluster0.5": "s"}
for e in agg.estimator.unique():
    s = C.EST_STYLE[e]
    for dsg, m in mk.items():
        r = agg[(agg.estimator == e) & (agg.dsg == dsg)]
        ax.errorbar(r.bsd, r.coverage, yerr=1.96 * r.cov_se, fmt=m, color=s["color"], ms=3.3, lw=0.5, alpha=0.8, mew=0.4,
                    label=s["label"] if dsg == "bern0.5" else None)
b = np.linspace(0, agg.bsd.max() * 1.05, 200)
ax.plot(b, norm.cdf(1.96 - b) - norm.cdf(-1.96 - b), "k--", lw=0.8, label="normal interval of correct width,\nbias b SDs")
ax.axhline(0.95, color="#999", lw=0.6, ls=":")
ax.set(xlabel=r"|bias| / SD of the estimator", ylabel="coverage of nominal 95% CI", ylim=(0, 1.02))
h, l = ax.get_legend_handles_labels()
from matplotlib.lines import Line2D
h += [Line2D([], [], color="#777", marker=m, ls="", ms=4) for m in mk.values()]
l += [C.DESIGN_LABEL[k] for k in mk]
ax.legend(h, l, frameon=False, fontsize=6, loc="upper left", bbox_to_anchor=(1.0, 1.0))
print("R per cell (min):", int(agg.R.min()))
print(C.save(fig, "fig4_coverage"))
