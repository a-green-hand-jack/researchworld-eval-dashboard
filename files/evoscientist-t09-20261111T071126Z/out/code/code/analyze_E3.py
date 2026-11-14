"""E3: design x estimator under nonlinear response; sample-size and noise sweeps."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from analysis_lib import *

reps, gr, cf = load("E3")
m = metrics(reps, cf, boot=True)
m.to_csv(os.path.join(TAB, "E3_metrics.csv"), index=False)
main = m[m.tag.str.startswith("main_")].copy()
main["graph"] = main.tag.str.replace("main_", "")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)

# exposure coverage diagnostics by graph x design
diag = main[main.est == "lin_frac"].groupby(["graph", "dkind"])[["cov_ext", "corr_zf", "sd_f"]].mean().round(3)
diag.to_csv(os.path.join(TAB, "E3_exposure_diag.csv"))
print(diag)
gs = gr.merge(cf[["cid", "tag"]], on="cid")
gs = gs[gs.tag.str.startswith("main_")].groupby("tag")[["n", "m", "mean_deg", "harm_deg", "n_clusters", "edge_within_cluster"]].mean().round(3)
gs.to_csv(os.path.join(TAB, "E3_graphs.csv")); print(gs)

for s in (0, 4, 8):
    t = main[main.s == s].pivot_table(index=["graph", "dkind"], columns="est", values="rel_rmse")
    print(f"--- rel RMSE, s={s}"); print(t.round(3))
    t = main[main.s == s].pivot_table(index=["graph", "dkind"], columns="est", values="rel_bias")
    print(f"--- rel bias, s={s}"); print(t.round(3))
print("hajek fail frac:"); print(main[main.est == "hajek"].pivot_table(index=["graph", "dkind"], columns="s", values="fail").round(2))

# best lin-type estimator per cell
cell = main[main.est.isin(["lin_frac", "quad_frac", "spline", "oracle_h", "dm", "hajek", "gbm"])]
best = cell[cell.est != "oracle_h"].sort_values("rel_rmse").groupby(["graph", "dkind", "s"]).first()[["est", "rel_rmse"]]
best.round(3).to_csv(os.path.join(TAB, 'E3_best.csv'))
print(best.round(3))

# Figure: heatmaps of relative RMSE (graph x design rows, estimator columns) for s = 0, 4, 8
order = ["sbm10", "sbm30", "ws", "er", "ba", "egofb", "stanford3"]
ests = ["dm", "lin_frac", "spline", "gbm", "hajek", "oracle_h"]
rowsl = [(g, d) for g in order for d in ("bernoulli", "cluster", "rsat")]
fig, axs = plt.subplots(1, 3, figsize=(11, 5.2), sharey=True)
for ax, s in zip(axs, (0, 4, 8)):
    M = np.full((len(rowsl), len(ests)), np.nan)
    for i, (g, d) in enumerate(rowsl):
        for j, e in enumerate(ests):
            r = main[(main.s == s) & (main.graph == g) & (main.dkind == d) & (main.est == e)]
            if len(r):
                M[i, j] = r.rel_rmse.iloc[0]
    im = ax.imshow(np.log10(np.clip(M, 0.03, 1.5)), cmap="viridis_r", vmin=np.log10(0.03), vmax=np.log10(1.2), aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if np.isfinite(M[i, j]):
                ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=6, color="w" if M[i, j] > 0.25 else "k")
            else:
                ax.text(j, i, "-", ha="center", va="center", fontsize=6)
    ax.set_xticks(range(len(ests))); ax.set_xticklabels(ests, rotation=45, fontsize=7)
    ax.set_title(f"$s={s}$", fontsize=9)
ax = axs[0]
ax.set_yticks(range(len(rowsl)))
ax.set_yticklabels([f"{g}/{ {'bernoulli': 'Bern', 'cluster': 'Clust', 'rsat': 'RSat'}[d]}" for g, d in rowsl], fontsize=6)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_designs.pdf"))

# sample-size sweep
ns = m[m.tag == "nsweep"]
fig, ax = plt.subplots(1, 2, figsize=(7.5, 3.0))
for dk, c in (("bernoulli", "C0"), ("cluster", "C1"), ("rsat", "C2")):
    for e, ls in (("lin_frac", "-"), ("spline", "--"), ("oracle_h", ":")):
        g = ns[(ns.dkind == dk) & (ns.est == e)].sort_values("n_spec")
        ax[0].errorbar(g.n_spec, g.rmse, yerr=[g.rmse - g.rmse_lo, g.rmse_hi - g.rmse], c=c, ls=ls, marker="o", ms=3, lw=1, label=f"{dk[:4]}/{e}")
ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xticks([2000, 8000, 32000]); ax[0].set_xticklabels(["2k", "8k", "32k"]); ax[0].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter()); ax[0].set_xlabel("n (cluster size ~80)"); ax[0].set_ylabel("RMSE ($s=4$)"); ax[0].legend(fontsize=5, ncol=2)
nz = m[m.tag == "noise"].copy()
base = main[(main.graph == "sbm10") & (main.s == 4) & (main.est.isin(["lin_frac", "spline", "oracle_h"]))].copy()
base["sigma"] = 1.0
nz = pd.concat([nz, base[nz.columns.intersection(base.columns)]])
for dk, c in (("bernoulli", "C0"), ("cluster", "C1"), ("rsat", "C2")):
    for e, ls in (("lin_frac", "-"), ("spline", "--"), ("oracle_h", ":")):
        g = nz[(nz.dkind == dk) & (nz.est == e)].sort_values("sigma")
        ax[1].plot(g.sigma, g.rmse, c=c, ls=ls, marker="o", ms=3, lw=1)
ax[1].set_xscale("log"); ax[1].set_yscale("log"); ax[1].set_xticks([0.5, 1, 2, 4]); ax[1].set_xticklabels(["0.5", "1", "2", "4"]); ax[1].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter()); ax[1].set_xlabel("noise sd $\\sigma$"); ax[1].set_ylabel("RMSE ($s=4$, SBM)")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_sweeps.pdf"))
print(ns[["dkind", "est", "n_spec", "bias", "sd", "rmse"]].sort_values(["dkind", "est", "n_spec"]).round(3))
print(nz[["dkind", "est", "sigma", "bias", "sd", "rmse"]].sort_values(["dkind", "est", "sigma"]).round(3))

# ---- extrapolation leverage  Delta^2 = n * se_mb^2 / s2  (model-based variance factor a'(X'X)^{-1}a * n)
lf = main[(main.est == "lin_frac") & (main.s == 0)].copy()
nmap = gr.groupby("cid").n.mean()
lf["n_graph"] = lf.cid.map(nmap)
lf["delta2"] = lf.n_graph * lf.se_mb ** 2 / lf.s2
lf["sd_over_semb"] = lf.sd_pop / lf.se_mb
lv = lf[["graph", "dkind", "delta2", "sd_pop", "se_mb", "se_hc", "sd_over_semb", "corr_zf", "cov_ext", "rel_rmse"]]
lv.to_csv(os.path.join(TAB, "E3_leverage.csv"), index=False)
print(lv.round(3).to_string())
