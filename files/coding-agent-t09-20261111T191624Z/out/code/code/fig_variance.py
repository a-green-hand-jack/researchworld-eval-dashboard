"""Fig. 1 + Table 1: variance side (leverage) -- from E1.csv."""
import numpy as np, pandas as pd
from ac import *

df = load("E1")
df["gl"] = gkey(df)
o = df[(df.estimator == "ols_s") & (df.tag != "er_siga")].copy()
o["family"] = o.gl + "/" + o.design_type.map({"bern": "Bernoulli", "cluster": "cluster"})
o["pred_raw"] = np.sqrt(o.lev_theory / o.n)

# one global kappa fitted on ER-Bernoulli runs only (log-scale LS), then used out of sample
er = o[(o.gl == "ER") & (o.design_type == "bern")]
kappa = float(np.exp(np.mean(np.log(er.rmse / er.pred_raw))))
o["pred"] = kappa * o.pred_raw
o["logerr"] = np.log(o.rmse / o.pred)
print("kappa (ER-Bernoulli fit) =", kappa)

fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.2))
# (a) RMSE vs mean degree
a = ax[0]
fam = [("ER/Bernoulli", "er_d", C["blue"], "o", "-"), ("SBM/Bernoulli", "sbm_d", C["orange"], "s", "-"), ("SBM/cluster", "sbm_d", C["orange"], "s", "--"),
       ("WS/Bernoulli", "ws_d", C["aqua"], "^", "-"), ("WS/cluster", "ws_d", C["aqua"], "^", "--"),
       ("BA/Bernoulli", "ba_m", C["violet"], "D", "-"), ("BA/cluster", "ba_m", C["violet"], "D", "--")]
for f, tag, col, mk, ls in fam:
    s = o[(o.family == f) & (o.tag == tag)]
    g = agg_worlds(s, ["graph_d", "graph_m"]).sort_values("mean_deg")
    a.errorbar(g.mean_deg, g.rmse, yerr=[g.rmse - g.rmse_min, g.rmse_max - g.rmse], color=col, marker=mk, ls=ls, mfc=col if ls == "-" else "white", capsize=1.5, elinewidth=.6, label=f)
xs = np.array([4, 260])
a.plot(xs, 0.0356 * np.sqrt(xs / 4.0) * 1.0, color=INK2, lw=0.8, ls=":")
a.text(6.5, 0.052, r"slope $\frac{1}{2}$", color=INK2, fontsize=7)
a.set_xscale("log"); a.set_yscale("log"); a.set_xlabel("mean degree"); a.set_ylabel("RMSE of GATE estimate"); a.set_title("(a) error vs. degree ($n$=4000)")

# (b) RMSE vs n
b = ax[1]
s = df[(df.tag == "er_n")]
for est, lab, col, mk in [("ols_s", "regression (1, z, s)", C["blue"], "o"), ("hajek", "Hájek (full exposure)", C["orange"], "s"), ("dm", "difference-in-means", C["magenta"], "^")]:
    t = s[s.estimator == est]
    if est == "hajek":
        t = t[t.fail < 0.5]
    g = agg_worlds(t, ["graph_n"]).sort_values("graph_n")
    b.errorbar(g.graph_n, g.rmse, yerr=[g.rmse - g.rmse_min, g.rmse_max - g.rmse], color=col, marker=mk, capsize=1.5, elinewidth=.6, label=lab)
ns = np.array([1000, 16000])
b.plot(ns, 0.27 * np.sqrt(1000 / ns), color=INK2, lw=0.8, ls=":")
b.text(2300, 0.2, r"slope $-\frac{1}{2}$", color=INK2, fontsize=7, rotation=0)
b.set_xscale("log"); b.set_yscale("log"); b.set_xlabel("number of units $n$"); b.set_title("(b) error vs. $n$ (ER, $d$=16, Bernoulli)")
b.legend(frameon=False, loc="lower left", fontsize=6.3)
# (c) predicted vs observed
c = ax[2]
cols = {"ER/Bernoulli": (C["blue"], "o"), "SBM/Bernoulli": (C["orange"], "s"), "WS/Bernoulli": (C["aqua"], "^"), "BA/Bernoulli": (C["violet"], "D"),
        "SBM/cluster": (C["orange"], "s"), "WS/cluster": (C["aqua"], "^"), "BA/cluster": (C["violet"], "D"),
        "Stanford3/Bernoulli": (C["red"], "P"), "ego-Facebook/Bernoulli": (C["yellow"], "X"), "Stanford3/cluster": (C["red"], "P"), "ego-Facebook/cluster": (C["yellow"], "X")}
for f, (col, mk) in cols.items():
    s = o[o.family == f]
    if len(s) == 0:
        continue
    hollow = "cluster" in f
    c.scatter(s.pred, s.rmse, s=14, marker=mk, facecolor="white" if hollow else col, edgecolor=col, linewidths=0.8, label=f if f.endswith("Bernoulli") or f.startswith(("Stan", "ego")) else None, zorder=3)
lim = [0.03, 0.8]
c.plot(lim, lim, color=INK2, lw=0.8); c.set_xlim(lim); c.set_ylim(lim)
c.set_xscale("log"); c.set_yscale("log")
c.set_xlabel(r"predicted $\hat\kappa\sqrt{L/n}$"); c.set_ylabel("observed RMSE"); c.set_title("(c) leverage predicts error")
from matplotlib.ticker import NullFormatter
c.xaxis.set_minor_formatter(NullFormatter()); c.yaxis.set_minor_formatter(NullFormatter())
c.text(0.034, 0.5, "filled: Bernoulli\nhollow: cluster", fontsize=6.3, color=INK2)
hh, ll = a.get_legend_handles_labels()
fig.tight_layout(w_pad=0.8)
fig.legend(hh, ll, loc="lower center", ncol=7, frameon=False, fontsize=6.2, bbox_to_anchor=(0.30, -0.07), handlelength=1.8, columnspacing=1.0)
save(fig, "fig_variance")

# table: log-ratio observed/predicted by family
t = o.groupby("family").agg(n_runs=("rmse", "size"), med_ratio=("logerr", lambda x: float(np.exp(np.median(x)))),
                            min_ratio=("logerr", lambda x: float(np.exp(x.min()))), max_ratio=("logerr", lambda x: float(np.exp(x.max()))))
print(t)
# leverage prediction accuracy
o["levratio"] = o.lev / o.lev_theory
print(o.groupby("family").levratio.agg(["median", "min", "max"]))
t.to_csv(f"{TAB}/pred_ratio_by_family.csv")
o.groupby("family").levratio.agg(["median", "min", "max"]).to_csv(f"{TAB}/lev_ratio_by_family.csv")
# summary numbers
bern = o[o.design_type == "bern"]
print("Bernoulli all-family log-ratio: median", np.exp(bern.logerr.median()), "IQR", np.exp(bern.logerr.quantile([.25, .75]).values))
ls = np.polyfit(np.log(er.mean_deg + 1), np.log(er.rmse), 1)
print("ER slope log rmse vs log(1+d):", ls)

sg = df[(df.estimator == "ols_s") & (df.tag == "er_siga")]
g = agg_worlds(sg, ["mech_sig_a"])
print(g[["mech_sig_a", "rmse", "bias"]])
print("log-log slope RMSE vs sig_a:", np.polyfit(np.log(g.mech_sig_a), np.log(g.rmse), 1))
