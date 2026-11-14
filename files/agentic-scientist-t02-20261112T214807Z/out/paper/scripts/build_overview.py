"""Export the grounded fallback after the designated concept renderer failed.

@evidence[[concept_figure_run.log]]
@evidence[[source_evidence/task/evaluate_final.py#L801]]
@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
@evidence[[paper_data.json#/grounding_sources/final.qualification.outcome]]
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from build_artifacts import provenance, save_json


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"


def draw_box(axis, bounds, text, color, fontsize=12.5):
    left, bottom, width, height = bounds
    axis.add_patch(FancyBboxPatch(
        (left, bottom), width, height, boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=0.8, edgecolor=color, facecolor=color + "10"))
    axis.text(left + width / 2, bottom + height / 2, text,
              ha="center", va="center", fontsize=fontsize, color="#243746")


def main():
    manifest_path = ROOT / "figure_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    overview = next(item for item in manifest["figures"] if item["figure_id"] == "study_overview")
    if (ROOT / ".concept_figure_complete").exists():
        return
    prompt_path = FIGURES / "study_overview.prompts.json"
    if overview.get("generator") == "generate-concept-figure" and bool(json.loads(prompt_path.read_text())):
        return
    if "renderer exit_code=1" not in (ROOT / "concept_figure_run.log").read_text():
        raise RuntimeError("Fallback requires recorded designated-renderer failure")
    data = json.loads((ROOT / "paper_data.json").read_text())
    if data["grounding_sources"]["final.qualification.outcome"]["value"] != "not_qualified":
        raise RuntimeError("Revisit fallback labels if qualification changes")
    figure, axes = plt.subplots(1, 2, figsize=(8, 2.4))
    for axis in axes:
        axis.set(xlim=(0, 1), ylim=(0, 1))
        axis.axis("off")
    axes[0].text(.5, .96, "(a) Width comparison", ha="center", va="top", fontsize=13, weight="bold")
    draw_box(axes[0], (.025, .48, .95, .32), "Input embeddings → sum + bias\nGELU → linear readout", "#186a9c")
    axes[0].text(.5, .37, "Width varies; architecture fixed", ha="center", va="center", fontsize=12.5)
    draw_box(axes[0], (.025, .03, .95, .24), "Studied · Reference\nZero decay · Norm matched", "#186a9c")
    axes[1].text(.5, .96, "(b) Evidence states", ha="center", va="top", fontsize=13, weight="bold")
    draw_box(axes[1], (.025, .63, .95, .17), "Observed onset: event recorded", "#28745e")
    draw_box(axes[1], (.025, .39, .95, .17), "Censored: no onset by horizon", "#b27a16")
    draw_box(axes[1], (.025, .15, .95, .17), "Missing: outcome unavailable", "#777777")
    axes[1].text(.5, .01, "Final qualification failed; cause unknown", ha="center", va="bottom", fontsize=12.5, color="#8c3643")
    figure.subplots_adjust(left=.025, right=.975, bottom=.035, top=.98, wspace=.12)
    for extension in ["pdf", "png"]:
        figure.savefig(FIGURES / ("study_overview." + extension), dpi=300, facecolor="white")
    plt.close(figure)
    overview.update({
        "generator": "matplotlib",
        "attempted_generator": "generate-concept-figure",
        "fallback_reason": "Designated renderer exited 1 before rendering because RWE_CODEX_API_KEY was unavailable; audit rejected the placeholder. Grounded vector fallback replaces it.",
        "files": {"pdf": "figures/study_overview.pdf", "png": "figures/study_overview.png"},
        "note": "Design-only fallback; no simulated trajectories. Original prompt log retained; PNG provenance remains host-owned.",
        "min_font_size_pt": 12.5,
        "estimated_min_rendered_font_pt": 12.5 * 5.5 / 8,
    })
    save_json(manifest_path, manifest)
    inputs = ["scripts/build_overview.py", "concept_figure_run.log",
              "source_evidence/task/evaluate_final.py#L801",
              "paper_data.json#/final_evaluation/evaluation_evidence/episodes",
              "paper_data.json#/grounding_sources/final.qualification.outcome"]
    provenance(FIGURES / "study_overview.pdf", inputs, "figure", script_path="scripts/build_overview.py")
    provenance(manifest_path, inputs + ["paper_strategy.json#/figure_specs"], script_path="scripts/build_overview.py")


if __name__ == "__main__":
    main()
