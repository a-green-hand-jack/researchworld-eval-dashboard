"""Fig. calibration: binned E[Y | Yhat] against the best affine fit of Y on Yhat, per dataset.

This is the object that decides whether any calibration-based gain over PPI++ exists: PPI++ is optimal among
estimators linear in Yhat, so the gap between the curve and the line (relative to Var(Y)) bounds the gain.
Built from the underlying ppi-python data (PPI_DATA_DIR), full labeled populations.
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from common import *

sys.path.insert(0, os.path.join(EXP_DIR, "src"))
import data as D   # experiment-repo's loader: (Y, f) per dataset

setup()
NB = 15
theory = load("theory_population.csv")
dsets = list(ORDER)
gap = {}
fig, axes = plt.subplots(3, 3, figsize=(TEXT_W, 5.0), squeeze=False)
for ax, ds in zip(axes.ravel(), dsets):
    p = D.population(ds)
    Y, f = p["Y"], p["f"]
    uq = np.unique(f)
    if len(uq) <= NB:                                   # few distinct predictor values: one group per value
        groups = [f == u for u in uq]
    else:                                               # equal-count bins by rank
        order = np.argsort(f, kind="stable")
        groups = []
        for chunk in np.array_split(order, NB):
            m = np.zeros(len(f), bool); m[chunk] = True; groups.append(m)
    xs, ys, se = [], [], []
    for m in groups:
        if m.sum() < 5:
            continue
        xs.append(f[m].mean()); ys.append(Y[m].mean()); se.append(Y[m].std(ddof=1) / np.sqrt(m.sum()))
    xs, ys, se = map(np.array, (xs, ys, se))
    slope, icpt = np.polyfit(f, Y, 1)
    gap[ds] = (xs, (ys - (icpt + slope * xs)) / Y.std(ddof=1), 1.96 * se / Y.std(ddof=1), (f - f.min()) / (f.max() - f.min()), xs)
    grid = np.linspace(f.min(), f.max(), 50)
    ax.plot(grid, icpt + slope * grid, color="#0072B2", lw=1.0, label="best affine fit (what PPI++ uses)")
    ax.errorbar(xs, ys, yerr=1.96 * se, fmt="o", color="#D55E00", ms=2.5, elinewidth=0.6, label="binned $E[Y\\mid \\hat Y]$ (95% CI)")
    th = theory[theory["dataset"] == ds].iloc[0]
    ax.set_title(f"{DATASET_LABEL[ds]}\n$\\rho^2$={th['rho2']:.3f}, $R^2_{{\\rm cal}}$={th['r2cal_iso']:.3f}", fontsize=7)
    ax.tick_params(labelsize=7)
    ax.grid(False)
for ax in axes[2]:
    ax.set_xlabel("$\\hat Y$", labelpad=1)
for ax in axes[:, 0]:
    ax.set_ylabel("$Y$", labelpad=1)
h, l = axes[0, 0].get_legend_handles_labels()
fig.tight_layout(rect=(0, 0.05, 1, 1), h_pad=0.8, w_pad=0.4)
fig.legend(h, l, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.01))
save(fig, "calibration_curves")

# Gap figure: departure of E[Y | Yhat] from the best affine fit, in units of sd(Y), against the predictor's quantile
fig, axes = plt.subplots(3, 3, figsize=(TEXT_W, 4.4), sharey=True, squeeze=False)
for ax, ds in zip(axes.ravel(), dsets):
    xs, d, e, _, _ = gap[ds]
    ax.axhline(0, color="#0072B2", lw=1.0)
    ax.errorbar(np.arange(len(xs)) / max(len(xs) - 1, 1), d, yerr=e, fmt="o", color="#D55E00", ms=2.5, elinewidth=0.6)
    ax.set_title(DATASET_LABEL[ds], fontsize=7)
    ax.tick_params(labelsize=7)
    ax.grid(False)
for ax in axes[2]:
    ax.set_xlabel("bins ordered by $\\hat Y$ (low to high)", labelpad=1, fontsize=7)
for ax in axes[:, 0]:
    ax.set_ylabel("$(E[Y|\\hat Y]-\\mathrm{affine})/\\mathrm{sd}(Y)$", fontsize=7)
fig.tight_layout(h_pad=0.8, w_pad=0.4)
save(fig, "calibration_gap")
