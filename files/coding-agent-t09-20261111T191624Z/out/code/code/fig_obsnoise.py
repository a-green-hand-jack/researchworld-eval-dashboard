"""Fig. 7: mis-measured network (fraction of edges replaced by random edges) -- E7.csv."""
import numpy as np, pandas as pd
from ac import *

df = load("E7")
df["gl"] = gkey(df)
df["setting"] = df.gl + "/" + df.design_type.map({"bern": "Bern", "cluster": "cluster"})
fig, ax = plt.subplots(1, 2, figsize=(5.2, 2.3))
sets = [("ER/Bern", C["blue"], "o", "-"), ("SBM/cluster", C["orange"], "s", "--"), ("ego-Facebook/Bern", C["yellow"], "X", "-"), ("ego-Facebook/cluster", C["yellow"], "X", "--"),
        ("Stanford3/Bern", C["red"], "P", "-"), ("Stanford3/cluster", C["red"], "P", "--")]
for k, (y, ttl) in enumerate([("bias", "(a) bias of 1-hop regression"), ("rmse", "(b) RMSE")]):
    a = ax[k]
    for st, col, mk, ls in sets:
        s = df[(df.setting == st) & (df.estimator == "ols_s")]
        g = agg_worlds(s, ["obs_noise_drop"]).sort_values("obs_noise_drop")
        a.errorbar(g.obs_noise_drop, g[y], yerr=[g[y] - g[y + "_min"], g[y + "_max"] - g[y]], color=col, ls=ls, marker=mk, mfc=col if ls == "-" else "white", capsize=1.2, elinewidth=.5, ms=3.8, label=st)
    a.set_xlabel("fraction of edges mis-recorded"); a.set_title(ttl)
ax[0].axhline(0, color=INK2, lw=0.5)
ax[1].set_yscale("log")
ax[0].legend(frameon=False, fontsize=5.4, loc="lower left")
fig.tight_layout(w_pad=0.8)
save(fig, "fig_obsnoise")
pd.set_option("display.width", 250)
T = agg_worlds(df[df.estimator.isin(["ols_s", "ols_s2", "dm"])], ["setting", "obs_noise_drop", "estimator"])[["setting", "obs_noise_drop", "estimator", "truth", "bias", "rmse"]]
print(T.round(3).to_string())
T.to_csv(f"{TAB}/obsnoise.csv", index=False)
