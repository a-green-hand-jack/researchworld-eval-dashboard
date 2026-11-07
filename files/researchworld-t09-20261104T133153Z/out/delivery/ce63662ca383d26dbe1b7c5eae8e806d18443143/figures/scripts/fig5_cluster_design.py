"""Fig 5 (claim C4; hypothesis H5): graph-cluster randomisation vs random clusters of identical sizes (control), by cluster
resolution (e4, spillover gamma=2, concave unless noted, cluster treatment prob. 0.5). Columns: share of units with
neighbour-treated fraction >= 0.9 (exposure support near the 'all treated' corner), |bias|, RMSE. Grey line: Bernoulli(0.5)."""
import numpy as np
import matplotlib.pyplot as plt
from common import *

EST = ["DM", "OLS_f", "ORACLE_D"]


def main(kind="concave"):
    style()
    e4 = load("e4"); e4 = e4[e4.o_kind == kind]
    graphs = present(["SBM", "Stanford3", "ego-Facebook"], e4.gname)
    fig, axs = plt.subplots(len(graphs), 3, figsize=(TEXTW, 1.75 * len(graphs) + 0.3), squeeze=False, sharex=True)
    for i, g in enumerate(graphs):
        d = e4[e4.gname == g]
        bern = d[(d.dkind == "bern") & (d.p == 0.5)]
        for j, (metric, lab) in enumerate([("supp_hi", "units with $f\\geq0.9$"), ("bias", "bias (symlog axis)"), ("rmse", "RMSE")]):
            ax = axs[i, j]
            for cl, ls, mk in [("louv", "-", "o"), ("rand", "--", "s")]:
                for est in (["OLS_f"] if metric == "supp_hi" else EST):
                    s = d[(d.dkind == cl) & (d.est_name == est)].sort_values("dres")
                    if s.empty:
                        continue
                    y = s[metric]
                    err = None if metric == "supp_hi" else 1.96 * (s.bias_se if metric == "bias" else rmse_se(s))
                    col = "#444444" if metric == "supp_hi" else ECOL[est]
                    ax.errorbar(s.dres, y, yerr=err, color=col, ls=ls, marker=mk, ms=3, lw=1, elinewidth=0.5, capsize=1,
                                label=(f"{ELAB[est]}, " if metric != "supp_hi" else "") + ("graph clusters" if cl == "louv" else "random clusters"))
            for est in (["OLS_f"] if metric == "supp_hi" else EST):
                b = bern[bern.est_name == est]
                if len(b):
                    y = b.supp_hi.iloc[0] if metric == "supp_hi" else (b.bias.iloc[0] if metric == "bias" else b.rmse.iloc[0])
                    ax.axhline(y, color=ECOL[est] if metric != "supp_hi" else "#444444", lw=0.6, ls=":", alpha=0.7)
            ax.set_xscale("log")
            ax.set_xticks(sorted(d.dres.dropna().unique())); ax.get_xaxis().set_major_formatter(plt.ScalarFormatter()); ax.minorticks_off()
            ax.tick_params(axis="x", labelsize=6)
            if metric == "bias":
                symlogy(ax); ax.axhline(0, color="k", lw=0.4)
            elif metric == "rmse":
                ax.set_yscale("log"); ax.minorticks_off(); ax.set_yticks([t for t in (0.2, 0.3, 0.5, 1, 2, 5, 10) if ax.get_ylim()[0] <= t <= ax.get_ylim()[1]]); plainlog(ax)
            if i == 0:
                ax.set_title(lab)
            if i == len(graphs) - 1:
                ax.set_xlabel("cluster resolution")
        axs[i, 0].set_ylabel(g)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=ECOL[e], marker="o", ms=3, label=ELAB[e]) for e in EST]
    h += [Line2D([], [], color="gray", ls="-", label="graph (Louvain) clusters"), Line2D([], [], color="gray", ls="--", label="random clusters, same sizes"),
          Line2D([], [], color="gray", ls=":", lw=0.7, label="Bernoulli(0.5)")]
    fig.tight_layout(w_pad=0.6, h_pad=0.5)
    fig.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, fontsize=6.5)
    save(fig, "fig5_cluster_design" + ("" if kind == "concave" else "_" + kind))


if __name__ == "__main__":
    import sys
    main(*(sys.argv[1:2]))
