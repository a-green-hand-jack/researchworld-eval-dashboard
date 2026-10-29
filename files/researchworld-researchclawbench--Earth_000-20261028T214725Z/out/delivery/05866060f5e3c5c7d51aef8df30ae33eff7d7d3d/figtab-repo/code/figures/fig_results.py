"""Result figures 3-8 and tables T2-T4 from experiment-repo's outputs/ (reconstruction) with the published GlaMBIE
series as benchmark. All uncertainties are 1 sigma as defined in outputs/README.md."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from common import *

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
os.makedirs(TAB, exist_ok=True)
NAME = {0: "Global", **REGIONS}
rc = recon("regional_calendar_years.csv")
pub = load_published("calendar_years")
rc["year"] = rc.start_dates
pr = recon("period_rates.csv")
acc = recon("acceleration.csv")
val = recon("validation_vs_published.csv")
valy = recon("validation_vs_published_by_year.csv")
prp = recon("period_rates_vs_published.csv")
cum = recon("cumulative_calendar_years.csv")
rob = recon("robustness_scenarios.csv")
grp = recon("group_series_calendar.csv")
YL = "Calendar year (label = start of the 12-month period)"


def panel_grid(ncols=4):
    fig, axes = plt.subplots(5, 4, figsize=(11, 11), sharex=True)
    axes = axes.ravel()
    for a in axes:
        a.tick_params(labelbottom=True)
    return fig, axes


# ---- Fig 3: regional series, reconstruction vs published (m w.e.)
fig, axes = panel_grid()
order = list(range(1, 20)) + [0]
for ax, rid in zip(axes, order):
    d = rc[rc.region_id == rid].sort_values("year")
    p = pub[pub.region_id == rid].sort_values("year")
    t = d.year + 0.5
    ax.axhline(0, color="0.7", lw=0.6)
    ax.fill_between(t, d.mwe - d.mwe_err, d.mwe + d.mwe_err, color=C_RECON, alpha=0.25, lw=0)
    ax.plot(t, d.mwe, color=C_RECON, lw=1.3, marker="o", ms=2.5)
    ax.plot(p.year + 0.5, p.combined_mwe, color=C_PUB, lw=1.0, ls="--")
    ax.set_title(NAME[rid].replace("Antarctic & Subantarctic", "Antarctic & Subant."), fontsize=8.5, loc="left", fontweight="bold" if rid == 0 else "normal")
    m = pr[(pr.region_id == rid) & (pr.period == "2000-2023")].iloc[0]
    ax.set_title(f"{m.rate_mwe:+.2f} ± {m.rate_mwe_err:.2f}", fontsize=7.5, loc="right", color="0.25")
for i, ax in enumerate(axes):
    if i >= 15: ax.set_xlabel("Calendar year")
    if i % 4 == 0: ax.set_ylabel("m w.e. a$^{-1}$")
fig.legend(handles=[Line2D([0], [0], color=C_RECON, marker="o", ms=3, label="This reconstruction ±1σ"),
                    Line2D([0], [0], color=C_PUB, ls="--", label="Published GlaMBIE")],
           frameon=False, fontsize=8, loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.0))
fig.suptitle("Annual specific mass change 2000–2023 by region (calendar years); y-axes free per panel;\n"
             "top-right of each panel: 2000–2023 mean rate ± 1σ in m w.e. a$^{-1}$ (ensemble, error correlation preserved)", fontsize=10)
fig.tight_layout(rect=(0, 0.025, 1, 1))
fig.savefig(os.path.join(IMG, "fig03_regional_series.png"), dpi=170)
plt.close(fig)

# ---- Fig 4: global annual (Gt) and cumulative with SLE
g = rc[rc.region_id == 0].sort_values("year")
gp = pub[pub.region_id == 0].sort_values("year")
gc = cum[cum.region_id == 0].sort_values("end_dates")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 4))
a1.errorbar(g.year + 0.38, g["gt"], yerr=g.gt_err, fmt="o", ms=3.5, color=C_RECON, lw=0.9, label="This reconstruction ±1σ")
a1.errorbar(gp.year + 0.62, gp.combined_gt, yerr=gp.combined_gt_errors, fmt="s", ms=3.2, color=C_PUB, lw=0.9, label="Published GlaMBIE ±1σ")
a1.axhline(0, color="k", lw=0.6)
a1.set_ylabel("Global mass change (Gt a$^{-1}$)"); a1.set_xlabel("Calendar year")
a1.legend(frameon=False, fontsize=8, loc="lower left")
a1.set_title("a  Annual", loc="left", fontsize=9.5)
a2.fill_between(gc.end_dates, gc.cum_gt - gc.cum_gt_err, gc.cum_gt + gc.cum_gt_err, color=C_RECON, alpha=0.25, lw=0)
a2.plot(gc.end_dates, gc.cum_gt, color=C_RECON, lw=1.8, label="This reconstruction ±1σ (ensemble)")
a2.plot(gp.year + 1, gp.combined_gt.cumsum(), color=C_PUB, ls="--", lw=1.4, label="Published GlaMBIE (sum of annual values)")
a2.set_ylabel("Cumulative mass change since 1 Jan 2000 (Gt)"); a2.set_xlabel("End of calendar year")
sec = a2.secondary_yaxis("right", functions=(lambda x: -x / SLE_GT_PER_MM, lambda s: -s * SLE_GT_PER_MM))
sec.set_ylabel("Sea-level equivalent (mm)")
a2.legend(frameon=False, fontsize=8, loc="lower left")
a2.set_title("b  Cumulative", loc="left", fontsize=9.5)
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig04_global_series.png"), dpi=180)
plt.close(fig)

# ---- Fig 5: validation vs published
fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.3), gridspec_kw=dict(width_ratios=[1, 1.15, 1.15]))
a = axes[0]
v = valy[(valy.year_type == "calendar") & (valy.region_id > 0)]
a.errorbar(v.mwe_pub, v.mwe_recon, xerr=v.mwe_err_pub, yerr=v.mwe_err_recon, fmt="none", ecolor="0.85", lw=0.5, zorder=0)
a.scatter(v.mwe_pub, v.mwe_recon, s=7, c=C_RECON, alpha=0.7, lw=0, zorder=2)
lim = [min(v.mwe_pub.min(), v.mwe_recon.min()) - 0.1, max(v.mwe_pub.max(), v.mwe_recon.max()) + 0.1]
a.plot(lim, lim, color="k", lw=0.8); a.set_xlim(lim); a.set_ylim(lim); a.set_aspect("equal")
r = np.corrcoef(v.mwe_pub, v.mwe_recon)[0, 1]
rm = np.sqrt(np.mean((v.mwe_pub - v.mwe_recon) ** 2))
a.text(0.04, 0.95, f"n = {len(v)} region-years\nr = {r:.2f}, RMSE = {rm:.2f} m w.e.", transform=a.transAxes, va="top", fontsize=8)
a.set_xlabel("Published GlaMBIE (m w.e. a$^{-1}$)"); a.set_ylabel("Reconstruction (m w.e. a$^{-1}$)")
a.set_title("a  Annual, 19 regions (grey: ±1σ)", loc="left", fontsize=9.5)
b = axes[1]
q = prp[prp.period == "2000-2023"].copy()
q["z"] = q.diff_over_recon_err  # (reconstruction - published) / recon sigma, as in experiment-repo outputs
q["label"] = q.region_id.map(NAME)
y = np.arange(len(q))[::-1]
b.axvspan(-1, 1, color="0.9", lw=0); b.axvline(0, color="k", lw=0.6)
b.scatter(q.z, y, s=18, color=[C_RECON if i else "k" for i in q.region_id > 0], zorder=3)
b.set_yticks(y, q.label, fontsize=7.5)
b.set_xlabel("(reconstruction − published) / σ$_{recon}$,  2000–2023 mean rate")
b.set_title("b  Period-rate difference (shaded ±1σ)", loc="left", fontsize=9.5)
b.set_xlim(-3, 3)
c = axes[2]
gv = valy[(valy.year_type == "calendar") & (valy.region_id == 0)].sort_values("start_dates")
c.axhline(0, color="k", lw=0.6)
c.fill_between(gv.start_dates + 0.5, -np.hypot(gv.gt_err_recon, gv.gt_err_pub), np.hypot(gv.gt_err_recon, gv.gt_err_pub), color="0.88", lw=0,
               label="±1σ combined (√(σ$_r^2$+σ$_p^2$))")
c.plot(gv.start_dates + 0.5, gv.gt_recon - gv.gt_pub, color=C_RECON, marker="o", ms=3, lw=1.2, label="reconstruction − published")
c.set_xlabel("Calendar year"); c.set_ylabel("Global annual difference (Gt a$^{-1}$)")
vg = val[(val.year_type == "calendar") & (val.region_id == 0)].iloc[0]
c.text(0.03, 0.04, f"bias {vg.bias_gt:+.1f} Gt a$^{{-1}}$, RMSE {vg.rmse_gt:.0f}, r = {vg.r_gt:.2f}\n"
       f"{vg.frac_within_1sigma*100:.0f}% of years within 1σ", transform=c.transAxes, fontsize=8)
c.legend(frameon=False, fontsize=7.5, loc="upper right")
c.set_title("c  Global annual difference", loc="left", fontsize=9.5)
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig05_validation_vs_published.png"), dpi=180)
plt.close(fig)

# ---- Fig 6: regional ranking, first vs second half, acceleration
p23 = pr[(pr.period == "2000-2023") & (pr.region_id > 0)].sort_values("rate_gt").reset_index(drop=True)
fig, axes = plt.subplots(1, 3, figsize=(13, 5.2), sharey=True)
yy = np.arange(len(p23))[::-1]
a = axes[0]
a.barh(yy, p23.rate_gt, xerr=p23.rate_gt_err, color=C_RECON, error_kw=dict(lw=0.9, ecolor="0.25", capsize=1.5))
tot = pr[(pr.period == "2000-2023") & (pr.region_id == 0)].iloc[0]
a.set_yticks(yy, p23.region_id.map(NAME), fontsize=8)
for yi, rg, e in zip(yy, p23.rate_gt, p23.rate_gt_err):
    a.text(2, yi, f"{rg/tot.rate_gt*100:.0f}%", va="center", fontsize=7, color="0.3")
a.set_xlim(-80, 8)
a.set_xlabel("Mean mass change 2000–2023 (Gt a$^{-1}$)")
a.set_title(f"a  Total; labels = share of global ({tot.rate_gt:.0f} ± {tot.rate_gt_err:.0f} Gt a$^{{-1}}$)", loc="left", fontsize=9)
b = axes[1]
for per, col, off in [("2000-2011", "#56B4E9", 0.17), ("2012-2023", "#D55E00", -0.17)]:
    d = pr[(pr.period == per)].set_index("region_id").loc[p23.region_id]
    b.errorbar(d.rate_mwe, yy + off, xerr=d.rate_mwe_err, fmt="o", ms=4, color=col, lw=1, label=per)
b.axvline(0, color="k", lw=0.6)
b.set_xlabel("Mean specific mass change (m w.e. a$^{-1}$)")
b.legend(frameon=False, fontsize=8, loc="lower left")
b.set_title("b  Specific, first vs second half", loc="left", fontsize=9)
c = axes[2]
d = acc.set_index("region_id").loc[p23.region_id]
c.errorbar(d.d_rate_2012_2023_minus_2000_2011_gt, yy, xerr=d.d_rate_err, fmt="o", ms=4, color="k", lw=1)
c.axvline(0, color="k", lw=0.6)
c.set_xlabel("Rate 2012–2023 minus 2000–2011 (Gt a$^{-1}$)\n(negative = loss increased)")
ga = acc[acc.region_id == 0].iloc[0]
c.set_title(f"c  Change in rate (global {ga.d_rate_2012_2023_minus_2000_2011_gt:.0f} ± {ga.d_rate_err:.0f} Gt a$^{{-1}}$)", loc="left", fontsize=9)
fig.suptitle("Regional contributions and change between halves (error bars ±1σ, ensemble)", fontsize=10.5)
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig06_regional_ranking_acceleration.png"), dpi=180)
plt.close(fig)

# ---- Fig 7: method-group agreement per region (common coverage), m w.e.
rows = []
for rid in range(1, 20):
    gg = grp[grp.region_id == rid]
    sets = {k: set(x.start_dates) for k, x in gg.groupby("group")}
    if len(sets) < 2:
        continue
    common = set.intersection(*sets.values())
    if len(common) < 3:
        # fall back to the two groups with the longest overlap
        continue
    for k, x in gg.groupby("group"):
        x = x[x.start_dates.isin(common)]
        rows.append(dict(region_id=rid, group=k, n=len(x), mwe=x.mwe.mean(), err=x.mwe_err.mean(),
                         y0=min(common), y1=max(common) + 1))
gm = pd.DataFrame(rows)
gm.to_csv(os.path.join(TAB, "group_agreement_common_period.csv"), index=False)
GCOL = {"demdiff_glaciological": "#E69F00", "altimetry": "#0072B2", "gravimetry": "#CC79A7"}
GLAB = {"demdiff_glaciological": "DEM + glaciological", "altimetry": "Altimetry", "gravimetry": "Gravimetry"}
regs = sorted(gm.region_id.unique())
fig, ax = plt.subplots(figsize=(8.5, 6.4))
yv = np.arange(len(regs))[::-1]
for j, k in enumerate(GCOL):
    s = gm[gm.group == k].set_index("region_id")
    xs = [(yv[i] + (j - 1) * 0.22) for i, r in enumerate(regs) if r in s.index]
    ax.errorbar([s.loc[r, "mwe"] for r in regs if r in s.index], xs, xerr=[s.loc[r, "err"] for r in regs if r in s.index],
                fmt="o", ms=4, color=GCOL[k], lw=1, label=GLAB[k])
ax.set_yticks(yv, [f"{NAME[r]}  ({int(gm[gm.region_id==r].y0.iloc[0])}–{int(gm[gm.region_id==r].y1.iloc[0])-1})" for r in regs], fontsize=8)
XMIN, XMAX = -1.7, 0.35
ax.set_xlim(XMIN, XMAX)
for j, k in enumerate(GCOL):
    s_ = gm[gm.group == k].set_index("region_id")
    for i, r in enumerate(regs):
        if r in s_.index and s_.loc[r, "mwe"] - s_.loc[r, "err"] < XMIN:
            ax.annotate(f"◂ to {s_.loc[r, 'mwe'] - s_.loc[r, 'err']:.1f}", (XMIN, yv[i] + (j - 1) * 0.22), xytext=(4, 0),
                        textcoords="offset points", fontsize=7, color=GCOL[k], va="center", ha="left",
                        bbox=dict(fc="white", ec="none", pad=0.5))
ax.axvline(0, color="k", lw=0.6)
ax.set_xlabel("Mean specific mass change over the period common to all groups present (m w.e. a$^{-1}$)")
ax.legend(frameon=False, fontsize=8, loc="lower left")
ax.set_title("Agreement between data groups over the period common to those present\nbars = mean annual 1σ (errors assumed fully correlated in time)\nx-axis clipped; ◂ marks bars that extend beyond it",
             fontsize=9, loc="left")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig07_group_agreement.png"), dpi=180)
plt.close(fig)

# ---- Fig 8: robustness of global 2000-2023 rate
rb = rob[rob.period == "2000-2023"].copy()
LAB = {"main": "Main reconstruction", "drop_altimetry": "Drop altimetry", "drop_gravimetry": "Drop gravimetry",
       "only_demdiff_glaciological": "Only DEM + glaciological", "hybrids_excluded": "Exclude hybrid solutions",
       "wgms_beta_excluded": "Exclude WGMS-beta series", "no_group_eligibility_rules": "No group-eligibility rules",
       "plain_mean_no_weights": "Plain mean (no weights)", "smoothing_window_3": "Smoothing window 3",
       "smoothing_window_7": "Smoothing window 7", "tau_0.05": "Weight floor 0.05 m w.e.",
       "tau_0.5": "Weight floor 0.5 m w.e.", "density_0.90": "Density 900 kg m$^{-3}$ (m → m w.e.)",
       "density_0.80": "Density 800 kg m$^{-3}$ (m → m w.e.)", "no_bootstrap_MC_only": "MC only (no bootstrap)",
       "errors_fully_correlated_in_time_per_solution": "Errors fully correlated in time"}
rb = rb[rb.scenario.isin(LAB)].reset_index(drop=True)
main = rb[rb.scenario == "main"].iloc[0]
tot_unc = recon("robustness_global_uncertainty.csv").iloc[0]
fig, ax = plt.subplots(figsize=(8, 5.4))
yr = np.arange(len(rb))[::-1]
ax.axvspan(main.rate_gt - tot_unc.err_total_independent, main.rate_gt + tot_unc.err_total_independent, color=C_RECON, alpha=0.15, lw=0,
           label="Main ±1σ (total, independent regional dispersion)")
ax.axvline(main.rate_gt, color=C_RECON, lw=1)
ax.axvline(-272.603, color=C_PUB, ls="--", lw=1, label="Published GlaMBIE (−272.6)")
for yi, (_, r) in zip(yr, rb.iterrows()):
    ax.errorbar(r.rate_gt, yi, xerr=None if pd.isna(r.mc_err) else r.mc_err, fmt="o", ms=5,
                color="k" if r.scenario != "main" else C_RECON, lw=1, capsize=2)
ax.set_yticks(yr, [LAB[s] for s in rb.scenario], fontsize=8)
ax.set_xlabel("Global mass change 2000–2023 (Gt a$^{-1}$)")
ax.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.45, -0.13), ncol=1)
ax.set_title("Sensitivity of the global rate (error bars where the scenario returns an ensemble σ)", fontsize=9, loc="left")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig08_robustness.png"), dpi=180)
plt.close(fig)

# ---- Tables
def fmt(x, e, d=1):
    return f"{x:.{d}f} ± {e:.{d}f}"

pt = pr.pivot(index="region_id", columns="period")
rows = []
for rid in [0] + list(range(1, 20)):
    r = {"region_id": rid, "region": NAME[rid], "area_2000_km2": rc[(rc.region_id == rid) & (rc.year == 2000)].area_km2.iloc[0]}
    for per in ["2000-2011", "2012-2023", "2000-2023"]:
        s = pr[(pr.region_id == rid) & (pr.period == per)].iloc[0]
        r[f"rate_gt_{per}"] = s.rate_gt; r[f"rate_gt_err_{per}"] = s.rate_gt_err
        r[f"rate_mwe_{per}"] = s.rate_mwe; r[f"rate_mwe_err_{per}"] = s.rate_mwe_err
    a_ = acc[acc.region_id == rid].iloc[0]
    r["d_rate_gt"] = a_.d_rate_2012_2023_minus_2000_2011_gt; r["d_rate_gt_err"] = a_.d_rate_err
    rows.append(r)
T2 = pd.DataFrame(rows)
T2.to_csv(os.path.join(TAB, "T2_regional_period_rates.csv"), index=False)
with open(os.path.join(TAB, "T2_regional_period_rates.md"), "w") as fh:
    fh.write("| # | Region | Area 2000 (km²) | 2000–2011 (Gt a⁻¹) | 2012–2023 (Gt a⁻¹) | 2000–2023 (Gt a⁻¹) | 2000–2023 (m w.e. a⁻¹) | Δrate 2012–23 vs 2000–11 (Gt a⁻¹) |\n")
    fh.write("|--:|:--|--:|--:|--:|--:|--:|--:|\n")
    for _, r in T2.iterrows():
        fh.write(f"| {'' if r.region_id == 0 else int(r.region_id)} | {r.region} | {r.area_2000_km2:,.0f} | "
                 f"{fmt(r['rate_gt_2000-2011'], r['rate_gt_err_2000-2011'])} | {fmt(r['rate_gt_2012-2023'], r['rate_gt_err_2012-2023'])} | "
                 f"{fmt(r['rate_gt_2000-2023'], r['rate_gt_err_2000-2023'])} | {fmt(r['rate_mwe_2000-2023'], r['rate_mwe_err_2000-2023'], 2)} | "
                 f"{fmt(r.d_rate_gt, r.d_rate_gt_err)} |\n")

T3 = g[["year", "area_km2", "gt", "gt_err", "mwe", "mwe_err"]].copy()
T3["cum_gt"] = gc.cum_gt.values; T3["cum_gt_err"] = gc.cum_gt_err.values; T3["cum_sle_mm"] = gc.cum_sle_mm.values
T3["pub_gt"] = gp.combined_gt.values; T3["pub_gt_err"] = gp.combined_gt_errors.values
T3.to_csv(os.path.join(TAB, "T3_global_annual.csv"), index=False)
with open(os.path.join(TAB, "T3_global_annual.md"), "w") as fh:
    fh.write("| Year | Gt a⁻¹ | m w.e. a⁻¹ | Cumulative (Gt) | Cumulative SLE (mm) | Published (Gt a⁻¹) |\n|--:|--:|--:|--:|--:|--:|\n")
    for _, r in T3.iterrows():
        fh.write(f"| {int(r.year)} | {fmt(r['gt'], r.gt_err, 0)} | {fmt(r.mwe, r.mwe_err, 2)} | {fmt(r.cum_gt, r.cum_gt_err, 0)} | "
                 f"{-r.cum_sle_mm:.1f} | {fmt(r.pub_gt, r.pub_gt_err, 0)} |\n".replace(f"| {-r.cum_sle_mm:.1f} |", f"| {r.cum_sle_mm:.1f} |"))

V = val[val.year_type == "calendar"][["region_id", "region", "n_years", "mean_gt", "mean_gt_pub", "bias_gt", "rmse_gt", "r_gt",
                                      "rmse_mwe", "r_mwe", "frac_within_1sigma", "frac_within_2sigma"]]
V.to_csv(os.path.join(TAB, "T4_validation_vs_published.csv"), index=False)
with open(os.path.join(TAB, "T4_validation_vs_published.md"), "w") as fh:
    fh.write("| Region | Mean recon. (Gt a⁻¹) | Mean published (Gt a⁻¹) | Bias (Gt a⁻¹) | RMSE (Gt a⁻¹) | r | RMSE (m w.e.) | within 1σ | within 2σ |\n|:--|--:|--:|--:|--:|--:|--:|--:|--:|\n")
    for _, r in V.iterrows():
        fh.write(f"| {NAME[r.region_id]} | {r.mean_gt:.1f} | {r.mean_gt_pub:.1f} | {r.bias_gt:+.1f} | {r.rmse_gt:.1f} | {r.r_gt:.2f} | "
                 f"{r.rmse_mwe:.2f} | {r.frac_within_1sigma*100:.0f}% | {r.frac_within_2sigma*100:.0f}% |\n")
print("done")
