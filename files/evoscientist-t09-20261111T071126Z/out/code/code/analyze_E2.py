"""E2: bias floor under nonlinear exposure response (Bernoulli design)."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analysis_lib import *
from gate.core import OutcomeSpec, bern_frac_pseudotrue, local_slope, var_law

reps, gr, cf = load("E2")
m = metrics(reps, cf, boot=True)
rows = []
for _, r in m[m.est == "lin_frac"].iterrows():
    spec = OutcomeSpec(s=r.s)
    g = gr[gr.cid == r.cid]
    sub = reps[(reps.cid == r.cid) & (reps.est == "lin_frac")]
    bp, vp, tl = [], [], []
    for pop in sorted(sub["pop"].unique()):
        deg = pop_degrees(r, pop)
        tau_pop = g[g["pop"] == pop].tau.iloc[0]
        bp.append(bern_frac_pseudotrue(deg, r.p, spec) - tau_pop)
        vp.append(var_law(deg, r.p, sub[sub["pop"] == pop].s2.mean()))
        tl.append(local_slope(r.p, spec) - tau_pop)
    rows.append(dict(cid=r.cid, bias_pred=np.mean(bp), var_pred=np.mean(vp), bias_localslope=np.mean(tl)))
pr = pd.DataFrame(rows)
mm = m.merge(pr, on="cid", how="left")
mm["rmse_pred"] = np.sqrt(mm.bias_pred ** 2 + mm.var_pred)
mm.to_csv(os.path.join(TAB, "E2_metrics.csv"), index=False)
lf = mm[mm.est == "lin_frac"]
print("bias pred vs obs corr", np.corrcoef(lf.bias_pred, lf.bias)[0, 1], "max abs diff", (lf.bias_pred - lf.bias).abs().max())
print("slope-through-origin", (lf.bias_pred * lf.bias).sum() / (lf.bias_pred ** 2).sum())
print("rmse pred vs obs: median ratio", (lf.rmse / lf.rmse_pred).median(), (lf.rmse / lf.rmse_pred).describe())
gg = lf[lf.tag == "grid"]
print("grid: bias diff abs", (gg.bias_pred - gg.bias).abs().describe())
rl = lf[lf.tag == "real"]
print(rl[["gkind", "s", "p", "bias", "bias_pred", "rmse", "rmse_pred", "rel_rmse"]])
print("local slope vs pred (d=40,s=16,p=.5):", lf[(lf.tag == "grid") & (lf.d_spec == 40) & (lf.s == 16) & (lf.p == .5)][["gkind", "bias", "bias_pred", "bias_localslope"]])
ora = mm[mm.est == "oracle_h"]
print("oracle_h rel_bias:", ora.rel_bias.abs().describe())
print("oracle_h vs lin_frac rmse (s>=4):")
piv = mm[(mm.tag == "grid") & (mm.s >= 4)].pivot_table(index="cid", columns="est", values="rel_rmse")
print((piv.lin_frac / piv.oracle_h).describe())
print("DM:", mm[mm.est == "dm"].rel_bias.describe())
nf = mm[mm.tag == "nfloor"].sort_values("n_spec")
print(nf[["est", "n_spec", "bias", "sd", "rmse", "rmse_lo", "rmse_hi", "bias_pred"]])

fig, ax = plt.subplots(1, 3, figsize=(11, 3.3))
for gk, mk in (("er", "o"), ("ba", "s"), ("stanford3", "*"), ("egofb", "P")):
    g = lf[lf.gkind == gk]
    ax[0].scatter(g.bias_pred, g.bias, marker=mk, s=26, alpha=.8, label=gk, c=g.p, cmap="viridis")
lim = [lf.bias.min() - .1, lf.bias.max() + .1]
ax[0].plot(lim, lim, "k--", lw=1); ax[0].set_xlabel("predicted bias floor (analytic)"); ax[0].set_ylabel("observed bias of $\\hat\\tau$")
ax[0].legend(fontsize=7)
for (d, p), c in zip([(10, .1), (10, .5), (40, .1), (40, .5)], ["C0", "C1", "C2", "C3"]):
    g = lf[(lf.tag == "grid") & (lf.gkind == "er") & (lf.d_spec == d) & (lf.p == p)].sort_values("s")
    ax[1].errorbar(g.s, g.bias, yerr=[g.bias - g.bias_lo, g.bias_hi - g.bias], c=c, marker="o", ms=3, label=f"d={d}, p={p}", lw=1)
    ax[1].plot(g.s, g.bias_pred, ":", c=c, lw=1)
ax[1].axhline(0, c="gray", lw=.5); ax[1].set_xlabel("nonlinearity $s$"); ax[1].set_ylabel("bias (ER, $n=8000$); dotted = analytic")
ax[1].legend(fontsize=6)
for e, c in (("lin_frac", "C3"), ("oracle_h", "C0")):
    g = nf[nf.est == e]
    ax[2].errorbar(g.n_spec, g.rmse, yerr=[g.rmse - g.rmse_lo, g.rmse_hi - g.rmse], marker="o", ms=3, c=c, label=f"{e} RMSE")
    ax[2].plot(g.n_spec, g.bias.abs(), "--", c=c, lw=1, label=f"{e} |bias|")
ax[2].set_xscale("log"); ax[2].set_yscale("log"); ax[2].set_xlabel("n"); ax[2].set_ylabel("error ($s=8$, $p=.5$, $d=10$)")
ax[2].legend(fontsize=6)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_bias.pdf"))
