"""Fig. A1 (C4, appendix): SYNTHETIC Bradley-Terry worlds (true scores ~ N(0, sigma^2), random pairing; not real data).
Smallest verified top-1 removal attack vs. the fitted leader gap z_top, against z_top (a) and against z_top*sqrt(N/p) (b), the scaling suggested by the log-log regression in results/summary_synthetic_regression.csv; colour = (participants p, comparisons N).
Reads results/synthetic.csv. Usage: figA1_synthetic.py [RESULTS_DIR] [OUT_DIR]"""
import sys, os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
sys.path.insert(0, os.path.dirname(__file__)); import style
res = sys.argv[1] if len(sys.argv) > 1 else "results"; out = sys.argv[2] if len(sys.argv) > 2 else "figures"
style.apply(); os.makedirs(out, exist_ok=True)
s = pd.read_csv(f"{res}/synthetic.csv"); s = s[(s.top1_drop > 0) & (s.z_top > 0)]
cfg = sorted(s.groupby(["p", "N"]).groups); cols = plt.cm.viridis(np.linspace(0.05, 0.9, len(cfg)))
fig, axs = plt.subplots(1, 2, figsize=(style.TEXTW, 2.45), sharex=False)
for (p, N), c in zip(cfg, cols):
    for sg, mk in ((0.3, "o"), (1.0, "^")):
        g = s[(s.p == p) & (s.N == N) & (s.sigma == sg)]
        if g.empty: continue
        axs[0].scatter(g.z_top, g.top1_drop, s=7, marker=mk, color=c, alpha=0.6, lw=0)
        axs[1].scatter(g.z_top * np.sqrt(N / p), g.top1_drop, s=7, marker=mk, color=c, alpha=0.6, lw=0)
for ax, yl, t, xl in zip(axs, ("smallest removal found, $k$", "smallest removal found, $k$"), ("(a) leader gap", "(b) gap scaled by $\\sqrt{N/p}$"), ("fitted leader gap, $z_{\\rm top}$ (SE units)", "$z_{\\rm top}\\sqrt{N/p}$")):
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel(xl); ax.set_ylabel(yl); ax.set_title(t, loc="left")
    ax.grid(alpha=0.25, lw=0.4); ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}")); ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
h = [plt.Line2D([], [], marker="o", ls="none", color=c, ms=4, label=f"$p{{=}}{p}$, $N{{=}}{N // 1000 if N >= 10000 else N / 1000:g}$k") for (p, N), c in zip(cfg, cols)]
h += [plt.Line2D([], [], marker=m, ls="none", color="0.3", ms=4, label=f"$\\sigma{{=}}{sg}$") for sg, m in ((0.3, "o"), (1.0, "^"))]
fig.legend(handles=h, loc="lower center", ncol=4, fontsize=6.3, columnspacing=0.8, handletextpad=0.2, bbox_to_anchor=(0.5, -0.17))
fig.suptitle("SYNTHETIC data (simulated Bradley-Terry worlds)", fontsize=7, y=1.02, color="#a00")
fig.tight_layout(w_pad=1.0); fig.savefig(f"{out}/figA1_synthetic.pdf"); fig.savefig(f"{out}/figA1_synthetic.png", dpi=200)
