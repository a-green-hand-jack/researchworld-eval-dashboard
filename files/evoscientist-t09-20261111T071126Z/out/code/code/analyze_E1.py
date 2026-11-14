"""E1: variance law.  Produces tables/E1_*.csv and figures/fig_varlaw.pdf"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from analysis_lib import *

reps, gr, cf = load("E1")
m = metrics(reps, cf, boot=False)
# theory: sigma2_res (plug-in), harmonic degree per population, n per population
rows = []
for _, r in m[m.est == "lin_frac"].iterrows():
    g = gr[gr.cid == r.cid]
    sub = reps[(reps.cid == r.cid) & (reps.est == "lin_frac")]
    v_pred, v_emp = [], []
    for pop, gp in sub.groupby("pop"):
        st = g[g["pop"] == pop].iloc[0]
        s2 = gp.s2.mean()
        v_pred.append(s2 * (1 + st.harm_deg) / (st.n * r.p * (1 - r.p)))
        v_emp.append(gp.hat.var())
    # alternative prediction using mean degree (to show harmonic mean matters)
    v_mean = np.mean([sub[sub["pop"] == pop].s2.mean() * (1 + g[g["pop"] == pop].iloc[0].mean_deg) /
                      (g[g["pop"] == pop].iloc[0].n * r.p * (1 - r.p)) for pop in sub["pop"].unique()])
    hac = sub.se_hc.mean()
    rows.append(dict(cid=r.cid, tag=r.tag, gkind=r.gkind, n=g.n.mean(), mean_deg=g.mean_deg.mean(), harm_deg=g.harm_deg.mean(), p=r.p,
                     comm_sd=r.comm_sd, sd_emp=np.sqrt(np.mean(v_emp)), sd_pred=np.sqrt(np.mean(v_pred)), sd_pred_meandeg=np.sqrt(v_mean),
                     se_hc=hac, bias=r.bias, rel_rmse=r.rel_rmse, rmse=r.rmse, tau=r.tau))
v = pd.DataFrame(rows)
v["ratio"] = v.sd_emp / v.sd_pred
v["ratio_meandeg"] = v.sd_emp / v.sd_pred_meandeg
v.to_csv(os.path.join(TAB, "E1_varlaw.csv"), index=False)
print(v.groupby(["comm_sd"]).ratio.describe())
print(v.groupby(["comm_sd", "tag"]).ratio.agg(["mean", "min", "max"]))
print(v.groupby(["comm_sd"]).ratio_meandeg.describe())
# log-log slope of sd on N for each graph family
sl = []
for (gk, cs), g in v[v.tag == "nscale"].groupby(["gkind", "comm_sd"]):
    b = np.polyfit(np.log(g.n), np.log(g.sd_emp), 1)[0]
    sl.append(dict(gkind=gk, comm_sd=cs, slope=b))
sl = pd.DataFrame(sl)
sl.to_csv(os.path.join(TAB, "E1_slopes.csv"), index=False)
print(sl)
# DM bias
dm = m[m.est == "dm"][["cid", "tag", "gkind", "bias", "rel_bias", "sd"]]
print("DM rel bias:", dm.rel_bias.describe())
# lin_both vs lin_frac sd ratio (cost of overparametrisation)
pv = m.pivot_table(index="cid", columns="est", values="sd")
print("lin_both/lin_frac sd:", (pv.lin_both / pv.lin_frac).describe())

fig, ax = plt.subplots(1, 3, figsize=(11, 3.3))
mk = dict(er="o", ba="s", ws="^", sbm="D", stanford3="*", egofb="P")
for cs, col in ((0.0, "C0"), (1.0, "C3")):
    for gk, mm in mk.items():
        g = v[(v.comm_sd == cs) & (v.gkind == gk)]
        ax[0].scatter(g.sd_pred, g.sd_emp, marker=mm, c=col, s=28, alpha=.8, label=None)
lo, hi = v.sd_emp.min() * .8, v.sd_emp.max() * 1.2
ax[0].plot([lo, hi], [lo, hi], "k--", lw=1)
ax[0].set_xscale("log"); ax[0].set_yscale("log")
ax[0].set_xlabel("predicted SD  $\\hat\\sigma\\sqrt{(1+d_H)/(np(1-p))}$"); ax[0].set_ylabel("empirical SD of $\\hat\\tau$")
ax[0].scatter([], [], c="C0", label="iid baseline"); ax[0].scatter([], [], c="C3", label="community baseline")
ax[0].legend(fontsize=7, loc="upper left")
for gk, c in zip(["er", "ba", "ws", "sbm"], ["C0", "C1", "C2", "C4"]):
    for cs, ls in ((0.0, "-"), (1.0, ":")):
        g = v[(v.tag == "nscale") & (v.gkind == gk) & (v.comm_sd == cs)].sort_values("n")
        ax[1].plot(g.n, g.sd_emp, ls, marker="o", ms=3, c=c, label=f"{gk}" if cs == 0 else None)
ns = np.array([1000, 32000]); ax[1].plot(ns, 0.3 * (ns / 1000) ** -.5 * 1.0, "k--", lw=1, label="$n^{-1/2}$")
ax[1].set_xscale("log"); ax[1].set_yscale("log"); ax[1].set_xlabel("n"); ax[1].set_ylabel("SD of $\\hat\\tau$ ($d=10$)")
ax[1].legend(fontsize=7)
for gk, c in zip(["er", "ba", "ws"], ["C0", "C1", "C2"]):
    g = v[(v.tag == "dscale") & (v.gkind == gk) & (v.comm_sd == 0.0)].sort_values("mean_deg")
    ax[2].plot(g.mean_deg, g.sd_emp, "o-", c=c, ms=3, label=gk + " (emp.)")
    ax[2].plot(g.mean_deg, g.sd_pred, "x--", c=c, ms=4, label=gk + " (pred.)")
ax[2].set_xscale("log"); ax[2].set_yscale("log"); ax[2].set_xlabel("mean degree ($n=8000$)")
ax[2].set_xticks([4, 8, 16, 32, 64]); ax[2].set_xticklabels(["4", "8", "16", "32", "64"])
ax[2].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax[2].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter()); ax[2].set_ylabel("SD of $\\hat\\tau$")
ax[2].legend(fontsize=6)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "fig_varlaw.pdf"))
