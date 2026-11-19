"""Build the quantitative figures (PDF + 300-DPI PNG) from derived per-case summaries.
Inputs:  analysis/final_per_case.json (from analysis/final_per_case.py),
         analysis/reconstructed_baselines.json (from analysis/reconstruct_baselines.py)
# @evidence[[analysis/final_per_case.json]]
# @evidence[[analysis/reconstructed_baselines.json]]
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig_dir = Path("figures"); fig_dir.mkdir(exist_ok=True)
F = json.load(open("analysis/final_per_case.json"))["cases"]
R = json.load(open("analysis/reconstructed_baselines.json"))["cases"]
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9.5, "xtick.labelsize": 9,
                     "ytick.labelsize": 8.5, "legend.fontsize": 8.5, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42})
COL = {"naive": "#8f8f8f", "bonf": "#8ab6d6", "resample": "#d8a038", "prop": "#1b3a73"}
LAB = {"naive": "Naive Wilson", "bonf": "Bonferroni-Wilson", "resample": "Resampling", "prop": "EB-IRT (ours)"}
KEY = {"naive": "naive_IS", "bonf": "bonferroni_IS", "resample": "resample_IS", "prop": "proposed_IS"}

# ---- Figure: per-case interval score
def panel_is(ax, cases, title, ymax):
    w = 0.2; x = np.arange(len(cases))
    for j, m in enumerate(("naive", "bonf", "resample", "prop")):
        mu = np.array([F[c][KEY[m]]["mean"] for c in cases]); sd = np.array([F[c][KEY[m]]["sd"] for c in cases])
        pos = x + (j - 1.5) * w
        ax.bar(pos, np.minimum(mu, ymax), w, yerr=np.where(mu > ymax, 0, sd), color=COL[m], label=LAB[m],
               capsize=1.5, error_kw={"lw": 0.8}, edgecolor="white", linewidth=0.4)
        for xi, v in zip(pos, mu):
            if v > ymax:
                ax.annotate(f"{v:.2f}", (xi, ymax), xytext=(xi + 0.02, ymax * 0.93), ha="center", va="top", fontsize=8,
                            color="white", rotation=90, fontweight="bold")
                ax.plot([xi - w / 2, xi + w / 2], [ymax * 0.985] * 2, color="k", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(cases); ax.set_ylim(0, ymax); ax.set_title(title, loc="left")
fig, axs = plt.subplots(1, 2, figsize=(5.5, 2.7), gridspec_kw={"width_ratios": [3, 5]}, sharey=True)
panel_is(axs[0], ["P1", "P2", "N1"], "(a) Synthetic worlds", 0.45)
panel_is(axs[1], ["P3", "P4", "P5", "P6", "N2"], "(b) Real LLM outcomes", 0.45)
axs[0].set_ylabel("Mean interval score (lower is better)")
h, l = axs[1].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02), columnspacing=1.0, handlelength=1.2)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(fig_dir / "per_case_interval_score.pdf"); fig.savefig(fig_dir / "per_case_interval_score.png", dpi=300); plt.close(fig)

# ---- Figure: bias and coverage
cases = ["P1", "P2", "P3", "P4", "P5", "P6"]
fig, axs = plt.subplots(1, 2, figsize=(5.5, 2.6))
x = np.arange(len(cases)); w = 0.36
for j, (m, mu, sd) in enumerate((
    ("naive", [F[c]["naive_bias"]["mean"] for c in cases], [F[c]["naive_bias"]["sd"] for c in cases]),
    ("prop", [F[c]["proposed_bias"]["mean"] for c in cases], [F[c]["proposed_bias"]["sd"] for c in cases]))):
    axs[0].bar(x + (j - 0.5) * w, mu, w, yerr=sd, color=COL[m], label=LAB[m], capsize=1.5, error_kw={"lw": 0.8}, edgecolor="white", linewidth=0.4)
axs[0].axhline(0, color="k", lw=0.8)
axs[0].set_xticks(x); axs[0].set_xticklabels(cases); axs[0].set_ylabel("Signed bias")
axs[0].set_title("(a) Point-estimate bias", loc="left")
for j, (m, mu, sd) in enumerate((
    ("naive", [R[c]["naive_cov"]["mean"] for c in cases], [R[c]["naive_cov"]["sd"] for c in cases]),
    ("prop", [F[c]["coverage"]["mean"] for c in cases], [F[c]["coverage"]["sd"] for c in cases]))):
    axs[1].bar(x + (j - 0.5) * w, mu, w, yerr=sd, color=COL[m], capsize=1.5, error_kw={"lw": 0.8}, edgecolor="white", linewidth=0.4)
axs[1].axhline(0.90, color="k", lw=0.9, ls="--", label="Nominal 0.90")
axs[1].set_ylim(0.4, 1.05); axs[1].set_xticks(x); axs[1].set_xticklabels(cases)
axs[1].set_ylabel("Empirical coverage"); axs[1].set_title("(b) Interval coverage", loc="left")
h, l = axs[0].get_legend_handles_labels()
h2, l2 = axs[1].get_legend_handles_labels(); h += h2; l += l2
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(fig_dir / "bias_and_coverage.pdf"); fig.savefig(fig_dir / "bias_and_coverage.png", dpi=300); plt.close(fig)

# ---- Concept-figure placeholder (never overwrite the orchestrator-rendered figure)
def placeholder():
    if Path(".concept_figure_complete").exists():
        return
    p = fig_dir / "overview_schematic.prompts.json"
    if p.exists() and p.read_text().strip() not in ("", "{}"):
        return
    fig = plt.figure(figsize=(5.5, 1.8)); fig.text(0.5, 0.5, "overview_schematic (placeholder)", ha="center", va="center")
    fig.savefig(fig_dir / "overview_schematic.png", dpi=300); plt.close(fig)
    p.write_text("{}")
placeholder()

# ---- Optional figure: interval width versus question budget (real exhaustive cases)
Ns = [("P5", 60), ("P3", 200), ("P6", 600)]
fig, ax = plt.subplots(figsize=(3.9, 2.5))
for m, getter, lab in (("naive", lambda c: R[c]["naive_width"]["mean"], LAB["naive"]), ("bonf", lambda c: R[c]["bonf_width"]["mean"], LAB["bonf"]),
                       ("prop", lambda c: F[c]["width"]["mean"], LAB["prop"])):
    ax.plot([n for _, n in Ns], [getter(c) for c, _ in Ns], marker="o", color=COL[m], label=lab, lw=1.6)
ax.set_xscale("log"); ax.set_xticks([60, 200, 600]); ax.set_xticklabels(["60", "200", "600"]); ax.minorticks_off()
ax.set_xlabel("Benchmark questions $N$"); ax.set_ylabel("Mean interval width"); ax.set_ylim(0, 0.31)
ax.legend(frameon=False, loc="upper right")
fig.tight_layout()
fig.savefig(fig_dir / "width_vs_n.pdf"); fig.savefig(fig_dir / "width_vs_n.png", dpi=300); plt.close(fig)
