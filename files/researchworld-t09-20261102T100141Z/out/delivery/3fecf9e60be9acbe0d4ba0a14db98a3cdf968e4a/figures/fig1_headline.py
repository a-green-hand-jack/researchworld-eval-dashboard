"""Fig. 1 (RQ1): relative RMSE of every estimator, mechanism x graph, main grid (experiment MAIN).
Usage: python3 fig1_headline.py [design]   design in {bern0.5 (main text, default), bern0.1, cluster0.5} (appendix variants).
Input: results/replicates.parquet (fit_data == observed). rel. RMSE = RMSE/|tau| (|tau| = 2 in every cell).
Hajek estimators are undefined in a replicate when no unit has a fully treated/control neighbourhood; their
RMSE is conditional on being defined, so cells with >5% undefined replicates are drawn as a cross on the
bottom axis instead of a point."""
import sys
import numpy as np
import matplotlib.pyplot as plt
import common as C

dsg = sys.argv[1] if len(sys.argv) > 1 else "bern0.5"
C.setup_style()
df = C.load_replicates()
df = df[(df.experiment == "MAIN") & (df.dsg == dsg)]
agg = C.aggregate(df, ["mechanism", "graph", "estimator"])
mechs = [m for m in C.MECH_LABEL if m in set(agg.mechanism)]
graphs = [g for g in C.GRAPH_LABEL if g in set(agg.graph)]
ests = [e for e in C.EST_STYLE if e in set(agg.estimator)]
Rmin = int(agg.R.min())
ylo = max(agg.rel_rmse_lo.min() * 0.8, 1e-3)
yhi = agg[agg.frac_undefined <= 0.05].rel_rmse_hi.max() * 1.3

# 2 x 2 panels at the natural width (5.5 in = \\linewidth), so that the 7 pt text is not scaled down in the paper
SHORT = {"fb_stanford": "Stanf.3"}  # Stanford3: shortened so that the six tick labels do not collide in a half-width panel
nr, nc = 2, 2
fig, axes = plt.subplots(nr, nc, figsize=(C.TEXTWIDTH, 3.7), sharex=True, sharey=True, squeeze=False)
off = np.linspace(-0.40, 0.40, len(ests))
for k, (ax, m) in enumerate(zip(axes.flat, mechs)):
    for j, e in enumerate(ests):
        s = C.EST_STYLE[e]
        for i, g in enumerate(graphs):
            r = agg[(agg.mechanism == m) & (agg.graph == g) & (agg.estimator == e)]
            if r.empty:
                continue
            r = r.iloc[0]
            lab = s["label"] if (i == 0 and m == mechs[0]) else None
            if r.frac_undefined > 0.05:
                ax.plot(i + off[j], ylo * 1.15, marker="x", ms=3.5, color=s["color"], mew=0.8, ls="", label=lab)
                continue
            ax.errorbar(i + off[j], r.rel_rmse,
                        yerr=[[r.rel_rmse - r.rel_rmse_lo], [r.rel_rmse_hi - r.rel_rmse]],
                        fmt=s["marker"], color=s["color"], ms=3.0, lw=0.7, capsize=0, label=lab)
    ax.axhline(1.0, color="#999", lw=0.6, ls=":")  # error as large as the effect itself
    ax.set_yscale("log")
    ax.set_ylim(ylo, yhi)
    ax.set_title(C.MECH_LABEL[m], loc="left", fontsize=7.5, pad=2)
    ax.grid(axis="x", visible=False)
    ax.set_xticks(range(len(graphs)))
    ax.set_xticklabels([SHORT.get(g, C.GRAPH_LABEL[g]) for g in graphs], fontsize=6)
    if k % nc == 0:
        ax.set_ylabel("rel. RMSE")
h, l = axes[0, 0].get_legend_handles_labels()
if (agg.frac_undefined > 0.05).any():  # a cross on the bottom axis = estimator undefined in >5% of replicates
    h.append(plt.Line2D([], [], marker="x", color="#777", ls="", ms=3.5, mew=0.8)); l.append("cross: undefined (>5% of runs)")
fig.legend(h, l, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.0), columnspacing=0.9, handletextpad=0.3, fontsize=6.5)
fig.subplots_adjust(top=0.80, left=0.085, right=0.995, hspace=0.35, wspace=0.08)
print(f"design={dsg}; min replicates per cell = {Rmin}")
print(C.save(fig, "fig1_headline" if dsg == "bern0.5" else f"figA1_headline_{dsg}"))
