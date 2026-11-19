"""Fig. 6b (C7, appendix): REG-L under graph cluster randomisation as the cluster scale varies.
x = Louvain resolution (small = few large clusters; large = many small ones); dotted line = the Bernoulli design of the same graph;
y = normalised RMSE (RMSE/(|beta|+|gamma|), DM = 0.5), band = 95% interval of the cell.  Reads results/summary/e5.csv."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import figstyle as S

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
e = pd.read_csv(os.path.join(ROOT, "results", "summary", "e5.csv")); e = e[e.est == "REG-L"].copy()
OUT = os.path.join(ROOT, "figures", "fig6b_gcr_ucurve.pdf")
def gname(r):
    return {"er": "ER", "ws": "WS"}.get(r["graph.kind"]) or f"SBM $\\mu={r['graph.kw.mu']:g}$"
e["g"] = e.apply(gname, axis=1)
RESP = [("linear", lambda x: (x["out.kappa"] == 0)), ("convex $\\kappa=1$", lambda x: (x["out.kappa"] == 1) & (x["out.shape"] == "convex") & x["out.w2"].isna()),
        ("two-hop linear mixture", lambda x: (x["out.w2"] == 0.5)), ("threshold $\\kappa=1$", lambda x: (x["out.shape"] == "thresh"))]
G = [("ER", "reg", "o"), ("SBM $\\mu=0.5$", "gcr", "s"), ("SBM $\\mu=0.8$", "stag", "^"), ("WS", "flex", "D")]
S.apply()
fig, axs = S.fig("text", aspect=0.40, ncols=4, sharey=True)
for ax, (ttl, sel) in zip(axs, RESP):
    x0 = e[sel(e)]
    for g, key, mk in G:
        x = x0[(x0.g == g) & (x0["design.kind"] == "gcr")].sort_values("design.res")
        ax.fill_between(x["design.res"], x.rmse_norm_lo, x.rmse_norm_hi, color=S.COLORS[key], alpha=0.2, lw=0)
        ax.plot(x["design.res"], x.rmse_norm, color=S.COLORS[key], marker=mk, ms=2.6, lw=1.0, label=g)
        b = x0[(x0.g == g) & (x0["design.kind"] == "bern")]
        ax.axhline(b.rmse_norm.iloc[0], color=S.COLORS[key], lw=0.8, ls=":")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(0.008, 1.0)
    ax.set_xticks([1, 5, 50]); ax.set_xticklabels(["1", "5", "50"]); ax.minorticks_off()
    ax.set_title(ttl, fontsize=8); ax.set_xlabel("Louvain resolution")
axs[0].set_ylabel("normalised RMSE")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="outside lower center", ncols=4, fontsize=8, handlelength=1.6, columnspacing=1.0)
S.save(fig, OUT)
