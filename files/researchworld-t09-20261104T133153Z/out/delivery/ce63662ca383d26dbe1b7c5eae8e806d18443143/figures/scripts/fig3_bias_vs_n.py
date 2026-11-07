"""Fig 3 (claim C1; hypothesis H3): does the misspecification bias shrink with n? Concave spillover (gamma=2), SBM, e10.
Top: bias vs n (does not vanish for the misspecified regressions). Bottom: SD vs n with the n^{-1/2} guide."""
import numpy as np
import matplotlib.pyplot as plt
from common import *

DES = [("bern:0.5", "Bernoulli(0.5)"), ("bern:0.1", "Bernoulli(0.1)"), ("louv:1.0,0.5", "Louvain clusters")]
EST = ["DM", "OLS_f", "OLS_quad", "ORACLE_D"]


def main():
    style()
    d = load("e10"); d = d[d.o_kind == "concave"]
    fig, axs = plt.subplots(2, 3, figsize=(TEXTW, 3.1), sharex=True)
    for j, (des, title) in enumerate(DES):
        s0 = d[d.design == des]
        for est in EST:
            s = s0[s0.est_name == est].sort_values("n_nom")
            if s.empty:
                continue
            kw = dict(color=ECOL[est], marker="o", ms=3, capsize=1.5, elinewidth=0.6, label=ELAB[est], ls="--" if est == "ORACLE_D" else "-")
            axs[0, j].errorbar(s.n_nom, s.bias, yerr=1.96 * s.bias_se, **kw)
            axs[1, j].errorbar(s.n_nom, s.sd, yerr=1.96 * sd_se(s), **kw)
        axs[0, j].axhline(0, color="k", lw=0.5); axs[0, j].set_title(title)
        s = s0[s0.est_name == "ORACLE_D"].sort_values("n_nom")
        if len(s):
            n = s.n_nom.values; axs[1, j].plot(n, s.sd.values[0] * np.sqrt(n[0] / n), color="gray", lw=0.8, ls=":")
        axs[1, j].set_xscale("log"); axs[1, j].set_yscale("log"); axs[1, j].set_xlabel("number of units $n$")
        symlogy(axs[0, j])
    axs[0, 0].set_ylabel("bias (symlog axis)"); axs[1, 0].set_ylabel("SD of estimate")
    axs[1, 0].text(0.04, 0.04, "dotted: $n^{-1/2}$ from oracle", transform=axs[1, 0].transAxes, ha="left", va="bottom", fontsize=6.5, color="gray")
    fig.legend(*axs[0, 0].get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=4, fontsize=6.5)
    fig.tight_layout(w_pad=0.6, h_pad=0.6)
    save(fig, "fig3_bias_vs_n")


if __name__ == "__main__":
    main()
