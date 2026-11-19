"""Build quantitative figures from derived/resolution.json (itself derived from paper_data.json).

Run: PYTHONPATH=$PYLIB python3 scripts/build_figures.py   (after scripts/derive_resolution.py)
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

root = Path(__file__).resolve().parent.parent
R = json.loads((root / "derived/resolution.json").read_text())  # @evidence[[derived/resolution.json]]
fig_dir = root / "figures"
fig_dir.mkdir(exist_ok=True)

C_CAND, C_REF, C_BOUND = "#1f5fa8", "#d9822b", "#6b6b6b"
C_SUP, C_INC, C_REF_REG = "#d7ead7", "#eeeeee", "#f2d9d9"
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
                     "legend.fontsize": 8.5, "axes.titlesize": 10, "pdf.fonttype": 42, "font.family": "DejaVu Sans"})


def save(fig, name):
    fig.savefig(fig_dir / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(fig_dir / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---- Figure: slope interval vs decision rule ------------------------------------------------
b = R["max_abs_slope_attainable"]
fig, ax = plt.subplots(figsize=(5.2, 2.5))
ax.axvspan(-b, 0, color=C_SUP, zorder=0)
ax.axvspan(0, b, color=C_REF_REG, zorder=0)
ax.text(-b / 2, 3.0, "CI entirely < 0:\nsupported", ha="center", va="center", fontsize=8.5)
ax.text(b / 2, 3.0, "CI $\\geq$ 0:\nrefuted", ha="center", va="center", fontsize=8.5)
ax.axvline(0, color="k", lw=1.0, zorder=1)
for s_ in (-b, b):
    ax.axvline(s_, color=C_BOUND, lw=1.0, ls=":", zorder=1)
ax.errorbar([R["slope"]], [1.55], xerr=[[R["ci_lower_arm"]], [R["ci_upper_arm"]]], fmt="o", color=C_CAND,
            capsize=4, lw=2, ms=6, zorder=3, label="model, 4 seeds, 95% CI")
ax.plot([R["reference_slope"]], [0.85], "D", color=C_REF, ms=6.5, zorder=3,
        label="reference, 1 seed")
mn = lambda v: f"{v:.3f}".replace("-", "\u2212")
ax.text(R["slope"], 1.95, f"{mn(R['slope'])}  [{mn(R['ci_low'])}, {mn(R['ci_high'])}]\nCI straddles 0",
        ha="center", va="bottom", fontsize=8, color=C_CAND, zorder=4,
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
ax.text(R["reference_slope"], 0.52, mn(R["reference_slope"]), ha="center", va="top", fontsize=8, color=C_REF)
ax.set_ylim(-0.45, 3.35)
ax.set_yticks([])
ax.set_xlim(-1.25, 1.25)
ax.set_xlabel("slope of ln(delay) vs $\\log_2$(width)")
ax.text(-b + 0.015, -0.33, f"$-{b:.2f}$", ha="left", va="center", fontsize=8, color=C_BOUND)
ax.text(b - 0.015, -0.33, f"$+{b:.2f}$", ha="right", va="center", fontsize=8, color=C_BOUND)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.5), frameon=False, ncol=1)
for sp in ("left", "right", "top"):
    ax.spines[sp].set_visible(False)
save(fig, "slope_interval_vs_decision_rule")

# ---- Figure: search-plane descriptive comparison ---------------------------------------------
V = R["search"]["variants"]
labels = ["V1\ninit scale", "V2\n+ output\nscaling", "V3\n+ hidden\nreparam."]
seeds = sorted({s for v in V for s in v["seed_scores"]})
# Drawn at 8.5 in wide (2400 px at 300 DPI) with fonts scaled by 1.5 so that, at full text width, rendered sizes stay near 9 pt.
S = 1.5
fig, axs = plt.subplots(1, 2, figsize=(8.5, 3.6), gridspec_kw={"width_ratios": [1.25, 1]})
ax = axs[0]
x = np.arange(len(V))
for k, s_ in enumerate(seeds):
    ax.plot(x + (k - 0.5) * 0.14, [v["seed_scores"][s_] for v in V], "o", color="#5a8fc7",
            mfc="white" if k else "#5a8fc7", ms=6 * S, label="per seed" if k == 0 else None)
ax.plot(x, [v["score"] for v in V], "_", color="k", ms=20 * S, mew=2 * S, label="mean of 2 seeds")
ax.set_xticks(x, labels)
ax.set_ylabel("validation-accuracy AUC", fontsize=9 * S)
ax.tick_params(labelsize=8.5 * S)
ax.set_ylim(0.74, 0.92)
ax.set_title("(a) development score", fontsize=10 * S)
ax.legend(frameon=False, loc="upper left", fontsize=8 * S)
ax = axs[1]
ax.bar(x, [v["n_censored_runs"] for v in V], color="#b8b8b8", width=0.55)
for xi, v in zip(x, V):
    ax.text(xi, v["n_censored_runs"] + 0.12, f"{v['n_censored_runs']}/{v['n_runs']}", ha="center", fontsize=8.5 * S)
ax.set_xticks(x, labels)
ax.set_ylabel("censored runs", fontsize=9 * S)
ax.tick_params(labelsize=8.5 * S)
ax.set_ylim(0, 7.2)
ax.set_title("(b) censoring", fontsize=10 * S)
for a in axs:
    for sp in ("right", "top"):
        a.spines[sp].set_visible(False)
fig.tight_layout()
save(fig, "search_variants_descriptive")

# ---- Placeholder for the orchestrator-rendered concept figure (never overwrite a real render) --
cf = root / "figures/protocol_overview"
if not (root / ".concept_figure_complete").exists() and not (
        cf.with_suffix(".prompts.json").exists() and cf.with_suffix(".prompts.json").stat().st_size > 4):
    fig = plt.figure(figsize=(8, 2.4))
    fig.text(0.5, 0.5, "protocol overview (placeholder; rendered by orchestrator)", ha="center", va="center")
    fig.savefig(cf.with_suffix(".png"), dpi=300)
    plt.close(fig)
    cf.with_suffix(".prompts.json").write_text("{}")
print("figures written")
