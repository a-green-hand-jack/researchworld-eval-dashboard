"""Build quantitative figures from derived/final_stats.json (itself derived from paper_data.json).

Run: python scripts/derive_final_stats.py && python scripts/build_figures.py
@evidence[[derived/final_stats.json]]
Also writes a placeholder for the orchestrator-owned concept figure unless it was already rendered.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
S = json.loads((ROOT / "derived" / "final_stats.json").read_text(encoding="utf-8"))
C = S["cases"]

plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "axes.titlesize": 10,
                     "xtick.labelsize": 9, "ytick.labelsize": 8.5, "legend.fontsize": 8.5,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
BLUE, ORANGE, GRAY = "#1f5fa6", "#e08a1e", "#8a8a8a"
SAND = "#d9c27a"


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=400, bbox_inches="tight")
    plt.close(fig)


def main_budget():
    designs = [("Crowd votes (arena, 52 models)", ["F1", "F2"]),
               ("NBA games (30 teams)", ["F3", "F4"])]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.6), sharey=True)
    w = 0.26
    for ax, (title, ids) in zip(axes, designs):
        for gi, cid in enumerate(ids):
            c = C[cid]
            vals = [(c["studied_percent"], c["studied_k"], BLUE, None),
                    (c["b2_percent"], c["b2_k"], ORANGE, "///"),
                    (c["b3_percent"], c["b3_k"], GRAY, None)]
            for si, (v, k, col, hatch) in enumerate(vals):
                x = gi + (si - 1) * w
                ax.bar(x, v, w * 0.92, color=col, hatch=hatch, edgecolor="white" if hatch else col,
                       linewidth=0.0 if not hatch else 0.8)
                ax.text(x, v * 1.18, f"{k}", ha="center", va="bottom", fontsize=8)
        cap = C[ids[0]]["cap_percent_of_rows"]
        ax.axhline(cap, color="#b22222", ls="--", lw=1.1)
        ax.text(1.48, cap * 1.06, "2% cap", color="#b22222", ha="right", va="bottom", fontsize=8)
        ax.set_yscale("log")
        ax.set_ylim(1.5e-3, 6)
        ax.set_xlim(-0.55, 1.55)
        ax.set_xticks([0, 1])
        ax.set_xticklabels([f"{lab}\nrandom removal flips\n{C[cid]['b1_flips']}/{C[cid]['b1_draws']} draws"
                            for lab, cid in zip(["top pair", "mid pair"], ids)], fontsize=8.5)
        ax.set_title(title)
    axes[0].set_ylabel("recorded removal budget (% of all comparisons)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=BLUE),
               plt.Rectangle((0, 0), 1, 1, facecolor=ORANGE, hatch="///", edgecolor="white"),
               plt.Rectangle((0, 0), 1, 1, color=GRAY)]
    fig.legend(handles, ["studied configuration", "influence only (B2)", "opponent-targeted (B3)"],
               loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    save(fig, "main_budget_by_case")


def controls():
    pc = S["permutation_controls"]
    fig, axes = plt.subplots(1, 2, figsize=(6.2, 2.8))
    ax = axes[0]
    w = 0.34
    for i, (real, perm) in enumerate([("F1", "F5"), ("F3", "F6")]):
        for j, (cid, col, lab) in enumerate([(real, BLUE, "real table"), (perm, SAND, "label-permuted")]):
            k = C[cid]["studied_k"]
            ax.bar(i + (j - 0.5) * w, k, w * 0.92, color=col, label=lab if i == 0 else None)
            ax.text(i + (j - 0.5) * w, k * 1.12, str(k), ha="center", va="bottom", fontsize=8.5)
    ax.set_yscale("log")
    ax.set_ylim(1, 1000)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["crowd votes", "NBA games"])
    ax.set_ylabel("recorded removal budget (rows)")
    ax.set_title("(a) top-pair budget")
    ax.legend(frameon=False, loc="upper left")
    ax = axes[1]
    ratios = [pc["F5"]["bt_std_ratio"], pc["F6"]["bt_std_ratio"]]
    ax.bar([0, 1], ratios, 0.5, color=SAND)
    for i, r in enumerate(ratios):
        ax.text(i, r + 0.015, f"{r:.3f}", ha="center", va="bottom", fontsize=8.5)
    ax.set_ylim(0, 0.2)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["crowd votes", "NBA games"])
    ax.set_ylabel("rating spread, permuted / real")
    ax.set_title("(b) spread after permutation")
    fig.tight_layout()
    save(fig, "controls_permutation")


def concept_placeholder():
    """Lightweight stand-in so the draft compiles; never clobbers the orchestrator render."""
    if (ROOT / ".concept_figure_complete").exists():
        return
    stub = FIG / "protocol_overview.prompts.json"
    if stub.exists() and stub.stat().st_size > 2:
        return
    fig, ax = plt.subplots(figsize=(7.0, 2.2))
    ax.axis("off")
    ax.text(0.5, 0.5, "protocol overview (placeholder; rendered by orchestrator)", ha="center", va="center")
    fig.savefig(FIG / "protocol_overview.png", dpi=300)
    plt.close(fig)
    stub.write_text("{}", encoding="utf-8")


if __name__ == "__main__":
    main_budget()
    controls()
    concept_placeholder()
