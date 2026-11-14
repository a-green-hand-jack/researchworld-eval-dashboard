"""Fig 2 (claim C1; hypotheses H1, H2): noiseless specification bias of OLS (z, f) vs its closed-form prediction (e9).
Left: simulated vs predicted bias, all cells. Right: bias vs treatment probability p for concave/convex spillover."""
import numpy as np
import matplotlib.pyplot as plt
from common import *


def main():
    style()
    T = pd.read_csv(os.path.join(RES, "theory_vs_sim_e9.csv"))
    T["gname"] = T.graph.map(lambda s: GNAME.get(s, s))
    T["p"] = pd.to_numeric(T.design.str.split(":").str[1])
    fig, axs = plt.subplots(1, 3, figsize=(TEXTW, 2.1), gridspec_kw={"width_ratios": [1.1, 1, 1]})
    ax = axs[0]
    lim = 1.05 * max(T.pred_exact.abs().max(), T.bias.abs().max())
    ax.plot([-lim, lim], [-lim, lim], color="k", lw=0.6)
    for g in present(GORDER, T.gname):
        s = T[T.gname == g]
        ax.errorbar(s.pred_exact, s.bias, yerr=1.96 * s.bias_se, ls="none", marker=GMARK[g], color=GCOL[g], ms=3,
                    elinewidth=0.5, alpha=0.8, label=g)
    ax.set_xlabel("closed-form bias"); ax.set_ylabel("simulated noiseless bias"); ax.legend(loc="upper left", fontsize=6.5)
    ax.set_title(f"{len(T)} cells; max |dev| {(T.bias-T.pred_exact).abs().max():.2f}"); panel_label(ax, "(a)")
    for ax, kind, lab in [(axs[1], "concave", "(b)"), (axs[2], "convex", "(c)")]:
        for g in present(GORDER, T.gname):
            for curv, ls in [(3.0, "-"), (8.0, ":")]:
                s = T[(T.gname == g) & (T.o_kind == kind) & (T.o_curv == curv)].sort_values("p")
                ax.errorbar(s.p, s.bias, yerr=1.96 * s.bias_se, marker=GMARK[g], color=GCOL[g], ls=ls, ms=3, elinewidth=0.5, lw=0.9)
                ax.plot(s.p, s.pred_exact, color="k", lw=0.5, ls=ls, alpha=0.5)
        ax.axhline(0, color="k", lw=0.4)
        ax.set_xlabel("treatment probability $p$"); ax.set_title(f"{kind} spillover"); panel_label(ax, lab)
    axs[1].set_ylabel("noiseless bias")
    from matplotlib.lines import Line2D
    fig.legend(handles=[Line2D([], [], color="gray", ls="-", label="curvature 3"), Line2D([], [], color="gray", ls=":", label="curvature 8"),
                           Line2D([], [], color="k", lw=0.5, alpha=0.5, label="closed form")], loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, fontsize=6.5)
    fig.tight_layout(w_pad=0.6)
    save(fig, "fig2_bias_theory")


if __name__ == "__main__":
    main()
