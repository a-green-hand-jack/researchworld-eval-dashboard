"""Fig. 4 (C3): RMSE vs degree d for regression, DM, exact HT and Hajek variants on the same draws.
Reads results/summary/e3.csv (ER n~2000, Bernoulli, sigma_idio=0.5, 300 replicates per cell)."""
import os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import figstyle as S

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "figures", "fig4_crossover.pdf")
d = pd.read_csv(os.path.join(ROOT, "results", "summary", "e3.csv"))
PANELS = [(0.0, "convex", 0.5, "linear response ($\\kappa=0$), $p=0.5$"),
          (1.0, "convex", 0.2, "convex ($\\kappa=1$), $p=0.2$"),
          (1.0, "thresh", 0.5, "threshold ($\\kappa=1$), $p=0.5$")]
SERIES = [("DM", "DM", "dm"), ("HT-exact", "HT (exact)", "ht"),
          ("HAJEK", "Hájek", "gcr"), ("HAJEK-r0.25", "Hájek, $\\delta=.25$", "stag"),
          ("REG-L", "REG-L", "reg")]
S.apply()
fig, axs = S.fig("text", aspect=0.35, ncols=3, sharey=True)
for ax, (k, sh, p, ttl) in zip(axs, PANELS):
    x = d[(d["out.kappa"] == k) & (d["out.shape"] == sh) & (d["design.p"] == p)]
    for est, lab, key in SERIES:
        y = x[x.est == est].sort_values("graph.d")
        ax.fill_between(y["graph.d"], y.rmse_lo, y.rmse_hi, color=S.COLORS[key], alpha=0.2, lw=0)
        ax.plot(y["graph.d"], y.rmse, color=S.COLORS[key], ls=S.LINES[key], marker=S.MARKERS[key], ms=2.8,
                lw=1.5 if est == "REG-L" else 1.0, label=lab, clip_on=True)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(0.02, 30)
    ax.set_xticks([2, 5, 10, 20, 50]); ax.set_xticklabels(["2", "5", "10", "20", "50"])
    ax.minorticks_off(); ax.set_title(ttl, fontsize=8)
    ax.set_xlabel("degree $d$")
axs[0].set_ylabel("RMSE of $\\hat\\tau$ (GATE $=2$)")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="outside lower center", ncols=5, fontsize=8, handlelength=1.6, columnspacing=1.0)
S.save(fig, OUT)
