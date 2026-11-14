"""Build figures/main_results.{pdf,png} from paper_data.json (final sealed metrics only).
Also drops an idempotent placeholder for the orchestrator-rendered protocol_overview figure."""
import json, os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

def placeholder():
    if (ROOT / ".concept_figure_complete").exists():
        return
    p = FIG / "protocol_overview.prompts.json"
    if p.exists() and p.stat().st_size > 4:
        return
    fig, ax = plt.subplots(figsize=(11, 3.0))
    ax.axis("off"); ax.text(0.5, 0.5, "protocol overview (placeholder)", ha="center", va="center")
    fig.savefig(FIG / "protocol_overview.png", dpi=150); plt.close(fig)
    p.write_text("{}")

placeholder()

# @evidence[[paper_data.json#final.metric.final_nrmse]]
M = json.load(open(ROOT / "paper_data.json"))["final_evaluation"]["metrics"]
BLUE, ORANGE, GREY = "#1f5fa8", "#d9822b", "#7a7a7a"
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "axes.spines.top": False, "axes.spines.right": False})
fig, axs = plt.subplots(1, 3, figsize=(7.2, 3.1), gridspec_kw={"width_ratios": [1.0, 1.0, 0.9]})

# (a) MTEB error vs k
ks = [2, 5, 10, 20]
ys = [M[f"final_nrmse_mteb_k{k}"] for k in ks]
ax = axs[0]
ax.plot(range(4), ys, "-o", color=BLUE, lw=1.8, ms=5)
for i, y in enumerate(ys):
    ax.annotate(f"{y:.3f}", (i, y), textcoords="offset points", xytext=(5, 4), ha="left", fontsize=8)
ax.set_xticks(range(4)); ax.set_xticklabels([f"k={k}" for k in ks]); ax.set_xlim(-0.3, 3.7)
ax.set_ylim(0.55, 0.9); ax.set_ylabel("held-out nRMSE")
ax.set_title("(a) MTEB: error vs. $k$", fontsize=10)

# (b) by leaderboard
ax = axs[1]
names = ["MTEB", "HELM", "OLL", "pooled"]
vals = [M["final_nrmse_mteb"], M["final_nrmse_helm"], M["final_nrmse_oll"], M["final_nrmse"]]
cols = [BLUE, BLUE, BLUE, GREY]
b = ax.bar(range(4), vals, color=cols, width=0.62)
for r, v in zip(b, vals):
    ax.text(r.get_x() + r.get_width() / 2, v + 0.012, f"{v:.3f}", ha="center", fontsize=8)
ax.set_xticks(range(4)); ax.set_xticklabels(names)
ax.set_ylim(0, 0.85); ax.set_ylabel("held-out nRMSE")
ax.set_title("(b) Error by board", fontsize=10)

# (c) skill vs baselines
ax = axs[2]
names = ["col.\nmean", "greedy\nridge", "rand.-k\nridge"]
vals = [M["final_score"], M["final_skill_vs_greedy_ridge"], M["final_skill_vs_random_selection"]]
b = ax.bar(range(3), vals, color=[ORANGE] * 3, width=0.55)
for r, v in zip(b, vals):
    ax.text(r.get_x() + r.get_width() / 2, v + 0.01, f"{v:.3f}", ha="center", fontsize=8)
ax.set_xticks(range(3)); ax.set_xticklabels(names)
ax.set_ylim(0, 0.55); ax.set_ylabel("skill vs. baseline")
ax.set_title("(c) Skill vs. baseline", fontsize=10)

fig.tight_layout()
fig.savefig(FIG / "main_results.pdf"); fig.savefig(FIG / "main_results.png", dpi=400)
json.dump({"schema_name": "scientific-evidence.artifact-manifest",
           "artifact": {"path": "figures/main_results.png", "kind": "figure"},
           "derived_from": ["@evidence[[paper_data.json#final.metric.final_nrmse]]",
                            "@evidence[[scripts/build_figures.py]]"]},
          open(FIG / "main_results.png.prov.json", "w"), indent=1)
json.dump({"schema_name": "scientific-evidence.artifact-manifest",
           "artifact": {"path": "figures/main_results.pdf", "kind": "figure"},
           "derived_from": ["@evidence[[paper_data.json#final.metric.final_nrmse]]",
                            "@evidence[[scripts/build_figures.py]]"]},
          open(FIG / "main_results.pdf.prov.json", "w"), indent=1)
print("ok")
