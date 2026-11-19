"""Plug-in cost (C1): measured paired width ratio M4/M3 relative to its asymptotic prediction, per dataset, N = 20n.

Prediction = pred_ratio_M4_vs_M3 (theory_predicted_ratios.csv): sqrt((1 - w R2cal)/(1 - w rho2)), w = N/(n+N), population
quantities with a cross-fitted E[Y|f]; measurement = geometric mean over replications of width(M4)/width(M3) on the same draws.
y = 100 (measured/predicted - 1): what learning the calibration map from n labels costs beyond the floor."""
import numpy as np
import matplotlib.pyplot as plt
from common import *

setup()
df = summary("real_primary")
df = df[(df["method"] == M4) & (df["N"] == 20 * df["n"])].copy()
df["pred"] = predicted(df["dataset"], df["n"], df["N"])
for c in ("ratio_geo", "ratio_lo", "ratio_hi"):
    df[c + "_x"] = 100 * (df[c] / df["pred"] - 1)
fig, ax = plt.subplots(figsize=(COL_W, 2.5))
ax.axhline(0, color="k", lw=0.7)
dsets = [d for d in PRIMARY if d in set(df["dataset"])]
cyc = [PAL[k] for k in ("blue", "vermil", "green", "orange", "pink", "grey")]
mks = "osD^vP"
for i, ds in enumerate(dsets):
    s = df[df["dataset"] == ds].sort_values("n")
    x = s["n"].values * (1 + 0.03 * (i - 2.5))
    ax.errorbar(x, s["ratio_geo_x"], yerr=[s["ratio_geo_x"] - s["ratio_lo_x"], s["ratio_hi_x"] - s["ratio_geo_x"]],
                color=cyc[i], marker=mks[i], elinewidth=0.6, label=DATASET_LABEL[ds])
ax.set_xscale("log")
ns = sorted(df["n"].unique())
ax.set_xticks(ns); ax.set_xticklabels([str(v) for v in ns]); ax.minorticks_off()
ax.set_xlabel("labeled $n$ ($N=20n$)")
ax.set_ylabel("measured / predicted ratio $-1$ (%)")
ax.legend(frameon=False, ncol=2, columnspacing=1.0, handletextpad=0.4)
fig.tight_layout()
save(fig, "plugin_cost")
