"""Fig. 3 (claim C4, headline): does the breadth-fraction ratio median-type / mean-type grow with m?

usage: make_fig3.py --results DIR --out DIR [--variant inf1]

Reads `m_effect_fit` only (the statistics and CIs are analysis'; nothing is recomputed here).
Top row, one panel per per-task budget b in {1, 2, 4} sigma: on HELM random subject subsets of
m tasks (same 79 models), the ratio of the mean breadth fraction k*/m of median-type rules to that of
mean-type rules (mean, z-mean), per draw-paired cell; the slope against ln m with its cluster
bootstrap CI is printed for the median-type group, which is the R4 statistic.
Bottom row, same budgets: the Open LLM Leaderboard, the same models priced at m=6 (bundled plans)
and m=39 (free plans); change in the ratio, m=39 minus m=6, with its CI (cluster bootstrap over
target families). Above 0 = the ratio rises with granularity.
`variant` is analysis' treatment of cells infeasible at the budget (`inf1`: breadth fraction 1;
`feasible`: cell dropped); the verdicts use `inf1`.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np

import common
import style

BUDGETS = [1.0, 2.0, 4.0]
HELM_PAIRS = [("median / mean+zmean", "median"), ("plurality / mean+zmean", "plurality"),
              ("copeland / mean+zmean", "copeland")]
OLLB_PAIRS = [("median-type / meanh+zmean", None), ("median / meanh+zmean", "median"),
              ("plurality / meanh+zmean", "plurality"), ("copeland / meanh+zmean", "copeland")]
GROUP = "median-type / mean+zmean"


def by_m(s):
    return {int(a): float(b) for a, b in (x.split(":") for x in s.split(";"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--variant", default="inf1")
    a = ap.parse_args()
    style.apply()
    fit, p = common.load(a.results, "m_effect_fit")
    fit = fit[fit.variant == a.variant]
    fig, axes = plt.subplots(2, 3, figsize=style.size("full", 0.78), gridspec_kw=dict(height_ratios=[1.25, 1]))
    top, bot = axes
    for j, b in enumerate(BUDGETS):
        ax = top[j]
        h = fit[(fit.regime == "helm_subset") & (fit.statistic == "slope_ratio_vs_ln_m") & np.isclose(fit.B_sigma, b)]
        for pair, rule in HELM_PAIRS:
            r = h[h.rule_pair == pair].iloc[0]
            d = by_m(r.by_m)
            ax.plot(list(d), list(d.values()), lw=0.9, ms=3, **style.RULE_STYLE[rule])
        r = h[h.rule_pair == GROUP].iloc[0]
        d = by_m(r.by_m)
        ax.plot(list(d), list(d.values()), color="k", lw=1.8, marker="o", ms=3.5, mfc="white", mew=1.0, zorder=5)
        ax.axhline(1, color="0.4", lw=0.7)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xticks([5, 9, 15, 25, 41, 57]); ax.set_xticklabels(["5", "9", "15", "25", "41", "57"])
        ax.minorticks_off()
        ax.set_ylim(0.22, 6)
        ax.set_yticks([0.25, 0.5, 1, 2, 4]); ax.set_yticklabels(["0.25", "0.5", "1", "2", "4"])
        ax.set_title(f"HELM subsets, $b={b:g}\\sigma$", loc="left")
        ax.text(0.04, 0.96, f"slope {r.slope:+.2f}\n[{r.ci_lo:+.2f}, {r.ci_hi:+.2f}]", transform=ax.transAxes,
                va="top", fontsize=style.venue()["min_font_pt"], bbox=dict(fc="white", ec="none", pad=1.0, alpha=0.85))
        ax.set_xlabel("tasks in subset $m$")
        if j == 0:
            ax.set_ylabel("breadth-fraction ratio\nmedian-type / mean-type")
        else:
            ax.tick_params(labelleft=False)
        ax = bot[j]
        o = fit[(fit.regime == "ollb_free_vs_bundled") & (fit.statistic == "ratio_m39_minus_m6") & np.isclose(fit.B_sigma, b)]
        for i, (pair, rule) in enumerate(OLLB_PAIRS):
            r = o[o.rule_pair == pair].iloc[0]
            st = dict(color="k", marker="o", ls="-") if rule is None else style.RULE_STYLE[rule]
            ax.errorbar(r.slope, i, xerr=[[r.slope - r.ci_lo], [r.ci_hi - r.slope]], color=st["color"], marker=st["marker"],
                        mfc="white" if rule is None else st["color"], ms=4, lw=1.0, capsize=1.5)
        ax.axvline(0, color="0.4", lw=0.7)
        ax.set_ylim(len(OLLB_PAIRS) - 0.4, -0.6)
        ax.set_xlim(-2.0, 3.0)
        ax.grid(axis="y", alpha=0)
        ax.set_xlabel("ratio$_{39}$ $-$ ratio$_{6}$")
        ax.set_title("OLLB: $m{=}6\\to39$" if j == 0 else "", loc="left")
        ax.set_yticks(range(len(OLLB_PAIRS)))
        if j == 0:
            ax.set_yticklabels(["median-type", "median", "plurality", "Copeland"])
        else:
            ax.set_yticklabels([])
    handles = [plt.Line2D([], [], color="k", lw=1.8, marker="o", mfc="white", ms=3.5, label="median-type (R4 statistic)")]
    handles += [plt.Line2D([], [], label=style.RULE_LABEL[r], lw=0.9, ms=3, **style.RULE_STYLE[r]) for _, r in HELM_PAIRS]
    fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.045), columnspacing=1.0, handlelength=1.8)
    fig.tight_layout(h_pad=0.8, w_pad=0.4, rect=(0, 0.06, 1, 1))
    common.save_fig(fig, a.out, "fig3_m_effect", [p], note=f"variant={a.variant}; HELM top row (random subsets), OLLB bottom row (meanh denominator)")


if __name__ == "__main__":
    main()
