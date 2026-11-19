"""Appendix Fig. (C6): D1 extrapolation score against |bias| per cell (was Fig. 7b). Reads c6_cover_cells.csv.
Split from Fig. 7 (C6): the pre-registered diagnostics are not a general bias detector; the curvature bound B holds only inside its class.
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
OUT = os.path.join(ROOT, "figures", "fig7_d1_scatter.pdf")
rank, cells, bvb = R("c6_rank.csv"), R("c6_cover_cells.csv"), R("c6_B_vs_bias.csv")
rank = rank[rank.level == "cell"]

MECH = {  # key: (label, colour, marker)
    "linear": ("linear", "#0072B2", "o"), "concave": ("concave", "#56B4E9", "s"), "convex": ("convex", "#009E73", "D"),
    "thresh": ("threshold", "#D55E00", "^"), "convex-2hop": ("convex 2-hop", "#CC79A7", "v"), "count": ("count", "#7f7f7f", "P"),
}
SCORES = [("D1 extrapolation", "D1"), ("D1 (REG-Q audited)", "D1 (audit)"), ("D2 family spread", "D2"),
          ("D3 curvature bound B", "D3 ($B$)"), ("corner distance Z (baseline b)", "base: $Z$"),
          ("leverage iid-SE (baseline a)", "base: leverage")]

S.apply()
fig, ax = S.fig("half", aspect=0.85)
for k, (lab, c, m) in MECH.items():
    d = cells[cells.mech == k]
    ax.plot(d["d1"], d["abs_bias"], m, color=c, ms=2.6, mfc="none", mew=0.5, ls="none", alpha=0.85, label=lab)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("D1 extrapolation score"); ax.set_ylabel("$|$bias$|$ of REG-L")
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False, handletextpad=0.2, columnspacing=0.6, fontsize=8)
S.save(fig, OUT)
