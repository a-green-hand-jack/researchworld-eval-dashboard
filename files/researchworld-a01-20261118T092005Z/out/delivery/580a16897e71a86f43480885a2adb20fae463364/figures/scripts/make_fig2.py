"""Fig. 2 (claims C1, C2, C5): the price map of the top-30 targets, one row per board.

usage: make_fig2.py --results DIR --out DIR [--B 10] [--incumbent own]

Reads `price` only, restricted to the 30 targets of best official rank on each board and to (target, rule) pairs with a positive gap to the incumbent (own-leader prices unless --incumbent says otherwise).
Column 1, at the per-task cap B: each small dot is one target's cheapest *breadth* k*/m (x) and the
total boost needed at that breadth (y, points); the large marker is the median over feasible targets.
Column 2: the share of targets for which first place is feasible at all, as the cap B grows
(infinity = task ceilings only).
Column 3, at ceilings only: the targeting multiplier (cost of an untargeted equal boost on all tasks
divided by the cost of the optimal targeted plan), one dot per target, bar = median.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np

import common
import style

BOARDS = [("helm_mmlu", "HELM MMLU, $m{=}57$"), ("ollb_bench", "OLLB benchmarks, $m{=}6$"), ("ollb_sub", "OLLB sub-tasks, $m{=}39$")]
YLIM1 = (0.1, 1500)   # points; targets within a tie margin of first place need less and fall below it
YLIM3 = (0.7, 150)
BGRID = [2.0, 5.0, 10.0, 20.0, 100.0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--B", type=float, default=10.0); ap.add_argument("--incumbent", default="own")
    a = ap.parse_args()
    style.apply()
    pr, p = common.load(a.results, "price")
    pr = pr[pr.incumbent == a.incumbent]
    rules = [r for r in style.RULES if r in set(pr.rule)]
    off = {}  # points outside the drawn range, counted per board and column
    fig, axes = plt.subplots(3, 3, figsize=style.size("full", 1.0))
    for row, (board, title) in zip(axes, BOARDS):
        d = pr[pr.board == board]
        top = d.groupby("target").init_rank.min().nsmallest(30).index
        d = d[d.target.isin(top) & (d.gap > 0)]  # a target already first under a rule has nothing to buy
        m = int(d.m.iloc[0])
        ax = row[0]
        at = d[np.isclose(d.B, a.B) & d.feasible.astype(bool)]
        for i, r in enumerate(rules):
            g = at[at.rule == r]
            st = style.RULE_STYLE[r]
            ax.scatter(g.k_star / m, g.depth_at_kstar, s=5, color=st["color"], alpha=0.35, lw=0, zorder=2)
            if len(g):
                ax.plot(g.k_star.median() / m, g.depth_at_kstar.median(), marker=st["marker"], ms=7, mfc=st["color"],
                        mec="white", mew=0.7, ls="", zorder=4)
        ax.set_yscale("log")
        ax.set_ylim(YLIM1)
        off[board + ":col1"] = int((at.depth_at_kstar < YLIM1[0]).sum())
        ax.set_xlim(-0.03, 1.03)
        ax.set_title(title, loc="left")
        ax.set_ylabel("total boost (points)")
        ax = row[1]
        for r in rules:
            g = d[d.rule == r]
            share = [g[np.isclose(g.B, b)].feasible.astype(bool).mean() for b in BGRID]
            ax.plot(range(len(BGRID)), share, ms=3.5, lw=1.0, **style.RULE_STYLE[r])
        ax.set_xticks(range(len(BGRID))); ax.set_xticklabels([f"{b:g}" for b in BGRID[:-1]] + ["$\\infty$"])
        ax.set_ylim(-0.04, 1.04)
        ax.set_ylabel("share of targets\nwith a feasible plan")
        ax = row[2]
        cap = d[np.isclose(d.B, BGRID[-1])]
        for i, r in enumerate(rules):
            g = cap[(cap.rule == r) & np.isfinite(cap.targeting_mult)].targeting_mult
            st = style.RULE_STYLE[r]
            ax.scatter(np.full(len(g), i) + np.linspace(-0.22, 0.22, len(g)), g.sort_values(), s=5, color=st["color"], alpha=0.5, lw=0, zorder=2)
            ax.plot([i - 0.33, i + 0.33], [g.median()] * 2, color="k", lw=1.4, zorder=4)
        ax.set_yscale("log")
        ax.set_ylim(YLIM3)
        off[board + ":col3"] = int((cap[np.isfinite(cap.targeting_mult)].targeting_mult < YLIM3[0]).sum())
        ax.axhline(1, color="0.5", lw=0.6)
        ax.set_xticks(range(len(rules))); ax.set_xticklabels([])
        ax.set_ylabel("targeting multiplier")
    axes[-1, 0].set_xlabel("breadth $k^*/m$ at $B{=}%g$" % a.B)
    axes[-1, 1].set_xlabel("per-task cap $B$ (points)")
    ticklabels = {"mean": "mean", "median": "median", "min": "min", "borda": "Borda", "plurality": "plural.", "copeland": "Copel."}
    axes[-1, 2].set_xticks(range(len(rules))); axes[-1, 2].set_xticklabels([ticklabels[r] for r in rules], rotation=60, ha="right")
    for ax in axes[:-1, 0]:
        ax.set_xticklabels([])
    for ax in axes[:-1, 1]:
        ax.set_xticklabels([])
    handles = [plt.Line2D([], [], label=style.RULE_LABEL[r], ms=5, lw=1.0, **style.RULE_STYLE[r]) for r in rules]
    fig.legend(handles=handles, loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.01), columnspacing=0.9, handlelength=1.8)
    fig.tight_layout(h_pad=0.6, w_pad=0.5, rect=(0, 0.045, 1, 1))
    common.save_fig(fig, a.out, "fig2_price_map", [p],
                    note=f"incumbent={a.incumbent}; column 1 at B={a.B} points; column 3 at ceilings (B=100 row, no per-task cap); points below the lower axis limit, by panel: " + str(off) + "; targets: the 30 best-ranked by the official rule (init_rank) on each board")


if __name__ == "__main__":
    main()
