"""F7 (claim E2/E3 link): the targeted budget against the amount of random removal that produces the same flip.

Reads s5_noise.csv (k_noise_05, k_noise_50: the smallest number of uniformly random removals, Monte Carlo with 200 draws per k,
at which the claim is flipped with probability >= 5% / 50%; NaN = the frequency stays below that level up to 98% of N) and adv_budgets.csv
(verified targeted budget k of the same claim). Claims: C1 and the adjacent-pair claims C2 (exact ties excluded). Each point is a claim, both axes
as a share of N; points on the dashed top line never reach the level under random removal up to 98% of N. Grey: claims of the NBA single seasons.
Writes fig7_noise.pdf.
"""
import os

import matplotlib.pyplot as plt
import numpy as np

import common as C

A = C.args(__doc__)
C.set_style()
b = C.read(A.results, "adv_budgets.csv")
b = b[b.claim_type.isin(["C1", "C2"]) & ~b.exact_tie & b.verified]
n = C.read(A.results, "s5_noise.csv").rename(columns={"unit": "dataset", "claim": "claim_id"})
n = n[~n.dataset.astype(str).str.endswith(C.SECONDARY_SUFFIX)]
m = b.merge(n[["dataset", "claim_id", "k_noise_05", "k_noise_50"]], on=["dataset", "claim_id"], how="inner")
m["x"] = m.budget / m.N
CEIL = 0.98
fig, axes = plt.subplots(1, 2, figsize=(C.TEXTWIDTH, 2.3), sharex=True, sharey=True)
lo, hi = 2e-5, 1.0
for ax, col, ttl in zip(axes, ["k_noise_05", "k_noise_50"], ["random removal flips it in $\\geq 5\\%$ of draws", "random removal flips it in $\\geq 50\\%$ of draws"]):
    y = m[col] / m.N
    never = y.isna()
    yy = y.fillna(CEIL * 1.0)
    s = ~m.dataset.isin(C.BASE_UNITS)
    ax.plot(m.x[s], yy[s], ".", color="#999999", ms=1.8, alpha=0.5, mew=0, label="NBA single seasons", rasterized=True)
    for u in C.BASE_UNITS:
        d = m.dataset == u
        des = C.design_of(u)
        ax.plot(m.x[d & ~never], yy[d & ~never], C.DESIGN_MARKER[des], color=C.DESIGN_COLOR[des], ms=3.6, mec="white", mew=0.3, label=C.SHORT_LABEL[u])
        ax.plot(m.x[d & never], yy[d & never], C.DESIGN_MARKER[des], color=C.DESIGN_COLOR[des], ms=3.6, mec="white", mew=0.3)
    ax.plot([lo, hi], [lo, hi], "-", color=C.MUTED, lw=0.7, zorder=0)
    ax.axhline(CEIL, color=C.MUTED, lw=0.7, ls=(0, (3, 2)))
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lo, 0.3); ax.set_ylim(lo, 1.3)
    ax.set_xlabel("targeted verified budget $k/N$"); ax.set_title(ttl, loc="left", fontsize=7)
axes[0].set_ylabel("random removals $/N$")
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=5, frameon=False, fontsize=6, columnspacing=0.8, handlelength=1.2)
C.panel_letter(axes[0], "a"); C.panel_letter(axes[1], "b")
fig.subplots_adjust(left=0.1, right=0.985, bottom=0.3, top=0.9, wspace=0.12)
fig.savefig(os.path.join(A.out, "fig7_noise.pdf"))
C.record_inputs(A.out, "fig7_noise.pdf", [os.path.join(A.results, f) for f in ["s5_noise.csv", "adv_budgets.csv"]])
print({u: int((m.dataset == u).sum()) for u in C.BASE_UNITS}, "season claims", int((~m.dataset.isin(C.BASE_UNITS)).sum()))
