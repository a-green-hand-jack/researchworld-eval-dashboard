import collections
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
RULES = ["mean", "median", "trimmed"]
LABELS = {"mean": "Mean", "median": "Median", "trimmed": "Trimmed"}
COLORS = {"mean": "#2468A0", "median": "#D56732", "trimmed": "#4A8858"}
SOURCE = "final.evidence.episodes"


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def provenance(path, inputs):
    write_json(str(path) + ".prov.json", {
        "schema_name": "scientific-evidence.artifact-manifest",
        "artifact": {"path": str(path), "kind": "figure" if str(path).startswith("figures") else "derived",
                     "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()},
        "derived_from": ["@evidence" + "[[" + item + "]]" for item in inputs],
        "generated_by": {"script_path": "scripts/build_paper_artifacts.py",
                         "command": ["python", "scripts/build_paper_artifacts.py"], "cwd": "."},
    })


def attained(row):
    return row["verified_feasible"] and row["exact_audit_pass"]


def main():
    Path("derived").mkdir(exist_ok=True)
    Path("figures").mkdir(exist_ok=True)
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    registry = json.loads(Path("paper_data.json").read_text())
    final = registry["final_evaluation"]
    episodes = final["evaluation_evidence"]["episodes"]
    seeds = [episode["seed"] for episode in episodes]
    rows = []
    intervals = []
    controls = []
    for episode in episodes:
        intervals.extend(dict(item, seed=episode["seed"]) for item in episode["solution"]["paired_intervals"])
        for block in episode["solution"]["episodes"]:
            if block["case"] == "ordinary":
                rows.extend(dict(row, family=block["family"], seed=episode["seed"]) for row in block["decisions"])
            else:
                controls.append({"seed": episode["seed"], "family": block["family"], "case": block["case"],
                                 "valid": block["valid"], "decisions": len(block["decisions"]),
                                 "passed": sum(row["exact_audit_pass"] for row in block["decisions"])})
    primary = [row for row in rows if row["panel"] == "primary"]
    central = []
    for seed in seeds:
        cells = {(row["slot"], row["rule"], row["alpha"]): row for row in primary
                 if row["family"] == "openllm" and row["seed"] == seed}
        slots = sorted({slot for slot, _, _ in cells if all(attained(cells[slot, rule, alpha])
                         for rule in ["mean", "median"] for alpha in [.5, 1.0])})
        contrasts = {}
        for alpha in [.5, 1.0]:
            chosen = [cells[slot, rule, alpha] for slot in slots for rule in ["mean", "median"]]
            assert all(row["status"] == "optimal" and row["lower"] == row["upper"] for row in chosen)
            values = [(cells[slot, "median", alpha]["upper"] - cells[slot, "mean", alpha]["upper"])/6
                      for slot in slots]
            contrasts[str(alpha)] = {"mean": float(np.mean(values)), "individual": values,
                                    "median_support": float(np.mean([cells[slot, "median", alpha]["upper"] for slot in slots])),
                                    "mean_support": float(np.mean([cells[slot, "mean", alpha]["upper"] for slot in slots]))}
        central.append({"seed": seed, "count": len(slots), "slots": slots, "contrasts": contrasts})
    grid = []
    support = []
    for family, size in [("helm", 57), ("openllm", 6)]:
        for alpha in [.25, .5, 1.0]:
            for rule in RULES:
                selected = [row for row in primary if row["family"] == family and row["alpha"] == alpha and row["rule"] == rule]
                grid.append({"family": family, "alpha": alpha, "rule": rule, "count": len(selected),
                             "attained": sum(attained(row) for row in selected),
                             "rate": float(np.mean([attained(row) for row in selected])),
                             "statuses": dict(collections.Counter(row["status"] for row in selected)),
                             "selected_effort": float(np.mean([row["effort_fraction"] for row in selected])),
                             **{policy + "_effort": float(np.mean([row["baseline"][policy]["effort_fraction"] for row in selected]))
                                for policy in ["zero", "random", "greedy"]}})
            if alpha == .25:
                continue
            groups = []
            for seed in seeds:
                cells = {(row["slot"], row["rule"]): row for row in primary
                         if row["family"] == family and row["seed"] == seed and row["alpha"] == alpha}
                slots = sorted({slot for slot, _ in cells if all(attained(cells[slot, rule]) for rule in RULES)})
                groups.append({"seed": seed, "count": len(slots),
                               "rules": {rule: {"lower": float(np.mean([cells[slot, rule]["lower"]/size for slot in slots])),
                                                "upper": float(np.mean([cells[slot, rule]["upper"]/size for slot in slots]))}
                                         for rule in RULES}})
            support.append({"family": family, "alpha": alpha, "counts": [group["count"] for group in groups],
                            "rules": {rule: {bound: float(np.mean([group["rules"][rule][bound] for group in groups]))
                                             for bound in ["lower", "upper"]} for rule in RULES}, "by_seed": groups})
    auxiliary = []
    for family, kind, selector in [("helm", "six-coordinate projection", lambda row: True),
                                   ("openllm", "six-task auxiliary", lambda row: row["slot"] % 2 == 0),
                                   ("openllm", "BBH 24-subtask sensitivity", lambda row: row["slot"] % 2 == 1)]:
        selected = [row for row in rows if row["family"] == family and row["panel"] == "auxiliary" and selector(row)]
        for rule in RULES:
            for alpha in [.25, .5, 1.0]:
                subset = [row for row in selected if row["rule"] == rule and row["alpha"] == alpha]
                auxiliary.append({"family": family, "kind": kind, "rule": rule, "alpha": alpha, "count": len(subset),
                                  "attained": sum(attained(row) for row in subset),
                                  "bounded": sum(row["status"] == "bounded" for row in subset)})
    # @evidence[[source_evidence/data/records.json]]
    # @evidence[[source_evidence/data/manifest.json]]
    records_path = Path("source_evidence/data/records.json")
    resources = json.loads(records_path.read_text())
    manifest = json.loads(Path("source_evidence/data/manifest.json").read_text())
    assert hashlib.sha256(records_path.read_bytes()).hexdigest() == manifest["data_sha256"]
    pool_counts = dict(collections.Counter(row["family"] for row in resources["records"]))
    pool_counts["bbh"] = sum(row.get("results") is not None for row in resources["records"])
    summary = {"seeds": seeds, "central": central, "grid": grid, "support": support,
               "auxiliary": auxiliary, "paired_intervals": intervals, "controls": controls,
               "pool_counts": pool_counts, "final_status": final["status"], "final_outcome": final["outcome"]}
    write_json("derived/summary.json", summary)
    provenance("derived/summary.json", ["paper_data.json#/final_evaluation/evaluation_evidence/episodes",
                                           "source_evidence/data/records.json", "source_evidence/data/manifest.json"])
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.labelsize": 10,
                         "axes.titlesize": 10, "xtick.labelsize": 9, "ytick.labelsize": 9,
                         "legend.fontsize": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42})
    figures = []
    def save(figure, identifier, panel_count, categories, series):
        for extension in ["pdf", "png"]:
            path = "figures/" + identifier + "." + extension
            figure.savefig(path, dpi=300, facecolor="white")
            provenance(path, ["derived/summary.json"])
        figures.append({"figure_id": identifier, "figure_type": "composite", "path_pdf": "figures/"+identifier+".pdf",
                        "path_png": "figures/"+identifier+".png", "n_panels": panel_count, "panels_per_row": 2,
                        "categories_per_panel": [categories]*panel_count, "series_per_panel": [series]*panel_count, "max_label_chars": 28,
                        "font_sizes": {"axis": 10, "ticks": 9, "legend": 9, "title": 10},
                        "uses_abbrev_labels": True, "uses_progression": False, "generator": "matplotlib",
                        "source_ids": [SOURCE], "placement": "full_width", "intended_latex_width_fraction": 1.0,
                        "estimated_min_rendered_font_pt": 9})
        plt.close(figure)
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.25), sharey=True)
    for axis, alpha, title in zip(axes, [.5, 1.0], ["(a) Half headroom", "(b) Full headroom"]):
        values = [item["contrasts"][str(alpha)]["mean"] for item in central]
        axis.axhline(0, color="0.45", linewidth=.8)
        axis.scatter(range(len(seeds)), values, s=45, color=COLORS["median"], zorder=3)
        axis.set_xticks(range(len(seeds)), [str(seed) for seed in seeds])
        axis.set_ylim(-.18, .20)
        axis.set_title(title)
        axis.set_xlabel("Sampling seed")
    axes[0].set_ylabel("Median − mean support fraction")
    figure.tight_layout(pad=.7, w_pad=1.0)
    save(figure, "exact_rule_contrast", 2, 3, 1)
    figure, axes = plt.subplots(2, 2, figsize=(5.5, 3.7))
    for row_index, family in enumerate(["helm", "openllm"]):
        left, right = axes[row_index]
        for rule_index, rule in enumerate(RULES):
            delta = (rule_index-1)*.13
            points = [next(item for item in grid if item["family"] == family and item["rule"] == rule and item["alpha"] == alpha)
                      for alpha in [.25, .5, 1.0]]
            left.scatter(np.arange(3)+delta, [point["rate"] for point in points], color=COLORS[rule], s=24, label=LABELS[rule])
            points = [next(item for item in support if item["family"] == family and item["alpha"] == alpha) for alpha in [.5, 1.0]]
            lower = np.array([point["rules"][rule]["lower"] for point in points])
            upper = np.array([point["rules"][rule]["upper"] for point in points])
            positions = np.arange(2)+delta
            right.errorbar(positions, (lower+upper)/2, yerr=(upper-lower)/2,
                           fmt="none", color=COLORS[rule], capsize=3)
            exact = np.isclose(lower, upper)
            right.scatter(positions[exact], lower[exact], color=COLORS[rule], s=20)
        left.set_xticks(range(3), [".25", ".50", "1.00"])
        right.set_xticks(range(2), [".50", "1.00"])
        for axis in [left, right]:
            axis.set_ylim(-.03, 1.03)
            axis.set_yticks([0, .5, 1])
        left.set_ylabel("Attainment rate")
        right.set_ylabel("Support fraction")
        name = "HELM (57)" if family == "helm" else "Open LLM (6)"
        left.set_title(f"({chr(97+row_index*2)}) {name}: all targets")
        right.set_title(f"({chr(98+row_index*2)}) Jointly attainable")
        if row_index == 1:
            left.set_xlabel("Headroom fraction α")
            right.set_xlabel("Headroom fraction α")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(.52, 1.015))
    figure.tight_layout(rect=[0, 0, 1, .95], pad=.6, w_pad=.8, h_pad=.8)
    save(figure, "attainability_and_support_scope", 4, 3, 3)
    concept = Path("figures/investment_overview.png")
    prompts = Path("figures/investment_overview.prompts.json")
    if not Path(".concept_figure_complete").exists() and not concept.exists():
        image = Image.new("RGB", (2400, 780), "white")
        draw = ImageDraw.Draw(image)
        draw.text((70, 365), "Concept figure reserved for synchronous rendering", fill="gray")
        image.save(concept)
        prompts.write_text("{}\n")
    figures.insert(0, {"figure_id": "investment_overview", "figure_type": "diagram", "path_png": str(concept),
                       "n_panels": 1, "panels_per_row": 1, "categories_per_panel": [6], "series_per_panel": [3],
                       "max_label_chars": 40, "font_sizes": {"axis": 10, "ticks": 9, "legend": 9, "title": 10}, "uses_abbrev_labels": False,
                       "uses_progression": False, "generator": "generate-concept-figure", "source_ids": [],
                       "prompt_log_path": str(prompts), "placement": "full_width",
                       "intended_latex_width_fraction": 1.0, "estimated_min_rendered_font_pt": 9})
    write_json("figure_manifest.json", {"figures": figures})
    write_tables(summary)
    write_json("derived/environment.json", {"python": platform.python_version(),
               "packages": {name: importlib.metadata.version(name) for name in ["numpy", "scipy", "matplotlib", "pyarrow", "Pillow", "requests", "beautifulsoup4"]}})
    provenance("derived/environment.json", ["scripts/build_paper_artifacts.py"])


def write_tables(summary):
    caption_rows = []
    for item in summary["grid"]:
        if item["alpha"] != .5:
            continue
        family = "HELM" if item["family"] == "helm" else "Open LLM"
        caption_rows.append(f"{family} & {LABELS[item['rule']]} & {item['selected_effort']:.3f} & {item['greedy_effort']:.3f} & {item['random_effort']:.3f} & {item['zero_effort']:.3f} " + chr(92)*2)
    Path("derived/comparators.tex").write_text("\n".join(caption_rows)+"\n")
    all_rows = []
    for item in summary["grid"]:
        family = "HELM" if item["family"] == "helm" else "Open LLM"
        all_rows.append(f"{family} & {LABELS[item['rule']]} & {item['alpha']:.2f} & {item['attained']}/{item['count']} & {item['selected_effort']:.3f} & {item['greedy_effort']:.3f} & {item['random_effort']:.3f} " + chr(92)*2)
    Path("derived/full_grid.tex").write_text("\n".join(all_rows)+"\n")
    interval_rows = []
    for item in summary["paired_intervals"]:
        interval = item["conditional_cluster_percentile_95"]
        family = "HELM" if item["family"] == "helm" else "Open LLM"
        interval_rows.append(f"{item['seed']} & {family} & {LABELS[item['rule']]} & {item['alpha']:.2f} & {item['baseline'].title()} & {item['mean_effort_difference']:+.3f} & [{interval[0]:+.3f}, {interval[1]:+.3f}] " + chr(92)*2)
    Path("derived/paired_intervals.tex").write_text("\n".join(interval_rows)+"\n")
    auxiliary_rows = []
    for item in summary["auxiliary"]:
        kind = "HELM projection" if item["family"] == "helm" else "Open LLM six" if item["kind"] == "six-task auxiliary" else "BBH 24"
        auxiliary_rows.append(f"{kind} & {LABELS[item['rule']]} & {item['alpha']:.2f} & {item['attained']}/{item['count']} & {item['bounded']} " + chr(92)*2)
    Path("derived/auxiliary.tex").write_text("\n".join(auxiliary_rows)+"\n")
    for filename in ["comparators", "full_grid", "paired_intervals", "auxiliary"]:
        provenance("derived/"+filename+".tex", ["derived/summary.json"])
    manuscript_path = Path("paper.tex")
    if manuscript_path.exists():
        manuscript = manuscript_path.read_text()
        for filename in ["comparators", "full_grid", "paired_intervals", "auxiliary"]:
            begin = "% BEGIN GENERATED " + filename
            end = "% END GENERATED " + filename
            content = begin + "\n" + Path("derived/"+filename+".tex").read_text() + end
            directive = "\\input{derived/"+filename+".tex}"
            if directive in manuscript:
                manuscript = manuscript.replace(directive, content)
            else:
                manuscript = re.sub(re.escape(begin)+r".*?"+re.escape(end), lambda match: content, manuscript, flags=re.S)
        manuscript_path.write_text(manuscript)


if __name__ == "__main__":
    main()
