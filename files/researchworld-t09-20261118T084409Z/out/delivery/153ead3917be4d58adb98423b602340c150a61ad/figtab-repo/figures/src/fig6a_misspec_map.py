"""Fig. 6a (H4, appendix): error of the regression estimators when the observed graph is wrong.
Normalised RMSE (RMSE/(|beta|+|gamma|); DM = 0.5) against the fraction q of the observed graph's edges that are wrong;
median over ER/SBM/BA/WS of the cell RMSE (c11_map.csv is already normalised), band = median of the cells' 95% intervals.  Reads results/summary/c11_map.csv."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import figstyle as S

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
m = pd.read_csv(os.path.join(ROOT, "results", "summary", "c11_map.csv"))
m = m[m.resp == "linear"]
OUT = os.path.join(ROOT, "figures", "fig6a_misspec_map.pdf")
S.apply()
fig, axs = S.fig("text", aspect=0.40, ncols=2, sharey=True)
SER = [("DM", "DM", "dm", 1.0), ("REG-G", "REG-G", "flex", 1.0), ("REG-L", "REG-L", "reg", 1.5), ("REG-O", "REG-O (true form)", "reg_o", 1.0)]
for ax, (rg, ttl) in zip(axs, [("1-hop", "interference through direct neighbours"), ("1+2-hop", "half through neighbours' neighbours")]):
    for est, lab, key, lw in SER:
        x = m[(m.est == est) & (m.range == rg)].sort_values("q")
        ax.fill_between(x.q, x.rmse_lo_median , x.rmse_hi_median , color=S.COLORS[key], alpha=0.2, lw=0)
        ax.plot(x.q, x.rmse_median , color=S.COLORS[key], ls=S.LINES[key] if est != "REG-O" else "--", marker=S.MARKERS[key], ms=3, lw=lw, label=lab)
    ax.set_title(ttl, fontsize=8); ax.set_xlabel("fraction of observed edges wrong, $q$")
    ax.set_xticks([0, 0.1, 0.25, 0.5, 0.75]); ax.set_ylim(0, 0.56)
axs[0].set_ylabel("normalised RMSE")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="outside lower center", ncols=4, fontsize=8, handlelength=1.8, columnspacing=1.0)
S.save(fig, OUT)
