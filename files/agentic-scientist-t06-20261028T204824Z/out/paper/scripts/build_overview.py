"""Overview schematic of the evaluation protocol (documented matplotlib fallback).

The schematic contains no quantitative claims; budget values and design names are
taken from the protocol description in paper.tex (Section 3).
Skips when the orchestrator has rendered its own concept figure.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
if (ROOT / ".concept_figure_complete").exists():
    raise SystemExit("orchestrator concept figure present; not overwriting")

plt.rcParams.update({"font.family": "DejaVu Sans"})
fig, ax = plt.subplots(figsize=(5.5, 3.5))
ax.set_xlim(0, 100)
ax.set_ylim(0, 64)
ax.axis("off")

BLUE, LIGHT, ORANGE = "#1f5fa8", "#e8f0fa", "#f3e3d0"
boxes = [
    ("1 Comparison data", "crowd, expert human,\nLLM judge, sports:\nrows (a, b, outcome)", LIGHT),
    ("2 Leaderboard fit", "ridge Bradley-Terry fit:\nrank-1 competitor,\nrunner-up, gap G", LIGHT),
    ("3 Proposer", "at most k rows to drop\nor reverse, with k from\n0.1% to 2% of rows", ORANGE),
    ("4 Evaluator", "applies the edit and\nrefits the edited data\n(exact refit)", LIGHT),
    ("5 Score", "1 if rank 1 is displaced,\nelse fraction of gap\nG closed", LIGHT),
]
w, h = 29.5, 24
xs = [0.8, 35.3, 69.8]
ys = [37, 6]
pos = [(xs[0], ys[0]), (xs[1], ys[0]), (xs[2], ys[0]), (xs[2], ys[1]), (xs[1], ys[1])]
for (title, body, col), (x, y) in zip(boxes, pos):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2",
                                fc=col, ec=BLUE, lw=1.2))
    ax.text(x + w / 2, y + h - 4, title, ha="center", va="center", fontsize=8.5, fontweight="bold", color=BLUE)
    ax.text(x + w / 2, y + h / 2 - 3, body, ha="center", va="center", fontsize=8, linespacing=1.4)
def arrow(p0, p1):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=11, color=BLUE, lw=1.3))
arrow((xs[0] + w + 0.8, ys[0] + h / 2), (xs[1] - 0.8, ys[0] + h / 2))
arrow((xs[1] + w + 0.8, ys[0] + h / 2), (xs[2] - 0.8, ys[0] + h / 2))
arrow((xs[2] + w / 2, ys[0] - 0.8), (xs[2] + w / 2, ys[1] + h + 0.8))
arrow((xs[2] - 0.8, ys[1] + h / 2), (xs[1] + w + 0.8, ys[1] + h / 2))
ax.text(xs[0] + w / 2, ys[1] + h / 2, "case score = mean over\nfive budgets and\nevaluation seeds", ha="center",
        va="center", fontsize=8, style="italic", linespacing=1.4)
arrow((xs[1] - 0.8 + 0.0, ys[1] + h / 2), (xs[0] + w + 0.8, ys[1] + h / 2))
FIG.mkdir(exist_ok=True)
fig.savefig(FIG / "overview_protocol.pdf", bbox_inches="tight")
fig.savefig(FIG / "overview_protocol.png", dpi=300, bbox_inches="tight")
