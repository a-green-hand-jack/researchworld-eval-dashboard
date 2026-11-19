"""Fig 4 (column, C2/S4): fraction of instances with r_3 >= 1-delta against budget, per explainer arm.
Budget axis = coalitions relative to the shipped KernelSHAP default of the same cell (x1). Panels: one per dataset,
models and seeds pooled (cluster bootstrap over seeds, then instances). Shipped defaults are marked: KernelSHAP at x1,
Permutation at its own max_evals=500 point. `--by-model` writes the appendix version with one panel per dataset x model."""
import os, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import figstyle as fs, common as C

K, DELTA = 3, 0.10
ap_a = C.args(__doc__, extra=("--by-model",))
by_model = ap_a.by_model
df, files = C.load_tidy(ap_a.pilot)
d3 = df[df.k == K].copy()
d3["rel"] = (d3.r >= 1 - DELTA).astype(float)
base = d3[(d3.arm == C.DEFAULT_ARM) & (d3.budget == "x1")].groupby("cell").N.mean()
d3["x"] = d3.N / d3.cell.map(base)
d3["panel"] = d3.dataset.map(lambda s: C.DATA_LABEL.get(s, s)) + ((" " + d3.model.map(lambda s: C.MODEL_LABEL.get(s, s.upper()))) if by_model else "")
panels = sorted(d3.panel.unique())
n = len(panels)
ncol = 2 if n <= 2 else 3
nrow = int(np.ceil(n / ncol))
H_in = 3.25 * 0.8 if not by_model else 1.75 * nrow + 1.0
fs.apply("column" if not by_model else "text", H_in / (3.25 if not by_model else 6.75))
fig, axs = plt.subplots(nrow, ncol, sharey=True, squeeze=False, gridspec_kw={"wspace": 0.12, "hspace": 0.45})
axs = axs.ravel()
for ax in axs[n:]:
    ax.axis("off")
for ax, p in zip(axs, panels):
    sub = d3[d3.panel == p]
    for arm in C.ARMS:
        a = sub[sub.arm == arm]
        pts = []
        for b in C.BUDGETS + ["perm500"]:
            s = a[a.budget == b].groupby(["cell", "inst"], as_index=False).agg(rel=("rel", "mean"), x=("x", "mean"), seed=("seed", "first"))
            if len(s) == 0 or (b == "perm500" and arm != "perm"):
                continue
            m, lo, hi = C.cluster_boot(s, lambda f: f.rel.mean(), B=300)
            pts.append((b, s.x.mean(), m, lo, hi))
        grid = [q for q in pts if q[0] != "perm500"]
        if not grid:
            continue
        g = np.array([q[1:] for q in grid])
        ax.plot(g[:, 0], g[:, 1], color=fs.ARM_COLOR_R[arm], marker=fs.ARM_MARKER_R[arm], ms=3, lw=1, label=fs.ARM_LABEL_R[arm])
        ax.fill_between(g[:, 0], g[:, 2], g[:, 3], color=fs.ARM_COLOR_R[arm], alpha=0.15, lw=0)
        mark = [q for q in pts if (q[0] == "x1" and arm == C.DEFAULT_ARM) or q[0] == "perm500"]
        for q in mark:
            ax.plot([q[1]], [q[2]], marker="*", ms=8, color=fs.ARM_COLOR_R[arm], mec="k", mew=0.6, zorder=6)
    ax.set_xscale("log", base=2)
    ax.set_xticks([0.25, 1, 4, 16]); ax.set_xticklabels(["¼", "1", "4", "16"])
    ax.minorticks_off()
    ax.set_ylim(0, 1.02)
    ax.set_title(p, fontsize=fs.MIN_PT, pad=2)
for i in range(nrow):
    axs[i * ncol].set_ylabel(r"fraction with $r_3\geq 0.9$")
for ax in axs[:n]:
    ax.set_xlabel("budget / shipped default")
h, l = axs[0].get_legend_handles_labels()
from matplotlib.lines import Line2D
h.append(Line2D([], [], marker="*", ms=8, color="w", mfc="0.7", mec="k", mew=0.6, ls="", label="shipped default"))
fig.legend(handles=h, loc="lower center", ncol=2 if not by_model else 3, frameon=False, handlelength=1.6, columnspacing=1.0)
fig.subplots_adjust(left=0.15 if not by_model else 0.08, right=0.98, top=0.93, bottom=0.40 if not by_model else 1.0 / H_in)
out = os.path.join(C.outdir(ap_a), "fig4_budget.pdf" if not by_model else "figA_budget_by_model.pdf")
fig.savefig(out)
json.dump(C.provenance(files), open(out.replace(".pdf", ".json"), "w"), indent=1)
print("wrote", out)
