"""figures/gap_ablations.{pdf,png}: |Retrained - Unlearned(-)| per metric vs the three ablation axes (CIFAR-10, from data.py)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from data import *

plt.rcParams.update({"mathtext.fontset": "stix", "font.family": "serif", "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
                     "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9, "legend.fontsize": 8,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "lines.linewidth": 1.4, "lines.markersize": 5})
METRICS = ["Test acc.", "Remaining acc.", "Forget acc.", "MIA score"]
# colour-blind-safe (Okabe-Ito) + distinct markers and linestyles
STY = [("#0072B2", "o", "-"), ("#E69F00", "s", "--"), ("#009E73", "^", "-."), ("#CC79A7", "D", ":")]

panels = [
    ("Forget-set size (%)", [5, 10, 15], [gap(*FORGET[s]) for s in (5, 10, 15)], ["5", "10", "15"]),
    ("# perturbations", [250, 500, 1000], [gap(PERT_RETRAINED, PERT[n]) for n in (250, 500, 1000)], ["250", "500", "1000"]),
    (r"$\ell_2$ regularisation $\lambda$", [0, 1, 2], [gap(LAM_RETRAINED, LAM[l]) for l in (0, 0.0005, 0.001)], ["0", r"$5{\times}10^{-4}$", r"$10^{-3}$"]),
]
fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.1), sharey=True)
for ax, (xl, xs, gaps, labs) in zip(axes, panels):
    xpos = list(range(3))
    for k, name in enumerate(METRICS):
        c, m, ls = STY[k]
        ax.plot(xpos, [g[k] for g in gaps], color=c, marker=m, ls=ls, label=name, clip_on=False)
    ax.set_xticks(xpos); ax.set_xticklabels(labs); ax.set_xlabel(xl)
    ax.set_xlim(-0.25, 2.25); ax.set_ylim(-0.5, 17); ax.grid(axis="y", lw=0.4, alpha=0.5)
    ax.spines[["top", "right"]].set_visible(False)
axes[0].set_ylabel("Gap to Retrained (pp)")
for ax, t in zip(axes, "abc"):
    ax.set_title(f"({t})", loc="left", fontsize=9)
axes[0].legend(frameon=False, loc="upper left", handlelength=2.6)
fig.tight_layout(pad=0.4)
out = os.path.join(os.path.dirname(__file__), "..", "figures")
fig.savefig(os.path.join(out, "gap_ablations.pdf")); fig.savefig(os.path.join(out, "gap_ablations.png"), dpi=300)
