"""F4 (claim E4): adversarial removal budget of adjacent-pair claims against the statistical margin z = gap / SE.

Reads adv_budgets.csv (points) and regression_coef.csv (lines: model M0, log k = const + dataset term + slope * log z, pooled
scope; natural logs). Panel b: parameter-free first-order prediction k_hat (s5_khat.csv, ceil of the linearised estimate) against the
verified budget, with the diagonal and the 2x band. Writes fig4_budget_vs_z.pdf.
"""
import os

import matplotlib.pyplot as plt
import numpy as np

import common as C

A = C.args(__doc__)
C.set_style()
b = C.adv_c2(A.results)
b = b[(b.z_gap > 0) & (b.budget > 0)]
co = C.read(A.results, "regression_coef.csv")
m0 = co[(co.scope == "pooled") & (co.model == "M0 log z")].set_index("term")
slope = m0.loc["log_z"]

fig, (ax, bx) = plt.subplots(1, 2, figsize=(C.TEXTWIDTH, 2.3), gridspec_kw={"width_ratios": [1.55, 1]})
seasons = b[~b.dataset.isin(C.BASE_UNITS)]
ax.plot(seasons.z_gap, seasons.budget, C.DESIGN_MARKER["sports"], color=C.DESIGN_COLOR["sports"], ms=2.2, alpha=0.25, mew=0,
        label=f"NBA single seasons ({seasons.dataset.nunique()} seasons, {len(seasons)} claims)", rasterized=True)
off = {"nba_seasons": m0.loc["const", "coef"], "arena55k": m0.loc["const", "coef"] + m0.loc["dataset_arena55k", "coef"],
       "mt_human": m0.loc["const", "coef"] + m0.loc["dataset_mt_human", "coef"],
       "mt_gpt4": m0.loc["const", "coef"] + m0.loc["dataset_mt_gpt4", "coef"]}
for unit in ["nba_all", "arena55k", "mt_human", "mt_gpt4"]:
    d = b[b.dataset == unit]; des = C.design_of(unit)
    ax.plot(d.z_gap, d.budget, C.DESIGN_MARKER[des], color=C.DESIGN_COLOR[des], ms=4.2 if unit != "nba_all" else 3.6, mec="white" if unit != "nba_all" else C.DESIGN_COLOR[des], mew=0.4,
            label=f"{C.SHORT_LABEL[unit]} ({len(d)} claims)" + (" — not in the pooled fit" if unit == "nba_all" else ""),
            zorder=3, fillstyle="full" if unit != "nba_all" else "none")
    if unit in off:
        z = np.geomspace(d.z_gap.min(), d.z_gap.max(), 20)
        ax.plot(z, np.exp(off[unit] + slope.coef * np.log(z)), "-", color=C.DESIGN_COLOR[des], lw=1.0, alpha=0.9)
zlo, zhi = seasons.z_gap.quantile([0.01, 0.99])
z = np.geomspace(zlo, zhi, 20)
ax.plot(z, np.exp(off["nba_seasons"] + slope.coef * np.log(z)), "-", color=C.DESIGN_COLOR["sports"], lw=1.0)
ns = co[(co.scope == "nba_seasons") & (co.model == "M0 log z")].set_index("term")
ax.plot(z, np.exp(ns.loc["const", "coef"] + ns.loc["log_z", "coef"] * np.log(z)), "--", color=C.DESIGN_COLOR["sports"], lw=1.0)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(2e-3, 25); ax.set_ylim(0.7, 900)
print(f"slope pooled {slope.coef:.3f} [{slope.ci_lo:.3f},{slope.ci_hi:.3f}]; claims below the x-limit: {int((seasons.z_gap < 2e-3).sum())}")
ax.set_xlabel("statistical margin $z$ = score gap / bootstrap SE of the gap")
ax.set_ylabel("removal budget $k$")
ax.legend(loc="upper left", frameon=False, fontsize=5.5, labelspacing=0.2, handletextpad=0.3, borderaxespad=0.1)
C.panel_letter(ax, "a")
# (b) parameter-free first-order prediction
kh = C.read(A.results, "s5_khat.csv")
kh = kh[(kh.budget > 0) & (kh.k_hat > 0)]
kh_season = kh[~kh.dataset.isin(C.BASE_UNITS)]
bx.plot(kh_season.budget, kh_season.k_hat, C.DESIGN_MARKER["sports"], color=C.DESIGN_COLOR["sports"], ms=2.2, alpha=0.25, mew=0, rasterized=True)
for unit in ["nba_all", "arena55k", "mt_human", "mt_gpt4"]:
    d = kh[kh.dataset == unit]; des = C.design_of(unit)
    bx.plot(d.budget, d.k_hat, C.DESIGN_MARKER[des], color=C.DESIGN_COLOR[des], ms=4.2 if unit != "nba_all" else 3.6,
            mec="white" if unit != "nba_all" else C.DESIGN_COLOR[des], mew=0.4, fillstyle="full" if unit != "nba_all" else "none", zorder=3)
lim = np.array([0.7, 900])
bx.plot(lim, lim, "-", color=C.INK, lw=0.7, zorder=1)
bx.fill_between(lim, lim / 2, lim * 2, color=C.MUTED, alpha=0.18, lw=0, zorder=0)
bx.set_xscale("log"); bx.set_yscale("log"); bx.set_xlim(lim); bx.set_ylim(lim)
bx.set_xlabel("verified removal budget $k$"); bx.set_ylabel(r"first-order prediction $\hat k$")
w2 = float(((kh.k_hat / kh.budget).between(0.5, 2)).mean())
bx.text(0.96, 0.05, f"{100 * w2:.1f}% of {len(kh)} claims within 2×", transform=bx.transAxes, fontsize=6, ha="right")
C.panel_letter(bx, "b")
fig.tight_layout(w_pad=0.8)
fig.savefig(os.path.join(A.out, "fig4_budget_vs_z.pdf"))
C.record_inputs(A.out, "fig4_budget_vs_z.pdf", [os.path.join(A.results, f) for f in ["adv_budgets.csv", "regression_coef.csv", "s5_khat.csv"]])
