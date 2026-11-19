"""Build derived metric files and quantitative figures for the paper.

All numbers are read from paper_data.json (final evaluation) and the per-variant metrics.json files (search).
Run: python build_figures.py
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
pd_ = json.load(open(ROOT / "paper_data.json"))
# @evidence[[paper_data.json#final_evaluation.metrics]]
fin = pd_["final_evaluation"]["metrics"]
episodes = pd_["final_evaluation"]["evaluation_evidence"]["episodes"]

variants = {}
for key in ("c01", "c02", "c03"):
    # @evidence[[derived/search_inputs/c02_metrics.json]]
    m = json.load(open(ROOT / f"derived/search_inputs/{key}_metrics.json"))
    ev = json.load(open(ROOT / f"derived/search_inputs/{key}_evaluation_evidence.json"))
    m["per_seed_utility"] = [e["score"] for e in ev["episodes"]]
    m["per_seed_seeds"] = [e["seed"] for e in ev["episodes"]]
    variants[key] = m

derived = {
    "final": {**fin, "per_seed_utility": [e["score"] for e in episodes], "seeds": [e["seed"] for e in episodes],
              "baseline_mae_derived": {
                  "random_mean": fin["mae"] + fin["delta_mae_vs_random_mean"],
                  "anchor_points": fin["mae"] + fin["delta_mae_vs_anchor_points"],
                  "irt_style": fin["mae"] + fin["delta_mae_vs_irt_style"]}},
    "search": variants,
}
json.dump(derived, open(ROOT / "derived/metrics_summary.json", "w"), indent=1)

C = {"cand": "#1f4e9c", "rand": "#7f7f7f", "anchor": "#d9822b", "irt": "#3a9d5d",
     "random_t": "#8fb4e3", "strong_t": "#1f4e9c"}
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9.5, "xtick.labelsize": 8,
                     "ytick.labelsize": 8.5, "legend.fontsize": 8.5, "axes.spines.top": False,
                     "axes.spines.right": False})

def save(fig, name):
    fig.savefig(ROOT / f"figures/{name}.pdf", bbox_inches="tight")
    fig.savefig(ROOT / f"figures/{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

# ---- Fig 2: main comparison -------------------------------------------------
b = derived["final"]["baseline_mae_derived"]
names = ["Stacked", "Random\nmean", "Anchor\npoints", "IRT-\nstyle"]
vals = [fin["mae"], b["random_mean"], b["anchor_points"], b["irt_style"]]
cols = [C["cand"], C["rand"], C["anchor"], C["irt"]]
fig, ax = plt.subplots(1, 2, figsize=(5.5, 2.45), gridspec_kw={"width_ratios": [1.2, 1]})
bars = ax[0].bar(range(4), vals, color=cols, width=0.65)
for i, (bar, v) in enumerate(zip(bars, vals)):
    if i > 0:
        bar.set_hatch("//"); bar.set_edgecolor("white")
    ax[0].text(i, v + 0.0012, f"{v:.4f}", ha="center", fontsize=8)
ax[0].set_xticks(range(4)); ax[0].set_xticklabels(names)
ax[0].set_ylabel("MAE (lower is better)"); ax[0].set_ylim(0, 0.082)
ax[0].set_title("(A) Overall MAE, held-out benchmarks")
# @evidence[[paper_data.json#final_evaluation.metrics.delta_mae_vs_best_baseline]]
rows = [("MAE gap", fin["delta_mae_vs_best_baseline"], fin["ci_lo_delta_mae_vs_best_baseline"], fin["ci_hi_delta_mae_vs_best_baseline"]),
        ("Utility gap", fin["delta_score_vs_best_baseline"], fin["ci_lo_delta_score_vs_best_baseline"], fin["ci_hi_delta_score_vs_best_baseline"])]
for i, (lab, m, lo, hi) in enumerate(rows):
    ax[1].errorbar(m, i, xerr=[[m - lo], [hi - m]], fmt="o", color=C["cand"], capsize=4, lw=1.6, ms=6)
    ax[1].text(hi + 0.002, i + 0.18, f"{m:+.4f}\n[{lo:+.4f}, {hi:+.4f}]", fontsize=7.5, va="bottom")
ax[1].axvline(0, color="k", lw=0.8, ls="--")
ax[1].set_yticks([0, 1]); ax[1].set_yticklabels([r[0] for r in rows]); ax[1].set_ylim(-0.6, 1.9)
ax[1].set_xlim(-0.025, 0.075); ax[1].set_xticks([-0.02, 0.02, 0.06])
ax[1].set_xlabel("Gain vs. random mean (>0 favours ours)")
ax[1].set_title("(B) Paired gain, 95% bootstrap CI")
fig.tight_layout(w_pad=1.2)
save(fig, "main_comparison")

# ---- Fig 3: extrapolation gap ----------------------------------------------
s = variants["c02"]
groups = ["Development\n(search, 2 seeds)", "Held-out\n(final, 3 seeds)"]
data = {"mae": [(s["mae_random_targets"], s["mae_strong_targets"]), (fin["mae_random_targets"], fin["mae_strong_targets"])],
        "spearman": [(s["spearman_random_targets"], s["spearman_strong_targets"]), (fin["spearman_random_targets"], fin["spearman_strong_targets"])]}
fig, ax = plt.subplots(1, 2, figsize=(5.5, 2.4))
w = 0.36
for a, (met, title, yl) in zip(ax, [("mae", "(A) MAE", "MAE (lower is better)"), ("spearman", "(B) Spearman", "Spearman (higher is better)")]):
    for j, (reg, col, lab) in enumerate([(0, C["random_t"], "Random targets"), (1, C["strong_t"], "Strong targets")]):
        v = [data[met][g][reg] for g in range(2)]
        pos = np.arange(2) + (j - 0.5) * w
        a.bar(pos, v, w, color=col, label=lab)
        for p, vv in zip(pos, v):
            a.text(p, vv + (0.0012 if met == "mae" else 0.006), f"{vv:.3f}" if met == "spearman" else f"{vv:.4f}", ha="center", fontsize=7.5)
    a.set_xticks(range(2)); a.set_xticklabels(groups); a.set_title(title); a.set_ylabel(yl)
ax[0].set_ylim(0, 0.06); ax[1].set_ylim(0, 1.1)
ax[0].legend(loc="upper left", frameon=False, fontsize=8)
fig.tight_layout(w_pad=1.5)
save(fig, "extrapolation_gap")

# ---- Overview placeholder (orchestrator renders the real figure) -------------
if not (ROOT / ".concept_figure_complete").exists():
    p = ROOT / "figures/overview_protocol.prompts.json"
    if not (p.exists() and p.stat().st_size > 2):
        fig = plt.figure(figsize=(5.5, 2.2)); fig.text(0.5, 0.5, "overview placeholder", ha="center")
        fig.savefig(ROOT / "figures/overview_protocol.png", dpi=300); plt.close(fig)
        p.write_text("{}")
print("done")
