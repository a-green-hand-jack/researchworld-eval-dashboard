"""Appendix figure (column, C1): the tail against budget. ECDF of per-instance exact r_3 for the shipped KernelSHAP default at x1 (solid) and
x16 (dashed), one colour per dataset x model, exact mean at x1 marked. Fig 1(a) draws x1 exact and eps-tolerant; this is the x16 half.
Input: results/tidy_*_R20.csv (main grid)."""
import os, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import figstyle as fs, common as C

K = 3
a = C.args(__doc__)
fs.apply("column", 0.95)
df, files = C.load_tidy(a.pilot)
d3 = df[(df.arm == C.DEFAULT_ARM) & (df.k == K)].copy()
d3["group"] = d3.dataset.map(lambda s: C.DATA_LABEL.get(s, s)) + " " + d3.model.map(lambda s: C.MODEL_LABEL.get(s, s.upper()))
groups = sorted(d3.group.unique())
pal = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000", "#F0E442"]   # same order as Fig 1
col = {g: pal[i % len(pal)] for i, g in enumerate(groups)}
fig, ax = plt.subplots()
fig.subplots_adjust(left=0.16, right=0.98, top=0.97, bottom=0.40)
for g in groups:
    for b, ls in (("x1", "-"), ("x16", (0, (3, 1.5)))):
        v = d3[(d3.group == g) & (d3.budget == b)].groupby(["cell", "inst"]).r.mean().values
        x, y = C.ecdf(v)
        ax.step(x, y, where="post", color=col[g], ls=ls, lw=1.0)
        if b == "x1":
            ax.plot([v.mean()], [0], marker="v", ms=4, color=col[g], clip_on=False, zorder=5)
ax.axvline(0.9, color="0.5", lw=0.6, ls=":")
ax.set_xlim(0, 1.02); ax.set_ylim(0, 0.5)
ax.set_xlabel(r"per-instance $r_3$ (P[top-3 correct])"); ax.set_ylabel("cumulative fraction of instances")
h = [Line2D([], [], color=col[g], lw=1.2, label=g) for g in groups]
h += [Line2D([], [], color="0.3", lw=1.0, label="$\\times$1 (shipped)"), Line2D([], [], color="0.3", lw=1.0, ls=(0, (3, 1.5)), label="$\\times$16 budget")]
fig.legend(handles=h, frameon=False, loc="lower center", ncol=2, handlelength=1.6, columnspacing=1.0, labelspacing=0.3)
out = os.path.join(C.outdir(a), "figA_ecdf_x16.pdf")
fig.savefig(out)
json.dump(C.provenance(files), open(out.replace(".pdf", ".json"), "w"), indent=1)
print("wrote", out)
