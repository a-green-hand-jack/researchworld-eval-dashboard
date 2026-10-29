import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from data import TASK1, FUNNEL

out = sys.argv[1]
plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.linewidth": 0.6,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
C = {"LMM": "#0072B2", "CLIP": "#D55E00"}  # Okabe-Ito, distinguishable in greyscale by marker too
M = {"LMM": "o", "CLIP": "s"}

# ---- Fig: Task 1, Recall@K per model + F1 --------------------------------------------
rows = sorted(TASK1, key=lambda r: r[5])  # by R@5, best on top
fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.7), gridspec_kw={"width_ratios": [2.3, 1]}, sharey=True)
for i, (n, fam, f1, r1, r3, r5) in enumerate(rows):
    a.plot([r1, r5], [i, i], color="0.75", lw=1.2, zorder=1)
    a.scatter([r1], [i], color=C[fam], marker=M[fam], s=22, zorder=3, facecolor="white", linewidths=1.2)
    a.scatter([r3], [i], color=C[fam], marker=M[fam], s=22, zorder=3, alpha=0.6)
    a.scatter([r5], [i], color=C[fam], marker=M[fam], s=22, zorder=3)
    b.barh(i, f1, color=C[fam], height=0.6)
    b.text(f1 + 0.008, i, f"{f1:.3f}", va="center", fontsize=6.5)
a.set_yticks(range(len(rows))); a.set_yticklabels([r[0] for r in rows])
a.set_xlabel("Recall@K (open $K{=}1$, light $K{=}3$, filled $K{=}5$)"); a.set_xlim(0.15, 0.65)
a.grid(axis="x", lw=0.3, color="0.85")
b.set_xlabel("F1"); b.set_xlim(0, 0.46); b.grid(axis="x", lw=0.3, color="0.85")
b.tick_params(axis="y", length=0)
h = [plt.Line2D([], [], color=C[k], marker=M[k], ls="", label=l) for k, l in (("LMM", "LMM (generate, then embed)"), ("CLIP", "CLIP-family (image–text similarity)"))]
a.legend(handles=h, loc="lower right", frameon=False, fontsize=7)
fig.tight_layout(); fig.savefig(os.path.join(out, "task1_recall_f1.pdf")); fig.savefig(os.path.join(out, "task1_recall_f1.png"), dpi=200)

# ---- Fig: curation funnel ---------------------------------------------------------------
labs = [r[0] for r in FUNNEL]
fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.2), sharey=True)
for ax, idx, t, log in zip(axs, (1, 2, 3), ("Images", "Bounding boxes", "Classes (log scale)"), (False, False, True)):
    v = [r[idx] for r in FUNNEL]
    ax.barh(range(len(v)), v, color="#0072B2", height=0.65)
    for i, x in enumerate(v):
        ax.text(x * (1.08 if log else 1) + (0 if log else max(v) * 0.02), i, f"{x:,}", va="center", fontsize=6.5)
    if log: ax.set_xscale("log"); ax.set_xlim(100, 2e4)
    else: ax.set_xlim(0, max(v) * 1.28)
    ax.set_title(t, fontsize=8)
axs[0].set_yticks(range(len(labs))); axs[0].set_yticklabels(labs); axs[0].invert_yaxis()
from matplotlib.ticker import FuncFormatter
for ax in axs[:2]:
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x/1000)}k" if x else "0"))
for ax in axs: ax.tick_params(labelsize=7)
fig.tight_layout(); fig.savefig(os.path.join(out, "curation_funnel.pdf")); fig.savefig(os.path.join(out, "curation_funnel.png"), dpi=200)
