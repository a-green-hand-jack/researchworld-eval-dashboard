"""Fig. 1 (C1): smallest verified attack that swaps an adjacent pair of the ranking vs. the pair's standardised gap.
Points = adjacent pairs of the full-data ranking (budget_k/N, remove | flip); light diamonds = NBA seasons (top-1 vs rank 2).
Reads results/adjacent_pairs_<ds>.csv, results/nba_seasons.csv. Usage: fig1_fragility_vs_gap.py [RESULTS_DIR] [OUT_DIR]"""
import sys, os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
sys.path.insert(0, os.path.dirname(__file__)); import style, common
res = sys.argv[1] if len(sys.argv) > 1 else "results"; out = sys.argv[2] if len(sys.argv) > 2 else "figures"
style.apply(); os.makedirs(out, exist_ok=True)
adj = common.load(res, "adjacent_pairs")
ns = pd.read_csv(f"{res}/nba_seasons.csv"); ns = ns[ns.replicate < 0]
fig, axs = plt.subplots(1, 2, figsize=(style.TEXTW, 2.45), sharex=True, sharey=True)
fmt = FuncFormatter(lambda v, _: f"{v:g}")
zero = 0
for ax, mode, col_s in zip(axs, ("drop", "flip"), ("top1_drop", "top1_flip")):
    s = ns[(ns[col_s] > 0) & (ns.z_top > 0)]; zero = int(((ns[col_s] <= 0) | (ns.z_top <= 0)).sum())
    ax.scatter(s.z_top, s[col_s] / s.N * 100, marker="+", s=9, color=style.DATASETS["nba"][1], alpha=0.6, lw=0.6, label="NBA single seasons (leader vs. ranks 2-4)")
    for k, d in adj.items():
        lab, col, mk, ls = style.DATASETS[k]
        if k == "nba": lab = "NBA pooled over all seasons"
        d = d[(d[f"k_{mode}"] > 0) & (d.z > 0)]
        ax.scatter(d.z, d[f"k_{mode}"] / d.N * 100, marker=mk, s=14 if len(d) > 10 else 22, color=col, label=lab, lw=0, alpha=0.9)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.grid(alpha=0.25, lw=0.4)
    ax.xaxis.set_major_formatter(fmt); ax.yaxis.set_major_formatter(fmt)
    ax.set_xlabel("pair gap in standard errors, $z$"); ax.set_title({"drop": "(a) remove $k$ comparisons", "flip": "(b) flip $k$ comparisons"}[mode], loc="left")
axs[0].set_ylabel("smallest swap found, $k/N$ (%)")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, fontsize=6.5, columnspacing=0.8, handletextpad=0.2, bbox_to_anchor=(0.5, -0.1))
fig.tight_layout(w_pad=1.0); fig.savefig(f"{out}/fig1_fragility_vs_gap.pdf"); fig.savefig(f"{out}/fig1_fragility_vs_gap.png", dpi=200)
print("NBA seasons excluded from log axes (k=0 or z=0):", zero)
