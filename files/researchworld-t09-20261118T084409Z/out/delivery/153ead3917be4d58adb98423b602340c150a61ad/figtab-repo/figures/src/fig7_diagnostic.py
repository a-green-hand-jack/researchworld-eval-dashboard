"""Fig. 7 (C6): the pre-registered diagnostics are not a general bias detector; the curvature bound B holds only inside its class.
(a) Spearman rank correlation of each score with |bias| over cells, by mechanism (95% bootstrap over cells)  [c6_rank.csv]
(b) extrapolation diagnostic D1 against |bias| per cell                                                      [c6_cover_cells.csv]
(c) curvature bound B against |bias| per cell; above the diagonal the bound fails                            [c6_B_vs_bias.csv]
Colours: blue/green = shapes inside the curvature-rule class, red/purple = violating it, grey = count."""
import os, sys
import numpy as np, pandas as pd
from matplotlib.lines import Line2D
sys.path.insert(0, os.path.dirname(__file__))
import figstyle as S

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
R = lambda f: pd.read_csv(os.path.join(ROOT, "results", "summary", f))
OUT = os.path.join(ROOT, "figures", "fig7_diagnostic.pdf")
rank, cells, bvb = R("c6_rank.csv"), R("c6_cover_cells.csv"), R("c6_B_vs_bias.csv")
rank = rank[rank.level == "cell"]

MECH = {  # key: (label, colour, marker)
    "linear": ("linear", "#0072B2", "o"), "concave": ("concave", "#56B4E9", "s"), "convex": ("convex", "#009E73", "D"),
    "thresh": ("thresh.", "#D55E00", "^"), "convex-2hop": ("2-hop", "#CC79A7", "v"), "count": ("count", "#7f7f7f", "P"),
}
SCORES = [("D1 extrapolation", "D1"), ("D1 (REG-Q audited)", "D1 (audit)"), ("D2 family spread", "D2"),
          ("D3 curvature bound B", "D3 ($B$)"), ("corner distance Z (baseline b)", "base: $Z$"),
          ("leverage iid-SE (baseline a)", "base: leverage")]

S.apply()
fig, axs = S.fig("text", aspect=0.38, ncols=3, gridspec_kw={"width_ratios": [1.3, 1, 0.95]})

ax = axs[0]
keys = list(MECH)
off = np.linspace(-0.34, 0.34, len(keys))
for i, (sk, lab) in enumerate(SCORES):
    y0 = len(SCORES) - 1 - i
    a = rank[(rank.score == sk) & (rank.group == "all")].iloc[0]
    ax.errorbar(a.spearman, y0, xerr=[[a.spearman - a.spearman_lo], [a.spearman_hi - a.spearman]], fmt="o", color="k", ms=3.6,
                mfc="k", elinewidth=1.0, capsize=0, zorder=3)
    for k, dy in zip(keys, off):
        r = rank[(rank.score == sk) & (rank.group == k)].iloc[0]
        _, c, m = MECH[k]
        ax.errorbar(r.spearman, y0 + dy, xerr=[[r.spearman - r.spearman_lo], [r.spearman_hi - r.spearman]], fmt=m, color=c,
                    ms=2.0, mfc=c, elinewidth=0.45, capsize=0, zorder=2)
ax.axvline(0, color="0.5", lw=0.6, zorder=0)
for y in np.arange(0.5, len(SCORES) + 0.5, 1.0):
    ax.axhline(y, color="0.85", lw=0.4, zorder=0)
ax.set_yticks(range(len(SCORES) + 1)); ax.set_yticklabels([l for _, l in SCORES][::-1] + ["D4"])
ax.set_ylim(-0.5, len(SCORES) + 0.5); ax.set_xlim(-0.95, 1.0)
ax.text(0.0, len(SCORES), "not in these cells", ha="center", va="center", color="0.45", style="italic")
ax.set_xlabel("Spearman $\\rho$ with $|$bias$|$")
ax.set_title("(a) rank correlation", fontsize=8)

def scatter(ax, df, xk, yk):
    for k, (lab, c, m) in MECH.items():
        d = df[df.mech == k]
        ax.plot(d[xk], d[yk], m, color=c, ms=2.2, mfc="none", mew=0.5, ls="none", alpha=0.85)

# (b) the degree-transport diagnostic D4 on grid e12, with its stress and control rows
ax = axs[1]
ax.sharey(axs[0])
r12 = R("c12_rank.csv")
H = "heterogeneous (BA, Stanford3, ego-Facebook)"
SUB = [(f"{H} | no degree dependence", "#E69F00", "o", "holds"),
       (f"{H} | stress (degree-dependent)", "#882255", "s", "stress"),
       ("control (ER) | no degree dependence", "0.45", "D", "ER ctrl")]
ROWS = [sk for sk, _ in SCORES] + ["D4 degree transport"]   # D4 at the top (y = 6)
off3 = [-0.22, 0.0, 0.22]
for i, sk in enumerate(ROWS):
    y0 = len(SCORES) - 1 - i if i < len(SCORES) else len(SCORES)
    for (sub, c, m, _), dy in zip(SUB, off3):
        r = r12[(r12.score == sk) & (r12.subset == sub)].iloc[0]
        ax.errorbar(r.spearman, y0 + dy, xerr=[[r.spearman - r.spearman_lo], [r.spearman_hi - r.spearman]], fmt=m, color=c,
                    ms=2.8, mfc=c, elinewidth=0.6, capsize=0, zorder=3)
ax.axvline(0, color="0.5", lw=0.6, zorder=0)
for y in np.arange(0.5, len(ROWS) - 0.5, 1.0):
    ax.axhline(y, color="0.85", lw=0.4, zorder=0)
ax.tick_params(labelleft=False); ax.set_xlim(-0.95, 1.0)
ax.set_xlabel("Spearman $\\rho$ with $|$bias$|$")
ax.set_title("(b) D4, 132 cells", fontsize=8)

ax = axs[2]
scatter(ax, bvb, "d3_B", "abs_bias")
lo, hi = 1e-4, 40
ax.plot([lo, hi], [lo, hi], color="0.3", lw=0.8)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
ax.set_xticks([1e-3, 1e-1, 10]); ax.set_yticks([1e-3, 1e-1, 10])
ax.set_box_aspect(1)
ax.set_xlabel("bound $B$"); ax.set_ylabel("$|$bias$|$ of REG-L")
under = (bvb.ratio < 1).groupby(bvb.mech).mean()
ax.text(0.04, 0.96, "fails above\nthe line", transform=ax.transAxes, va="top", ha="left", fontsize=8)
ax.set_title("(c) bound $B$", fontsize=8)

h = [Line2D([], [], marker=m, color=c, ls="none", ms=3.5, mfc="none", mew=0.7, label=lab) for k, (lab, c, m) in MECH.items()]
h.insert(0, Line2D([], [], marker="o", color="k", ls="none", ms=3.6, label="all"))
h2 = [Line2D([], [], marker=m, color=c, ls="none", ms=3.6, label=lab) for _, c, m, lab in SUB]
blank = Line2D([], [], ls="none", label=" ")
cols = []
for j in range(7):   # row 1: mechanisms (a, c); row 2: graph/response subsets of (b)
    cols += [h[j], h2[j] if j < len(h2) else blank]
fig.legend(handles=cols, loc="outside lower center", ncol=7, frameon=False, handletextpad=0.2, columnspacing=0.7, borderaxespad=0.0)
S.save(fig, OUT)
print({k: round(v, 3) for k, v in under.items()})
