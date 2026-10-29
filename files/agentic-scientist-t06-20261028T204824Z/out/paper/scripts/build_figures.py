"""Build the quantitative figure (design_scores).

All plotted values are read from paper_data.json (sealed final metrics).
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

data = json.loads((ROOT / "paper_data.json").read_text(encoding="utf-8"))
M = data["final_evaluation"]["metrics"]
# @evidence[[paper_data.json#final_evaluation.metrics]]

BLUE, GREY = "#1f5fa8", "#a0a0a0"
plt.rcParams.update({"font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9,
                     "xtick.labelsize": 8, "ytick.labelsize": 8.5, "font.family": "DejaVu Sans"})


def bars(ax, labels, vals, colors, title):
    xs = range(len(vals))
    ax.bar(xs, vals, color=colors, width=0.62, edgecolor="none")
    for x, v in zip(xs, vals):
        ax.text(x, v + 0.015, f"{v:.3f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.12)
    ax.set_title(title, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#e6e6e6", linewidth=0.7)


fig, (a, b) = plt.subplots(1, 2, figsize=(6.4, 2.9), gridspec_kw={"wspace": 0.28})
designs = [("Crowd\nvotes", "score_crowd"), ("Sports\n(NBA)", "score_sports"),
           ("Expert\nhuman", "score_expert_human"), ("LLM\njudge", "score_llm_judge")]
bars(a, [d[0] for d in designs], [M[d[1]] for d in designs], [BLUE] * 4, "(a) Influence search by design")
a.set_ylabel("Edit success score")
pol = [("Constant", "score_constant", GREY), ("Random", "score_random", GREY),
       ("Win-rate\nheuristic", "score_winrate", GREY), ("Influence\nsearch", "score_influence", BLUE)]
bars(b, [p[0] for p in pol], [M[p[1]] for p in pol], [p[2] for p in pol], "(b) Family-averaged by policy")
fig.savefig(FIG / "design_scores.pdf", bbox_inches="tight")
fig.savefig(FIG / "design_scores.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# The overview schematic is produced by scripts/build_overview.py (documented fallback).
