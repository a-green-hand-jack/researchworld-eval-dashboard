"""Generate descriptive artifacts from retained evaluator observations.

@evidence[[paper_data.json#/best_correct/evaluation_evidence/episodes]]
@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
@evidence[[source_evidence/task/evaluate_final.py#L1001]]
"""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
DERIVED = ROOT / "derived"
ARMS = ["candidate", "fixed_reference", "zero_decay", "initial_norm"]
LABELS = ["Studied", "Reference", "No decay", "Norm matched"]
COLORS = ["#186a9c", "#777777", "#d48420", "#9a4b93"]
WIDTHS = [32, 128, 256]


def save_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def provenance(path, inputs, kind="derived", notes="", script_path="scripts/build_artifacts.py"):
    artifact = {"path": str(path.relative_to(ROOT)), "kind": kind}
    if path.name != "figure_manifest.json":
        artifact["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    save_json(Path(str(path) + ".prov.json"), {
        "schema_name": "scientific-evidence.artifact-manifest",
        "artifact": artifact,
        "derived_from": ["@" + "evidence[[" + item + "]]" for item in inputs],
        "generated_by": {"script_path": script_path},
        "notes": notes,
    })


def sustained(curve, field, threshold):
    for index in range(len(curve) - 2):
        if all(point[field] >= threshold for point in curve[index:index + 3]):
            return curve[index]["step"]
    return None


def rows_for(root, scope):
    rows = []
    for episode in root["evaluation_evidence"]["episodes"]:
        for record in episode["solution"]["widths"]:
            if record is None:
                continue
            for arm, observed in record["arms"].items():
                curve = observed["curves"]
                event = record["events"][arm]
                assert sustained(curve, "train_accuracy", .99) == event["memorization_step"]
                assert sustained(curve, "evaluation_accuracy", .95) == event["generalization_step"]
                rows.append({"scope": scope, "seed": episode["seed"], "width": record["width"],
                             "arm": arm, "horizon": record["horizon"],
                             "configuration": record["configuration"],
                             "accuracy": curve[-1]["evaluation_accuracy"],
                             "train_accuracy": curve[-1]["train_accuracy"],
                             "train_loss": curve[-1]["train_loss"],
                             "evaluation_loss": curve[-1]["evaluation_loss"],
                             "fit": event["memorization_step"],
                             "generalize": event["generalization_step"],
                             "delayed_event": event["grokking"],
                             "censored": event["right_censored"],
                             "normalized_capped_delay": event["restricted_delay"],
                             "parameter_count": curve[0]["parameter_count"],
                             "initial_norm": curve[0]["global_norm"],
                             "final_norm": curve[-1]["global_norm"],
                             "initial_hash": observed["initial_state_sha256"],
                             "final_hash": observed["final_state_sha256"],
                             "duration_seconds": observed["duration_seconds"],
                             "updates": observed["updates"]})
    return rows


def export(figure, stem, source_refs):
    for extension in ["pdf", "png"]:
        target = FIGURES / (stem + "." + extension)
        figure.savefig(target, dpi=450 if extension == "png" else 300, facecolor="white")
        provenance(target, source_refs + ["scripts/build_artifacts.py"], "figure")
    plt.close(figure)


def main():
    FIGURES.mkdir(exist_ok=True)
    DERIVED.mkdir(exist_ok=True)
    data = json.loads((ROOT / "paper_data.json").read_text())
    evidence_refs = ["paper_data.json#/best_correct/evaluation_evidence/episodes",
                     "paper_data.json#/final_evaluation/evaluation_evidence/episodes"]
    rows = rows_for(data["best_correct"], "development") + rows_for(data["final_evaluation"], "final")
    save_json(DERIVED / "observations.json", {"rows": rows})
    provenance(DERIVED / "observations.json", evidence_refs)
    summary = {"cells": {}, "paired": {}, "scope": "descriptive; conditional on retained records"}
    for scope in ["development", "final"]:
        for width in WIDTHS:
            group = [row for row in rows if row["scope"] == scope and row["width"] == width and row["arm"] == "candidate"]
            if not group:
                continue
            values = np.array([row["accuracy"] for row in group])
            successes = sum(row["delayed_event"] for row in group)
            count = len(group)
            interval = [0.0 if not successes else float(beta.ppf(.025, successes, count - successes + 1)),
                        1.0 if successes == count else float(beta.ppf(.975, successes + 1, count - successes))]
            summary["cells"][scope + "_" + str(width)] = {
                "n": count, "seeds": [row["seed"] for row in group],
                "accuracy_mean": float(values.mean()), "accuracy_sd": float(values.std(ddof=1)) if count > 1 else None,
                "accuracy_values": values.tolist(), "fit_values": [row["fit"] for row in group],
                "generalize_values": [row["generalize"] for row in group],
                "event_count": successes, "conditional_exact_95_interval": interval,
            }
    for scope in ["development", "final"]:
        for low, high in [(32, 128), (32, 256)]:
            indexed = {(row["seed"], row["width"]): row for row in rows if row["scope"] == scope and row["arm"] == "candidate"}
            seeds = sorted({seed for seed, width in indexed if width == low and (seed, high) in indexed})
            if seeds:
                summary["paired"][f"{scope}_{high}_minus_{low}"] = {
                    "seeds": seeds, "accuracy_differences": [indexed[seed, high]["accuracy"] - indexed[seed, low]["accuracy"] for seed in seeds],
                    "fit_differences": [indexed[seed, high]["fit"] - indexed[seed, low]["fit"] for seed in seeds],
                }
    final_rows = [row for row in rows if row["scope"] == "final" and row["arm"] == "candidate"]
    assert len(final_rows) == len({(row["seed"], row["width"]) for row in final_rows})
    summary["final_available_cells"] = len(final_rows)
    summary["final_planned_cells"] = len(data["final_evaluation"]["evaluation_evidence"]["episodes"]) * len(WIDTHS)
    summary["final_event_count"] = sum(row["delayed_event"] for row in final_rows)
    summary["final_observed_endpoint_mean"] = float(np.mean([row["accuracy"] for row in final_rows]))
    summary["qualification"] = {key: data["final_evaluation"][key] for key in ["status", "outcome", "correct"]}
    summary["runtime_by_scope_seconds"] = {scope: [episode["duration_seconds"] for episode in data[key]["evaluation_evidence"]["episodes"]]
                                                  for scope, key in [("development", "best_correct"), ("final", "final_evaluation")]}
    save_json(DERIVED / "summary.json", summary)
    provenance(DERIVED / "summary.json", evidence_refs)
    plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
                         "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
                         "legend.fontsize": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.55), sharey=True)
    for axis, scope, title in zip(axes, ["development", "final"], ["(a) Development: 6,000 updates", "(b) Final: 24,000 updates"]):
        for position, width in enumerate(WIDTHS):
            for arm_index, arm in enumerate(ARMS):
                group = [row for row in rows if row["scope"] == scope and row["width"] == width and row["arm"] == arm]
                for seed_index, row in enumerate(group):
                    offset = (arm_index - 1.5) * .17 + (seed_index - (len(group) - 1) / 2) * .035
                    axis.scatter(position + offset, 100 * row["accuracy"], s=23, marker=["o", "s", "v", "D"][arm_index],
                                 color=COLORS[arm_index], edgecolor="white", linewidth=.35, zorder=3)
            if scope == "final" and width == 256:
                axis.text(position, 50, "missing\n3/3", ha="center", va="center", fontsize=8.5, color="#555555")
            if scope == "final" and width == 128:
                axis.text(position, 64, "missing 1/3", ha="center", fontsize=8.5, color="#555555")
        axis.set(xlim=(-.5, 2.5), ylim=(-3, 104), xticks=range(3), xticklabels=WIDTHS, xlabel="Hidden width", title=title)
        axis.grid(axis="y", color="#e7e7e7", linewidth=.6, zorder=0)
    axes[0].set_ylabel("Held-out accuracy (%)")
    legend = [plt.Line2D([], [], linestyle="none", marker=marker, color=color, markersize=4.5, label=label)
              for marker, color, label in zip(["o", "s", "v", "D"], COLORS, LABELS)]
    figure.legend(handles=legend, loc="lower center", ncol=4, frameon=False, handletextpad=.3, columnspacing=.7)
    figure.subplots_adjust(left=.12, right=.99, bottom=.29, top=.87, wspace=.13)
    export(figure, "width_endpoint_comparison", evidence_refs)
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.55), sharey=True)
    for axis, scope, title in zip(axes, ["development", "final"], ["(a) Development: H = 6,000", "(b) Final: H = 24,000"]):
        group = [row for row in rows if row["scope"] == scope and row["arm"] == "candidate"]
        horizon = max(row["horizon"] for row in group)
        seeds = sorted({row["seed"] for row in group})
        for row in group:
            vertical = WIDTHS.index(row["width"]) + (seeds.index(row["seed"]) - (len(seeds) - 1) / 2) * .16
            axis.scatter(row["fit"], vertical, color=COLORS[0], s=24, marker="o", zorder=3)
            if row["generalize"] is not None:
                axis.plot([row["fit"], row["generalize"]], [vertical, vertical], color="#aaaaaa", linewidth=.8)
                axis.scatter(row["generalize"], vertical, color=COLORS[2], s=32, marker="*", zorder=3)
            else:
                axis.annotate("", xy=(horizon, vertical), xytext=(horizon * .93, vertical),
                              arrowprops={"arrowstyle": "->", "color": COLORS[2], "lw": 1.2})
        if scope == "final":
            axis.text(horizon * .50, 2, "all missing", ha="center", va="center", fontsize=8.5)
        axis.set(xlim=(-.025 * horizon, horizon * 1.04), ylim=(2.4, -.45), yticks=range(3), yticklabels=WIDTHS,
                 xlabel="Optimizer updates", title=title)
        axis.set_xticks([0, horizon / 2, horizon], labels=["0", f"{horizon // 2000}k", f"{horizon // 1000}k"])
        axis.grid(axis="x", color="#e7e7e7", linewidth=.6)
    axes[0].set_ylabel("Hidden width")
    handles = [plt.Line2D([], [], linestyle="none", color=COLORS[0], marker="o", label="Training fit"),
               plt.Line2D([], [], linestyle="none", color=COLORS[2], marker="*", label="Held-out onset"),
               plt.Line2D([], [], linestyle="none", color=COLORS[2], marker=r"$\rightarrow$", markersize=10, label="Censored at H")]
    figure.legend(handles=handles, loc="lower center", ncol=3, frameon=False, handletextpad=.3, columnspacing=.8)
    figure.subplots_adjust(left=.11, right=.98, bottom=.29, top=.87, wspace=.16)
    export(figure, "fit_and_generalization_onsets", evidence_refs)
    planned = json.loads((ROOT / "paper_strategy.json").read_text())["figure_specs"]
    concept_id = next(item["figure_id"] for item in planned if item["preferred_generator"] == "generate-concept-figure")
    prompt_path = FIGURES / (concept_id + ".prompts.json")
    already_rendered = (ROOT / ".concept_figure_complete").exists()
    if prompt_path.exists():
        already_rendered = already_rendered or bool(json.loads(prompt_path.read_text()))
    if not already_rendered and not (FIGURES / (concept_id + ".png")).exists():
        figure = plt.figure(figsize=(8, 2.0))
        figure.text(.5, .5, "Concept overview pending orchestrator rendering", ha="center", va="center", fontsize=14)
        figure.savefig(FIGURES / (concept_id + ".png"), dpi=300, facecolor="white")
        plt.close(figure)
        save_json(prompt_path, {})
    manifest_path = ROOT / "figure_manifest.json"
    existing_figures = {}
    if manifest_path.exists():
        existing_figures = {item["figure_id"]: item for item in json.loads(manifest_path.read_text())["figures"]}
    manifest = {"figures": []}
    for spec in planned:
        identifier = spec["figure_id"]
        conceptual = spec["preferred_generator"] == "generate-concept-figure"
        files = {"png": "figures/" + identifier + ".png"}
        if not conceptual:
            files["pdf"] = "figures/" + identifier + ".pdf"
        entry = {"figure_id": identifier, "figure_type": spec["figure_type"],
                 "generator": spec["preferred_generator"], "files": files, "panel_count": 2,
                 "panels_per_row": 2, "panels": [{"panel_id": name, "category_count": 3 if not conceptual else 4,
                 "series_count": 4 if identifier == "width_endpoint_comparison" or conceptual else 2} for name in ["a", "b"]],
                 "uses_progression": False, "uses_abbrev_labels": True, "source_ids": spec["source_ids"],
                 "placement": "full_width", "intended_latex_width_fraction": 1.0,
                 "min_font_size_pt": 8.5, "estimated_min_rendered_font_pt": 8.5, "required": True}
        if conceptual:
            entry["prompt_log_path"] = "figures/" + identifier + ".prompts.json"
            entry["note"] = "Orchestrator-owned rendering; current placeholder is not a scientific result."
            if identifier in existing_figures:
                entry = existing_figures[identifier]
        manifest["figures"].append(entry)
    save_json(ROOT / "figure_manifest.json", manifest)
    provenance(ROOT / "figure_manifest.json", evidence_refs + ["paper_strategy.json#/figure_specs"])
    header = "\\begin{tabular}{rrrrrr}\n\\toprule\nSeed & Width & Arm & Accuracy (\\%) & Fit & Onset \\\\\n\\midrule\n"
    table = []
    for row in rows:
        if row["scope"] != "final":
            continue
        label = {"candidate": "S", "fixed_reference": "R", "zero_decay": "Z", "initial_norm": "N"}[row["arm"]]
        fit = str(row["fit"]) if row["fit"] is not None else "--"
        onset = str(row["generalize"]) if row["generalize"] is not None else "$>24000$"
        table.append(f'{row["seed"]} & {row["width"]} & {label} & {100 * row["accuracy"]:.3f} & {fit} & {onset} \\\\')
    target = DERIVED / "final_records.tex"
    target.write_text(header + "\n".join(table) + "\n\\bottomrule\n\\end{tabular}\n")
    provenance(target, ["derived/observations.json"], "table")
    norm_table = ["\\begin{tabular}{rrrrrr}", "\\toprule", "Seed & Width & Initial norm & Final norm & Train loss & Held-out loss \\\\", "\\midrule"]
    for row in final_rows:
        norm_table.append(f'{row["seed"]} & {row["width"]} & {row["initial_norm"]:.2f} & {row["final_norm"]:.2f} & {row["train_loss"]:.3g} & {row["evaluation_loss"]:.3f} \\\\')
    norm_table.extend(["\\bottomrule", "\\end{tabular}"])
    target = DERIVED / "norm_loss_records.tex"
    target.write_text("\n".join(norm_table) + "\n")
    provenance(target, ["derived/observations.json"], "table")
    coverage_table = [r"\begin{tabular}{lccc}", r"\toprule", r"Seed & Width 32 & Width 128 & Width 256 \\", r"\midrule"]
    for episode in data["final_evaluation"]["evaluation_evidence"]["episodes"]:
        available = {record["width"]: record for record in episode["solution"]["widths"] if record is not None}
        states = ["M" if width not in available else "D" if available[width]["events"]["candidate"]["grokking"] else "C" for width in WIDTHS]
        coverage_table.append(str(episode["seed"]) + " & " + " & ".join(states) + r" \\")
    coverage_table.extend([r"\bottomrule", r"\end{tabular}"])
    target = DERIVED / "coverage_table.tex"
    target.write_text("\n".join(coverage_table) + "\n")
    provenance(target, evidence_refs, "table")
    development_table = [r"\begin{tabular}{lrrr}", r"\toprule", r"Width & Parameters & Training-fit onsets & Held-out accuracy (\%) \\", r"\midrule"]
    for width in WIDTHS:
        cell = summary["cells"]["development_" + str(width)]
        parameter_count = next(row["parameter_count"] for row in rows if row["scope"] == "development" and row["width"] == width)
        onsets = "; ".join(f"{value:,}" for value in cell["fit_values"])
        accuracy = f'{100 * cell["accuracy_mean"]:.2f}'
        deviation = f'{100 * cell["accuracy_sd"]:.2f}'
        development_table.append(f'{width} & {parameter_count:,} & {onsets} & $' + accuracy + r"\pm" + deviation + r"$ \\")
    development_table.extend([r"\bottomrule", r"\end{tabular}"])
    target = DERIVED / "development_table.tex"
    target.write_text("\n".join(development_table) + "\n")
    provenance(target, evidence_refs + ["derived/summary.json"], "table")
    source_manifest = {}
    for source in sorted((ROOT / "source_evidence").rglob("*")):
        if source.is_file():
            source_manifest[str(source.relative_to(ROOT))] = hashlib.sha256(source.read_bytes()).hexdigest()
    save_json(DERIVED / "source_manifest.json", source_manifest)
    assert source_manifest["source_evidence/task/evaluate_final.py"] == data["final_evaluation"]["evaluator_sha256"].removeprefix("sha256:")
    provenance(DERIVED / "source_manifest.json", ["source_evidence/task/evaluate_final.py", "paper_data.json#/final_evaluation/evaluator_sha256"])
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
