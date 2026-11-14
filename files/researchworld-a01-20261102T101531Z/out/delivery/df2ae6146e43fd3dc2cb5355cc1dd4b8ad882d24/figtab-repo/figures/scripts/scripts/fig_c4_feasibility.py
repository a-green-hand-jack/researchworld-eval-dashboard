"""Fig. C4: share of targets that can reach rank 1 by targeting alone, by initial rank (rank under the mean, so the same targets in every row) and rule.

Heatmap: rows = rule, columns = rank bin (n targets in the label), colour and text = share feasible. Wilson 95% intervals are in
tables/feasibility_*.tex; cells with fewer than 10 targets are outlined dashed. Under G1 every target is feasible (no figure); use
--gain-model G2_0.5 or G1_add10.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from common import *

RULES = ["mean", "geomean", "median", "min", "trimmed_mean", "borda", "copeland", "condorcet_winner", "plurality"]
BINS = ["1-2", "3-10", "11-100", "rest"]


def main():
    def extra(p):
        p.add_argument("--gain-model", default="G2_0.5")
    a = args(__doc__, extra)
    setup(a.width)
    df = read(a, "feasibility.csv")
    df = df[(df.gain_model == a.gain_model) & (df.rank_basis == "mean") & (df.field == "all") & (df.normalisation == "normalised")
            & (df.rule.isin(RULES)) & (df.rule_param.isna() | (df.rule_param == 0.2) | (df.rule == "geomean"))]
    fig, axs = plt.subplots(1, 3, figsize=(a.width, 3.0), sharey=True, constrained_layout=True)
    for ax, (lb, gr, pop, title) in zip(axs, BOARDS):
        d = df[(df.leaderboard == lb) & (df.granularity == gr) & (df.population == pop)]
        bins = [b for b in BINS if b in set(d.rank_bin)]
        M = np.full((len(RULES), len(bins)), np.nan); N = {}
        for i, r in enumerate(RULES):
            for j, b in enumerate(bins):
                x = d[(d.rule == r) & (d.rank_bin == b)]
                if len(x):
                    M[i, j] = x.frac_feasible.iloc[0]; N[b] = int(x.n_targets.iloc[0])
                    if N[b] < 10:
                        ax.add_patch(Rectangle((j - .5, i - .5), 1, 1, fill=False, ec="k", ls="--", lw=0.6))
        im = ax.imshow(M, vmin=0, vmax=1, cmap="Blues", aspect="auto")
        for i in range(len(RULES)):
            for j in range(len(bins)):
                if not np.isnan(M[i, j]):
                    ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=6, color="white" if M[i, j] > 0.6 else "black")
        ax.set_xticks(range(len(bins)), [f"{b}\n$n$={N.get(b, 0)}" for b in bins]); ax.set_yticks(range(len(RULES)), [RULE_LABEL[r] for r in RULES])
        ax.set_title(title, fontsize=6.5); ax.tick_params(axis="x", labelsize=6); ax.set_xlabel("rank under the mean", fontsize=7); ax.grid(False)
    fig.colorbar(im, ax=axs.tolist(), location="bottom", shrink=0.35, aspect=25, pad=0.02, label="share feasible")
    caption(a, f"fig_c4_feasibility_{a.gain_model}", f"gain model {a.gain_model}, normalised scores, field=all; dashed = <10 targets. OLB headline targets: rank-stratified sample, not all models.")
    save(fig, a, f"fig_c4_feasibility_{a.gain_model}")


if __name__ == "__main__":
    main()
