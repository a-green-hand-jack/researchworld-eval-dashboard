"""Fig. 1: the corner picture. Reads results/fig1_corner.parquet (ER n=1e4, p=0.25, kappa=1, REG-L, one draw)."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import figstyle as S
import matplotlib.pyplot as plt

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SHAPE = sys.argv[1] if len(sys.argv) > 1 else "convex"
OUT = os.path.join(ROOT, "figures", "fig1_corner.pdf")

df = pd.read_parquet(os.path.join(ROOT, "results", "fig1_corner.parquet"))
df = df[df["shape"] == SHAPE]
S.apply()
fig, axs = S.fig("text", aspect=0.34, ncols=2, sharey=True)
C0, C1 = "#0072B2", "#D55E00"   # control / treated branch
rng = np.random.default_rng(0)
for ax, d in zip(axs, sorted(df["d"].unique())):
    x = df[df["d"] == d]
    smp = x[x.kind == "sample"]
    for z, c in ((0, C0), (1, C1)):
        s = smp[smp.z == z]
        s = s.iloc[rng.permutation(len(s))[:400]]
        ax.scatter(s.g, s.value, s=2, color=c, alpha=0.25, linewidths=0, rasterized=True)
        t = x[(x.kind == "true") & (x.z == z)]
        f = x[(x.kind == "fit") & (x.z == z)]
        ax.plot(t.g, t.value, color=c, lw=1.4)
        ax.plot(f.g, f.value, color=c, lw=1.2, ls="--")
    ct = x[x.kind == "corner_true"]; cp = x[x.kind == "corner_pred"]
    ax.scatter(ct.g, ct.value, marker="o", s=22, facecolor="white", edgecolor="k", zorder=5, linewidths=0.9)
    ax.scatter(cp.g, cp.value, marker="x", s=22, color="k", zorder=5, linewidths=0.9)
    gs = float(x[x.kind == "g_sd"].value.iloc[0]); p = float(x.p.iloc[0])
    ax.axvspan(p - 2 * gs, p + 2 * gs, color="0.85", zorder=0, lw=0)
    gt, gh = float(x[x.kind == "gate"].value.iloc[0]), float(x[x.kind == "gate_hat"].value.iloc[0])
    ax.set_title(f"$d\\approx{x.d_mean.iloc[0]:.0f}$:  GATE {gt:.2f},  estimate {gh:.2f}", loc="left")
    ax.set_xlabel("treated-neighbour fraction $g$")
    ax.set_xlim(-0.02, 1.02)
axs[0].set_ylabel("outcome")
from matplotlib.lines import Line2D
h = [Line2D([], [], color=C1, lw=1.4), Line2D([], [], color=C0, lw=1.4),
     Line2D([], [], color="k", lw=1.2, ls="--"),
     Line2D([], [], marker="o", mfc="white", mec="k", ls="", ms=4), Line2D([], [], marker="x", color="k", ls="", ms=4)]
from matplotlib.patches import Patch
h.append(Patch(color="0.85"))
fig.legend(h, ["treated", "control", "REG-L fit", "true corner", "predicted", r"$p\pm2\,$sd$(g)$"],
           loc="outside lower center", ncols=6, fontsize=8, handlelength=1.4, columnspacing=0.8, handletextpad=0.4)
S.save(fig, OUT)
