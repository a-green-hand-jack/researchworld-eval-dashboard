"""Build quantitative figures for the paper from read-only evidence files.

Inputs (all read from disk, nothing hardcoded):
  paper_data.json            final_evaluation.metrics / evaluation_evidence.episodes
  source_evidence/search_metrics/*.json   search-stage metrics of the three configurations
@evidence[[paper_data.json#final_evaluation.metrics]]
@evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]
The concept figure (overview_schematic) is orchestrator-owned; a placeholder is written only if no
rendered figure exists.
"""
import json, glob, os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.titlesize": 10, "axes.labelsize": 9, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "legend.fontsize": 8, "font.family": "DejaVu Sans"})
PNG_DPI = 440  # 5.5 in wide -> 2420 px, meets the full-width raster minimum
C_PLANNER, C_BASE, C_REF, C_CTRL = "#1b6ca8", "#c8782a", "#555555", "#4a9d6b"

pd_ = json.loads((ROOT / "paper_data.json").read_text())
fin = pd_["final_evaluation"]
m = fin["metrics"]
eps = fin["evaluation_evidence"]["episodes"]

# ---------------- Figure: final efficiency comparison ----------------
fig, ax = plt.subplots(1, 2, figsize=(5.5, 2.6), gridspec_kw={"width_ratios": [1, 1.25]})
a = ax[0]
vals = [m["main_efficiency"], m["baseline_main_efficiency"]]
bars = a.bar(["Verified\nplanner", "Naive\nbaselines"], vals, color=[C_PLANNER, C_BASE], width=0.55)
a.axhline(1.0, color=C_REF, ls="--", lw=1)
a.text(0.98, 1.01, "reference = 1", transform=a.get_yaxis_transform(), ha="right", va="bottom", fontsize=8, color=C_REF)
for b, v in zip(bars, vals):
    a.text(b.get_x() + b.get_width() / 2, v + 0.015, f"{v:.4f}", ha="center", va="bottom", fontsize=8)
a.set_ylim(0, 1.2)
a.set_ylabel("Main efficiency")
a.set_title("(a) Main cases, final boards")

b_ = ax[1]
names = ["Main", "Control", "Combined"]
cv = [m["main_efficiency"], m["control_efficiency"], m["combined_score"]]
bars = b_.bar(names, cv, color=[C_PLANNER, C_CTRL, C_REF], width=0.55)
b_.axhline(1.0, color=C_REF, ls="--", lw=1)
b_.set_ylim(0.998, 1.0045)
for bb, v in zip(bars, cv):
    b_.text(bb.get_x() + bb.get_width() / 2, v + 0.00012, f"{v:.4f}", ha="center", va="bottom", fontsize=8)
seed_scores = [e["score"] for e in eps]
b_.scatter([2, 2], seed_scores, color="black", s=14, zorder=5, label="per-seed combined")
b_.set_ylabel("Efficiency (zoomed axis)")
b_.set_title("(b) Planner diagnostics")
b_.legend(loc="upper right", frameon=False)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(FIG / f"final_efficiency_comparison.{ext}", dpi=300 if ext == "pdf" else PNG_DPI)
plt.close(fig)

# ---------------- Figure: search-stage variants ----------------
rows = []
for d in sorted(glob.glob(str(ROOT / "source_evidence/search_metrics/config_0*_metrics.json"))):
    rows.append(json.loads(Path(d).read_text()))
labels = ["Base\nsolvers", "Base +\nMILP layer", "Base +\nboundary polish"]
fig, ax = plt.subplots(figsize=(5.5, 2.8))
x = range(3)
w = 0.36
mv = [r["main_efficiency"] for r in rows]
cv = [r["control_efficiency"] for r in rows]
b1 = ax.bar([i - w / 2 for i in x], mv, w, color=C_PLANNER, label="Main efficiency")
b2 = ax.bar([i + w / 2 for i in x], cv, w, color=C_CTRL, label="Control efficiency")
for bs, vs in ((b1, mv), (b2, cv)):
    for bb, v in zip(bs, vs):
        ax.text(bb.get_x() + bb.get_width() / 2, v + 0.0003, f"{v:.4f}", ha="center", va="bottom", fontsize=8)
ax.axhline(1.0, color=C_REF, ls="--", lw=1)
ax.set_xticks(list(x)); ax.set_xticklabels(labels)
ax.set_ylim(0.994, 1.0085)
ax.set_ylabel("Efficiency (zoomed axis)")
ax.set_title("Search-stage configurations on HELM MMLU v1.13.0")
ax.legend(loc="upper left", frameon=False, ncol=2)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(FIG / f"search_variant_comparison.{ext}", dpi=300 if ext == "pdf" else PNG_DPI)
plt.close(fig)

# ---------------- concept figure placeholder (never clobber a rendered figure) ----------------
def placeholder():
    if (ROOT / ".concept_figure_complete").exists():
        return
    p = FIG / "overview_schematic.png"
    pj = FIG / "overview_schematic.prompts.json"
    if pj.exists() and pj.stat().st_size > 4:
        return
    fig, ax = plt.subplots(figsize=(7.0, 2.2), dpi=200)
    ax.text(0.5, 0.5, "overview schematic (rendered by orchestrator)", ha="center", va="center")
    ax.axis("off")
    fig.savefig(p, dpi=200)
    plt.close(fig)
    pj.write_text("{}\n")
placeholder()
print("ok", mv, cv, seed_scores)
