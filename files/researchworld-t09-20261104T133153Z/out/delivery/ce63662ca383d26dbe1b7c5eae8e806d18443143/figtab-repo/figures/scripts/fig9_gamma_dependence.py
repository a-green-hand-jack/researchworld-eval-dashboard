"""Fig 9 (claim C1, C3; hypothesis H3, e11 post-freeze): bias of the GATE estimate vs interference strength gamma when the outcome
model is NOT linear (concave / sigmoid 1-hop spillover), Bernoulli(0.5) and Bernoulli(0.1). The misspecified regression OLS (z,f) has
bias proportional to gamma (sign and size set by shape x p); the correctly specified regression has none; DM bias is -gamma.
Colour = estimator, marker = graph; bars +-1.96 MC SE; dotted: weighted through-origin fit of the OLS (z,f) bias. OLS quad (gamma-independent bias of -2...-10 at p=0.1) is off the scale and
listed in results/tables/t14_gamma_dependence.csv."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from common import *

EST = ["DM", "OLS_f", "ORACLE_D"]


def main():
    style()
    d = load("e11")
    fig, axs = plt.subplots(2, 2, figsize=(TEXTW, 3.9), sharex=True)
    for i, kind in enumerate(["concave", "sigmoid"]):
        for j, des in enumerate(["bern:0.5", "bern:0.1"]):
            ax = axs[i, j]
            for g in present(GORDER, d.gname):
                for est in EST:
                    s = d[(d.gname == g) & (d.o_kind == kind) & (d.design == des) & (d.est_name == est)].sort_values("o_gamma")
                    if est == "OLS_f":  # weighted through-origin fit bias = b*gamma (thin dotted)
                        w = 1 / s.bias_se ** 2; b = (w * s.o_gamma * s.bias).sum() / (w * s.o_gamma ** 2).sum()
                        ax.plot([0, 4], [0, 4 * b], color="k", lw=0.5, ls=":", zorder=0)
                    ax.errorbar(s.o_gamma, s.bias, yerr=1.96 * s.bias_se, color=ECOL[est], marker=GMARK[g], ms=3, lw=0.8, elinewidth=0.5,
                                capsize=1, ls="--" if est == "ORACLE_D" else "-", alpha=0.9)
            ax.axhline(0, color="k", lw=0.4)
            ax.set_title(f"{kind}, Bernoulli({des.split(':')[1]})")
            ax.set_xticks([0.5, 1, 2, 4])
            if i == 1:
                ax.set_xlabel("interference strength $\\gamma$")
            if j == 0:
                ax.set_ylabel("bias of GATE estimate")
    h = [Line2D([], [], color=ECOL[e], ls="--" if e == "ORACLE_D" else "-", label=ELAB[e]) for e in EST]
    h += [Line2D([], [], color="k", lw=0.5, ls=":", label="OLS $z,f$ fit $b\\gamma$")]
    h += [Line2D([], [], color="gray", marker=GMARK[g], ls="none", ms=3.5, label=g) for g in present(GORDER, d.gname)]
    fig.tight_layout(h_pad=0.8, w_pad=0.8)
    fig.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=8, fontsize=6.2, columnspacing=0.8)
    save(fig, "fig9_gamma_dependence")


if __name__ == "__main__":
    main()
