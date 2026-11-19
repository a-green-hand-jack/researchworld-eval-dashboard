"""Fig. 2 + Table 2: extrapolation bias under nonlinear exposure response -- E2.csv (+E2g.csv)."""
import numpy as np, pandas as pd, os
from ac import *
from matplotlib.ticker import NullFormatter

df = load("E2")
df["gl"] = gkey(df)
shape_lab = lambda r: (f"k={r.mech_k:g}" if r.mech_shape == "pow" else "sigmoid")
df["shape"] = df.apply(shape_lab, axis=1)
fig, ax = plt.subplots(1, 4, figsize=(7.4, 2.15))

# (a) simulated bias vs closed-form projection bias (Bernoulli, ols_s, all E2 runs)
a = ax[0]
o = df[(df.estimator == "ols_s") & (df.design_type == "bern")]
g = agg_worlds(o, ["tag", "gl", "shape", "graph_d", "graph_n"])
gcol = {"ER": (C["blue"], "o"), "Reg": (C["aqua"], "^"), "BA": (C["violet"], "D"), "SBM": (C["orange"], "s"), "Stanford3": (C["red"], "P"), "ego-Facebook": (C["yellow"], "X")}
for gl, (col, mk) in gcol.items():
    s = g[g.gl == gl]
    if len(s):
        a.scatter(s.proj_bias_theory, s.bias, s=13, color=col, marker=mk, label=gl, zorder=3, linewidths=0.5)
lim = [-0.8, 0.8]
a.plot(lim, lim, color=INK2, lw=0.8)
a.set_xlabel("closed-form projection bias $B$"); a.set_ylabel("simulated bias"); a.set_title("(a) bias: theory vs. sim.")
a.legend(frameon=False, fontsize=5.4, loc="upper left")
err = (g.bias - g.proj_bias_theory)
print("(a) n points:", len(g), " max |bias-theory|:", err.abs().max(), " median:", err.abs().median(), " RMS:", np.sqrt((err**2).mean()))
print(g.assign(err=err).sort_values("err", key=abs, ascending=False).head(6)[["tag","gl","shape","graph_d","graph_n","bias","proj_bias_theory","err"]])
# (b) bias vs degree, regular graphs
b = ax[1]
r = df[(df.tag == "reg_d") & (df.estimator == "ols_s")]
for sh, col, mk in [("k=0.5", C["blue"], "o"), ("k=4", C["orange"], "s"), ("sigmoid", C["violet"], "^")]:
    s = agg_worlds(r[r["shape"] == sh], ["graph_d"]).sort_values("graph_d")
    b.errorbar(s.graph_d, s.bias, yerr=[s.bias - s.bias_min, s.bias_max - s.bias], color=col, marker=mk, capsize=1.2, elinewidth=.5, label=f"sim., {sh}")
    b.plot(s.graph_d, s.proj_bias_theory, color=col, ls=":", lw=1.0)
b.set_xscale("log"); b.axhline(0, color=INK2, lw=0.5)
b.set_xlabel("degree $d$ (regular)"); b.set_title("(b) vs. degree (dotted: theory)")
b.legend(frameon=False, fontsize=5.4, loc="center left"); b.xaxis.set_minor_formatter(NullFormatter())
# (c) bias vs n
c = ax[2]
r = df[(df.tag == "n_sweep")]
for sh, col in [("k=4", C["orange"]), ("sigmoid", C["violet"])]:
    for est, ls, mk, lab in [("ols_s", "-", "o", "linear (1,z,s)"), ("ols_s_quad", "--", "s", "+ $s^2$")]:
        s = agg_worlds(r[(r["shape"] == sh) & (r.estimator == est)], ["graph_n"]).sort_values("graph_n")
        c.errorbar(s.graph_n, s.bias, yerr=[s.bias - s.bias_min, s.bias_max - s.bias], color=col, ls=ls, marker=mk, mfc=col if ls == "-" else "white", capsize=1.2, elinewidth=.5, label=f"{sh}, {lab}")
c.set_xscale("log"); c.axhline(0, color=INK2, lw=0.5); c.set_xlabel("$n$ (ER, $d$=30)"); c.set_title("(c) bias vs. $n$")
c.legend(frameon=False, fontsize=5.0, loc="center left"); c.xaxis.set_minor_formatter(NullFormatter())
# (d) unified prediction RMSE^2 = B^2 + kappa^2 L / n   (closed-form B and L; kappa from E1)
import json
kappa = json.load(open(f"{TAB}/headline_numbers.json"))["kappa"]
d = ax[3]
o = df[(df.estimator == "ols_s") & (df.design_type == "bern")].copy()
o["pred"] = np.sqrt(o.proj_bias_theory ** 2 + kappa ** 2 * o.lev_theory / o.n)
o["ratio"] = o.rmse / o.pred
for gl, (col, mk) in gcol.items():
    t = o[o.gl == gl].groupby(["tag", "shape", "graph_d", "graph_n"], dropna=False)[["pred", "rmse"]].mean()
    d.scatter(t.pred, t.rmse, s=11, color=col, marker=mk, linewidths=0.5, zorder=3)
lim = [0.07, 2.5]
d.plot(lim, lim, color=INK2, lw=0.8); d.set_xscale("log"); d.set_yscale("log"); d.set_xlim(lim); d.set_ylim(lim)
d.set_xlabel(r"predicted $\sqrt{B^2+\hat\kappa^2L/n}$"); d.set_ylabel("observed RMSE"); d.set_title("(d) bias + leverage")
d.xaxis.set_minor_formatter(NullFormatter()); d.yaxis.set_minor_formatter(NullFormatter())
print("(d) per-world rows:", o.ratio.notna().sum(), "median ratio", o.ratio.median(), "IQR", o.ratio.quantile([.25, .75]).values, "range", o.ratio.min(), o.ratio.max(), "frac within 10%:", ((o.ratio > .9) & (o.ratio < 1.1)).mean())
fig.tight_layout(w_pad=0.6)
save(fig, "fig_extrap")

# Table 2: bias / RMSE of regression family for the hard shapes on three graphs, Bernoulli vs cluster
rows = []
dd = df[df.tag == "shape"]
if os.path.exists(f"{RES}/E2g.csv"):
    g2 = load("E2g"); g2["gl"] = gkey(g2); g2["shape"] = g2.apply(shape_lab, axis=1)
    dd = pd.concat([dd, g2[g2.estimator == "gbm"].assign(tag="shape_gbm")])
for gl in ["ER", "ego-Facebook", "Stanford3"]:
    for sh in ["k=0.5", "k=4", "sigmoid"]:
        for des in ["bern", "cluster"]:
            s = dd[(dd.gl == gl) & (dd["shape"] == sh) & (dd.design_type == des)]
            row = dict(graph=gl, shape=sh, design=des)
            for est in ["dm", "ols_s", "ols_s_quad", "ols_s_cub", "ols_s_int", "ols_s2", "gbm", "hajek"]:
                t = s[s.estimator == est]
                if len(t):
                    t = t[t.fail < 0.5]
                if len(t):
                    row[est + "_bias"] = t.bias.mean(); row[est + "_rmse"] = t.rmse.mean()
            row["truth"] = s.truth.mean()
            rows.append(row)
T = pd.DataFrame(rows)
T.to_csv(f"{TAB}/extrap_table.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(T.round(3).to_string())
