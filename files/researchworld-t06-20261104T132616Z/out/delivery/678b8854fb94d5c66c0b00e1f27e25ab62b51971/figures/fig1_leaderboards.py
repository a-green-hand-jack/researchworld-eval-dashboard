"""F1 (claim E1): BT scores with 95% bootstrap CI and bootstrap rank interval, per dataset.

Reads base_<unit>.csv (stage 0). Writes fig1_leaderboards.pdf (Arena + MT-Bench) and fig1b_nba.pdf (appendix).
"""
import os

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import common as C

A = C.args(__doc__)
C.set_style()
DESIGN = {"arena55k": "crowd", "mt_human": "expert", "mt_gpt4": "llm_judge", "nba_all": "sports"}
files = {u: os.path.join(A.results, f"base_{u}.csv") for u in DESIGN}


def panel(ax, unit, show_x=True):
    d = C.read(A.results, f"base_{unit}.csv").sort_values("rank").reset_index(drop=True)
    des = DESIGN[unit]
    y = range(len(d))
    ax.hlines(y, d.ci_lo_elo, d.ci_hi_elo, color=C.DESIGN_COLOR[des], lw=1.4)
    ax.plot(d.score_elo, y, C.DESIGN_MARKER[des], color=C.DESIGN_COLOR[des], ms=3.5, mec="white", mew=0.4)
    ax.set_yticks(list(y))
    ax.set_yticklabels(d.participant)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_title(C.DATASET_LABEL[unit], loc="left", color=C.INK)
    # bootstrap rank interval at the right edge, in axes coordinates for x and data coordinates for y
    for yi, (lo, hi) in enumerate(zip(d.rank_lo, d.rank_hi)):
        ax.annotate(f"{int(lo)}" if lo == hi else f"{int(lo)}–{int(hi)}", (1.0, yi), xycoords=("axes fraction", "data"),
                    xytext=(3, 0), textcoords="offset points", va="center", ha="left", fontsize=6.5, color=C.MUTED)
    if show_x:
        ax.set_xlabel("BT score (Elo), 95% CI")
    return d


fig = plt.figure(figsize=(C.TEXTWIDTH, 3.1))
gs = GridSpec(2, 2, figure=fig, width_ratios=[1.05, 1], height_ratios=[1, 1], wspace=1.0, hspace=0.75,
              left=0.25, right=0.93, top=0.94, bottom=0.14)
panel(fig.add_subplot(gs[:, 0]), "arena55k")
a2 = fig.add_subplot(gs[0, 1]); panel(a2, "mt_human", show_x=False)
a3 = fig.add_subplot(gs[1, 1]); panel(a3, "mt_gpt4")
lim = (min(a2.get_xlim()[0], a3.get_xlim()[0]), max(a2.get_xlim()[1], a3.get_xlim()[1]))
a2.set_xlim(lim); a3.set_xlim(lim)
fig.savefig(os.path.join(A.out, "fig1_leaderboards.pdf"))

fig = plt.figure(figsize=(C.TEXTWIDTH * 0.8, 3.6))
ax = fig.add_axes([0.28, 0.12, 0.62, 0.8])
panel(ax, "nba_all")
fig.savefig(os.path.join(A.out, "fig1b_nba.pdf"))
C.record_inputs(A.out, "fig1_leaderboards.pdf", [files[u] for u in DESIGN])
