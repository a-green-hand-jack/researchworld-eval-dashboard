"""Build the main comparison figure (and the concept-figure placeholder) from paper_data.json."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

# @evidence[[paper_data.json#final_evaluation.metrics]]
metrics = json.loads((ROOT / "paper_data.json").read_text(encoding="utf-8"))["final_evaluation"]["metrics"]

rows = [  # label, metric key, color
    ("Five-stat.\nridge", "macro_log_mae", "#1f5fa8"),
    ("Constant\n(train\ngeo-mean)", "const_macro_log_mae", "#c9a227"),
    ("Ridge vs.\nshuffled\ntargets", "shuffle_macro_log_mae", "#b5533c"),
    ("Bound\n$2m(n-1)$", "bound_macro_log_mae", "#6b6b6b"),
]


def main_comparison():
    plt.rcParams.update({"font.size": 11, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10})
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    xs = range(len(rows))
    vals = [metrics[k] for _, k, _ in rows]
    bars = ax.bar(xs, vals, color=[c for _, _, c in rows], width=0.62)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.03, f"{v:.3f}", ha="center", va="bottom", fontsize=10)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([r[0] for r in rows])
    ax.set_ylabel("Family-macro log MAE", fontsize=11)
    ax.set_ylim(0, max(vals) * 1.14)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIG / "main_comparison.pdf")
    fig.savefig(FIG / "main_comparison.png", dpi=300)
    plt.close(fig)


def concept_placeholder():
    # Never clobber the orchestrator-rendered concept figure.
    if (ROOT / ".concept_figure_complete").exists():
        return
    png = FIG / "overview_pipeline.png"
    log = FIG / "overview_pipeline.prompts.json"
    if log.exists() and log.read_text().strip() not in ("", "{}"):
        return
    fig, ax = plt.subplots(figsize=(11, 3.2))
    ax.text(0.5, 0.5, "overview_pipeline (placeholder)", ha="center", va="center")
    ax.axis("off")
    fig.savefig(png, dpi=220)
    plt.close(fig)
    log.write_text("{}\n")


if __name__ == "__main__":
    main_comparison()
    concept_placeholder()
