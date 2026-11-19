"""F5 (claim E5): the same MT-Bench pairs under a different labeller, N matched.

Reads matched_pairs.csv, comparison `mt_human_1perkey_draws_vs_gpt4`: GPT-4 judgments on the 1,814 matched keys (x) against one
human judgment per key (y; median and min-max over 20 random draws of that judgment). Each point is one of the 15 model pairs.
Left: statistical margin z. Right: verified removal budget. Hollow marker (only if it occurs): the human order of the pair differs from GPT-4's in some draws. Writes fig5_matched.pdf.
"""
import os

import matplotlib.pyplot as plt

import common as C

A = C.args(__doc__)
C.set_style()
m = C.read(A.results, "matched_pairs.csv")
m = m[m.comparison == "mt_human_1perkey_draws_vs_gpt4"]
fig, axes = plt.subplots(1, 2, figsize=(C.TEXTWIDTH, 2.3))
for ax, (xc, yc, ylo, yhi, lab, ttl) in zip(axes, [
        ("ref_z", "alt_z_median", None, None, "$z$", "statistical margin"),
        ("ref_budget", "alt_budget_median", "alt_budget_min", "alt_budget_max", "verified removal budget $k$ (comparisons)", "adversarial budget")]):
    same = m.alt_hi_same_share >= 1
    if ylo:
        ax.errorbar(m[xc], m[yc], yerr=[m[yc] - m[ylo], m[yhi] - m[yc]], fmt="none", ecolor=C.DESIGN_COLOR["expert"], elinewidth=0.6, alpha=0.6)
    for flag, fs in [(True, "full"), (False, "none")]:
        d = m[same == flag]
        if d.empty:
            continue
        ax.plot(d[xc], d[yc], C.DESIGN_MARKER["expert"], color=C.DESIGN_COLOR["expert"], fillstyle=fs, ms=4.5, mew=0.9,
                label="same order in all draws" if flag else "order differs in some draws")
    lim = [min(m[xc].min(), m[yc].min()) * 0.8, max(m[xc].max(), m[yc].max()) * 1.25]
    ax.plot(lim, lim, "-", color=C.MUTED, lw=0.7, zorder=0)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim)
    q = "$z$" if xc == "ref_z" else "$k$"
    ax.set_xlabel(f"GPT-4 judge, {q}"); ax.set_ylabel(f"human, {q}")
    ax.minorticks_off()
    t = [1, 2, 5, 10, 20] if xc == "ref_z" else [10, 20, 50, 100, 200, 500]
    t = [v for v in t if lim[0] <= v <= lim[1]]
    ax.set_xticks(t); ax.set_yticks(t); ax.set_xticklabels(t); ax.set_yticklabels(t)
    ax.set_title(ttl, loc="left", fontsize=8)
if (m.alt_hi_same_share < 1).any():
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, frameon=False, fontsize=6.5)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
else:  # all 15 pairs keep their order in every human draw (stated in the caption)
    fig.tight_layout()
fig.savefig(os.path.join(A.out, "fig5_matched.pdf"))
C.record_inputs(A.out, "fig5_matched.pdf", [os.path.join(A.results, "matched_pairs.csv")])
