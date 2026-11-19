import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binomtest, t

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "paper_data.json"
METHODS = ["candidate", "ppi_plus_plus_mean", "prediction_powered_mean",
           "labeled_only_asymptotic_mean", "labeled_only_exact_binomial"]
LABELS = ["Score control", "PPI++", "PPI", "Label normal", "Exact binomial"]
COLORS = ["#007C83", "#CB6438", "#8E689D", "#758195", "#31548B"]


def provenance(path, inputs=None):
    payload = {
        "schema_name": "scientific-evidence.artifact-manifest",
        "artifact": {"path": str(path.relative_to(ROOT)), "kind": "derived",
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
        "derived_from": inputs or ["@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]"],
        "generated_by": {"script_path": "scripts/build_artifacts.py",
                         "command": ["python", "scripts/build_artifacts.py"]},
    }
    Path(str(path) + ".prov.json").write_text(json.dumps(payload, indent=2) + "\n")


def save_panel(figure, name):
    for axis in figure.axes:
        axis.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(axis.get_xticks()))
    scale = 8 / figure.get_figwidth()
    figure.set_size_inches(8, figure.get_figheight() * scale)
    for text in figure.findobj(match=matplotlib.text.Text):
        text.set_fontsize(text.get_fontsize() * scale)
    for extension in ["pdf", "png"]:
        path = ROOT / "figures" / f"{name}.{extension}"
        figure.savefig(path, dpi=300, facecolor="white")
        provenance(path, inputs=["@evidence[[analysis_results.json#/cases]]"])
    plt.close(figure)


def mean_interval(values):
    values = np.asarray(values)
    center = float(values.mean())
    margin = float(t.ppf(.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values)))
    return {"mean": center, "lower95": center - margin, "upper95": center + margin}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--figures-only", action="store_true")
    args = parser.parse_args()
    if args.figures_only:
        render_figures(json.loads((ROOT / "analysis_results.json").read_text())["cases"])
        return
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    data = json.loads(DATA.read_text())
    episodes = data["final_evaluation"]["evaluation_evidence"]["episodes"]
    summaries = episodes[0]["solution"]["case_summaries"]
    results = []
    for position, reference in enumerate(summaries):
        records = [episode["solution"]["cases"][position] for episode in episodes]
        assert all(record["case"] == reference["case"] for record in records)
        truth_values = sorted(set(record["truth"] for record in records))
        row = {"case": reference["case"], "truths": truth_values, "methods": {}, "differences": {}}
        for method in METHODS:
            intervals = [record["response"] if method == "candidate" else record["baselines"][method] for record in records]
            widths = np.array([item["upper"] - item["lower"] for item in intervals])
            covered = np.array([item["lower"] <= record["truth"] <= item["upper"] for item, record in zip(intervals, records)])
            bounds = binomtest(int(covered.sum()), len(covered)).proportion_ci(method="exact")
            row["methods"][method] = {"coverage": float(covered.mean()), "covered": int(covered.sum()),
                "coverage_lower95": float(bounds.low), "coverage_upper95": float(bounds.high),
                "width": mean_interval(widths), "zero_width_count": int(np.count_nonzero(widths == 0)),
                "widths": widths.tolist()}
        candidate_widths = np.array(row["methods"]["candidate"]["widths"])
        for method in METHODS[1:]:
            row["differences"][method] = mean_interval(candidate_widths - row["methods"][method]["widths"])
            recorded = reference["comparisons"][method]["difference"]
            assert np.isclose(row["differences"][method]["mean"], recorded["mean_difference"], atol=1e-12)
            assert np.isclose(row["differences"][method]["lower95"], recorded["lower95"], atol=1e-10)
        results.append(row)
    out = {"repetitions": len(episodes), "seeds": [episode["seed"] for episode in episodes],
           "case_count": len(results), "cases": results,
           "interpretation": "Pointwise exact binomial coverage intervals; paired t width-difference intervals. No multiplicity correction or new evaluation."}
    path = ROOT / "analysis_results.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    provenance(path)
    headers = "Condition & Score control & PPI++ & PPI & Label normal & Exact binomial"
    coverage_rows = [headers + r" \\", r"\midrule"]
    width_rows = [headers + r" \\", r"\midrule"]
    for row in results:
        coverage_rows.append("C%d & " % row["case"] + " & ".join(f'{row["methods"][method]["coverage"]:.3f}' for method in METHODS) + r" \\")
        width_rows.append("C%d & " % row["case"] + " & ".join(f'{row["methods"][method]["width"]["mean"]:.5f}' for method in METHODS) + r" \\")
    for name, rows in [("coverage", coverage_rows), ("width", width_rows)]:
        path = ROOT / "tables" / f"{name}.tex"
        path.write_text("% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]\n" + "\n".join(rows) + "\n\\bottomrule\n")
        provenance(path)
    extended = []
    for row in results:
        for method, label in zip(METHODS, LABELS):
            value = row["methods"][method]
            extended.append(f'C{row["case"]} & {label} & {value["coverage"]:.3f} [{value["coverage_lower95"]:.3f}, {value["coverage_upper95"]:.3f}] & {value["width"]["mean"]:.5f} & {value["zero_width_count"]}' + r" \\")
        extended.append(r"\midrule")
    path = ROOT / "tables" / "complete.tex"
    path.write_text("% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]\n" + "\n".join(extended) + "\n\\bottomrule\n")
    provenance(path)
    differences = []
    for row in results:
        for method, label in zip(METHODS[1:], LABELS[1:]):
            value = row["differences"][method]
            differences.append(f'C{row["case"]} & {label} & {value["mean"]:+.6f} & [{value["lower95"]:+.6f}, {value["upper95"]:+.6f}]' + r" \\")
        differences.append(r"\midrule")
    path = ROOT / "tables" / "differences.tex"
    path.write_text("% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]\n" + "\n".join(differences) + "\n\\bottomrule\n")
    provenance(path)
    render_figures(results)
    for row in results:
        print("C", row["case"], "truth", row["truths"], "coverage", row["methods"]["candidate"]["coverage"], "width", row["methods"]["candidate"]["width"]["mean"], "PPI++ difference", row["differences"][METHODS[1]])


def render_figures(results):
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
                         "xtick.labelsize": 8.5, "ytick.labelsize": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    plotted = [0, 1, 3, 4]
    figure, axes = plt.subplots(2, 2, figsize=(5.5, 4.3), gridspec_kw={"width_ratios": [1, 1.1]})
    for group_index, indices in enumerate([range(4), range(4, 7)]):
        coverage_axis, width_axis = axes[group_index]
        offsets = np.linspace(-.23, .23, len(plotted))
        for method_index, offset in zip(plotted, offsets):
            for local_index, case_index in enumerate(indices):
                value = results[case_index]["methods"][METHODS[method_index]]
                coverage_axis.errorbar(value["coverage"], local_index + offset,
                    xerr=[[value["coverage"] - value["coverage_lower95"]], [value["coverage_upper95"] - value["coverage"]]],
                    fmt="o", ms=3.4, lw=.8, color=COLORS[method_index], capsize=1.5)
        for method_index, offset in zip([1, 3, 4], [-.18, 0, .18]):
            for local_index, case_index in enumerate(indices):
                value = results[case_index]["differences"][METHODS[method_index]]
                width_axis.errorbar(1000 * value["mean"], local_index + offset,
                    xerr=[[1000 * (value["mean"] - value["lower95"])], [1000 * (value["upper95"] - value["mean"])]],
                    fmt="o", ms=3.4, lw=.8, color=COLORS[method_index], capsize=1.5)
        for axis in [coverage_axis, width_axis]:
            axis.set_yticks(range(len(indices)), [f"C{position + 1}" for position in indices])
            axis.set_ylim(len(indices)-.5, -.5)
            axis.grid(axis="x", alpha=.13)
        coverage_axis.axvline(.95, ls="--", lw=.8, color="#444444")
        coverage_axis.set_xlim((.84, 1.005) if group_index == 0 else (.48, 1.015))
        width_axis.axvline(0, ls="--", lw=.8, color="#444444")
    axes[0, 0].set_title("(a) Coverage: C1–C4", loc="left")
    axes[0, 1].set_title("(b) Width differences: C1–C4", loc="left")
    axes[1, 0].set_title("(c) Coverage: C5–C7", loc="left")
    axes[1, 1].set_title("(d) Width differences: C5–C7", loc="left")
    axes[1, 0].set_xlabel("Empirical coverage")
    axes[1, 1].set_xlabel("Width difference (×10⁻³)")
    handles = [plt.Line2D([], [], color=COLORS[index], marker="o", ms=4, lw=1, label=LABELS[index]) for index in plotted]
    figure.legend(handles=handles, loc="upper center", ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(.51, 1.005))
    figure.subplots_adjust(left=.09, right=.98, bottom=.13, top=.79, wspace=.46, hspace=.62)
    save_panel(figure, "coverage_width_comparison")
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.3), gridspec_kw={"width_ratios": [1.25, 1]})
    rare = results[4]
    for method_index in [0, 1, 2, 4]:
        values = np.sort(rare["methods"][METHODS[method_index]]["widths"])
        axes[0].step(np.r_[0, values], np.r_[0, np.arange(1, len(values)+1)/len(values)], where="post", color=COLORS[method_index], lw=1.25, label=LABELS[method_index])
    axes[0].set(xlabel="Interval width", ylabel="Empirical CDF", ylim=(0, 1.03), xlim=(0, None))
    axes[0].set_title("(a) C5 width distribution", loc="left")
    selected = [0, 1, 2, 4]
    counts = [rare["methods"][METHODS[index]]["zero_width_count"] for index in selected]
    axes[1].barh(range(4), counts, color=[COLORS[index] for index in selected], height=.6)
    axes[1].set_yticks(range(4), [LABELS[index] for index in selected], fontsize=8.5)
    axes[1].invert_yaxis()
    axes[1].set_xlim(0, max(counts)*1.25)
    axes[1].set_xlabel("Zero-width intervals")
    for position, count in enumerate(counts):
        axes[1].text(count + 2, position, str(count), va="center", fontsize=9)
    axes[1].set_title("(b) Collapse counts", loc="left")
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", ncol=4, frameon=False, fontsize=8.5, bbox_to_anchor=(.5, 1.015), handlelength=1.2, columnspacing=.9)
    figure.subplots_adjust(left=.1, right=.99, bottom=.24, top=.73, wspace=.67)
    save_panel(figure, "rare_outcome_diagnostic")
    concept = ROOT / "figures" / "frozen_score_overview.png"
    prompt_log = concept.with_suffix(".prompts.json")
    manifest_path = ROOT / "figure_manifest.json"
    previous_entries = {entry["figure_id"]: entry for entry in
                        json.loads(manifest_path.read_text())["figures"]} if manifest_path.exists() else {}
    previous_concept = previous_entries.get("frozen_score_overview", {})
    fallback = (previous_concept.get("generator") is None
                and previous_concept.get("attempted_generator") == "generate-concept-figure"
                and bool(previous_concept.get("fallback_reason")))
    regenerate_placeholder = (not (ROOT / ".concept_figure_complete").exists()
                              and (not concept.exists() or fallback))
    if regenerate_placeholder:
        from PIL import Image, ImageDraw, ImageFont
        image = Image.new("RGB", (2400, 720), "white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("DejaVuSans.ttf", 64)
        draw.text((50, 320), "Concept figure reserved for synchronous rendering", font=font, fill="#666666")
        image.save(concept)
    if not prompt_log.exists():
        prompt_log.write_text("{}\n")
    figures = []
    specifications = {item["figure_id"]: item for item in
                      json.loads((ROOT / "paper_strategy.json").read_text())["figure_specs"]}
    for name, panels, categories, series, height in [
        ("frozen_score_overview", 1, 4, 2, 1.8),
        ("coverage_width_comparison", 4, 4, 4, 4.3),
        ("rare_outcome_diagnostic", 2, 4, 4, 2.3)]:
        entry = {"figure_id": name, "path_png": f"figures/{name}.png",
                 "figure_type": specifications[name]["figure_type"],
                 "n_panels": panels, "panels_per_row": 1 if panels == 1 else 2,
                 "categories_per_panel": [categories] * panels, "series_per_panel": [series] * panels,
                 "max_label_chars": 30, "font_sizes": {"title": 10, "axis": 9, "legend": 8.5, "ticks": 8.5},
                 "uses_abbrev_labels": True, "uses_progression": False,
                 "source_ids": [] if panels == 1 else ["final.evidence.episodes"],
                 "generator": "generate-concept-figure" if panels == 1 else "matplotlib",
                 "placement": "full_width", "intended_latex_width_fraction": 1.0,
                 "estimated_min_rendered_font_pt": 8.5}
        if panels == 1:
            if previous_concept:
                entry.update(previous_concept)
            if regenerate_placeholder:
                entry["font_sizes"] = {key: 10.56 for key in ["title", "axis", "legend", "ticks"]}
                entry["estimated_min_rendered_font_pt"] = 10.56
            entry["prompt_log_path"] = f"figures/{name}.prompts.json"
        else:
            entry["path_pdf"] = f"figures/{name}.pdf"
        figures.append(entry)
    (ROOT / "figure_manifest.json").write_text(json.dumps({"figures": figures}, indent=2) + "\n")


if __name__ == "__main__":
    main()
