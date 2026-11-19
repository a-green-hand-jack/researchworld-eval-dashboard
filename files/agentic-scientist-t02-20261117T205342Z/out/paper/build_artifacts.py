import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
EPISODE_REF = "@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]"
DECAY_COLORS = {0: "#28628c", 1: "#cb6d32"}
OPERATIONS = ("addition", "subtraction")



def sidecar(path, kind, refs=None):
    payload = {
        "schema_name": "scientific-evidence.artifact-manifest",
        "artifact": {"path": str(path), "kind": kind, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
        "derived_from": refs or [EPISODE_REF, "@evidence[[build_artifacts.py]]"],
        "generated_by": {"script_path": "build_artifacts.py", "command": ["python", "build_artifacts.py"], "cwd": "."},
    }
    Path(str(path) + ".prov.json").write_text(json.dumps(payload, indent=2) + "\n")


def write_output(path, text, kind):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    sidecar(path, kind)


def sustained(trace, field, threshold):
    for index in range(len(trace) - 2):
        if all(point[field] >= threshold for point in trace[index:index + 3]):
            return trace[index]["step"]
    return None


def save_plot(figure, stem):
    figure.savefig(f"figures/{stem}.pdf")
    figure.savefig(f"figures/{stem}.png", dpi=300)
    for suffix in ("pdf", "png"):
        sidecar(Path(f"figures/{stem}.{suffix}"), "figure")
    plt.close(figure)


def overview_placeholder():
    target = Path("figures/study_overview.png")
    log = Path("figures/study_overview.prompts.json")
    if Path(".concept_figure_complete").exists():
        return
    if log.exists() and json.loads(log.read_text() or "{}"):
        return
    if not target.exists():
        image = Image.new("RGB", (2400, 780), "white")
        drawer = ImageDraw.Draw(image)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
        drawer.rectangle((12, 12, 2388, 768), outline="#777777", width=3)
        drawer.text((120, 260), "Study overview reserved for orchestrator rendering", fill="#555555", font=font)
        drawer.text((120, 350), "Not a result plot; see caption for grounded study design", fill="#555555", font=font)
        image.save(target, dpi=(300, 300))
    if not log.exists():
        log.write_text("{}\n")


def main():
    paper_data = json.loads(Path("paper_data.json").read_text())
    episodes = paper_data["final_evaluation"]["evaluation_evidence"]["episodes"]
    widths = tuple(sorted({record["case"]["width"] for episode in episodes for record in episode["solution"]}))
    records = []
    grouped = defaultdict(list)
    for episode in episodes:
        for record in episode["solution"]:
            case, observed = record["case"], record["observations"]
            trace = observed["trace"]
            horizon = trace[-1]["step"]
            memorization = sustained(trace, "train_accuracy", .99)
            generalization = sustained(trace, "heldout_accuracy", .95)
            lag = horizon if memorization is None else max(0, (horizon if generalization is None else generalization) - memorization)
            assert (memorization, generalization, lag) == (observed["memorization"], observed["generalization"], observed["lag"])
            late = trace[-5:]
            row = dict(case, memorization=memorization, generalization=generalization, lag=lag,
                       late_train=statistics.fmean(point["train_accuracy"] for point in late),
                       late_heldout=statistics.fmean(point["heldout_accuracy"] for point in late),
                       complete=observed["complete"], parameter_count=trace[0]["parameter_count"],
                       final_train_loss=trace[-1]["train_loss"], final_heldout_loss=trace[-1]["heldout_loss"],
                       initial_norm=trace[0]["weight_norm"], final_norm=trace[-1]["weight_norm"],
                       controls={name: statistics.fmean(point["controls"][name] for point in late) for name in late[0]["controls"]})
            assert abs(row["late_heldout"] - observed["score"]) < 1e-12
            records.append(row)
            grouped[(case["operation"], case["decay"], case["width"])].append(row)
    seeds = sorted({row["seed"] for row in records})
    summaries = []
    for (operation, decay, width), rows in grouped.items():
        summaries.append({"operation": operation, "decay": decay, "width": width,
                          "memorization": [row["memorization"] for row in rows],
                          "generalization_count": sum(row["generalization"] is not None for row in rows),
                          "mean_train_percent": 100 * statistics.fmean(row["late_train"] for row in rows),
                          "mean_heldout_percent": 100 * statistics.fmean(row["late_heldout"] for row in rows),
                          "sd_heldout_percent": 100 * statistics.stdev(row["late_heldout"] for row in rows),
                          "mean_lag": statistics.fmean(row["lag"] for row in rows)})
    contrasts = {}
    for decay in (0, 1):
        contrasts[decay] = [statistics.fmean(next(row["lag"] for row in records if row["seed"] == seed and row["operation"] == operation and row["decay"] == decay and row["width"] == 16)
                               - next(row["lag"] for row in records if row["seed"] == seed and row["operation"] == operation and row["decay"] == decay and row["width"] == 256)
                               for operation in OPERATIONS) for seed in seeds]
    metrics = paper_data["final_evaluation"]["metrics"]
    assert statistics.fmean(contrasts[1]) == metrics["width_lag_contrast"]
    assert abs(statistics.fmean(contrasts[1]) - statistics.fmean(contrasts[0]) - metrics["decay_interaction"]) < 1e-10
    assert abs(statistics.fmean(row["lag"] for row in records) - metrics["restricted_mean_lag"]) < 1e-10
    derived = {"seeds": seeds, "records": records, "conditions": summaries, "paired_contrasts": contrasts,
               "memorization_count": sum(row["memorization"] is not None for row in records),
               "generalization_count": sum(row["generalization"] is not None for row in records),
               "complete_count": sum(row["complete"] for row in records),
               "horizon": horizon, "overall_heldout_percent": 100 * statistics.fmean(row["late_heldout"] for row in records),
               "control_means_percent": {name: 100 * statistics.fmean(row["controls"][name] for row in records) for name in records[0]["controls"]},
               "duration_seconds_by_seed": {episode["seed"]: episode["duration_seconds"] for episode in episodes}}
    write_output("analysis/derived_results.json", json.dumps(derived, indent=2) + "\n", "derived")

    heading = r"Operation & $\lambda$ & Width & " + " & ".join(f"$T_M^{{({seed})}}$" for seed in seeds) + r" & $G$ observed \\"
    event_lines = ["% " + EPISODE_REF, r"\begin{tabular}{llrrrrr}", r"\toprule", heading, r"\midrule"]
    for entry in summaries:
        values = [r"\textemdash" if value is None else f"{value:,}" for value in entry["memorization"]]
        event_lines.append(f"{entry['operation'].capitalize()} & {entry['decay']} & {entry['width']} & " + " & ".join(values) + f" & {entry['generalization_count']}/3 " + r"\\")
    event_lines.extend([r"\bottomrule", r"\end{tabular}"])
    write_output("tables/events.tex", "\n".join(event_lines) + "\n", "table")

    full_lines = ["% " + EPISODE_REF, r"\begin{longtable}{llrrrrrr}", r"\toprule", r"Op. & $\lambda$ & Width & Seed & $T_M$ & $L_H$ & Train (\%) & Held-out (\%) \\", r"\midrule\endhead"]
    for row in sorted(records, key=lambda entry: (entry["operation"], entry["decay"], entry["width"], entry["seed"])):
        value = r"\textemdash" if row["memorization"] is None else str(row["memorization"])
        full_lines.append(f"{row['operation'][:3]}. & {row['decay']} & {row['width']} & {row['seed']} & {value} & {row['lag']} & {100*row['late_train']:.3f} & {100*row['late_heldout']:.3f} " + r"\\")
    full_lines.extend([r"\bottomrule", r"\end{longtable}"])
    write_output("tables/full_observations.tex", "\n".join(full_lines) + "\n", "table")

    diagnostic_lines = ["% " + EPISODE_REF, r"\begin{tabular}{llrrrr}", r"\toprule", r"Op. & $\lambda$ & Width & Train CE & Held-out CE & Weight norm \\", r"\midrule"]
    for (operation, decay, width), rows in grouped.items():
        values = [statistics.fmean(row[key] for row in rows) for key in ("final_train_loss", "final_heldout_loss", "final_norm")]
        diagnostic_lines.append(f"{operation.capitalize()} & {decay} & {width} & " + " & ".join(f"{value:.3g}" for value in values) + r" \\")
    diagnostic_lines.extend([r"\bottomrule", r"\end{tabular}"])
    write_output("tables/diagnostics.tex", "\n".join(diagnostic_lines) + "\n", "table")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13.5, "axes.titlesize": 14,
                         "axes.labelsize": 13.5, "xtick.labelsize": 13.5, "ytick.labelsize": 13.5,
                         "legend.fontsize": 13.5, "pdf.fonttype": 42, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.linewidth": .8})
    figure, axes = plt.subplots(2, 2, figsize=(8.25, 5.15), sharex=True, sharey="row")
    figure.subplots_adjust(left=.13, right=.98, top=.84, bottom=.14, hspace=.28, wspace=.13)
    for column, operation in enumerate(OPERATIONS):
        for row_index, metric in enumerate(("late_train", "late_heldout")):
            axis = axes[row_index, column]
            for decay in (0, 1):
                for width_index, width in enumerate(widths):
                    rows = grouped[(operation, decay, width)]
                    xcenter = width_index + (-.12 if decay == 0 else .12)
                    values = [100 * row[metric] for row in rows]
                    for seed_index, value in enumerate(values):
                        axis.plot(xcenter + (seed_index-1)*.035, value, marker=("o", "s", "^")[seed_index], color=DECAY_COLORS[decay], ms=5, ls="none", alpha=.85)
                    axis.plot([xcenter-.075, xcenter+.075], [statistics.fmean(values)]*2, lw=2, color=DECAY_COLORS[decay])
            axis.set_xticks(range(len(widths)), [str(width) for width in widths])
            axis.set_xlim(-.4, 2.4)
            axis.grid(axis="y", alpha=.18)
            axis.set_title(f"({chr(97 + row_index*2 + column)}) {operation.capitalize()}", loc="left", pad=5)
            if row_index == 0:
                axis.set_ylim(45, 103)
                axis.set_yticks([50, 75, 100])
            else:
                axis.set_ylim(-.025, .60)
                axis.set_yticks([0, .2, .4, .6])
                axis.set_xlabel("Hidden width")
            if column == 0:
                axis.set_ylabel("Train accuracy (%)" if row_index == 0 else "Held-out accuracy (%)")
    handles = [plt.Line2D([], [], marker="o", ls="none", color=DECAY_COLORS[decay], label=f"Decay {decay}") for decay in (0, 1)]
    figure.legend(handles=handles, loc="upper center", bbox_to_anchor=(.53, 1), ncol=2, frameon=False)
    save_plot(figure, "width_decay_outcomes")

    figure, axes = plt.subplots(1, 2, figsize=(8.25, 3.2), sharey=True)
    figure.subplots_adjust(left=.15, right=.98, top=.78, bottom=.22, wspace=.17)
    for decay, axis in enumerate(axes):
        for operation_index, operation in enumerate(OPERATIONS):
            marker = ("o", "s")[operation_index]
            for width_index, width in enumerate(widths):
                rows = grouped[(operation, decay, width)]
                xcenter = width_index + (-.10 if operation_index == 0 else .10)
                for seed_index, row in enumerate(rows):
                    axis.scatter(xcenter + (seed_index-1)*.045, row["lag"], marker=marker, s=35,
                                 facecolor="#444444" if row["memorization"] is not None else "white", edgecolor="#444444", zorder=3)
                center = statistics.fmean(row["lag"] for row in rows)
                axis.plot([xcenter-.07, xcenter+.07], [center]*2, color="#111111", lw=1.6)
        axis.set_title(f"({chr(97+decay)}) Decay {decay}", loc="left")
        axis.set_xticks(range(len(widths)), [str(width) for width in widths])
        axis.set_xlim(-.4, 2.4)
        axis.set_ylim(18350, 20230)
        axis.set_yticks([18500, 19000, 19500, 20000], ["18,500", "19,000", "19,500", "20,000"])
        axis.set_xlabel("Hidden width")
        axis.grid(axis="y", alpha=.18)
    axes[0].set_ylabel("Capped lag (updates)")
    handles = [plt.Line2D([], [], marker=marker, ls="none", color="#444444", label=operation.capitalize()) for operation, marker in zip(OPERATIONS, ("o", "s"))]
    figure.legend(handles=handles, ncol=2, frameon=False, loc="upper center", bbox_to_anchor=(.53, 1.03))
    save_plot(figure, "censoring_audit")
    overview_placeholder()

    manifest = {"figures": []}
    for figure_id, figure_type, panel_count, categories, series in [
        ("study_overview", "diagram", 2, 3, 1),
        ("width_decay_outcomes", "composite", 4, 3, 2),
        ("censoring_audit", "composite", 2, 3, 2),
    ]:
        entry = {"figure_id": figure_id, "figure_type": figure_type, "path_png": f"figures/{figure_id}.png",
                 "n_panels": panel_count, "panels_per_row": 2, "categories_per_panel": [categories] * panel_count,
                 "series_per_panel": [series] * panel_count, "max_label_chars": 28,
                 "font_sizes": {"title": 14, "axis": 13.5, "ticks": 13.5, "legend": 13.5},
                 "uses_abbrev_labels": False, "uses_progression": False,
                 "generator": "generate-concept-figure" if figure_id == "study_overview" else "matplotlib",
                 "source_ids": ["final.evidence.episodes"], "placement": "full_width",
                 "intended_latex_width_fraction": 1.0, "estimated_min_rendered_font_pt": 9.0}
        if figure_id == "study_overview":
            entry["prompt_log_path"] = "figures/study_overview.prompts.json"
        else:
            entry["path_pdf"] = f"figures/{figure_id}.pdf"
        manifest["figures"].append(entry)
    write_output("figure_manifest.json", json.dumps(manifest, indent=2) + "\n", "derived")


if __name__ == "__main__":
    main()
