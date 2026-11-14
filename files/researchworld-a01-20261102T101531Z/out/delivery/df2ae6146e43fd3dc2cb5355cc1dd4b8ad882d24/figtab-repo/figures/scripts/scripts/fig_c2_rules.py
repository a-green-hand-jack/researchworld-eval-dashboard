"""Fig. C2: does a rule need more tasks than the mean?  Paired median difference in k_min (other rule minus mean) per target, per gain model.

Encoding: dot-and-interval plot (95% percentile bootstrap over targets, from paired_stats.csv), one panel per board, one row per rule,
one colour/marker per gain model; zero line = same cost as the mean. Right of zero = the rule needs MORE tasks than the mean (C2 holds),
left = FEWER (C2 reversed). Hollow marker: fewer than 20 paired targets. Pairs = targets with mean-rank >= 2 feasible under both rules.
Each panel has its own x scale (tasks differ: n = 57, 6, 39).
"""
import numpy as np
import matplotlib.pyplot as plt
from common import *

RULES = ["median", "trimmed_mean:0.2", "min", "geomean:0", "borda", "copeland", "condorcet_winner", "plurality"]


def main():
    def extra(p):
        p.add_argument("--gains", default="G1,G1_add10,G2_0.5,ceil")
    a = args(__doc__, extra)
    setup(a.width)
    df = read(a, "paired_stats.csv")
    df = df[(df.metric == "k_min") & (df.estimate_type == "median_diff(other-mean)") & (df.rank_stratum == "all_attackers")
            & (df.cost == "linear") & (df.normalisation == "normalised") & (df.field == "all")]
    gains = a.gains.split(",")
    fig, axs = plt.subplots(1, 3, figsize=(a.width, 2.9), sharey=True, constrained_layout=True)
    for ax, (lb, gr, pop, title) in zip(axs, BOARDS):
        d = df[(df.leaderboard == lb) & (df.granularity == gr) & (df.population == pop)]
        for gi, g in enumerate(gains):
            c, m = GAIN_STYLE[g]
            for ri, r in enumerate(RULES):
                x = d[(d.gain_model == g) & (d.contrast == f"mean vs {r}")]
                if len(x) == 0:
                    continue
                x = x.iloc[0]
                y = ri + (gi - (len(gains) - 1) / 2) * 0.16
                ax.plot([x.ci_lo, x.ci_hi], [y, y], color=c, lw=1.0, solid_capstyle="butt")
                ax.plot(x.estimate, y, marker=m, ms=3.5, color=c, mfc=c if x.n_pairs >= 20 else "white", mew=0.8, ls="none")
        ax.axvline(0, color="k", lw=0.7)
        ax.set_title(title, fontsize=6.5)
        ax.set_xlabel(r"$\Delta k_{\min}$ vs mean (tasks)")
        ax.set_yticks(range(len(RULES)), [RULE_LABEL[r] for r in RULES]); ax.set_ylim(len(RULES) - 0.5, -0.5)
        ax.grid(axis="y", visible=False)
    for g in gains:
        c, m = GAIN_STYLE[g]
        axs[0].plot([], [], marker=m, color=c, lw=1, ms=3.5, label=GAIN_LABEL[g])
    fig.legend(*axs[0].get_legend_handles_labels(), frameon=False, loc="outside lower center", ncol=len(gains))
    caption(a, "fig_c2_rules", "median paired difference [95% bootstrap CI over target models, 2000 resamples], linear cost, normalised scores, "
            "targets with mean-rank >= 2 feasible under both rules; hollow = <20 pairs. OLB headline targets are a rank-stratified sample.")
    save(fig, a, "fig_c2_rules")


if __name__ == "__main__":
    main()
