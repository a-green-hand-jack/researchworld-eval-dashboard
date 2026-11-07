import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
SOURCE = "@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]"
COLORS = {1.0: "#176A91", 0.5: "#C15D26"}
LABELS = {"helm": "HELM MMLU", "openllm": "Open LLM"}
RULES = ["mean", "median", "borda"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.labelsize": 10, "axes.titlesize": 11,
                     "xtick.labelsize": 9, "ytick.labelsize": 9,
                     "legend.fontsize": 9, "pdf.fonttype": 42,
                     "axes.spines.top": False, "axes.spines.right": False})


def sidecar(path, sources=None, kind="figure"):
    payload = {
        "schema_name": "scientific-evidence.artifact-manifest",
        "artifact": {"path": str(path.relative_to(ROOT)), "kind": kind,
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
        "derived_from": sources or [SOURCE],
        "generated_by": {"script_path": "scripts/build_results.py",
                         "command": ["python", "scripts/build_results.py"], "cwd": "."},
    }
    Path(str(path) + ".prov.json").write_text(json.dumps(payload, indent=2))


def save_plot(figure, stem):
    for suffix in ["pdf", "png"]:
        path = ROOT / "figures" / (stem + "." + suffix)
        figure.savefig(path, dpi=600 if suffix == "png" else 300, bbox_inches="tight", facecolor="white")
        if suffix == "png":
            with Image.open(path) as image:
                image.load()
                image.save(path, dpi=(300, 300))
        sidecar(path)
    plt.close(figure)


def count_text(observation, policy="allocation"):
    record = observation["allocation"] if policy == "allocation" else observation["baselines"][policy]
    feasible = record["status"] == "feasible" if policy == "allocation" else record["attainable"]
    return str(len(record["tasks"])) if feasible else r"$\infty$"


def main():
    (ROOT / "derived").mkdir(exist_ok=True)
    (ROOT / "figures").mkdir(exist_ok=True)
    (ROOT / "tables").mkdir(exist_ok=True)
    paper = json.loads((ROOT / "paper_data.json").read_text())
    episodes = paper["final_evaluation"]["evaluation_evidence"]["episodes"]
    resources = {family: json.loads((ROOT / "data" / (family + ".json")).read_text())
                 for family in LABELS}
    dimensions = {family: len(resource["tasks"]) for family, resource in resources.items()}
    records = []
    controls = []
    by_seed = defaultdict(dict)
    for episode_index, episode in enumerate(episodes):
        for case_index, case in enumerate(episode["solution"]["cases"]):
            if case["case"] != "original":
                controls.append({"seed": episode["seed"], "family": case["family"],
                                 "case": case["case"], "failure": case["failure"],
                                 "validated": sum(obs.get("validated", False) for obs in case["observations"]),
                                 "total": len(case["observations"])})
                continue
            assert case["failure"] is None
            for observation_index, observation in enumerate(case["observations"]):
                # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
                reference = observation["reference"]
                allocation = observation["allocation"]
                assert observation["validated"] and reference["exact"]
                assert reference["lower"] == reference["upper"]
                if reference["attainable"]:
                    assert allocation["status"] == "feasible"
                    assert len(allocation["tasks"]) == reference["lower"]
                    budget = len(allocation["tasks"])
                else:
                    assert allocation["status"] == "unattainable"
                    budget = None
                key = (case["family"], observation["target"], observation["rule"], observation["fraction"])
                by_seed[key][episode["seed"]] = (allocation["status"], tuple(allocation["tasks"]))
                records.append({"seed": episode["seed"], "family": case["family"],
                                "dimension": dimensions[case["family"]], "budget": budget,
                                "normalized_budget": None if budget is None else budget / dimensions[case["family"]],
                                "pointer": f"/final_evaluation/evaluation_evidence/episodes/{episode_index}/solution/cases/{case_index}/observations/{observation_index}",
                                **observation})
    assert all(len(set(signatures.values())) == 1 for signatures in by_seed.values())
    first_seed = episodes[0]["seed"]
    originals = [record for record in records if record["seed"] == first_seed]
    lookup = {(record["family"], record["target"], record["rule"], record["fraction"]): record
              for record in originals}
    targets = {family: list(dict.fromkeys(record["target"] for record in originals if record["family"] == family))
               for family in LABELS}
    reachability = {family: {str(cap): {rule: sum(lookup[(family, target, rule, cap)]["budget"] is not None
                                                               for target in targets[family]) for rule in RULES}
                            for cap in COLORS} for family in LABELS}
    summary = {"seeds": [episode["seed"] for episode in episodes], "dimensions": dimensions,
               "targets": targets, "reachability": reachability, "unique_original_decisions": len(originals),
               "original_records": len(records), "repeated_allocations_identical": True,
               "reference_bounds_all_closed": True, "replay_present": [episode["solution"].get("replay") is not None for episode in episodes],
               "controls": controls}
    summary["comparators"] = {}
    for family in LABELS:
        for rule in RULES:
            chosen = [record for record in records if record["family"] == family and record["rule"] == rule and record["budget"] is not None]
            summary["comparators"][family + "." + rule] = {
                policy: {"excess_min": min(len(record["baselines"][policy]["tasks"]) - record["budget"] for record in chosen),
                         "excess_max": max(len(record["baselines"][policy]["tasks"]) - record["budget"] for record in chosen)}
                for policy in ["greedy", "random"]}
    for path, payload in [(ROOT / "derived/summary.json", summary), (ROOT / "derived/original_records.json", records)]:
        path.write_text(json.dumps(payload, indent=2))
        sidecar(path, kind="derived")
    with (ROOT / "derived/allocations.csv").open("w") as stream:
        fields = ["seed", "family", "target", "rule", "fraction", "status", "budget", "normalized_budget", "tasks", "lower", "upper", "greedy", "random", "pointer"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({"seed": record["seed"], "family": record["family"], "target": record["target"],
                             "rule": record["rule"], "fraction": record["fraction"], "status": record["allocation"]["status"],
                             "budget": record["budget"], "normalized_budget": record["normalized_budget"],
                             "tasks": json.dumps(record["allocation"]["tasks"]), "lower": record["reference"]["lower"],
                             "upper": record["reference"]["upper"], "greedy": count_text(record, "greedy"),
                             "random": count_text(record, "random"), "pointer": record["pointer"]})
    sidecar(ROOT / "derived/allocations.csv", kind="table")
    main_lines = [r"\begin{tabular}{llrrrrrr}", r"\toprule", r" & & \multicolumn{3}{c}{$\rho=1$} & \multicolumn{3}{c}{$\rho=1/2$} \\",
                  r"Snapshot & Target & Mean & Median & Borda & Mean & Median & Borda \\", r"\midrule"]
    for family in LABELS:
        for index, target in enumerate(targets[family]):
            values = [count_text(lookup[(family, target, rule, cap)]) for cap in COLORS for rule in RULES]
            main_lines.append((LABELS[family] if index == 0 else "") + " & " + str(target) + " & " + " & ".join(values) + r" \\")
        main_lines.append(r"\midrule")
    main_lines[-1] = r"\bottomrule"
    main_lines.append(r"\end{tabular}")
    (ROOT / "tables/budgets.tex").write_text("\n".join(main_lines) + "\n% " + SOURCE + "\n")
    sidecar(ROOT / "tables/budgets.tex", kind="table")
    for family in LABELS:
        lines = [r"\begin{longtable}{llrrr rr r rr}", r"\caption{Complete original decisions for " + LABELS[family] + r". $B$ is the selected minimum; $L=U$ is the independent reference bound when finite. $G$ is marginal greedy; $R$ is the range across the recorded seeded random orders. $\infty$ denotes independently certified unattainability, not zero investment.}\\",
                 r"\toprule", r"Target & Rule & $\rho$ & $B$ & $B/d$ & $L$ & $U$ & $G$ & \multicolumn{2}{c}{$R$ (min--max)} \\", r"\midrule\endfirsthead",
                 r"\toprule Target & Rule & $\rho$ & $B$ & $B/d$ & $L$ & $U$ & $G$ & \multicolumn{2}{c}{$R$ (min--max)} \\ \midrule\endhead"]
        for target in targets[family]:
            for rule in RULES:
                for cap in COLORS:
                    record = lookup[(family, target, rule, cap)]
                    budget = count_text(record)
                    if record["budget"] is None:
                        normalized, lower, upper, random_min, random_max = [r"$\infty$"] * 5
                    else:
                        normalized = f"{record['normalized_budget']:.3f}"
                        lower, upper = str(record["reference"]["lower"]), str(record["reference"]["upper"])
                        random_sizes = [len(other["baselines"]["random"]["tasks"]) for other in records
                                        if (other["family"], other["target"], other["rule"], other["fraction"]) == (family, target, rule, cap)]
                        random_min, random_max = str(min(random_sizes)), str(max(random_sizes))
                    lines.append(" & ".join([str(target), rule.capitalize(), str(cap), budget, normalized, lower, upper,
                                              count_text(record, "greedy"), random_min, random_max]) + r" \\")
        lines += [r"\bottomrule\end{longtable}", "% " + SOURCE]
        path = ROOT / "tables" / (family + "_complete.tex")
        path.write_text("\n".join(lines) + "\n")
        sidecar(path, kind="table")
    figure, axes = plt.subplots(2, 2, figsize=(5.5, 4.8), sharex=True, sharey=True)
    for row, family in enumerate(LABELS):
        for column, cap in enumerate(COLORS):
            axis = axes[row, column]
            points = Counter()
            for target in targets[family]:
                mean = lookup[(family, target, "mean", cap)]["normalized_budget"]
                median = lookup[(family, target, "median", cap)]["normalized_budget"]
                points[(1.16 if mean is None else mean, 1.16 if median is None else median)] += 1
            axis.axline((0, 0), (1, 1), color="#aeb6bf", linewidth=.9, zorder=0)
            axis.axvspan(1.09, 1.23, color="#eeeeee", zorder=0)
            axis.axhspan(1.09, 1.23, color="#eeeeee", zorder=0)
            for (mean, median), multiplicity in points.items():
                axis.scatter(mean, median, s=46, color=COLORS[cap], edgecolor="white", linewidth=.7, zorder=3)
                if multiplicity > 1:
                    axis.annotate(f"×{multiplicity}", (mean, median), xytext=(3, -13), textcoords="offset points", fontsize=9)
            exemplar = 10 if family == "helm" else 1609
            example_mean = lookup[(family, exemplar, "mean", cap)]["normalized_budget"]
            example_median = lookup[(family, exemplar, "median", cap)]["normalized_budget"]
            offset = (12, -21) if family == "helm" and column == 0 else (-25, -26)
            if family == "openllm":
                offset = (-12, 16) if column == 0 else (15, -28)
            axis.annotate(str(exemplar), (example_mean, example_median), xytext=offset,
                          textcoords="offset points", fontsize=9, arrowprops={"arrowstyle": "-", "color": "#666666"})
            axis.set_title(f"{LABELS[family]} · ρ = {'1' if cap == 1 else '½'}", loc="left")
            axis.set_xlim(-.04, 1.24)
            axis.set_ylim(-.04, 1.24)
            axis.set_xticks([0, .5, 1, 1.16], ["0", "0.5", "1", "NA"])
            axis.set_yticks([0, .5, 1, 1.16], ["0", "0.5", "1", "NA"])
            axis.set_aspect("equal")
            axis.tick_params(labelbottom=True, labelleft=True)
            axis.set_xlabel("Mean task fraction", fontsize=9)
            axis.set_ylabel("Median task fraction", fontsize=9)
    figure.tight_layout(w_pad=1.6, h_pad=1.3)
    save_plot(figure, "paired_mean_median_budgets")
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.1), sharey=True)
    for axis, family in zip(axes, LABELS):
        for cap, offset, marker in [(1.0, -.10, "o"), (.5, .10, "s")]:
            values = [reachability[family][str(cap)][rule] for rule in RULES]
            axis.plot(np.arange(len(RULES)) + offset, values, marker=marker, linestyle="none", markersize=7,
                      color=COLORS[cap], label=f"ρ = {'1' if cap == 1 else '½'}")
            for position, value in enumerate(values):
                axis.annotate(str(value), (position + offset, value), xytext=(-10 if offset < 0 else 9, 3),
                              textcoords="offset points", ha="center", fontsize=9, color=COLORS[cap])
        axis.set_title(LABELS[family], loc="left")
        axis.set_xticks(range(3), ["Mean", "Median", "Borda"])
        target_count = len(targets[family])
        axis.set_ylim(-.4, target_count + .9)
        axis.set_yticks(np.arange(0, target_count + 1, max(1, target_count // 4)))
        axis.grid(axis="y", color="#e5e5e5", linewidth=.6)
    axes[0].set_ylabel(f"Reachable targets / {len(targets['helm'])}")
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(.54, 1.09), frameon=False)
    figure.tight_layout()
    save_plot(figure, "cap_conditioned_reachability")
    concept = ROOT / "figures/score_space_overview.png"
    prompt_path = ROOT / "figures/score_space_overview.prompts.json"
    rendered = (ROOT / ".concept_figure_complete").exists()
    nonempty_log = prompt_path.exists() and prompt_path.read_text().strip() not in ["", "{}"]
    if not rendered and not nonempty_log and not concept.exists():
        Image.new("RGB", (2400, 880), "white").save(concept)
        prompt_path.write_text("{}\n")
    manifest_path = ROOT / "figure_manifest.json"
    existing_figures = {entry["figure_id"]: entry for entry in
                        json.loads(manifest_path.read_text())["figures"]} if manifest_path.exists() else {}
    figures = []
    for stem, figure_type, panels, categories, series, minimum_font in [
        ("score_space_overview", "diagram", 1, [5], [3], 9),
        ("paired_mean_median_budgets", "scatter", 4, [4] * 4, [4] * 4, 6.5),
        ("cap_conditioned_reachability", "composite", 2, [3] * 2, [2] * 2, 6.5),
    ]:
        entry = {"figure_id": stem, "figure_type": figure_type, "path_png": f"figures/{stem}.png",
                 "generator": "generate-concept-figure" if figure_type == "diagram" else "matplotlib",
                 "n_panels": panels, "categories_per_panel": categories, "series_per_panel": series,
                 "panels_per_row": 1 if panels == 1 else 2, "max_label_chars": 28,
                 "uses_abbrev_labels": True, "uses_progression": False,
                 "source_ids": ["final.evidence.episodes"], "placement": "full_width",
                 "intended_latex_width_fraction": 1.0, "estimated_min_rendered_font_pt": minimum_font,
                 "font_sizes": {"title": 11, "axis": 10, "ticks": 9, "legend": 9}}
        if figure_type == "diagram":
            entry["prompt_log_path"] = str(prompt_path.relative_to(ROOT))
            entry = existing_figures.get(stem, entry)
        else:
            entry["path_pdf"] = f"figures/{stem}.pdf"
            entry["estimated_min_rendered_font_pt"] = 8.5
        figures.append(entry)
    (ROOT / "figure_manifest.json").write_text(json.dumps({"figures": figures}, indent=2))
    print(json.dumps({key: summary[key] for key in ["dimensions", "reachability", "original_records", "comparators"]}, indent=2))


if __name__ == "__main__":
    main()
