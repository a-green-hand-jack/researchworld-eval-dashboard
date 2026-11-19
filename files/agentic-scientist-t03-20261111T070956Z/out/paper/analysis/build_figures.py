#!/usr/bin/env python3
"""Build quantitative figures from paper_data.json and analysis/derived_metrics.json.

Run: PYTHONPATH=$TMPDIR/pylib python3 analysis/build_figures.py
Idempotent; never overwrites the orchestrator-rendered concept figure.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

# @evidence[[paper_data.json#final_evaluation.metrics]]
M = json.loads((ROOT / "paper_data.json").read_text(encoding="utf-8"))["final_evaluation"]["metrics"]
# @evidence[[analysis/derived_metrics.json]]
D = json.loads((ROOT / "analysis" / "derived_metrics.json").read_text(encoding="utf-8"))

C_DIAG, C_BASE, C_CTRL, C_LOW, C_HIGH, C_LB = "#1f6f8b", "#8c8c8c", "#d98324", "#9ecae1", "#2171b5", "#222222"
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
                     "legend.fontsize": 8.5, "axes.titlesize": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42})


PNG_DPI = 450  # 5.5 in-wide figures -> >= 2400 px wide raster


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=PNG_DPI, bbox_inches="tight")
    plt.close(fig)


# ---- Figure: main comparison -------------------------------------------------------------
cats = ["vs\nalways-\nreliable", "vs\nconstant\n0.5", "vs\nsplit-half\ngap", "vs\npermuted\ncontrol"]
est = [M["skill_vs_always_reliable"], M["skill_vs_constant_half"], M["skill_vs_gap_heuristic"],
       M["combined_score"] - M["control_permuted_score"]]
lb = [M["skill_vs_always_reliable_ci_low"], M["skill_vs_constant_half_ci_low"],
      M["skill_vs_gap_heuristic_ci_low"], M["combined_minus_control_ci_low"]]
cols = [C_BASE, C_BASE, C_BASE, C_CTRL]

fig, (a, b) = plt.subplots(1, 2, figsize=(5.5, 3.0), gridspec_kw={"width_ratios": [2.2, 1]})
x = range(len(cats))
a.bar(x, est, color=cols, width=0.62)
a.scatter(x, lb, marker="D", s=22, color=C_LB, zorder=3, label="2.5% lower bound")
for i, (e, l) in enumerate(zip(est, lb)):
    a.text(i, e + 0.004, f"{e:.4f}", ha="center", va="bottom", fontsize=8)
a.set_xticks(list(x)); a.set_xticklabels(cats)
a.set_ylabel("MSE reduction")
a.set_ylim(0, 0.19)
a.legend(frameon=False, loc="upper right", handletextpad=0.2)
a.set_title("(a) Skill over baselines and control", fontsize=10, loc="left")

lab = [M["mean_label_low_budget"], M["mean_label_high_budget"]]
b.bar([0, 1], lab, color=[C_LOW, C_HIGH], width=0.6)
for i, v in enumerate(lab):
    b.text(i, v + 0.012, f"{v:.3f}", ha="center", va="bottom", fontsize=8)
b.set_xticks([0, 1]); b.set_xticklabels(["4d", "16d"])
b.set_xlabel("coalition budget per run")
b.set_ylabel("mean top-3 Jaccard")
b.set_ylim(0, 1.08)
b.set_title("(b) Single-run agreement", fontsize=10, loc="left")
fig.tight_layout(w_pad=1.2)
save(fig, "main_comparison")

# ---- Figure: error accounting (derived) ---------------------------------------------------
names = ["diagnostic", "split-half gap", "permuted control", "always reliable", "constant 0.5"]
keys = ["diagnostic", "split_half_gap", "permuted_control", "always_reliable", "constant_half"]
cs = [C_DIAG, C_BASE, C_CTRL, C_BASE, C_BASE]
vals = [D["rmse"][k] for k in keys]
fig, (a, b) = plt.subplots(1, 2, figsize=(5.5, 2.7), gridspec_kw={"width_ratios": [1.5, 1.1]})
ypos = list(range(len(names)))[::-1]
a.barh(ypos, vals, color=cs, height=0.62)
for y, v in zip(ypos, vals):
    a.text(v + 0.006, y, f"{v:.3f}", va="center", fontsize=8)
a.set_yticks(ypos); a.set_yticklabels(names)
a.set_xlabel("RMSE against rerun-agreement label")
a.set_xlim(0, 0.49)
a.set_title("(a) Prediction error", fontsize=10, loc="left")

dec = D["decomposition_of_gain_over_always_reliable"]
b.bar([0], [dec["retained_under_pairing_permutation"]], color=C_CTRL, width=0.8,
      label="kept under permutation")
b.bar([0], [dec["instance_specific"]], bottom=[dec["retained_under_pairing_permutation"]], color=C_DIAG,
      width=0.8, label="instance-specific")
b.text(0.45, dec["retained_under_pairing_permutation"] / 2,
       f"kept under pairing\npermutation: {dec['retained_under_pairing_permutation']:.4f}",
       ha="left", va="center", fontsize=8, color=C_CTRL)
b.text(0.45, dec["retained_under_pairing_permutation"] + dec["instance_specific"] / 2,
       f"instance-specific:\n{dec['instance_specific']:.4f}", ha="left", va="center", fontsize=8, color=C_DIAG)
b.set_xlim(-0.45, 2.1); b.set_xticks([])
b.set_ylabel("MSE reduction vs\nalways reliable")
b.set_ylim(0, 0.042)
b.set_title("(b) Where the gain sits", fontsize=10, loc="left")
fig.tight_layout(w_pad=1.0)
save(fig, "error_accounting")

# ---- Placeholder for orchestrator-owned concept figure (never clobber the rendered one) ----
if not (ROOT / ".concept_figure_complete").exists() and not (
        (FIG / "protocol_overview.prompts.json").exists() and (FIG / "protocol_overview.prompts.json").stat().st_size > 4):
    fig = plt.figure(figsize=(5.5, 1.6)); fig.text(0.5, 0.5, "protocol_overview (placeholder)", ha="center")
    fig.savefig(FIG / "protocol_overview.png", dpi=300)
    plt.close(fig)
    (FIG / "protocol_overview.prompts.json").write_text("{}", encoding="utf-8")
