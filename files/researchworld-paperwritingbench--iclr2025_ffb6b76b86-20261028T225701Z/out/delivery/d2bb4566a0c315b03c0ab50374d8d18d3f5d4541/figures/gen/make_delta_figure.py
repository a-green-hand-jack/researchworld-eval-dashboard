"""figures/fig_deltas.pdf: (a) byte-minus-token score per model and benchmark,
(b) top-2 byte ensemble minus best single model. Source: gen/data.py (experimental log)."""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
from data import *

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "Liberation Serif", "Nimbus Roman", "DejaVu Serif"],
                     "font.size": 8, "axes.linewidth": 0.6, "pdf.fonttype": 42})
INK, MUTED, GRID = "#222222", "#6b6b6b", "#e3e3e3"
MODELS = [("Llama2-7B", T2["Llama2-7B"], "#1b6ca8"), ("Yi-1.5-6B", T2["Yi-1.5-6B"], "#d95f02"),
          ("Mistral-7B-v0.3", T2["Mistral-7B-v0.3"], "#1b9e77"),
          ("CodeLlama-7b", T3["CodeLlama-7b"], "#7b3294"), ("CodeLlama-13b", T3["CodeLlama-13b"], "#8c8c3a"),
          ("Yi-Coder-1.5B", T3["Yi-Coder-1.5B"], "#c51b7d")]
MARK = ["o", "s", "^", "D", "v", "P"]
BENCH = T2_BENCH + T3_BENCH
ALL = {**{m: d for m, d in T2.items()}, **{m: d for m, d in T3.items()}}

fig, (a, b) = plt.subplots(1, 2, figsize=(5.5, 2.6), gridspec_kw={"width_ratios": [1.45, 1]}, sharey=False)
y = {bn: i for i, bn in enumerate(BENCH[::-1])}
for k, (m, d, c) in enumerate(MODELS):
    for bn in d:
        a.scatter(d[bn][1] - d[bn][0], y[bn] + (k - 2.5) * 0.09, s=16, color=c, marker=MARK[k],
                  edgecolor="white", linewidth=0.4, zorder=3, label=m if bn == list(d)[0] else None)
a.axvline(0, color=INK, lw=0.7, zorder=2)
a.set_title("(a) byte-level $-$ token-level", fontsize=8.5, color=INK, loc="left")
a.set_xlabel("score difference (points)", color=INK)
a.set_xlim(-4.2, 2.4)
b_vals = []
for bn in BENCH:
    best_single = max(x for m, d in ALL.items() if bn in d for x in d[bn])
    ens = T2_ENS[bn] if bn in T2_ENS else T3_ENS[bn]
    b_vals.append(ens - best_single)
cols = ["#1b6ca8" if v > 0 else ("#b2182b" if v < 0 else MUTED) for v in b_vals]
b.barh([y[bn] for bn in BENCH], b_vals, height=0.5, color=cols, zorder=3)
for bn, v in zip(BENCH, b_vals):
    b.text(v + (0.25 if v >= 0 else -0.25), y[bn], "%+.1f" % v, va="center", ha="left" if v >= 0 else "right",
           fontsize=7, color=INK)
b.axvline(0, color=INK, lw=0.7, zorder=2)
b.set_title("(b) ensemble $-$ best single", fontsize=8.5, color=INK, loc="left")
b.set_xlabel("score difference (points)", color=INK)
b.set_xlim(-8.0, 6.5)
for ax in (a, b):
    ax.set_yticks(list(y.values()))
    ax.set_yticklabels(list(y.keys()) if ax is a else [], color=INK)
    ax.set_ylim(-0.6, len(BENCH) - 0.4)
    ax.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    ax.axhline(1.5, color=MUTED, lw=0.4, ls=":")  # code | general separator
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=2, width=0.5, colors=INK)
b.set_yticks([])
h, l = a.get_legend_handles_labels()
fig.legend(h, l, loc="lower left", fontsize=6.5, frameon=False, handletextpad=0.1, columnspacing=1.0, ncol=6,
           bbox_to_anchor=(0.0, 0.0))
fig.tight_layout(pad=0.4, w_pad=0.8, rect=(0, 0.07, 1, 1))
os.makedirs(os.path.join(os.path.dirname(__file__), ".."), exist_ok=True)
fig.savefig(os.path.join(os.path.dirname(__file__), "..", "fig_deltas.pdf"))
fig.savefig("/tmp/fig_deltas.png", dpi=200)
print(b_vals)
