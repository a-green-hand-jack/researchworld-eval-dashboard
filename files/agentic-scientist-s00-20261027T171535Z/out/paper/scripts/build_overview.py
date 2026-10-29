"""Native matplotlib overview of the evaluation pipeline (documented fallback for the concept figure)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)


def box(ax, x, y, w, h, text, fc, fs=10.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                                fc=fc, ec="#333333", lw=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, p, q):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12, lw=1.1, color="#333333"))


fig, ax = plt.subplots(figsize=(11, 4.0))
ax.set_xlim(0, 11)
ax.set_ylim(0, 4)
ax.axis("off")

blue, grey, gold, red, green = "#dbe7f5", "#e6e6e6", "#f6edc8", "#f3d9d2", "#dcefdc"

box(ax, 0.1, 1.55, 1.8, 1.1, "Connected graph\n$6\\leq n\\leq 30$\n12 families", green)
box(ax, 2.5, 2.45, 2.3, 1.1, "Five statistics\n$\\log n,\\ \\log m,\\ \\log\\bar d,$\n$\\log\\Delta,\\ \\log\\mathrm{diam}$", blue)
box(ax, 5.3, 2.45, 1.6, 1.1, "Ridge model\n$\\lambda=1$\n$\\to$ predicted $\\log C$", blue)
box(ax, 2.5, 0.35, 4.4, 1.5, "Controls (same scoring)\n$2m(n-1)$ bound\nconstant predictor\nshuffled-target ridge", grey)
box(ax, 9.3, 0.05, 1.6, 0.95, "Monte Carlo\nstart-averaged\ncover time", gold)
box(ax, 9.3, 1.45, 1.6, 1.5, "Clipped log error\n$\\to$ family mean\n$\\to$ macro mean\n(lower is better)", red)

arrow(ax, (1.9, 2.25), (2.5, 2.85))
arrow(ax, (1.9, 1.95), (2.5, 1.35))
arrow(ax, (4.8, 3.0), (5.3, 3.0))
arrow(ax, (6.9, 3.0), (9.3, 2.7))
arrow(ax, (6.9, 1.1), (9.3, 1.7))
arrow(ax, (10.1, 1.0), (10.1, 1.45))
fig.tight_layout()
fig.savefig(FIG / "overview_pipeline.pdf")
fig.savefig(FIG / "overview_pipeline.png", dpi=300)
