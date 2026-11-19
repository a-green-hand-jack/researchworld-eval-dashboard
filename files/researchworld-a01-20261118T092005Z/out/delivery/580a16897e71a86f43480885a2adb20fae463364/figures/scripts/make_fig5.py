"""Fig. 5 (claims C6, C8): what predicts price, and how large real boosts are.

usage: make_fig5.py --results DIR --out DIR [--B 100]

(a) `predictors`: held-out R^2 of log price within a rule, model fitted on one board and tested on another.
    One dot per (fit board, test board) pair (6 pairs); the bar is the median over pairs. Plotted is
    `r2_recentred` (the slope transfers, the intercept is re-estimated on the test board); the
    uncentred `r2_heldout` is far below 0 for most cells and is quoted in Table 3 (R3).
    B = 100 means ceilings only, the budget of the R3 verdict.
(b) `calibration_summary`: among (fine-tune, task) pairs of the Open LLM Leaderboard, the share whose gain over
    the parent model is at least t points, by parent-size bucket, with the cluster-bootstrap CI of the file;
    the vertical lines are the per-task budgets B of the price grid.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np

import common
import style

MODELS = [("rank", "official rank", "#999999", "s"), ("gap", "rule-specific gap", "#0072B2", "o"),
          ("gap+disp+corr", "gap + dispersion + correlation", "#D55E00", "^")]
BUCKETS = ["<3B", "3-9B", "9-20B", "20-40B", ">40B"]
BSTYLE = {"<3B": ("#000000", "o", "-"), "3-9B": ("#0072B2", "s", "--"), "9-20B": ("#009E73", "^", "-."),
          "20-40B": ("#D55E00", "v", ":"), ">40B": ("#CC79A7", "D", "-")}
THRESH = [1, 2, 5, 10, 20, 30]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--B", type=float, default=100.0)
    a = ap.parse_args()
    style.apply()
    pr, p1 = common.load(a.results, "predictors")
    cs, p2 = common.load(a.results, "calibration_summary")
    pr = pr[np.isclose(pr.B, a.B)]
    rules = [r for r in style.RULES if r in set(pr.rule)]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(5.3, 2.65), gridspec_kw=dict(width_ratios=[1.15, 1]))
    for i, r in enumerate(rules):
        for k, (mod, _, col, mk) in enumerate(MODELS):
            g = pr[(pr.rule == r) & (pr.model == mod)].r2_recentred
            y = i + (k - 1) * 0.24
            ax.scatter(g, np.full(len(g), y), s=7, color=col, marker=mk, alpha=0.45, lw=0, zorder=2)
            ax.plot([g.median()] * 2, [y - 0.1, y + 0.1], color=col, lw=2.0, zorder=4)
    clipped = int((pr.r2_recentred < -1.4).sum())
    ax.axvline(0, color="0.4", lw=0.7)
    ax.set_yticks(range(len(rules)))
    ax.set_yticklabels([{"borda": "Borda"}.get(r, style.RULE_LABEL[r].replace("mean rank (Borda)", "Borda")) for r in rules])
    ax.set_ylim(len(rules) - 0.5, -0.6)
    ax.set_xlim(-1.4, 1.05)
    ax.set_xlabel("held-out $R^2$ of log price (slope transfer)")
    ax.set_title("(a) predicting price on another board", loc="left")
    ax.grid(axis="y", alpha=0)
    for bk in BUCKETS:
        d = cs[(cs.size_bucket == bk)].set_index("statistic")
        idx = [f"share_task_gain_ge_{t}" for t in THRESH]
        val, lo, hi = d.loc[idx, "value"].values, d.loc[idx, "ci_lo"].values, d.loc[idx, "ci_hi"].values
        col, mk, ls = BSTYLE[bk]
        n = d.iloc[0]
        bx.plot(THRESH, val, color=col, marker=mk, ls=ls, ms=3.5, lw=1.0, label=f"{bk} ({int(n.n_children)} fine-tunes)")
        bx.fill_between(THRESH, lo, hi, color=col, alpha=0.12, lw=0)
    for b in [2, 5, 10, 20]:
        bx.axvline(b, color="0.6", lw=0.6, ls=(0, (1, 2)))
    bx.set_xscale("log"); bx.set_yscale("log")
    bx.set_xticks([1, 2, 5, 10, 20, 30]); bx.set_xticklabels(["1", "2", "5", "10", "20", "30"])
    bx.minorticks_off()
    bx.set_ylim(1e-3, 1)
    bx.set_xlabel("gain over parent, $t$ points (task level)")
    bx.set_ylabel("share of (fine-tune, task) pairs\nwith gain $\\geq t$")
    bx.set_title("(b) observed boosts by parent size", loc="left")
    h1 = [plt.Line2D([], [], color=c, marker=m, ls="", ms=4, label=n) for _, n, c, m in MODELS]
    fig.legend(handles=h1, loc="lower left", bbox_to_anchor=(0.0, -0.01), ncol=1, handletextpad=0.3, labelspacing=0.25, title="model in (a)", alignment="left")
    bx.legend(loc="lower left", ncol=1, handlelength=2.0, labelspacing=0.25, fontsize=style.venue()["min_font_pt"], title="parent size in (b)", alignment="left")
    fig.tight_layout(w_pad=1.2, rect=(0, 0.2, 1, 1))
    common.save_fig(fig, a.out, "fig5_predictors_calibration", [p1, p2],
                    note=f"(a) {clipped} of {len(pr)} cells have r2_recentred < -1.4 and fall off the left edge; B={a.B} points (100 = ceilings only), r2_recentred, one dot per (fit, test) board pair, bar = median; (b) grid lines at B in 2,5,10,20")


if __name__ == "__main__":
    main()
