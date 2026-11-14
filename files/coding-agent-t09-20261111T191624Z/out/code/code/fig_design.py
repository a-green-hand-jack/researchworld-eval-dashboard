"""Fig. 5: design factors -- treatment probability p and cluster granularity K -- E5.csv."""
import numpy as np, pandas as pd
from ac import *
from matplotlib.ticker import NullFormatter

df = load("E5")
df["gl"] = gkey(df)
fig, ax = plt.subplots(2, 3, figsize=(7.4, 3.4))
gl_col = {"SBM": (C["orange"], "s"), "ego-Facebook": (C["yellow"], "X"), "Stanford3": (C["red"], "P")}
# row 1: p sweep.  (a) RMSE (linear mech) ; (b) bias pow4 ; (c) bias pow0.5   (ols_s), Bernoulli solid / cluster dashed
for k, (tag, ttl, y) in enumerate([("p_lin", "(a) linear: RMSE of reg. vs $p$", "rmse"), ("p_pow4", "(b) $k$=4 response: bias vs $p$", "bias"), ("p_pow05", "(c) $k$=0.5 response: bias vs $p$", "bias")]):
    a = ax[0, k]
    for gl, (col, mk) in gl_col.items():
        for des, ls in [("bern", "-"), ("cluster", "--")]:
            s = df[(df.tag == tag) & (df.gl == gl) & (df.design_type == des) & (df.estimator == "ols_s")]
            g = agg_worlds(s, ["design_p"]).sort_values("design_p")
            a.errorbar(g.design_p, g[y], yerr=[g[y] - g[y + "_min"], g[y + "_max"] - g[y]], color=col, ls=ls, marker=mk, mfc=col if ls == "-" else "white", capsize=1.2, elinewidth=.5, ms=3.8,
                       label=f"{gl}, {'Bern.' if des == 'bern' else 'cluster'}")
            if y == "bias" and des == "bern":
                a.plot(g.design_p, g.proj_bias_theory, color=col, ls=":", lw=0.9)
    a.set_xlabel("treated fraction $p$"); a.set_title(ttl)
    if y == "rmse":
        a.set_yscale("log"); a.set_ylabel("RMSE")
    else:
        a.axhline(0, color=INK2, lw=0.5); a.set_ylabel("bias")
hh0, ll0 = ax[0, 0].get_legend_handles_labels()
# row 2: K sweep. (d) RMSE lin; (e) bias pow4 ; (f) bias mh06
for k, (tag, ttl, y) in enumerate([("K_lin", "(d) linear: RMSE vs #clusters", "rmse"), ("K_pow4", "(e) $k$=4 response: bias vs #clusters", "bias"), ("K_mh06", r"(f) multi-hop $\lambda$=0.6: bias", "bias")]):
    a = ax[1, k]
    for gl, (col, mk) in gl_col.items():
        for est, ls, mfc in [("ols_s", "-", col)] + ([("dm", "--", "white")] if k == 0 else []):
            s = df[(df.tag == tag) & (df.gl == gl) & (df.estimator == est)]
            g = agg_worlds(s, ["design_K"]).sort_values("n_clusters")
            a.errorbar(g.n_clusters, g[y], yerr=[g[y] - g[y + "_min"], g[y + "_max"] - g[y]], color=col, ls=ls, marker=mk, mfc=mfc, capsize=1.2, elinewidth=.5, ms=3.8,
                       label=f"{gl}" if est == "ols_s" else None)
    a.set_xscale("log"); a.set_xlabel("number of clusters (Louvain)"); a.set_title(ttl)
    a.xaxis.set_minor_formatter(NullFormatter())
    if y == "rmse":
        a.set_yscale("log"); a.set_ylabel("RMSE (dashed: DiM)")
    else:
        a.axhline(0, color=INK2, lw=0.5); a.set_ylabel("bias")
fig.tight_layout(w_pad=0.8, h_pad=1.0)
fig.legend(hh0, ll0, loc="lower center", ncol=6, frameon=False, fontsize=6.0, bbox_to_anchor=(0.5, -0.055), handlelength=1.8, columnspacing=1.0)
save(fig, "fig_design")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
# cluster quality table
q = df[(df.tag == "K_lin") & (df.estimator == "ols_s")]
print(agg_worlds(q, ["gl", "design_K"])[["gl", "design_K", "n_clusters", "rmse", "bias", "lev", "lev_theory", "cut_frac"]].round(3).to_string())
