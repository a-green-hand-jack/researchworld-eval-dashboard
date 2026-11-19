"""F3 (claim E3): verified adversarial removal budget of each adjacent-pair claim (C2) against the pair's rank.

Reads adv_budgets.csv. Left: budget as a fraction of all N comparisons; right: budget as a fraction of the comparisons that involve
either participant of the pair (budget_frac_pair). The noise-equivalent "leverage" is not plotted: it is ~ z*sqrt((N-k)/k) and carries
no information beyond z and k/N (see adv_budgets.csv, column leverage_identity).
Single NBA seasons (69 seasons, pooled by rank) are shown as median and interquartile range.
Writes fig3_budgets.pdf.
"""
import os

import matplotlib.pyplot as plt
import numpy as np

import common as C

A = C.args(__doc__)
C.set_style()
b = C.adv_c2(A.results)
b = b[np.isfinite(b.budget_frac_pair) & (b.budget > 0)]
seasons = b[~b.dataset.isin(C.BASE_UNITS)]

fig, axes = plt.subplots(1, 2, figsize=(C.TEXTWIDTH, 2.2), sharex=True)
for ax, col, ylab in zip(axes, ["budget_frac_N", "budget_frac_pair"],
                         ["adversarial removal budget / $N$", "budget / comparisons of the pair"]):
    g = seasons.groupby("rank")[col]
    q = g.quantile([0.25, 0.5, 0.75]).unstack()
    q = q[g.size() >= 10]
    ax.fill_between(q.index, q[0.25], q[0.75], color=C.DESIGN_COLOR["sports"], alpha=0.2, lw=0)
    ax.plot(q.index, q[0.5], "-", color=C.DESIGN_COLOR["sports"], lw=1.0, label="NBA seasons (median, IQR)")
    for unit in C.BASE_UNITS:
        d = b[b.dataset == unit].sort_values("rank"); des = C.design_of(unit)
        ax.plot(d["rank"], d[col], "-" + C.DESIGN_MARKER[des], color=C.DESIGN_COLOR[des], ms=3.2, lw=0.8, mec="white", mew=0.3,
                label=C.SHORT_LABEL[unit])
    ax.set_yscale("log"); ax.set_xlabel("rank $r$ of the pair ($r$ vs $r+1$)"); ax.set_ylabel(ylab)
    ax.set_xlim(0.5, 20)
    ax.set_xticks([1, 5, 10, 15, 19])
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=5, frameon=False, fontsize=6, columnspacing=0.8, handlelength=1.6)
C.panel_letter(axes[0], "a"); C.panel_letter(axes[1], "b")
fig.subplots_adjust(left=0.1, right=0.985, bottom=0.2, top=0.84, wspace=0.3)
fig.savefig(os.path.join(A.out, "fig3_budgets.pdf"))
C.record_inputs(A.out, "fig3_budgets.pdf", [os.path.join(A.results, "adv_budgets.csv")])
