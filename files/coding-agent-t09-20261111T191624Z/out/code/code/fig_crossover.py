"""Fig. 4: regression vs difference-in-means as a function of spillover strength gamma -- E4.csv."""
import numpy as np, pandas as pd
from ac import *
from matplotlib.ticker import NullFormatter, ScalarFormatter

df = load("E4")
df["gl"] = gkey(df)
er = df[df.tag == "cross"]
fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.15))
a = ax[0]
cols = {8: C["blue"], 32: C["orange"], 128: C["violet"]}
for d, col in cols.items():
    for est, ls, mk, mfc in [("ols_s", "-", "o", col), ("dm", "--", "s", "white")]:
        s = er[(er.graph_d == d) & (er.graph_n == 4000) & (er.estimator == est)]
        g = agg_worlds(s, ["mech_gamma"]).sort_values("mech_gamma")
        g = g[g.mech_gamma > 0]
        a.plot(g.mech_gamma, g.rmse, color=col, ls=ls, marker=mk, mfc=mfc, label=f"$d$={d}" if est == "ols_s" else None)
a.set_xscale("log"); a.set_yscale("log"); a.set_xlabel(r"spillover strength $\gamma$ ($\beta$=1)"); a.set_ylabel("RMSE")
a.set_title("(a) ER, $n$=4000: reg. (solid) vs DiM (dashed)")
a.legend(frameon=False, fontsize=6, loc="upper left")
a.xaxis.set_minor_formatter(NullFormatter())

# crossover gamma*: smallest gamma at which regression RMSE < DiM RMSE (log-linear interpolation, per world, then mean)
def crossover(d_):
    piv = d_.pivot_table(index="mech_gamma", columns="estimator", values="rmse")
    gam = piv.index.values
    diff = np.log(piv["ols_s"].values) - np.log(piv["dm"].values)  # >0: DiM better
    idx = np.where((diff[:-1] > 0) & (diff[1:] <= 0))[0]
    if len(idx) == 0:
        return np.nan
    i = idx[0]
    t = diff[i] / (diff[i] - diff[i + 1])
    return float(np.exp(np.log(max(gam[i], 1e-3)) + t * (np.log(gam[i + 1]) - np.log(max(gam[i], 1e-3)))))
rows = []
for (d, n), s in er.groupby(["graph_d", "graph_n"]):
    xs = []
    for w, sw in s.groupby("world_i"):
        xs.append(crossover(sw[sw.estimator.isin(["ols_s", "dm"])]))
    s0 = s[(s.mech_gamma == 0)]
    ols0 = s0[s0.estimator == "ols_s"].rmse.mean()
    dm0 = s0[s0.estimator == "dm"].rmse.mean()
    lev = s0[s0.estimator == "ols_s"].lev_theory.mean()
    rows.append(dict(d=d, n=n, gstar=np.nanmean(xs), gstar_min=np.nanmin(xs), gstar_max=np.nanmax(xs), n_cross=int(np.sum(~np.isnan(xs))),
                     ols0=ols0, dm0=dm0, pred=np.sqrt(max(ols0 ** 2 - dm0 ** 2, 0)), lev=lev))
T = pd.DataFrame(rows)
T["pred_closed"] = np.sqrt(1.124 ** 2 * T.lev / T.n)  # kappa from E1 ER fit
print(T.round(3).to_string())
T.to_csv(f"{TAB}/crossover.csv", index=False)
b = ax[1]
for d, col in cols.items():
    s = T[T.d == d].sort_values("n")
    b.plot(s.n, s.gstar, color=col, marker="o", label=f"$d$={d}")
    b.plot(s.n, s.pred_closed, color=col, ls=":")
b.set_xscale("log"); b.set_yscale("log"); b.set_xlabel("number of units $n$"); b.set_ylabel(r"crossover $\gamma^*$")
b.set_title(r"(b) $\gamma^*$ (dotted: $\hat\kappa\sqrt{L/n}$)")
b.legend(frameon=False, fontsize=6); b.xaxis.set_minor_formatter(NullFormatter())

c = ax[2]
rr = df[df.tag == "cross_real"]
for gl, col in [("ego-Facebook", C["yellow"]), ("Stanford3", C["red"])]:
    for des, ls, mfc in [("bern", "-", col), ("cluster", "--", "white")]:
        for est, mk in [("ols_s", "o"), ("dm", "s")]:
            s = rr[(rr.gl == gl) & (rr.design_type == des) & (rr.estimator == est) & (rr.mech_gamma > 0)]
            g = agg_worlds(s, ["mech_gamma"]).sort_values("mech_gamma")
            if est == "ols_s":
                c.plot(g.mech_gamma, g.rmse, color=col, ls=ls, marker="o", mfc=mfc, ms=3.5, label=f"{gl}, {'Bern.' if des=='bern' else 'cluster'}")
            else:
                c.plot(g.mech_gamma, g.rmse, color=col, ls=ls, marker="s", mfc=mfc, ms=3.0, alpha=0.4)
c.set_xscale("log"); c.set_yscale("log"); c.set_xlabel(r"spillover strength $\gamma$"); c.set_title("(c) real graphs (faint: DiM)")
c.legend(frameon=False, fontsize=5.6, loc="upper left"); c.xaxis.set_minor_formatter(NullFormatter())
fig.tight_layout(w_pad=0.8)
save(fig, "fig_crossover")
