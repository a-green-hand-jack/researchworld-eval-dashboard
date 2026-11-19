"""Fig. C3: median k_min along the power-mean family M_p (min = p->-inf, geometric mean p=0, mean p=1), per gain model.

Encoding: p on an ordinal x axis (the grid is not equally spaced), band = 95% bootstrap CI over targets (power_mean_curve.csv).
A monotone C3 would be a monotone line; U-shapes are visible. One panel per board; all attackers (mean-rank >= 2).
"""
import numpy as np
import matplotlib.pyplot as plt
from common import *

PS = [-np.inf, -2, -1, 0, 0.5, 1, 2, 4, 8]
PLAB = ["$-\\infty$", "-2", "-1", "0", "0.5", "1", "2", "4", "8"]


def main():
    def extra(p):
        p.add_argument("--gains", default="G1,G2_0.5,ceil")
    a = args(__doc__, extra)
    setup(a.width)
    df = read(a, "power_mean_curve.csv")
    df = df[(df.family == 1) & (df.rank_stratum == "all_attackers") & (df.cost == "linear") & (df.normalisation == "normalised") & (df.field == "all")]
    gains = a.gains.split(",")
    fig, axs = plt.subplots(1, 3, figsize=(a.width, 2.2), constrained_layout=True)
    for ax, (lb, gr, pop, title) in zip(axs, BOARDS):
        d = df[(df.leaderboard == lb) & (df.granularity == gr) & (df.population == pop)]
        for g in gains:
            c, m = GAIN_STYLE[g]
            x = d[d.gain_model == g].copy()
            x["i"] = [PS.index(p) for p in x.p.astype(float)]
            x = x.sort_values("i")
            if len(x) == 0:
                continue
            ax.fill_between(x.i, x.ci_lo, x.ci_hi, color=c, alpha=0.15, lw=0)
            ax.plot(x.i, x.median_k_min, color=c, marker=m, ms=3, lw=1, label=GAIN_LABEL[g])
        ax.set_xticks(range(len(PS)), PLAB); ax.tick_params(axis="x", labelsize=6); ax.set_xlabel("power-mean exponent $p$"); ax.set_title(title, fontsize=6.5)
    axs[0].set_ylabel(r"median $k_{\min}$ (tasks)")
    fig.legend(*axs[0].get_legend_handles_labels(), frameon=False, loc="outside lower center", ncol=len(gains))
    caption(a, "fig_c3_powermean", "median over all attackers (mean-rank >= 2); band = 95% bootstrap CI over targets; linear cost, normalised scores. "
            "A target infeasible at a given p is excluded from that point's median (see frac_feasible in power_mean_curve.csv).")
    save(fig, a, "fig_c3_powermean")


if __name__ == "__main__":
    main()
