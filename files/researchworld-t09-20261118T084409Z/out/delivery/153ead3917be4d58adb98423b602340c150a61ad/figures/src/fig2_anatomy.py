"""Fig. 2 (C1): error follows leverage when the model is right; the network sandwich needs many independent 2-hop balls.
(a) RMSE vs n for REG-L against sqrt(sigma^2 L/n)  [results/summary/e1.csv, ER, linear response, p=.3, sigma=1]
(b) sd(tau_hat)/sqrt(sigma^2 L/n) in every cell    [e1.csv: 150 ER cells; e1b.csv: ER/SBM/BA/WS at n=2000]
(c) coverage of the iid and the network-sandwich interval vs effective independent units n/|2-hop ball|
    [e9.csv: ER/SBM/BA, n in 2000..16000, d in {10,40}, p=.5, linear and convex responses (no bias at p=.5)]"""
import os, sys
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import figstyle as S

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
R = lambda f: pd.read_csv(os.path.join(ROOT, "results", "summary", f))
OUT = os.path.join(ROOT, "figures", "fig2_anatomy.pdf")
e1 = R("e1.csv"); e1 = e1[e1.est == "REG-L"]
e1b = R("e1b.csv"); e1b = e1b[(e1b.est == "REG-L") & (e1b["out.kappa"] == 0)]
e9 = R("e9.csv"); e9 = e9[e9.est == "REG-L"]

S.apply()
fig, axs = S.fig("text", aspect=0.35, ncols=3, gridspec_kw={"width_ratios": [1, 1, 1.1]})

# (a) RMSE vs n
ax = axs[0]
ds = [5, 20, 80]; cols = ["#0072B2", "#E69F00", "#D55E00"]; mk = ["o", "s", "^"]
for d, c, m in zip(ds, cols, mk):
    x = e1[(e1["graph.d"] == d) & (e1["design.p"] == 0.3) & (e1["out.sigma"] == 1.0)].sort_values("graph.n")
    ax.fill_between(x["graph.n"], x.rmse_lo, x.rmse_hi, color=c, alpha=0.25, lw=0)
    ax.plot(x["graph.n"], x.rmse, color=c, marker=m, ms=3, lw=0.8, ls="none", label=f"$d={d}$")
    ax.plot(x["graph.n"], x.sd_iid_pred, color=c, lw=1.0, ls="--")
ax.set_xscale("log"); ax.set_yscale("log"); ax.minorticks_off()
ax.set_xticks([500, 1000, 2000, 4000, 8000]); ax.set_xticklabels(["500", "1k", "2k", "4k", "8k"])
ax.set_yticks([0.1, 0.2, 0.5, 1, 2]); ax.set_yticklabels(["0.1", "0.2", "0.5", "1", "2"])
ax.set_xlabel("sample size $n$"); ax.set_ylabel("RMSE of $\\hat\\tau$")
ax.set_title("(a) error vs $n$", fontsize=8)
ax.legend(loc="lower left", handlelength=1.2, borderaxespad=0.1)
ax.plot([], [], color="0.3", ls="--", lw=1.0, label="$\\sqrt{\\sigma^2L/n}$")
h, l = ax.get_legend_handles_labels(); ax.legend(h, l, loc="lower left", handlelength=1.4, borderaxespad=0.1, labelspacing=0.25)

# (b) ratio to the leverage formula
ax = axs[1]
ns = sorted(e1["graph.n"].unique()); cm = plt.get_cmap("viridis")
Rrep = int(e1.n_rep.iloc[0]); half = 1.96 / np.sqrt(2 * (Rrep - 1))
ax.axhspan(1 - half, 1 + half, color="0.85", lw=0, zorder=0)
ax.axhline(1, color="0.4", lw=0.6, zorder=1)
for i, n in enumerate(ns):
    x = e1[e1["graph.n"] == n]
    ax.plot(x["graph.d"] * 1.035 ** (i - 2) ** 1 * (1 + 0.04 * (i - 2)), x.sd / x.sd_iid_pred, ls="none", marker="o", ms=2.3,
            mfc=cm(i / (len(ns) - 1) * 0.9), mec="none", alpha=0.9, label=(f"$n={n}$" if i == 0 else f"{n}"))
FAM = {"er": "o", "sbm": "s", "ba": "^", "ws": "D"}
for k, m in FAM.items():
    x = e1b[e1b["graph.kind"] == k]
    ax.plot(x["graph.d"] * 1.28, x.sd / x.sd_iid_pred, ls="none", marker=m, ms=3, mfc="none", mec="k", mew=0.6,
            label=k.upper())
ax.set_xscale("log"); ax.set_xticks([5, 10, 20, 40, 80]); ax.set_xticklabels(["5", "10", "20", "40", "80"]); ax.minorticks_off()
ax.set_ylim(0.85, 1.2); ax.set_xlim(4, 120)
ax.set_xlabel("degree $d$"); ax.set_ylabel("sd / $\\sqrt{\\sigma^2L/n}$")
ax.set_title("(b) ratio, every cell", fontsize=8)

# (c) coverage vs effective independent units
ax = axs[2]
ax.axhline(0.95, color="0.4", lw=0.6)
for col, lab, c, m, off in [("iid", "iid OLS", "#0072B2", "o", 0.97), ("sandwich", "network sandwich", "#D55E00", "^", 1.03)]:
    y = e9[f"cover_{col}"]
    ax.errorbar(e9.n_indep * off, y, yerr=[y - e9[f"cover_{col}_lo"], e9[f"cover_{col}_hi"] - y], fmt=m, ms=2.6, color=c,
                elinewidth=0.5, capsize=0, label=lab, alpha=0.9)
ax.set_xscale("log"); ax.set_xticks([2, 5, 10, 30, 100]); ax.set_xticklabels(["2", "5", "10", "30", "100"]); ax.minorticks_off()
ax.set_ylim(0.4, 1.02); ax.set_xlabel("independent balls $n/|B_2|$"); ax.set_ylabel("95% interval coverage")
ax.set_title("(c) coverage", fontsize=8)
from matplotlib.lines import Line2D
ax.legend([Line2D([], [], ls="none", marker="o", ms=3, color="#0072B2"), Line2D([], [], ls="none", marker="^", ms=3, color="#D55E00")],
          ["iid OLS", "network sandwich"], loc="lower right", handletextpad=0.2, borderaxespad=0.1, labelspacing=0.25)

# legend for (b) under the figure
h, l = axs[1].get_legend_handles_labels()
fig.legend(h, l, loc="outside lower center", ncols=9, fontsize=8, handlelength=0.9, columnspacing=0.8, handletextpad=0.3,
           title=None)
S.save(fig, OUT)
