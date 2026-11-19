"""Fig. C5: how the minimal investment scales with the number of subdatasets n (random task subsets, 20 per n, from subsample_curves_summary.csv).

Rows: k_min/n (share of tasks) and k_min (tasks); columns: HELM (n=5..57) and OLB sub-tasks (n=3..39). Targets are boards of the subset, at mean-rank
2,5,10,20; we plot the aggregate row `2-20 (median of 4)`. Band (top row): 2.5-97.5% range across subsets (not a CI of the mean).
"""
import numpy as np
import matplotlib.pyplot as plt
from common import *


def main():
    def extra(p):
        p.add_argument("--gain-model", default="G1"); p.add_argument("--rules", default="mean,median,min,borda,copeland")
    a = args(__doc__, extra)
    setup(a.width)
    df = read(a, "subsample_curves_summary.csv")
    df = df[(df.gain_model == a.gain_model) & (df.target_rank == "2-20 (median of 4)")]
    rules = a.rules.split(",")
    cols = [("helm_mmlu", "headline", "HELM MMLU"), ("openllm_v2", "subtask", "Open LLM Lb. v2, sub-tasks")]
    fig, axs = plt.subplots(2, 2, figsize=(a.width, 3.6), sharex="col", constrained_layout=True)
    for j, (lb, gr, title) in enumerate(cols):
        d = df[(df.leaderboard == lb) & (df.granularity == gr)]
        for r in rules:
            x = d[d.rule == r].sort_values("n_tasks")
            if len(x) == 0:
                continue
            c, m = RULE_STYLE[r]
            axs[0, j].fill_between(x.n_tasks, x.k_frac_lo, x.k_frac_hi, color=c, alpha=0.12, lw=0)
            axs[0, j].plot(x.n_tasks, x.k_frac_mean, color=c, marker=m, ms=3, lw=1, label=RULE_LABEL[r])
            axs[1, j].plot(x.n_tasks, x.k_mean, color=c, marker=m, ms=3, lw=1)
        axs[0, j].set_title(title, fontsize=7); axs[1, j].set_xlabel(r"number of subdatasets $n$")
    axs[0, 0].set_ylabel(r"$k_{\min}/n$"); axs[1, 0].set_ylabel(r"$k_{\min}$ (tasks)")
    for ax in axs[0]:
        ax.set_ylim(0, 1.02)
    fig.legend(*axs[0, 0].get_legend_handles_labels(), frameon=False, loc="outside lower center", ncol=len(rules))
    caption(a, "fig_c5_subsample", f"gain model {a.gain_model}; target = board of the subset at mean-rank 2,5,10,20 (aggregate row); mean over 20 task subsets per n, "
            "band = 2.5-97.5% range over subsets (k/n only).")
    save(fig, a, "fig_c5_subsample")


if __name__ == "__main__":
    main()
