"""Fig. baselines: share of targets that reach rank 1 with a budget of k tasks, for the optimal task choice, the greedy-by-headroom
choice and a random choice of k tasks (100 draws per target); rules mean and median. 95% percentile bootstrap bands over targets."""
import numpy as np
import matplotlib.pyplot as plt
from common import *

STRAT = {"optimal": ("#0072B2", "-", "optimal choice"), "greedy_headroom": ("#E69F00", "--", "greedy by headroom"), "random": ("#999999", ":", "random tasks")}


def main():
    a = args(__doc__)
    setup(a.width)
    df = read(a, "baselines.csv")
    df = df[(df.budget_type == "k") & (df.rank_stratum == "all_attackers") & (df.gain_model == "G1")]
    cols = [("helm_mmlu", "all", "HELM MMLU"), ("openllm_v2", "no_flagged", "Open LLM Lb. v2, headline")]
    fig, axs = plt.subplots(2, 2, figsize=(a.width, 3.4), sharey=True, constrained_layout=True)
    for j, (lb, pop, title) in enumerate(cols):
        for i, rule in enumerate(["mean", "median"]):
            ax = axs[i, j]
            for s, (c, ls, lab) in STRAT.items():
                x = df[(df.leaderboard == lb) & (df.population == pop) & (df.rule == rule) & (df.strategy == s)].sort_values("budget")
                if len(x) == 0:
                    continue
                ax.fill_between(x.budget, x.ci_lo, x.ci_hi, color=c, alpha=0.15, lw=0)
                ax.plot(x.budget, x.frac_first, color=c, ls=ls, lw=1.2, marker="o", ms=2.5, label=lab)
            ax.set_title(f"{title}, {RULE_LABEL[rule]} rule", fontsize=6.5); ax.set_ylim(-0.02, 1.02)
            if i == 1:
                ax.set_xlabel(r"budget: tasks targeted, $k$")
    for i in range(2):
        axs[i, 0].set_ylabel("share ranked first")
    fig.legend(*axs[0, 0].get_legend_handles_labels(), frameon=False, loc="outside lower center", ncol=3)
    caption(a, "fig_baselines", "gain model G1, linear cost, all attackers (mean-rank >= 2); band = 95% bootstrap over targets (random: also over 100 draws). Under the mean rule greedy-by-headroom coincides with the optimal choice (curves overlap).")
    save(fig, a, "fig_baselines")


if __name__ == "__main__":
    main()
