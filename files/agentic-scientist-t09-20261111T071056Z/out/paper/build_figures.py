"""Build derived statistics and figures for the paper from paper_data.json (read-only)."""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
data = json.loads((ROOT / "paper_data.json").read_text())
fin = data["final_evaluation"]
M = fin["metrics"]  # @evidence[[paper_data.json#final_evaluation.metrics]]
eps = fin["evaluation_evidence"]["episodes"]  # @evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]

C = {"oracle": "#009E73", "frozen": "#0072B2", "linear": "#E69F00", "dim": "#999999", "ht": "#CC79A7"}
plt.rcParams.update({"font.size": 8, "axes.labelsize": 8, "axes.titlesize": 10,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
                     "axes.spines.top": False, "axes.spines.right": False})

# ---- derived statistics -------------------------------------------------------------
seed_err = np.array([-e["score"] for e in eps])  # per-seed mean relative error over 8 cases
seeds = np.array([e["seed"] for e in eps])
rng = np.random.default_rng(0)
boot = np.array([rng.choice(seed_err, len(seed_err)).mean() for _ in range(10000)])
stats = {
    "n_seeds": int(len(seed_err)),
    "seed_mean": float(seed_err.mean()),
    "seed_median": float(np.median(seed_err)),
    "seed_min": float(seed_err.min()), "seed_max": float(seed_err.max()),
    "seed_std": float(seed_err.std(ddof=1)),
    "boot_ci_low": float(np.percentile(boot, 2.5)), "boot_ci_high": float(np.percentile(boot, 97.5)),
    "n_seeds_above_0p15": int((seed_err > 0.15).sum()),
    "outlier_seeds": [int(s) for s in seeds[seed_err > 0.15]],
    "mean_excluding_outliers": float(seed_err[seed_err <= 0.15].mean()),
    "median_duration_seconds": float(np.median([e["duration_seconds"] for e in eps])),
    "min_duration_seconds": float(min(e["duration_seconds"] for e in eps)),
    "max_duration_seconds": float(max(e["duration_seconds"] for e in eps)),
    "case_mean_of_8": float(np.mean([M[f"rmse_rel_case_{k}"] for k in range(1, 9)])),
    "cases_1_to_5_range": [float(min(M[f"rmse_rel_case_{k}"] for k in range(1, 6))),
                           float(max(M[f"rmse_rel_case_{k}"] for k in range(1, 6)))],
    "frozen_over_oracle": float(M["rmse_rel"] / M["baseline_oracle_rmse_rel"]),
    "frozen_vs_linear_abs_gap": float(M["baseline_linear_rmse_rel"] - M["rmse_rel"]),
    "coverage_shortfall": float(0.95 - M["ci_coverage"]),
    "oracle_over_linear": float(M["baseline_oracle_rmse_rel"] / M["baseline_linear_rmse_rel"]),
    "dim_over_linear": float(M["baseline_dim_rmse_rel"] / M["baseline_linear_rmse_rel"]),
    "ht_over_linear": float(M["baseline_ht_rmse_rel"] / M["baseline_linear_rmse_rel"]),
    "worst_over_next_worst_case": float(M["rmse_rel_case_8"] / M["rmse_rel_case_6"]),
    "bias_over_rmse": float(M["bias_rel_abs_mean"] / M["rmse_rel"]),
}
(ROOT / "derived_stats.json").write_text(json.dumps(stats, indent=1))
(ROOT / "derived_stats.json.prov.json").write_text(json.dumps({
    "schema_name": "scientific-evidence.artifact-manifest",
    "artifact": {"path": "derived_stats.json", "kind": "analysis"},
    "derived_from": ["@evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]",
                     "@evidence[[paper_data.json#final_evaluation.metrics]]",
                     "@evidence[[build_figures.py]]"]}, indent=1))

def save(fig, name, sources):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=500, bbox_inches="tight")
    (FIG / f"{name}.png.prov.json").write_text(json.dumps({
        "schema_name": "scientific-evidence.artifact-manifest",
        "artifact": {"path": f"figures/{name}.png", "kind": "figure"},
        "derived_from": ["@evidence" + "[[" + s + "]" + "]" for s in sources] + ["@evidence[[build_figures.py]]"]}, indent=1))
    plt.close(fig)

# ---- Fig 2: main accuracy -----------------------------------------------------------
fig, (a, b) = plt.subplots(1, 2, figsize=(5.5, 2.8), gridspec_kw={"width_ratios": [1, 1.55]})
names = ["Oracle", "Frozen", "Linear", "DiM", "HT"]
vals = [M["baseline_oracle_rmse_rel"], M["rmse_rel"], M["baseline_linear_rmse_rel"],
        M["baseline_dim_rmse_rel"], M["baseline_ht_rmse_rel"]]
cols = [C["oracle"], C["frozen"], C["linear"], C["dim"], C["ht"]]
a.bar(range(5), vals, color=cols)
for i, v in enumerate(vals):
    a.text(i, v * 1.05, f"{v:.3f}", ha="center", va="bottom", fontsize=7)
a.set_yscale("log"); a.set_ylim(0.02, 2.5)
a.set_xticks(range(5)); a.set_xticklabels(names, rotation=35, ha="right")
a.set_ylabel("Rel. RMSE (mean of 8 cases)")
a.set_title("(a) Aggregate, final plane", loc="left")
cases = ["1\nSBM", "2\nclus.", "3\nBA", "4\nWS", "5\nstr.", "6\nsat.", "7\nc×d", "8\n2-hop"]
cv = [M[f"rmse_rel_case_{k}"] for k in range(1, 9)]
b.bar(range(8), cv, color=C["frozen"])
for i, v in enumerate(cv):
    b.text(i, v + 0.008, f"{v:.3f}", ha="center", va="bottom", fontsize=7)
b.axhline(M["baseline_oracle_rmse_rel"], color=C["oracle"], ls="--", lw=1.2, label="oracle (plane mean)")
b.axhline(M["baseline_linear_rmse_rel"], color=C["linear"], ls="--", lw=1.2, label="linear (plane mean)")
b.set_xticks(range(8)); b.set_xticklabels(cases, fontsize=7)
b.set_ylim(0, 0.52); b.set_ylabel("Rel. RMSE (24 seeds)")
b.set_title("(b) Frozen estimator, per case", loc="left"); b.legend(frameon=False, loc="upper left")
fig.tight_layout()
save(fig, "main_accuracy", ["paper_data.json#final_evaluation.metrics"])

# ---- Fig 3: reliability -------------------------------------------------------------
fig, (a, b) = plt.subplots(1, 2, figsize=(5.0, 2.6), gridspec_kw={"width_ratios": [1.7, 1]})
a.scatter(seeds, seed_err, s=22, color=C["frozen"], zorder=3)
for s, v in zip(seeds, seed_err):
    if v > 0.15:
        a.annotate(str(s), (s, v), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7)
a.axhline(stats["seed_mean"], color="k", lw=1.2, label=f"mean {stats['seed_mean']:.3f}")
a.axhspan(stats["boot_ci_low"], stats["boot_ci_high"], color="k", alpha=0.15,
          label=f"95% bootstrap [{stats['boot_ci_low']:.3f}, {stats['boot_ci_high']:.3f}]")
a.set_xlabel("Evaluation seed"); a.set_ylabel("Mean rel. error (8 cases)")
a.set_ylim(0.05, 0.215); a.legend(frameon=False, loc="upper right", ncol=1, bbox_to_anchor=(1.0, 0.64))
a.set_title("(a) Per-seed error", loc="left")
b.bar([0], [M["ci_coverage"]], color=C["frozen"], width=0.5)
b.axhline(0.95, color="crimson", ls="--", lw=1.2); b.text(-0.45, 0.97, "nominal 0.95", color="crimson", ha="left", fontsize=7)
b.text(0, M["ci_coverage"] - 0.06, f"{M['ci_coverage']:.3f}", ha="center", color="w", fontsize=7)
b.text(0, 0.05, f"rel. width\n{M['ci_width_rel']:.3f}", ha="center", color="w", fontsize=7)
b.set_xlim(-0.5, 0.5); b.set_ylim(0, 1.05); b.set_xticks([0]); b.set_xticklabels(["Frozen"])
b.set_ylabel("Interval coverage"); b.set_title("(b) Coverage", loc="left")
fig.tight_layout()
save(fig, "reliability", ["paper_data.json#final_evaluation.evaluation_evidence.episodes",
                          "paper_data.json#final_evaluation.metrics"])


# ---- placeholder for orchestrator-rendered concept figure (never clobber the real one) ----
def placeholder():
    if (ROOT / ".concept_figure_complete").exists():
        return
    p = FIG / "overview_schematic.prompts.json"
    if p.exists() and p.stat().st_size > 2:
        return
    fig = plt.figure(figsize=(7, 2.6)); fig.text(0.5, 0.5, "overview_schematic (placeholder)", ha="center")
    fig.savefig(FIG / "overview_schematic.png", dpi=200); plt.close(fig)
    p.write_text("{}")
placeholder()
print(json.dumps(stats, indent=1))
