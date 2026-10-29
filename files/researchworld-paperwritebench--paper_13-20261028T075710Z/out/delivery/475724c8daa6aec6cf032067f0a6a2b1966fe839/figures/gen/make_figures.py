"""Render figures/*.pdf from figures/gen/data.py. Usage: python3 figures/gen/make_figures.py"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from data import TASK1, VS, VS_MODEL

OUT = os.path.join(os.path.dirname(__file__), "..")
plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42})
COL = {"R@1": "#0072B2", "R@3": "#E69F00", "R@5": "#009E73"}

# ---- Fig: Task 1 recall@K per model (one row per model, sorted within type by R@1)
rows = sorted([r for r in TASK1 if r[1] == "LMM"], key=lambda r: -r[3]) + \
       sorted([r for r in TASK1 if r[1] == "CLIP"], key=lambda r: -r[3])
n_lmm = sum(r[1] == "LMM" for r in rows)
ypos = [i if i < n_lmm else i + 0.8 for i in range(len(rows))]
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9), sharey=True,
                              gridspec_kw={"width_ratios": [3, 1.6], "wspace": 0.05})
for y, r in zip(ypos, rows):
    ax.plot([r[3], r[5]], [y, y], color="0.75", lw=1.5, zorder=1)
    for k, v, m in (("R@1", r[3], "o"), ("R@3", r[4], "s"), ("R@5", r[5], "D")):
        ax.scatter(v, y, color=COL[k], marker=m, s=22, zorder=3, label=k if y == ypos[0] else None)
    ax2.barh(y, r[2], color="0.45", height=0.55)
    ax2.text(r[2] + 0.008, y, "%.3f" % r[2], va="center", fontsize=7)
ax.set_yticks(ypos)
ax.set_yticklabels([r[0] for r in rows])
ax.set_ylim(ypos[-1] + 0.6, -1.2)
ax.set_xlim(0.15, 0.65)
ax.set_xlabel("Recall@$K$ (fraction of crops)")
ax.grid(axis="x", color="0.9", lw=0.6, zorder=0)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False, ncol=3, handletextpad=0.2, columnspacing=1.0)
ax.axhline((ypos[n_lmm - 1] + ypos[n_lmm]) / 2, color="0.6", lw=0.6, ls=":")
ax.text(0.152, ypos[n_lmm] - 0.55, "contrastive encoders", fontsize=6.5, color="0.35", style="italic", va="top")
ax.text(0.152, -0.45, "large multimodal models", fontsize=6.5, color="0.35", style="italic", va="bottom")
ax2.set_xlim(0, 0.48)
ax2.set_xlabel("F1")
ax2.set_xticks([0, 0.2, 0.4])
ax2.spines["left"].set_visible(False)
ax2.tick_params(axis="y", length=0)
fig.savefig(os.path.join(OUT, "fig_task1_recall.pdf"), bbox_inches="tight")
plt.close(fig)

# ---- Fig: Task 3, with vs without menu description (paired values per metric)
mets = ["F1", "P@1", "R@1", "R@3", "R@5"]
a, b = VS["w/o description"], VS["w/ description"]
fig, ax = plt.subplots(figsize=(3.3, 2.2))
for j, m in enumerate(mets):
    up = b[j] > a[j]
    c = "#009E73" if up else "#D55E00"
    ax.annotate("", xy=(j, b[j]), xytext=(j, a[j]),
                arrowprops=dict(arrowstyle="-|>", color=c, lw=1.5, shrinkA=0, shrinkB=0))
    ax.scatter(j, a[j], color="white", edgecolor="0.2", s=22, zorder=3,
               label="w/o description" if j == 0 else None)
    ax.scatter(j, b[j], color="0.2", s=22, zorder=3, label="w/ description" if j == 0 else None)
    ax.text(j + 0.12, (a[j] + b[j]) / 2, "%+.3f" % (b[j] - a[j]), fontsize=7, color=c, va="center")
ax.set_xticks(range(5))
ax.set_xticklabels(mets)
ax.set_xlim(-0.4, 4.7)
ax.set_ylim(0, 0.52)
ax.set_ylabel("score")
ax.grid(axis="y", color="0.9", lw=0.6, zorder=0)
ax.legend(loc="lower right", frameon=False, fontsize=7)
fig.savefig(os.path.join(OUT, "fig_task3_menu_effect.pdf"), bbox_inches="tight")
plt.close(fig)
print("ok")
