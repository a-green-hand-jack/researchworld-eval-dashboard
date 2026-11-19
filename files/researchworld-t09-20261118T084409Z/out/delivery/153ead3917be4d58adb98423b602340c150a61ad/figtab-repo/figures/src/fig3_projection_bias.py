"""Fig. 3 (C2): the bias floor is the exact projection bias and does not shrink with n.
(a) measured REG-L bias vs bias predicted from the design alone (no fitting noise), all 320 cells  [results/summary/e2.csv]
(b) bias vs n at d=20, p=1/4, kappa=1, sigma=.5 for REG-L, REG-Q, REG-O                           [results/summary/e2b.csv]"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import figstyle as S

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
R = lambda f: pd.read_csv(os.path.join(ROOT, "results", "summary", f))
OUT = os.path.join(ROOT, "figures", "fig3_projection_bias.pdf")
e2 = R("e2.csv"); e2 = e2[e2.est == "REG-L"]
e2b = R("e2b.csv"); e2b = e2b[e2b["out.sigma"] == 0.5]

S.apply()
fig, axs = S.fig("text", aspect=0.34, ncols=2, gridspec_kw={"width_ratios": [1, 1.25]})

ax = axs[0]
SH = {"convex": ("convex", "#0072B2", "o"), "concave": ("concave", "#E69F00", "s"), "thresh": ("threshold", "#D55E00", "^")}
lim = (-1.0, 1.75)
ax.plot(lim, lim, color="0.4", lw=0.7, zorder=0)
for k, (lab, c, m) in SH.items():
    x = e2[e2["out.shape"] == k]
    ax.errorbar(x.bias_pred, x.bias, yerr=1.96 * x.bias_se, fmt=m, ms=2.4, color=c, mfc="none", mew=0.6, elinewidth=0.4,
                capsize=0, label=lab, alpha=0.9)
r = np.corrcoef(e2.bias_pred, e2.bias)[0, 1]
ax.text(0.04, 0.96, f"{len(e2)} cells: $r={r:.4f}$\nmedian |gap| {np.median(np.abs(e2.bias - e2.bias_pred)):.3f}", transform=ax.transAxes, va="top", fontsize=8)
ax.set_xlim(lim); ax.set_ylim(lim); ax.set_box_aspect(1)
ax.set_xlabel("bias predicted from the design"); ax.set_ylabel("measured bias of REG-L")
ax.legend(loc="lower right", handletextpad=0.2, borderaxespad=0.1, labelspacing=0.25)
ax.set_title("(a) all cells", fontsize=8)

ax = axs[1]
ser = [("REG-L", "convex", "reg", "o", "REG-L, convex"), ("REG-L", "thresh", "reg", "s", "REG-L, threshold"),
       ("REG-Q", "thresh", "flex", "D", "REG-Q, threshold"), ("REG-O", "thresh", "reg_o", "x", "REG-O (true shape)")]
for est, sh, key, m, lab in ser:
    x = e2b[(e2b.est == est) & (e2b["out.shape"] == sh)].sort_values("graph.n")
    ax.errorbar(x["graph.n"], x.bias, yerr=1.96 * x.bias_se, fmt=m, ms=3, color=S.COLORS[key], elinewidth=0.6, capsize=0,
                mfc=S.COLORS[key] if sh == "convex" else "none", mew=0.8, ls="none")
    if est != "REG-O":
        ax.plot(x["graph.n"], x.bias_pred, color=S.COLORS[key], lw=1.0, ls="--")
    xr = x["graph.n"].max() * 1.12
    ax.text(xr, x.bias.iloc[-3:].mean() + {"REG-O": 0.13, "REG-Q": 0.0}.get(est, -0.1 if sh == "thresh" else 0.0), lab, color=S.COLORS[key] if key != "reg_o" else "#2b8cbe",
            fontsize=8, va="center")
ax.axhline(-1.0, color="k", lw=0.8, ls=":")
ax.text(260, -0.93, "DM ($-\\gamma$)", fontsize=8, va="bottom")
ax.axhline(0, color="0.6", lw=0.5, zorder=0)
ax.set_xscale("log"); ax.set_xticks([250, 500, 1000, 2000, 4000, 8000]); ax.set_xticklabels(["250", "500", "1k", "2k", "4k", "8k"])
ax.minorticks_off(); ax.set_xlim(220, 8000 * 4.2)
ax.set_ylim(-1.2, 1.8); ax.set_xlabel("sample size $n$"); ax.set_ylabel("bias of $\\hat\\tau$ ($d=20$, $p=0.25$)")
ax.set_title("(b) bias vs $n$ (dashed: predicted)", fontsize=8)
S.save(fig, OUT)
