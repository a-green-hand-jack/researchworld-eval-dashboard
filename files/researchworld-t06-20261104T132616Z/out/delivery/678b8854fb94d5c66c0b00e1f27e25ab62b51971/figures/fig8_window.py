"""F8 (claim E3, window choice): how the Arena and pooled-NBA budgets depend on the size of the claim window.

Reads s5_window_sweep.csv (one row per data set x rule x window size w: `c1` = verified C1 budget, `median_c2` = median verified budget over the
w-1 adjacent-pair claims of the window). Rule "score": the w top participants by BT score, every participant of the fit as challenger for C1
(the rule used in the paper, w = 20); rule "count": the w participants with the most comparisons. Left: C1 budget; right: median C2 budget.
The window we use is marked by the vertical line. The largest score window is every participant (64 models, 53 teams).
Writes fig8_window.pdf.
"""
import os

import matplotlib.pyplot as plt
import numpy as np

import common as C

A = C.args(__doc__)
C.set_style()
w = C.read(A.results, "s5_window_sweep.csv", secondary=True)
fig, axes = plt.subplots(1, 2, figsize=(C.TEXTWIDTH, 2.2), sharex=True)
for ax, col, yl in zip(axes, ["c1", "median_c2"], ["C1 budget $k$", "median C2 budget $k$"]):
    for ds in ["arena55k", "nba_all"]:
        des = C.design_of(ds)
        for rule, ls, fill in [("score", "-", "full"), ("count", "--", "none")]:
            d = w[(w.dataset == ds) & (w.rule == rule)].sort_values("size")
            ax.plot(d["size"], d[col], ls, marker=C.DESIGN_MARKER[des], color=C.DESIGN_COLOR[des], ms=4, lw=0.9, fillstyle=fill, mec=C.DESIGN_COLOR[des],
                    label=f"{C.SHORT_LABEL[ds]}, top by {rule}")
    ax.axvline(20, color=C.MUTED, lw=0.8, zorder=0)
    ax.set_yscale("log"); ax.set_xscale("log"); ax.set_xticks([10, 20, 30, 40, 53, 64]); ax.set_xticklabels(["10", "20", "30", "40", "53", "64"])
    ax.xaxis.set_minor_formatter(plt.NullFormatter())
    ax.set_xlabel("window size $w$ (participants)"); ax.set_ylabel(yl)
axes[1].set_ylim(top=1000)
axes[1].legend(loc="upper right", frameon=False, fontsize=5.5, labelspacing=0.2, handletextpad=0.3, borderaxespad=0.1)
C.panel_letter(axes[0], "a"); C.panel_letter(axes[1], "b")
fig.tight_layout(w_pad=1.0)
fig.savefig(os.path.join(A.out, "fig8_window.pdf"))
C.record_inputs(A.out, "fig8_window.pdf", [os.path.join(A.results, "s5_window_sweep.csv")])
