"""Fig. 4 (claims C2, C3): paired log price ratios between rules (forest plot), one panel per board.

usage: make_fig4.py --results DIR --out DIR [--B VALUE] [--pairs mean:median,mean:min,...]

Row = rule pair (A vs B); x = mean log(price_A/price_B) over targets with the CI from
`paired` (cluster bootstrap, computed by analysis); < 0 means A is cheaper.
Filled marker = price against each rule's own leader; open = against the common incumbent set.
Bottom row: mean Kendall tau between the rule orderings of two targets (`rule_order`), against the per-task cap B,
with its cluster-bootstrap interval; it rises with B.
The share of targets with A cheaper is in Table 3 / the appendix, not printed here.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np

import common
import style

BOARDS = [("helm_mmlu", "HELM MMLU, $m=57$"), ("ollb_bench", "OLLB, $m=6$"), ("ollb_sub", "OLLB, $m=39$")]
PAIRS = "mean:median,mean:min,mean:borda,mean:plurality,mean:copeland,median:plurality,median:borda,median:copeland".split(",")
INC = {"own": (-0.14, "#0072B2", "o", True), "common": (0.14, "#D55E00", "s", False)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--B", type=float, default=20.0); ap.add_argument("--pairs", default=",".join(PAIRS))
    a = ap.parse_args()
    style.apply()
    df, p = common.load(a.results, "paired")
    df = df[np.isclose(df.B, a.B)]
    pairs = [tuple(s.split(":")) for s in a.pairs.split(",")]
    pairs = [q for q in pairs if ((df.rule_a == q[0]) & (df.rule_b == q[1])).any()]
    ro, p2 = common.load(a.results, "rule_order")
    fig, axes = plt.subplots(3, 3, figsize=style.size("full", 1.0), gridspec_kw=dict(height_ratios=[1, 1, 0.62]))
    for row, (metric, mlabel) in zip(axes[:2], [("depth", "total boost (depth)"), ("breadth", "tasks touched (breadth)")]):
        for ax, (b, title) in zip(row, BOARDS):
            for i, (ra, rb) in enumerate(pairs):
                for inc, (dy, col, mk, filled) in INC.items():
                    g = df[(df.board == b) & (df.metric == metric) & (df.rule_a == ra) & (df.rule_b == rb) & (df.incumbent == inc)]
                    for _, r in g.iterrows():
                        ax.errorbar(np.exp(r.mean_log_ratio), i + dy,
                                    xerr=[[np.exp(r.mean_log_ratio) - np.exp(r.ci_lo)], [np.exp(r.ci_hi) - np.exp(r.mean_log_ratio)]],
                                    color=col, marker=mk, ms=3.5, mfc=col if filled else "white", lw=0.9, capsize=1.2)
            ax.axvline(1, color="k", lw=0.8)
            ax.set_xscale("log")
            ax.minorticks_off()
            ticks = [0.1, 1, 10, 100] if metric == "depth" else [0.25, 0.5, 1, 2]
            ax.set_xticks(ticks); ax.set_xticklabels([f"{t:g}" for t in ticks])
            ax.set_xlim(0.05, 600) if metric == "depth" else ax.set_xlim(0.15, 4)
            ax.grid(axis="y", alpha=0)
            if metric == "depth":
                ax.set_title(title, loc="left", fontsize=style.venue()["min_font_pt"] + 0.5)
            ax.set_yticks(range(len(pairs)))
            ax.set_ylim(len(pairs) - 0.5, -0.5)
            if ax is not row[0]:
                ax.set_yticklabels([])
        row[0].set_ylabel(mlabel)
        row[1].set_xlabel("geometric-mean price ratio A / B  ($<1$: A cheaper)")
    for r in axes[:2]:
        r[0].set_yticklabels([f"{style.RULE_LABEL.get(x, x)} vs {style.RULE_LABEL.get(y, y)}" for x, y in pairs])
    bgrid = sorted(ro.B.unique())
    for ax, (b, _) in zip(axes[2], BOARDS):
        for inc, (dy, col, mk, filled) in INC.items():
            g = ro[(ro.board == b) & (ro.incumbent == inc)].sort_values("B")
            x = [bgrid.index(v) + dy / 2 for v in g.B]
            ax.errorbar(x, g.kendall_tau_mean, yerr=[g.kendall_tau_mean - g.ci_lo, g.ci_hi - g.kendall_tau_mean], color=col, marker=mk,
                        mfc=col if filled else "white", ms=3.5, lw=0.9, capsize=1.2)
        ax.set_xticks(range(len(bgrid))); ax.set_xticklabels([f"{v:g}" if v < 100 else "$\\infty$" for v in bgrid])
        ax.set_ylim(-0.1, 1.05)
        ax.set_xlim(-0.4, len(bgrid) - 0.6)
        ax.set_xlabel("cap $B$ (points)")
    axes[2, 0].set_ylabel("Kendall $\\tau$\nbetween targets")
    for ax in axes[2, 1:]:
        ax.set_yticklabels([])
    handles = [plt.Line2D([], [], color=c, marker=m, mfc=c if f else "white", ls="", label=n)
               for (c, m, f), n in zip([v[1:] for v in INC.values()], ["own leader", "common incumbent set"])]
    fig.legend(handles=handles, loc="lower center", ncol=2, bbox_to_anchor=(0.55, -0.01))
    fig.tight_layout(w_pad=0.6, rect=(0, 0.035, 1, 1))
    common.save_fig(fig, a.out, "fig4_pairs", [p, p2], note=f"B={a.B} points; rows depth and breadth; x axis exp(mean log ratio) with exp(CI); bottom row: mean Kendall tau of rule orders between targets vs B, B=100 plotted as infinity")


if __name__ == "__main__":
    main()
