"""Fig. 3 (H7): does a data-computable exposure-support statistic predict the extrapolation error?
x = ext = max(1-f_mean, f_mean)/f_sd (distance, in SDs of the realised neighbour-fraction f, from the
design's mean exposure to the farther of the two global-effect points 0 / 1), averaged over replicates
(as in code/scripts/analysis_h7.py); y = |population bias| of OLS(z, f): the noise- and baseline-free
fit, i.e. the pure approximation error. One point per main-grid cell; per-mechanism R^2 of the
pre-specified log-log regression is printed in the panel. Cells with |bias| <= 1e-3 (exact
specification, M1) are drawn as open markers at the floor and excluded from the regression.
Input: results/diagnostics.csv (estimator == ols_f, experiment MAIN)."""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import common as C

C.setup_style()
d = pd.read_csv(os.path.join(C.RESULTS, "diagnostics.csv"))
d = d[(d.experiment == "MAIN") & (d.estimator == "ols_f")].copy()
t = d.tag.str.split("|", expand=True)
d["graph"], d["mech"], d["dsg"] = t[0], t[1], t[2]
d["ext"] = np.maximum(1 - d.f_mean, d.f_mean) / d.f_sd
d["ab"] = d.pop_bias.abs() / 2.0  # relative to |tau| = 2 (tau_true in replicates.parquet)
FLOOR = 1e-3
mcol = {"M1": "#555555", "M3": "#0072B2", "M4": "#009E73", "M5": "#D55E00"}
dmk = {"bern0.5": "o", "bern0.1": "^", "cluster0.5": "s"}
fig, ax = plt.subplots(figsize=(C.TEXTWIDTH * 0.7, 2.9))
lines = []
for m, g in d.groupby("mech"):
    for dsg, gg in g.groupby("dsg"):
        z = gg.ab <= FLOOR
        ax.plot(gg.ext[~z], gg.ab[~z], ls="", marker=dmk[dsg], color=mcol[m], ms=4, alpha=0.85, mew=0.5)
        ax.plot(gg.ext[z], np.full(z.sum(), FLOOR), ls="", marker=dmk[dsg], mfc="none", color=mcol[m], ms=4, mew=0.7)
    gg = g[g.ab > FLOOR]
    if len(gg) >= 5 and gg.ext.std() > 0:
        x, y = np.log(gg.ext), np.log(gg.ab)
        r2 = np.corrcoef(x, y)[0, 1] ** 2
        b = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 20)
        ax.plot(np.exp(xs), np.exp(np.polyval(b, xs)), color=mcol[m], lw=0.8)
        lines.append((m, r2, len(gg)))
    elif m == "M1":
        lines.append((m, None, 0))  # linear in f: OLS(z, f) exactly specified, no approximation error to explain
    else:
        lines.append((m, np.nan, len(gg)))
ax.set(xscale="log", yscale="log", xticks=[1, 2, 3, 5, 10], xlabel=r"exposure-support statistic  max$(1-\bar f,\bar f)/\mathrm{SD}(f)$",
       ylabel=r"|population bias| / $|\tau|$")
from matplotlib.lines import Line2D
ax.set_xticklabels(["1", "2", "3", "5", "10"]); ax.minorticks_off() if False else ax.tick_params(axis="x", which="minor", labelbottom=False)
h = [Line2D([], [], color=mcol[m], marker="o", ls="-", ms=4, label=(f"{m}: $R^2$ = {r2:.2f} (n={k})" if r2 == r2 else f"{m}: no fit (n={k})") if r2 is not None else f"{m}: bias = 0 (open, at floor)") for m, r2, k in lines]
h += [Line2D([], [], color="#777", marker=mk, ls="", ms=4, label=C.DESIGN_LABEL[k]) for k, mk in dmk.items()]
ax.legend(handles=h, frameon=False, fontsize=6, loc="upper left", bbox_to_anchor=(1.0, 1.0))
print(lines)
print(C.save(fig, "fig3_h7_diagnostic"))
