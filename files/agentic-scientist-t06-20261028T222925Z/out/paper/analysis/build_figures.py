"""Build the quantitative figures of the paper from analysis/derived_stats.json.

No result number is hardcoded; all values come from derived_stats.json, which is itself
derived from paper_data.json (sealed final evaluation).
Also writes a placeholder for the orchestrator-owned concept figure, but only if the
orchestrator has not already rendered it (guarded by .concept_figure_complete).
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
# @evidence[[analysis/derived_stats.json#cases]]
stats = json.loads((ROOT / "analysis" / "derived_stats.json").read_text(encoding="utf-8"))

plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.titlesize": 10,
                     "axes.labelsize": 9, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
                     "legend.fontsize": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42})
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
TARGET_COLORS = {"drop_top1": "#2a78d6", "flip_top1": "#eb6834", "drop_topk": "#1baf7a"}
TARGET_LABELS = {"drop_top1": "drop, top-1", "flip_top1": "flip, top-1", "drop_topk": "drop, top-$k$ set"}
SOURCES = ["arena140k", "mtbench_human", "mtbench_gpt4", "nba2014", "nba2015"]
SRC_LABEL = {"arena140k": "Arena\ncrowd", "mtbench_human": "MTB\nexpert",
             "mtbench_gpt4": "MTB\nGPT-4", "nba2014": "NBA\n2014", "nba2015": "NBA\n2015"}
SRC_SHORT = {"arena140k": "Arena crowd", "mtbench_human": "MTB expert",
             "mtbench_gpt4": "MTB GPT-4", "nba2014": "NBA 2014", "nba2015": "NBA 2015"}


def slot(case):
    return "drop_topk" if case["perturbation"] == "drop" and case["target"] != "top1" else \
        f"{case['perturbation']}_top1"


cases = {(c["source"], slot(c)): c for c in stats["cases"]}


# Sidecar token built from parts so this source file carries no unresolved template ref.
EVIDENCE_TOKEN = "@" + "evidence[[{}]]"


def save(fig, name, sources):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=400, bbox_inches="tight")
    for ext in ("pdf", "png"):
        (FIG / f"{name}.{ext}.prov.json").write_text(json.dumps({
            "schema_name": "scientific-evidence.artifact-manifest",
            "artifact": {"path": f"figures/{name}.{ext}", "kind": "figure"},
            "derived_from": [EVIDENCE_TOKEN.format(s) for s in sources + ["analysis/build_figures.py"]]}, indent=2), encoding="utf-8")
    plt.close(fig)


# ---------------------------------------------------------------- Figure: two scales
fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.8))
x = np.arange(len(SOURCES))
w = 0.26
for panel, (ax, key, ylabel) in enumerate(zip(
        axes, ("k", "frac_pct"),
        ("verified size $k$ (comparisons)", "verified size $k/n$ (% of comparisons)"))):
    for j, tg in enumerate(("drop_top1", "flip_top1", "drop_topk")):
        vals = [cases[(s, tg)][key] for s in SOURCES]
        xs = x + (j - 1) * w
        ax.bar(xs, vals, width=w - 0.03, color=TARGET_COLORS[tg], label=TARGET_LABELS[tg],
               edgecolor="white", linewidth=0.6, zorder=3)
        if key == "k":
            for xi, v in zip(xs, vals):
                ax.text(xi, v * 1.12, f"{v:d}", ha="center", va="bottom", fontsize=7.6, color=MUTED)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([SRC_LABEL[s] for s in SOURCES], fontsize=8)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color=GRID, linewidth=0.6, zorder=0)
    ax.tick_params(axis="x", length=0)
    ax.set_title("(a) absolute count" if panel == 0 else "(b) fraction of the data", loc="left")
axes[0].set_ylim(0.6, 600)
axes[1].set_ylim(0.008, 15)
axes[1].yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.06))
fig.tight_layout(w_pad=2.0)
save(fig, "fragility_by_design_two_scales", ["analysis/derived_stats.json#cases"])

# ---------------------------------------------------------------- Figure: controlled contrasts
fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.6), gridspec_kw={"width_ratios": [1.25, 1]})
ax = axes[0]
rows = ["drop_top1", "flip_top1", "drop_topk"]
row_lab = {"drop_top1": "drop, top-1", "flip_top1": "flip, top-1", "drop_topk": "drop, top-3 set"}
for i, tg in enumerate(rows):
    h = cases[("mtbench_human", tg)]["frac_pct"]
    g = cases[("mtbench_gpt4", tg)]["frac_pct"]
    y = len(rows) - 1 - i
    ax.plot([h, g], [y, y], color="#b9b8b2", linewidth=2, zorder=1)
    ax.scatter([h], [y], s=46, color=TARGET_COLORS[tg], zorder=3, edgecolor="white", linewidth=1.5)
    ax.scatter([g], [y], s=46, marker="s", facecolor="white", edgecolor=TARGET_COLORS[tg],
               linewidth=1.8, zorder=3)
    kh = cases[("mtbench_human", tg)]["k"]
    kg = cases[("mtbench_gpt4", tg)]["k"]
    lo_is_h = h <= g
    ax.text(h, y + 0.2, f"{kh}", ha="right" if lo_is_h else "left", fontsize=8, color=MUTED)
    ax.text(g, y + 0.2, f"{kg}", ha="left" if lo_is_h else "right", fontsize=8, color=MUTED)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([row_lab[t] for t in rows[::-1]])
ax.set_ylim(-0.6, len(rows) - 0.3)
ax.set_xlim(0, 8)
ax.set_xlabel("verified size $k/n$ (%)")
ax.grid(axis="x", color=GRID, linewidth=0.6, zorder=0)
ax.scatter([], [], s=40, color=MUTED, label="expert humans")
ax.scatter([], [], s=40, marker="s", facecolor="white", edgecolor=MUTED, linewidth=1.6, label="GPT-4 judge")
ax.legend(loc="center right", frameon=False, handletextpad=0.3, bbox_to_anchor=(1.0, 0.47))
ax.set_title("(a) MT-Bench: expert vs GPT-4 judge", loc="left")

ax = axes[1]
drop = {s: cases[(s, "drop_top1")] for s in SOURCES}
rank_count = {s: r for r, s in enumerate(sorted(SOURCES, key=lambda s: drop[s]["k"]), start=1)}
rank_frac = {s: r for r, s in enumerate(sorted(SOURCES, key=lambda s: drop[s]["frac_pct"]), start=1)}
for s in SOURCES:
    moved = rank_count[s] != rank_frac[s]
    col = "#4a3aa7" if moved else "#9a9993"
    ax.plot([0, 1], [rank_count[s], rank_frac[s]], color=col, linewidth=2 if moved else 1.4,
            marker="o", markersize=5, zorder=3)
    ax.text(-0.06, rank_count[s], f"{SRC_SHORT[s]} ({drop[s]['k']})", ha="right", va="center",
            fontsize=8, color=INK if moved else MUTED)
    ax.text(1.06, rank_frac[s], f"{drop[s]['frac_pct']:.3g}%", ha="left", va="center",
            fontsize=8, color=INK if moved else MUTED)
ax.set_xlim(-1.0, 1.55)
ax.set_ylim(len(SOURCES) + 0.5, 0.5)
ax.set_xticks([0, 1])
ax.set_xticklabels(["count\n$k$", "fraction\n$k/n$"])
ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.tick_params(axis="x", length=0)
ax.set_title("(b) drop, top-1 rank (top = most fragile)", loc="left")
fig.tight_layout(w_pad=1.5)
save(fig, "controlled_contrasts", ["analysis/derived_stats.json#cases"])

# ---------------------------------------------------------------- concept-figure placeholder
# The orchestrator renders figures/protocol_overview.png after the drafting step.  Never
# overwrite a rendered figure: skip if the completion marker exists or the prompt log is non-empty.
concept_png = FIG / "protocol_overview.png"
concept_log = FIG / "protocol_overview.prompts.json"
already = (ROOT / ".concept_figure_complete").exists() or (
    concept_log.exists() and concept_log.read_text(encoding="utf-8").strip() not in ("", "{}"))
if not already and not concept_png.exists():
    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    ax.axis("off")
    ax.text(0.5, 0.5, "Protocol overview (placeholder; rendered by the concept-figure step)",
            ha="center", va="center", fontsize=10, color=MUTED)
    fig.savefig(concept_png, dpi=300)
    plt.close(fig)
if not already and not concept_log.exists():
    concept_log.write_text("{}\n", encoding="utf-8")
print("figures written")
