"""GlaMBIE 2000-2023 glacier mass change analysis.

Reads the published GlaMBIE result tables (calendar years, hydrological years)
and the input estimate files, then produces summary tables (outputs/) and
figures (report/images/). Run from the workspace root:
    python3 code/analysis.py
"""
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = "data/glambie"
OUT = "outputs"
IMG = "report/images"
os.makedirs(OUT, exist_ok=True)
os.makedirs(IMG, exist_ok=True)

# ---------- 1. load calendar-year results ----------
cal = {}
for f in sorted(glob.glob(f"{ROOT}/results/calendar_years/*.csv")):
    name = os.path.basename(f)[:-4].split("_", 1)[1]
    cal[name] = pd.read_csv(f)
regions = [k for k in cal if k != "global"]
glob_df = cal["global"].set_index("start_dates")
years = glob_df.index.values.astype(int)

# Long-format regional table
rows = []
for r in regions + ["global"]:
    d = cal[r]
    for _, x in d.iterrows():
        rows.append(dict(region=r, year=int(x.start_dates), gt=x.combined_gt,
                         gt_err=x.combined_gt_errors, mwe=x.combined_mwe,
                         mwe_err=x.combined_mwe_errors, area_km2=x.glacier_area))
long = pd.DataFrame(rows)
long.to_csv(f"{OUT}/calendar_year_all_regions_long.csv", index=False)

# ---------- 2. global series, consistency checks ----------
g = glob_df
reg_sum = sum(cal[r].set_index("start_dates").combined_gt for r in regions)
reg_err_quad = np.sqrt(sum(cal[r].set_index("start_dates").combined_gt_errors ** 2 for r in regions))
check = pd.DataFrame({
    "global_gt": g.combined_gt,
    "sum_regions_gt": reg_sum,
    "diff_gt": g.combined_gt - reg_sum,
    "global_err": g.combined_gt_errors,
    "quad_sum_region_err": reg_err_quad,
})
check.to_csv(f"{OUT}/global_vs_regional_sum_check.csv")
print("Max |global - sum(regions)| (Gt):", np.abs(check.diff_gt).max().round(3))

# Trend and cumulative with simple error propagation (independent-year assumption, reported as bounds)
tot_gt = g.combined_gt.sum()
tot_err_indep = np.sqrt((g.combined_gt_errors ** 2).sum())
tot_err_fullcorr = g.combined_gt_errors.sum()
slope, intercept = np.polyfit(years, g.combined_gt, 1, w=1 / g.combined_gt_errors)
early = g.loc[2000:2011]
late = g.loc[2012:2023]
summary = {
    "global_cum_2000_2023_Gt": tot_gt,
    "global_cum_err_indep_Gt": tot_err_indep,
    "global_cum_err_fullcorr_Gt": tot_err_fullcorr,
    "global_mean_rate_2000_2011_Gt_yr": early.combined_gt.mean(),
    "global_mean_rate_2000_2011_err_Gt_yr": np.sqrt((early.combined_gt_errors ** 2).sum()) / len(early),
    "global_mean_rate_2012_2023_Gt_yr": late.combined_gt.mean(),
    "global_mean_rate_2012_2023_err_Gt_yr": np.sqrt((late.combined_gt_errors ** 2).sum()) / len(late),
    "global_wls_trend_Gt_yr2": slope,
    "global_cum_mwe_2000_2023": g.combined_mwe.sum(),
}
pd.Series(summary).to_csv(f"{OUT}/global_summary.csv", header=["value"])
for k, v in summary.items():
    print(f"{k}: {v:.3f}")

# ---------- 3. regional totals ----------
reg_tot = []
for r in regions:
    d = cal[r]
    reg_tot.append(dict(region=r, cum_gt=d.combined_gt.sum(),
                        cum_gt_err_indep=np.sqrt((d.combined_gt_errors ** 2).sum()),
                        cum_mwe=d.combined_mwe.sum(),
                        mean_mwe_yr=d.combined_mwe.mean(),
                        area_km2_2000=d.glacier_area.iloc[0]))
reg_tot = pd.DataFrame(reg_tot).sort_values("cum_gt")
reg_tot.to_csv(f"{OUT}/regional_totals_2000_2023.csv", index=False)
print(reg_tot.round(2).to_string(index=False))

# ---------- 4. method comparison (hydrological years, per region) ----------
hyd = {}
for f in sorted(glob.glob(f"{ROOT}/results/hydrological_years/*.csv")):
    name = os.path.basename(f)[:-4].split("_", 1)[1]
    hyd[name] = pd.read_csv(f)
method_rows = []
for r, d in hyd.items():
    if r == "global":
        continue
    for m in ["altimetry", "gravimetry", "demdiff_and_glaciological"]:
        sub = d[[f"{m}_mwe", f"{m}_mwe_errors", "start_dates", "end_dates"]].dropna()
        if len(sub) == 0:
            continue
        method_rows.append(dict(region=r, method=m,
                                n_periods=len(sub),
                                mean_mwe_yr=sub[f"{m}_mwe"].mean(),
                                mean_err=sub[f"{m}_mwe_errors"].mean(),
                                period_start=sub.start_dates.min(),
                                period_end=sub.end_dates.max()))
meth = pd.DataFrame(method_rows)
meth.to_csv(f"{OUT}/method_summary_by_region.csv", index=False)
print(meth.round(3).head(20).to_string(index=False))

# ---------- 5. figures ----------
plt.rcParams.update({"font.size": 10, "figure.dpi": 150})

# Fig 1: global annual mass change with uncertainty
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.axhline(0, color="k", lw=0.6)
ax.errorbar(years + 0.5, g.combined_gt, yerr=g.combined_gt_errors, fmt="o-", ms=3, capsize=2,
            color="C0", ecolor="0.6", label="GlaMBIE combined (±1σ as reported)")
ax.set_xlabel("Calendar year")
ax.set_ylabel("Mass change (Gt yr$^{-1}$)")
ax.set_title("Global glacier mass change, 2000–2023")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{IMG}/fig1_global_annual.png"); plt.close(fig)

# Fig 2: cumulative global mass change
cum = g.combined_gt.cumsum()
cum_err = np.sqrt((g.combined_gt_errors ** 2).cumsum())
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(years + 1, cum, color="C3", lw=2)
ax.fill_between(years + 1, cum - cum_err, cum + cum_err, color="C3", alpha=0.2, label="±1σ (independent years)")
ax.set_xlabel("Year (end of interval)")
ax.set_ylabel("Cumulative mass change (Gt)")
ax.set_title("Cumulative global glacier mass change")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{IMG}/fig2_global_cumulative.png"); plt.close(fig)

# Fig 3: regional cumulative totals with error bars
rt = reg_tot.sort_values("cum_gt")
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(rt.region, rt.cum_gt, xerr=rt.cum_gt_err_indep, color="C0", ecolor="0.4", capsize=2)
ax.axvline(0, color="k", lw=0.6)
ax.set_xlabel("Cumulative mass change 2000–2023 (Gt)")
ax.set_title("Regional cumulative mass change (error: independent-year propagation)")
fig.tight_layout(); fig.savefig(f"{IMG}/fig3_regional_cumulative.png"); plt.close(fig)

# Fig 4: regional specific mass change heatmap (m w.e. yr-1)
piv = long[long.region != "global"].pivot(index="region", columns="year", values="mwe")
piv = piv.loc[reg_tot.sort_values("cum_gt").region]
fig, ax = plt.subplots(figsize=(10, 6))
im = ax.imshow(piv.values, aspect="auto", cmap="RdBu", vmin=-2.5, vmax=2.5)
ax.set_yticks(range(len(piv.index)), piv.index)
ax.set_xticks(range(0, len(piv.columns), 2), piv.columns[::2])
ax.set_title("Regional specific mass change (m w.e. yr$^{-1}$)")
fig.colorbar(im, ax=ax, label="m w.e. yr$^{-1}$")
fig.tight_layout(); fig.savefig(f"{IMG}/fig4_regional_mwe_heatmap.png"); plt.close(fig)

# Fig 5: method comparison for the 4 regions with most data (hydrological years)
ex_regions = ["alaska", "western_canada_us", "arctic_canada_north", "svalbard", "southern_andes", "iceland"]
fig, axes = plt.subplots(2, 3, figsize=(12, 7), sharey=False)
for ax, r in zip(axes.ravel(), ex_regions):
    d = hyd[r]
    for i, m in enumerate(["altimetry", "gravimetry", "demdiff_and_glaciological"]):
        s = d[["start_dates", f"{m}_mwe", f"{m}_mwe_errors"]].dropna()
        if len(s):
            ax.errorbar(s.start_dates + 0.02 * i, s[f"{m}_mwe"], yerr=s[f"{m}_mwe_errors"],
                        fmt="o", ms=3, capsize=1.5, label=m, color=f"C{i+1}", alpha=0.7)
    c = d[["start_dates", "combined_mwe", "combined_mwe_errors"]].dropna()
    ax.errorbar(c.start_dates, c.combined_mwe, yerr=c.combined_mwe_errors, fmt="k-", lw=1.2, label="combined")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_title(r)
    ax.set_xlabel("Period start (yr)")
    ax.set_ylabel("m w.e. per period")
axes[0, 0].legend(fontsize=7, frameon=False)
fig.suptitle("Method-level estimates vs. GlaMBIE combined solution (hydrological years)")
fig.tight_layout(); fig.savefig(f"{IMG}/fig5_method_comparison.png"); plt.close(fig)

# Fig 6: sum-of-regions check
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(years, check.global_gt, "o-", label="GlaMBIE global")
ax.plot(years, check.sum_regions_gt, "s--", label="Sum of 19 regions")
ax.set_xlabel("Calendar year"); ax.set_ylabel("Gt yr$^{-1}$")
ax.set_title("Consistency of global aggregate with regional sum")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{IMG}/fig6_global_regional_consistency.png"); plt.close(fig)

# ---------- 6. input inventory ----------
inv = []
for f in glob.glob(f"{ROOT}/input/*/*.csv"):
    base = os.path.basename(f)
    parts = base[:-4].split("_")
    inv.append(dict(region_folder=os.path.basename(os.path.dirname(f)), file=base))
inv = pd.DataFrame(inv)
inv["method"] = inv.file.str.extract(r"_(altimetry|gravimetry|demdiff|glaciological|combined)_")[0]
inv.to_csv(f"{OUT}/input_inventory.csv", index=False)
print("Input files:", len(inv))
print(inv.method.value_counts().to_string())
