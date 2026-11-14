"""Fig. noise (appendix): median k needed to rank first with probability >= q under item-level evaluation noise (Gaussian approx. of the binomial error).

Only 40 HELM and 16 OLB headline targets were evaluated by the analysis. q = 0 is the noise-free k_min; targets that do not reach the
probability within the search range are excluded from the median and the number that do is printed at each point."""
import numpy as np
import matplotlib.pyplot as plt
from common import *


def main():
    a = args(__doc__)
    setup(a.width)
    df = read(a, "per_target_noise.csv")
    df = df[(df.normalisation != "points") | (df.leaderboard == "helm_mmlu")]
    partial = []
    fig, axs = plt.subplots(1, 2, figsize=(a.width, 2.4), constrained_layout=True)
    for ax, (lb, title) in zip(axs, [("helm_mmlu", "HELM MMLU"), ("openllm_v2", "Open LLM Lb. v2, headline")]):
        d = df[df.leaderboard == lb]
        ntar = d.target_id.nunique()
        for r in ["mean", "median", "min", "trimmed_mean", "borda", "plurality"]:
            x = d[d.rule == r]
            qs = sorted(x.noise_margin.unique())
            med = [x[x.noise_margin == q].k_min.median() for q in qs]
            cnt = [int(x[x.noise_margin == q].k_min.notna().sum()) for q in qs]
            c, m = RULE_STYLE[r]
            ax.plot(range(len(qs)), med, color=c, marker=m, ms=3.5, lw=1, label=RULE_LABEL[r])
            for i, (mm, n) in enumerate(zip(med, cnt)):
                if n < len(x[x.noise_margin == qs[i]]):
                    partial.append(f"{lb} {r} q={qs[i]}: {n}/{len(x[x.noise_margin == qs[i]])}")
                    ax.annotate(f"{n}", (i, mm), fontsize=5, xytext=(3, 3), textcoords="offset points", color=c)
        ax.set_xticks(range(3), ["none", r"$\geq$0.5", r"$\geq$0.9"]); ax.set_xlabel("required P(rank first)")
        ax.set_title(f"{title} ({ntar} targets)", fontsize=7)
    axs[0].set_ylabel(r"median $k$ (tasks)")
    fig.legend(*axs[0].get_legend_handles_labels(), frameon=False, loc="outside lower center", ncol=6)
    caption(a, "fig_noise", "gain G1, linear cost. Targets not reaching the probability are excluded from the median; where fewer than all reached: " + "; ".join(partial) + ".")
    save(fig, a, "fig_noise")


if __name__ == "__main__":
    main()
