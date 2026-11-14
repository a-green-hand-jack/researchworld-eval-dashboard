"""Fig. 6: coverage of nominal 95% CIs for the 1-hop regression estimator -- E6.csv."""
import numpy as np, pandas as pd
from ac import *

df = load("E6")
df["gl"] = gkey(df)
o = df[df.estimator == "ols_s"].copy()
o["scen"] = o.tag.map({"inf_lin": "correct model (linear)", "inf_pow05": r"concave response $k$=0.5", "inf_mh04": r"multi-hop $\lambda$=0.4"})
o["setting"] = o.gl + "/" + o.design_type.map({"bern": "Bern", "cluster": "cluster"})
settings = ["ER/Bern", "SBM/Bern", "SBM/cluster", "ego-Facebook/Bern", "ego-Facebook/cluster", "Stanford3/Bern", "Stanford3/cluster"]
# the two ER graphs (d=10,30) are merged as separate rows
o["setting"] = np.where(o.gl == "ER", "ER d=" + o.graph_d.astype("Int64").astype(str) + "/Bern", o.setting)
settings = ["ER d=10/Bern", "ER d=30/Bern", "SBM/Bern", "SBM/cluster", "ego-Facebook/Bern", "ego-Facebook/cluster", "Stanford3/Bern", "Stanford3/cluster"]
fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.6), sharey=True)
meth = [("cov_hc", "HC sandwich", C["blue"], "o"), ("cov_cr", "community-clustered", C["orange"], "s"), ("cov_hac", "2-hop HAC", C["violet"], "^")]
for a, scen in zip(ax, ["correct model (linear)", r"concave response $k$=0.5", r"multi-hop $\lambda$=0.4"]):
    s = o[o.scen == scen]
    g = agg_worlds(s, ["setting"]).set_index("setting").reindex(settings)
    for j, (c, lab, col, mk) in enumerate(meth):
        y = np.arange(len(settings)) + (j - 1) * 0.2
        a.errorbar(g[c], y, xerr=[g[c] - g[c + "_min"], g[c + "_max"] - g[c]], fmt=mk, color=col, ms=3.8, capsize=1.2, elinewidth=.6, label=lab)
    a.axvline(0.95, color=INK2, lw=0.8, ls=":")
    a.set_yticks(range(len(settings))); a.set_yticklabels(settings)
    a.set_xlim(-0.02, 1.02); a.set_title(scen); a.set_xlabel("empirical coverage"); a.invert_yaxis(); a.grid(axis="y", visible=False)
ax[0].legend(frameon=False, fontsize=5.8, loc="lower left", bbox_to_anchor=(0.0, 0.02))
fig.tight_layout(w_pad=0.6)
save(fig, "fig_inference")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
T = agg_worlds(o, ["scen", "setting"])[["scen", "setting", "bias", "sd", "rmse", "cov_hc", "cov_cr", "cov_hac", "se_ratio_hc", "se_ratio_cr", "se_ratio_hac"]]
print(T.round(3).to_string())
T.to_csv(f"{TAB}/inference.csv", index=False)
print("hac density:", o.groupby("setting").hac_density.mean() if "hac_density" in o else None)

# coverage predicted from bias, SD and mean SE assuming normal errors
from scipy.stats import norm
o["se_hc"] = o.se_ratio_hc * o.sd
o["cov_pred_hc"] = norm.cdf((1.96 * o.se_hc - o.bias) / o.sd) - norm.cdf((-1.96 * o.se_hc - o.bias) / o.sd)
print("coverage pred vs obs (HC), per world rows:", len(o), "mean abs diff", (o.cov_pred_hc - o.cov_hc).abs().mean(), "max", (o.cov_pred_hc - o.cov_hc).abs().max(),
      "corr", np.corrcoef(o.cov_pred_hc, o.cov_hc)[0, 1])
good = o[o.tag == "inf_lin"]
print("correct model: HC coverage range", good.cov_hc.min(), good.cov_hc.max(), "mean", good.cov_hc.mean(), "| CR mean", good.cov_cr.mean(), "| HAC mean", good.cov_hac.mean())
print("correct model: se_ratio HC mean", good.se_ratio_hc.mean(), "CR", good.se_ratio_cr.mean(), "HAC", good.se_ratio_hac.mean())
bad = o[o.tag != "inf_lin"]
print("misspecified: HC cov mean", bad.cov_hc.mean(), "min", bad.cov_hc.min(), "max", bad.cov_hc.max())
print("misspecified: |bias|/sd vs cov corr", np.corrcoef(np.abs(bad.bias) / bad.sd, bad.cov_hc)[0, 1])
