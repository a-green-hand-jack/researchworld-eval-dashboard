"""Fig 1 (claims C2, C3; hypothesis H6): bias and RMSE of the estimators vs interference strength gamma (e1).
Truth is linear-in-means spillover, GATE = tau + gamma. Usage: fig1_strength.py [main|app]"""
import sys
import numpy as np
import matplotlib.pyplot as plt
from common import *

EST = ["DM", "OLS_f", "OLS_big", "ORACLE_D"]


def draw(ax, d, metric, est):
    s = d[d.est_name == est].sort_values("o_gamma")
    if s.empty:
        return
    y = s[metric]
    err = 1.96 * (s.bias_se if metric == "bias" else rmse_se(s))
    ax.errorbar(s.o_gamma, y, yerr=err, color=ECOL[est], marker="o", ms=3, lw=1.1, capsize=1.5, elinewidth=0.7,
                ls="--" if est == "ORACLE_D" else "-", label=ELAB[est])


def main(kind):
    style()
    e1 = load("e1")
    if kind == "main":
        graphs, design = present(["SBM", "BA", "Stanford3"], e1.gname), "bern:0.5"
        fig, axs = plt.subplots(2, len(graphs), figsize=(TEXTW, 3.0), sharex=True, squeeze=False)
        for j, g in enumerate(graphs):
            d = e1[(e1.gname == g) & (e1.design == design)]
            for est in EST:
                draw(axs[0, j], d, "bias", est); draw(axs[1, j], d, "rmse", est)
            axs[0, j].set_title(f"{g}, Bernoulli(0.5)")
            axs[0, j].axhline(0, color="k", lw=0.5)
            axs[1, j].set_xlabel("interference strength $\\gamma$")
            axs[1, j].set_yscale("log")
        axs[0, 0].set_ylabel("bias of GATE estimate"); axs[1, 0].set_ylabel("RMSE")
        fig.legend(*axs[0, 0].get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=4, fontsize=6.5)
        name = "fig1_strength"
    else:  # appendix: all graphs, both designs, RMSE only
        graphs = present(GORDER, e1.gname)
        fig, axs = plt.subplots(2, len(graphs), figsize=(TEXTW * 1.35, 3.0), sharex=True, sharey=True, squeeze=False)
        for i, design in enumerate(["bern:0.5", "louv:1.0,0.5"]):
            for j, g in enumerate(graphs):
                d = e1[(e1.gname == g) & (e1.design == design)]
                for est in EST:
                    draw(axs[i, j], d, "rmse", est)
                axs[i, j].set_yscale("log")
                if i == 0:
                    axs[0, j].set_title(g)
                if i == 1:
                    axs[1, j].set_xlabel("$\\gamma$")
            axs[i, 0].set_ylabel("RMSE (" + ("Bernoulli(0.5)" if i == 0 else "Louvain clusters") + ")")
        fig.legend(*axs[0, 0].get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=4, fontsize=6.5)
        name = "fig1_strength_all"
    fig.tight_layout(w_pad=0.6, h_pad=0.6)
    save(fig, name)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
