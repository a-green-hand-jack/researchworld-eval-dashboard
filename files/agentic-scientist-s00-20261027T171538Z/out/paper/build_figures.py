"""Build the quantitative figures and derived tables for paper.tex.

All numbers are read from paper_data.json (sealed final evaluation); nothing is hardcoded.
Run: python build_figures.py
"""
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
ANALYSIS = ROOT / "analysis"
ANALYSIS.mkdir(exist_ok=True)

# @evidence[[paper_data.json#final_evaluation.metrics]]
DATA = json.loads((ROOT / "paper_data.json").read_text())
M = DATA["final_evaluation"]["metrics"]

FAMILIES = ["path", "cycle", "star", "complete", "grid", "binary_tree", "lollipop",
            "random_tree", "erdos_renyi", "random_regular3"]
LABEL = {"path": "Path", "cycle": "Cycle", "star": "Star", "complete": "Complete", "grid": "Grid",
         "binary_tree": "Binary tree", "lollipop": "Lollipop", "random_tree": "Random tree",
         "erdos_renyi": "Erdős–Rényi", "random_regular3": "Random 3-reg."}

C_PRED = "#2a6fb0"   # studied predictor
C_BOUND = "#d1782a"  # best generic bound
C_REF = "#8c8c8c"    # other references
C_CTRL = "#b23a48"   # permuted-feature control

plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.titlesize": 10,
                     "axes.labelsize": 9, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
                     "legend.fontsize": 8.5, "pdf.fonttype": 42, "mathtext.fontset": "stix"})


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=450, bbox_inches="tight")
    plt.close(fig)
    for ext in ("pdf", "png"):
        sidecar = {
            "schema_name": "scientific-evidence.artifact-manifest",
            "artifact": {"path": f"figures/{name}.{ext}", "kind": "figure"},
            "derived_from": ["@evidence[[paper_data.json#final_evaluation.metrics]]",
                             "@evidence[[build_figures.py]]"],
        }
        (FIG / f"{name}.{ext}.prov.json").write_text(json.dumps(sidecar, indent=1))


# ---------------------------------------------------------------- per-family table (derived)
# Best-bound error per family is derived as predictor error minus paired delta.
# @evidence[[paper_data.json#final_evaluation.metrics.final_log_err_<family>]]
# @evidence[[paper_data.json#final_evaluation.metrics.delta_vs_best_bound_<family>]]
rows = []
for f in FAMILIES:
    pred = M[f"final_log_err_{f}"]
    d = M[f"delta_vs_best_bound_{f}"]
    lo, hi = M[f"delta_vs_best_bound_{f}_ci_low"], M[f"delta_vs_best_bound_{f}_ci_high"]
    rows.append({"family": f, "pred_err": pred, "best_bound_err_derived": pred - d, "delta": d,
                 "delta_ci_low": lo, "delta_ci_high": hi, "ci_excludes_zero": hi < 0 or lo > 0})
derived = {
    "per_family": rows,
    "n_families_ci_excludes_zero": sum(r["ci_excludes_zero"] for r in rows),
    "geo_ratio_predictor": math.exp(M["final_main_log_err"]),
    "geo_ratio_best_bound": math.exp(M["best_bound_log_err"]),
    "geo_ratio_predictor_ci": [math.exp(M["final_main_log_err_ci_low"]),
                               math.exp(M["final_main_log_err_ci_high"])],
    "best_bound_minus_predictor_plane": M["best_bound_log_err"] - M["final_main_log_err"],
    "fraction_of_best_bound_error_removed": 1 - M["final_main_log_err"] / M["best_bound_log_err"],
    "share_of_total_complete_grid_er": (M["final_log_err_complete"] + M["final_log_err_grid"]
                                        + M["final_log_err_erdos_renyi"]) / (10 * M["final_main_log_err"]),
    "per_family_error_spread_ratio": max(r["pred_err"] for r in rows) / min(r["pred_err"] for r in rows),
    "error_factors": {k: math.exp(M[k]) for k in ("final_main_log_err", "ols_ref_log_err", "constant_log_err",
                      "permuted_feature_log_err", "matthews_ref_log_err", "best_bound_log_err",
                      "feige_lead_log_err", "aklrr_log_err")},
    "family_factors_predictor": {r["family"]: math.exp(r["pred_err"]) for r in rows},
    "family_factors_best_bound": {r["family"]: math.exp(r["best_bound_err_derived"]) for r in rows},
    "note": "best_bound_err_derived = final_log_err_<f> - delta_vs_best_bound_<f>; geo ratios = exp(mean abs log error)",
}
(ANALYSIS / "derived_metrics.json").write_text(json.dumps(derived, indent=1))
(ANALYSIS / "derived_metrics.json.prov.json").write_text(json.dumps({
    "schema_name": "scientific-evidence.artifact-manifest",
    "artifact": {"path": "analysis/derived_metrics.json", "kind": "table"},
    "derived_from": ["@evidence[[paper_data.json#final_evaluation.metrics]]", "@evidence[[build_figures.py]]"],
}, indent=1))

# ---------------------------------------------------------------- held-out roster (derived from evaluator source)
# @evidence[[analysis/evaluator_snapshot/evaluate_final.py#det_catalogue]]
# @evidence[[analysis/evaluator_snapshot/plane_config.json#final_eval_random_per_family]]
SNAP = ANALYSIS / "evaluator_snapshot"  # copy of task/evaluate_final.py and task/resources/final/plane_config.json
src = (SNAP / "evaluate_final.py").read_text()
ns = {"math": math, "N_MIN": 5, "N_MAX": 30, "SPLIT_NAMES": {0: "train", 1: "search_eval", 2: "final_eval"}}
exec(src[src.index("def det_catalogue"):src.index("def random_graph")], ns)
cfg = json.loads((SNAP / "plane_config.json").read_text())
roster = {}
for split, key in (("train", "train_random_per_family"), ("final_eval", "final_eval_random_per_family")):
    counts = {f: 0 for f in FAMILIES}
    for fam, _p, s in ns["det_catalogue"]():
        if s == split:
            counts[fam] += 1
    for fam in ("random_tree", "erdos_renyi", "random_regular3"):
        counts[fam] = cfg[key]
    counts["total"] = sum(counts[f] for f in FAMILIES)
    roster[split] = counts
roster["walks_per_graph"] = cfg["walks"]
roster["bootstrap_reps"] = cfg["bootstrap_reps"]
(ANALYSIS / "roster.json").write_text(json.dumps(roster, indent=1))
(ANALYSIS / "roster.json.prov.json").write_text(json.dumps({
    "schema_name": "scientific-evidence.artifact-manifest",
    "artifact": {"path": "analysis/roster.json", "kind": "table"},
    "derived_from": ["@evidence[[analysis/evaluator_snapshot/evaluate_final.py]]",
                     "@evidence[[analysis/evaluator_snapshot/plane_config.json]]", "@evidence[[build_figures.py]]"],
}, indent=1))

# ---------------------------------------------------------------- Fig: per-family reliability
order = sorted(rows, key=lambda r: r["best_bound_err_derived"])  # sorted by bound slack
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(5.5, 3.1), sharey=True,
                               gridspec_kw={"width_ratios": [1.15, 1.0], "wspace": 0.08})
ys = list(range(len(order)))
for y, r in zip(ys, order):
    ax1.plot([r["pred_err"], r["best_bound_err_derived"]], [y, y], color="#cfcfcf", lw=1.2, zorder=1)
ax1.scatter([r["pred_err"] for r in order], ys, color=C_PRED, s=26, zorder=3, label="Statistics predictor")
ax1.scatter([r["best_bound_err_derived"] for r in order], ys, color=C_BOUND, marker="s", s=24, zorder=3,
            label="Best bound (derived)")
ax1.set_xscale("log")
ax1.set_xlim(0.04, 4)
ax1.set_yticks(ys)
ax1.set_yticklabels([LABEL[r["family"]] for r in order])
ax1.set_xlabel("Mean abs. log error (log scale)")
ax1.set_title("(a) Error per family")
ax1.grid(axis="x", which="major", color="#eeeeee")
fig.legend(*ax1.get_legend_handles_labels(), loc="upper center", ncol=2, frameon=False,
           bbox_to_anchor=(0.5, 1.07), handletextpad=0.3, columnspacing=1.5)

for y, r in zip(ys, order):
    col = C_PRED if r["ci_excludes_zero"] else C_REF
    ax2.errorbar(r["delta"], y, xerr=[[r["delta"] - r["delta_ci_low"]], [r["delta_ci_high"] - r["delta"]]],
                 fmt="o", color=col, ms=4.5, capsize=2.5, lw=1.2)
ax2.axvline(0, color="black", lw=0.8, ls="--")
ax2.set_xlabel("Paired Δ error vs. best bound")
ax2.set_title("(b) Paired gain, 95% CI")
ax2.grid(axis="x", color="#eeeeee")
ax2.set_xlim(-2.7, 0.3)
save(fig, "per_family_reliability")

# ---------------------------------------------------------------- Fig: plane-level comparison
fitted = [("Statistics predictor", M["final_main_log_err"], C_PRED,
           (M["final_main_log_err_ci_low"], M["final_main_log_err_ci_high"])),
          ("OLS (ln n, ln m)", M["ols_ref_log_err"], C_REF, None),
          ("Constant", M["constant_log_err"], C_REF, None),
          ("Permuted features", M["permuted_feature_log_err"], C_CTRL, None)]
bounds = [("Matthews ref.", M["matthews_ref_log_err"], C_REF, None),
          ("Best bound", M["best_bound_log_err"], C_BOUND, None),
          (r"$(4/27)n^3$", M["feige_lead_log_err"], C_REF, None),
          (r"$2m(n-1)$", M["aklrr_log_err"], C_REF, None)]
fig, axes = plt.subplots(1, 2, figsize=(4.85, 2.0), sharex=True, gridspec_kw={"wspace": 0.8})
for ax, group, title in ((axes[0], fitted, "(a) Fitted predictors and control"),
                         (axes[1], bounds, "(b) Bound-based predictors")):
    names = [g[0] for g in group][::-1]
    vals = [g[1] for g in group][::-1]
    cols = [g[2] for g in group][::-1]
    ax.barh(range(len(group)), vals, color=cols, height=0.62)
    for i, g in enumerate(group[::-1]):
        if g[3] is not None:
            ax.errorbar(g[1], i, xerr=[[g[1] - g[3][0]], [g[3][1] - g[1]]], color="black", capsize=2.5, lw=1)
        xt = (g[3][1] if g[3] is not None else g[1]) + 0.05
        ax.text(xt, i, f"{g[1]:.3f}", va="center", fontsize=8)
    ax.set_yticks(range(len(group)))
    ax.set_yticklabels(names)
    ax.set_xlim(0, 2.35)
    ax.set_title(title)
    ax.set_xlabel("Mean abs. log error")
    ax.grid(axis="x", color="#eeeeee")
    ax.set_axisbelow(True)
save(fig, "plane_level_comparison")


# ---------------------------------------------------------------- concept-figure placeholder (guarded)
def concept_placeholder():
    if (ROOT / ".concept_figure_complete").exists():
        return
    log = FIG / "overview_concept.prompts.json"
    if log.exists() and log.read_text().strip() not in ("", "{}"):
        return
    png = FIG / "overview_concept.png"
    if png.exists():
        return
    fig, ax = plt.subplots(figsize=(5.5, 1.6))
    ax.axis("off")
    ax.text(0.5, 0.5, "Overview figure placeholder (rendered by orchestrator)", ha="center", va="center")
    fig.savefig(png, dpi=300, bbox_inches="tight")
    plt.close(fig)
    log.write_text("{}")


concept_placeholder()
print(json.dumps({k: v for k, v in derived.items() if k != "per_family"}, indent=1))
for r in order:
    print(r)
print(roster)
