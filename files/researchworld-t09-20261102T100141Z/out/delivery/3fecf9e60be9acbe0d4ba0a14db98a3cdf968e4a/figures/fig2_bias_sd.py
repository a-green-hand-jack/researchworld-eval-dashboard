"""Fig. 2 (RQ2): is the error bias or variance? |bias| vs SD of the (relative) error for every
main-grid cell (aggregated over graph draws x assignments) and estimator, log-log, with the bias = SD diagonal.
Points above the diagonal are bias-dominated, below it variance-dominated.
Input: results/replicates.parquet, experiment MAIN, fit_data observed (R, per-cell reps, see MANIFEST.md).
Aggregation: bias and SD of err/|tau| over all replicates of a cell (synthetic cells pool 5 graph draws)."""
import numpy as np
import matplotlib.pyplot as plt
import common as C

C.setup_style()
df = C.load_replicates()
df = df[df.experiment == "MAIN"]
agg = C.aggregate(df, ["tag", "mechanism", "dsg", "graph", "estimator"])
agg = agg[agg.frac_undefined < 0.05]
shown = [e for e in ("dm", "hajek_q0.75", "ols_f", "ols_f_deg", "ols_f2", "ols_poly") if e in set(agg.estimator)]
designs = [d for d in C.DESIGN_LABEL if d in set(agg.dsg)]
fig, axes = plt.subplots(1, len(designs), figsize=(C.TEXTWIDTH, 2.2), sharex=True, sharey=True)
lim = (3e-3, max(3, 1.2 * max(agg.sd.max(), agg.bias.abs().max())))  # no point is clipped
for ax, d in zip(np.atleast_1d(axes), designs):
    for e in shown:
        s = C.EST_STYLE[e]
        r = agg[(agg.dsg == d) & (agg.estimator == e)]
        ax.plot(r.sd, r.bias.abs(), ls="", marker=s["marker"], ms=3, mfc="none" if e == "dm" else s["color"],
                color=s["color"], mew=0.6, alpha=0.85, label=s["label"])
    x = np.geomspace(*lim, 50)
    ax.text(0.04, 0.95, "bias-\ndominated", transform=ax.transAxes, fontsize=6, color="#777", va="top")  # inside the axes, clear of the frame
    ax.text(0.97, 0.05, "variance-\ndominated", transform=ax.transAxes, fontsize=6, color="#777", ha="right", va="bottom")
    ax.plot(x, x, color="#888", lw=0.6)  # bias = SD
    ax.set(xscale="log", yscale="log", xlim=lim, ylim=lim, xlabel=r"SD / $|\tau|$")
    ax.set_title(C.DESIGN_LABEL[d], fontsize=7.5)
np.atleast_1d(axes)[0].set_ylabel(r"|bias| / $|\tau|$")
h, l = np.atleast_1d(axes)[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.22), columnspacing=1.0, handletextpad=0.3)
print("cells per panel:", agg.groupby("dsg").tag.nunique().to_dict())
print(C.save(fig, "fig2_bias_sd"))
