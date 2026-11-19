"""Build paper figures from paper_data.json (read-only evidence registry).

Outputs (PDF + 300 DPI PNG): figures/final_comparison, figures/variant_profile.
Also drops a guarded placeholder for the orchestrator-owned concept figure.
Run: python scripts/build_figures.py
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

# @evidence[[paper_data.json#final_evaluation]]
D = json.loads((ROOT / "paper_data.json").read_text(encoding="utf-8"))
FE = D["final_evaluation"]
M = FE["metrics"]  # @evidence[[paper_data.json#final_evaluation.metrics]]
EP = FE["evaluation_evidence"]["episodes"]  # @evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]

C_PROC = "#1f5fa8"   # studied procedure (final and development variant 2)
C_BASE = "#7a7a7a"   # evaluator baselines / plain Mondrian variant
C_V3 = "#2a9d8f"     # quantile-regression variant
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8.5,
                     "ytick.labelsize": 8.5, "axes.spines.top": False,
                     "axes.spines.right": False, "font.family": "DejaVu Sans"})


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def final_comparison():
    fig, (a, b) = plt.subplots(1, 2, figsize=(5.5, 2.3), gridspec_kw={"width_ratios": [1, 1.15]})
    m, lo, hi = M["score_margin_vs_best_baseline"], M["score_margin_ci_lower"], M["score_margin_ci_upper"]
    a.errorbar([m], [0], xerr=[[m - lo], [hi - m]], fmt="o", color=C_PROC, capsize=4, ms=6)
    a.axvline(0, color="k", lw=0.8, ls=":")
    a.set_yticks([])
    a.set_ylim(-1, 1)
    a.set_xlim(-0.01, 0.06)
    a.set_xlabel("Paired score margin vs. best baseline")
    a.text(m, 0.35, f"{m:.4f}", ha="center", fontsize=8.5)
    a.text(lo, -0.45, f"{lo:.4f}", ha="center", fontsize=8)
    a.text(hi, -0.45, f"{hi:.4f}", ha="center", fontsize=8)
    a.set_title("(a) Margin, 95% bootstrap interval", fontsize=9)
    seeds = [e["seed"] for e in EP]
    sc = [e["score"] for e in EP]
    x = np.arange(len(sc))
    b.scatter(x, sc, color=C_PROC, zorder=3, s=26)
    b.axhline(M["final_score"], color=C_PROC, lw=1.2, label=f"Aggregate score {M['final_score']:.3f}")
    b.axhline(M["best_baseline_score"], color=C_BASE, lw=1.2, ls="--",
              label=f"Best-baseline aggregate {M['best_baseline_score']:.3f}")
    b.set_xticks(x)
    b.set_xticklabels([str(s) for s in seeds], rotation=0)
    b.set_xlabel("Final seed")
    b.set_ylabel("Composite reliability score")
    b.set_ylim(0.78, 0.91)
    b.legend(frameon=False, fontsize=7.5, loc="upper center")
    b.set_title("(b) Per-seed scores", fontsize=9)
    fig.tight_layout()
    save(fig, "final_comparison")


def variant_profile():
    progs = sorted(D["all_programs"], key=lambda p: p["eval_index"])
    names = ["V1\nMondrian", "V2\n+gated wts", "V3\n+QR thr."]
    cols = [C_BASE, C_PROC, C_V3]
    # search-stage metrics are recorded in each variant's metrics file (also quoted in paper_data memory)
    met = []
    for tag in ("V1", "V2", "V3"):
        local = ROOT / "source_evidence" / tag / "metrics.json"
        met.append(json.loads(local.read_text(encoding="utf-8")))  # @evidence[[source_evidence/V2/metrics.json]]
    fig, axs = plt.subplots(2, 2, figsize=(5.5, 4.0))
    spec = [("shift_coverage_gap", "Shift-case marginal gap"),
            ("worst_slice_coverage_gap", "Worst-slice gap"),
            ("mean_set_size_ratio", "Set-size ratio")]
    x = np.arange(3)
    for ax, (k, t) in zip(axs.flat[:3], spec):
        v = [mm[k] for mm in met]
        ax.scatter(x, v, c=cols, s=48, zorder=3)
        for xi, vi in zip(x, v):
            ax.annotate(f"{vi:.3f}", (xi, vi), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels(names, fontsize=7.5)
        ax.set_title(t, fontsize=9)
        lo, hi = min(v), max(v)
        pad = (hi - lo) * 0.35 + 1e-3
        ax.set_ylim(lo - pad, hi + pad * 1.4)
        ax.set_xlim(-0.5, 2.5)
    ax = axs.flat[3]
    for i, p in enumerate(progs):
        sc = [e["score"] for e in p["evaluation_evidence"]["episodes"]]  # @evidence[[paper_data.json#all_programs]]
        ax.scatter([i] * len(sc), sc, color=cols[i], s=22, alpha=0.8, zorder=3)
        ax.hlines(np.mean(sc), i - 0.25, i + 0.25, color="k", lw=1.5, zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=7.5)
    ax.set_title("Per-seed development score\n(bar = mean of 3 seeds)", fontsize=9)
    ax.set_xlim(-0.5, 2.5)
    fig.tight_layout()
    save(fig, "variant_profile")


def loss_decomposition():
    # @evidence[[derived/derived_stats.json#final_loss_decomposition]]
    dd = json.loads((ROOT / "derived" / "derived_stats.json").read_text(encoding="utf-8"))["final_loss_decomposition"]
    parts = [("Marginal term (implied)", dd["implied_marginal_term_0.5x"], "#c0504d"),
             ("Worst-slice term", dd["slice_term_0.25x"], "#e6a23c"),
             ("Set-size term", dd["size_term_0.25x"], C_PROC)]
    fig, ax = plt.subplots(figsize=(5.5, 2.6))
    left = 0.0
    for name, v, c in parts:
        ax.barh([1], [v], left=left, color=c, label=f"{name}: {v:.4f}", height=0.55)
        left += v
    ax.barh([0], [dd["best_baseline_mean_loss"]], color="white", edgecolor=C_BASE, hatch="///",
            height=0.55, label=f"Best baseline total (not decomposed): {dd['best_baseline_mean_loss']:.4f}")
    ax.text(left + 0.003, 1, f"{left:.4f}", va="center", fontsize=8.5)
    ax.text(dd["best_baseline_mean_loss"] + 0.003, 0, f"{dd['best_baseline_mean_loss']:.4f}", va="center", fontsize=8.5)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Best baseline", "Studied\nprocedure"])
    ax.set_xlim(0, 0.27)
    ax.set_xlabel("Mean loss (1 $-$ composite score), sealed final")
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=7.5, loc="lower center", ncol=2)
    fig.subplots_adjust(left=0.2, right=0.97, top=0.97, bottom=0.42)
    save(fig, "loss_decomposition")


def concept_placeholder():
    if (ROOT / ".concept_figure_complete").exists():
        return
    prompts = FIG / "protocol_overview.prompts.json"
    if prompts.exists() and prompts.read_text().strip() not in ("", "{}"):
        return
    png = FIG / "protocol_overview.png"
    if png.exists() and (prompts.exists() and prompts.read_text().strip() not in ("", "{}")):
        return
    fig = plt.figure(figsize=(5.5, 1.8))
    fig.text(0.5, 0.5, "protocol overview (placeholder)", ha="center", va="center")
    fig.savefig(png, dpi=300)
    plt.close(fig)
    if not prompts.exists():
        prompts.write_text("{}\n")


if __name__ == "__main__":
    final_comparison()
    variant_profile()
    loss_decomposition()
    concept_placeholder()
