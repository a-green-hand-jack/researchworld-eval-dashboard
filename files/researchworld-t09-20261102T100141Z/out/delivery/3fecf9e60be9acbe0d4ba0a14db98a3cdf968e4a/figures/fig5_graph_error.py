"""Fig. 5 (H5 / robustness): relative RMSE and |bias| vs the fraction of edges dropped-and-re-added at random
in the graph used to build the features (experiment E11_grapherr; sbm and ego-FB, linear-in-fraction mechanism,
two interference strengths gamma). Input: results/replicates.parquet (observed)."""
import numpy as np
import matplotlib.pyplot as plt
import common as C

C.setup_style()
df = C.load_replicates()
df = df[df.experiment == "E11_grapherr"].copy()
t = df.tag.str.split("|", expand=True)
df["err_rate"] = t[0].str[3:].astype(float)
df["gname"] = t[1]
df["gam"] = t[2].str[5:].astype(float)
agg = C.aggregate(df, ["gname", "gam", "err_rate", "estimator"])
combos = [(g, ga) for ga in sorted(agg.gam.unique(), reverse=True) for g in ("sbm", "fb_ego")]
fig, axes = plt.subplots(2, len(combos), figsize=(C.TEXTWIDTH, 3.3), sharex=True, squeeze=False)
for k, (g, ga) in enumerate(combos):
    for e in agg.estimator.unique():
        s = C.EST_STYLE[e]
        r = agg[(agg.gname == g) & (agg.gam == ga) & (agg.estimator == e)].sort_values("err_rate")
        axes[0, k].errorbar(r.err_rate, r.rel_rmse, yerr=[r.rel_rmse - r.rel_rmse_lo, r.rel_rmse_hi - r.rel_rmse],
                            fmt="-" + s["marker"], color=s["color"], ms=3, lw=0.9, capsize=0, label=s["label"])
        axes[1, k].errorbar(r.err_rate, r.bias, yerr=[r.bias - r.bias_lo, r.bias_hi - r.bias],
                            fmt="-" + s["marker"], color=s["color"], ms=3, lw=0.9, capsize=0)
    axes[0, k].set_title(f"{C.GRAPH_LABEL[g]}\n"+rf"spill-over $\gamma$ = {ga:g}", fontsize=7)
    axes[1, k].set_xlabel("edge error rate")
    axes[1, k].axhline(0, color="#999", lw=0.6)
axes[0, 0].set_ylabel("rel. RMSE"); axes[1, 0].set_ylabel("bias / |tau|")
h, l = axes[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.06))
fig.tight_layout(rect=(0, 0.04, 1, 1))
print("R per cell (min):", int(agg.R.min()))
print(C.save(fig, "fig5_graph_error"))
