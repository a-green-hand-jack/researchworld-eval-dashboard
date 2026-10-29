"""Additional analyses requested in review (experiment-repo#6): acceleration significance under alternative error
assumptions, Zemp 2019 comparison on matched hydrological years, DEM+glaciological-only and Hugonnet 2021 comparison,
drop-DEM/glaciological robustness, group-validation summary. Usage: python review_analyses.py [--ndraw 1000]"""
import argparse, os, warnings
import numpy as np, pandas as pd
import glambie_recon as g
import run_all as ra            # reuses run_regions / helpers (argparse defaults apply: pass --out via env if needed)

warnings.filterwarnings("ignore")
OUT = ra.OUT
ND = ra.args.ndraw
starts = 2000.0 + np.arange(24)


def tot_gt(res):
    C = sum(r["C"] * reg["area"] / 1000 for reg, r in res.values())
    c0 = sum(r["c0"] * reg["area"] / 1000 for reg, r in res.values())
    return C, c0


def disp_period(res, a, b):
    """Inter-group dispersion of the period-mean rate per region (as in period_rates.csv)."""
    m = (starts >= a) & (starts <= b)
    out = {}
    for rid, (reg, r) in res.items():
        gm = [np.nanmean(v[m]) * reg["area"][m].mean() / 1000 for v in r["G0"].values() if np.mean(~np.isnan(v[m])) >= 0.8]
        out[rid] = np.std(gm, ddof=1) / np.sqrt(len(gm)) if len(gm) > 1 else 0.0
    return out


# ---------------------------------------------------------------- 1. acceleration significance under error variants
def accel_variants():
    rows = []
    for vname, corr in (("errors_independent_between_intervals (main)", "interval"), ("errors_fully_correlated_in_time_per_solution", "solution")):
        g.CORR = corr
        res = ra.run_regions(False, ND, seed=11)
        C, c0 = tot_gt(res)
        d1, d2, dall = disp_period(res, 2000, 2011), disp_period(res, 2012, 2023), disp_period(res, 2000, 2023)
        m1, m2, ma = starts <= 2011, starts >= 2012, np.ones(24, bool)
        t = starts - starts.mean(); slope = lambda y: (t * (y - y.mean(-1, keepdims=True))).sum(-1) / (t ** 2).sum() * 10
        for dvar in ("independent_regional_dispersion (main)", "fully_correlated_regional_dispersion", "no_dispersion"):
            def comb(dd):
                v = np.array(list(dd.values()))
                return {"independent_regional_dispersion (main)": np.sqrt((v ** 2).sum()), "fully_correlated_regional_dispersion": v.sum(),
                        "no_dispersion": 0.0}[dvar]
            s1, s2, sa = comb(d1), comb(d2), comb(dall)
            quant = {"rate_2000_2011": (c0[m1].mean(), C[:, m1].mean(1).std(), s1),
                     "rate_2012_2023": (c0[m2].mean(), C[:, m2].mean(1).std(), s2),
                     "rate_2000_2023": (c0.mean(), C.mean(1).std(), sa),
                     # difference of halves; group dispersion of the two halves treated as independent
                     "diff_2012_2023_minus_2000_2011": (c0[m2].mean() - c0[m1].mean(), (C[:, m2].mean(1) - C[:, m1].mean(1)).std(), np.hypot(s1, s2)),
                     # linear trend (Gt/yr per decade); dispersion contribution approximated as the half-difference dispersion / 12 yr * 10
                     "linear_trend_gt_per_yr_per_decade": (slope(c0), slope(C).std(), np.hypot(s1, s2) / 12 * 10)}
            for q, (val, smc, sd) in quant.items():
                tt = np.hypot(smc, sd)
                rows.append(dict(quantity=q, error_assumption_in_time=vname, regional_group_dispersion=dvar, value=val, sigma_ensemble=smc,
                                 sigma_group_dispersion=sd, sigma_total=tt, n_sigma=abs(val) / tt if q.startswith(("diff", "linear")) else np.nan))
    g.CORR = "interval"
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/acceleration_significance_variants.csv", index=False, float_format="%.6g")
    return df


# ---------------------------------------------------------------- 2. Zemp 2019 on matched hydrological years
ZEMP = {1: (-73, 17, -0.85), 2: (-12, 6, -0.83), 3: (-60, 84, -0.57), 4: (-23, 28, -0.57), 5: (-51, 17, -0.63), 6: (-5, 4, -0.50), 7: (-16, 8, -0.47),
        8: (-1, 1, -0.49), 9: (-24, 19, -0.47), 10: (-1, 1, -0.37), 11: (-2, 0, -0.87), 12: (-1, 1, -0.90), 13: (-7, 6, -0.15), 14: (-1, 4, -0.03),
        15: (-5, 2, -0.35), 16: (-2, 2, -1.03), 17: (-34, 11, -1.18), 18: (-1, 1, -0.68), 19: (-14, 108, -0.11)}


def zemp_matched():
    res = ra.run_regions(True, ND, seed=13)
    rows, rec = [], {}
    for rid, (reg, r) in res.items():
        st = reg["starts"]
        s0 = st[np.argmin(np.abs(st - 2006.75))]            # hydrological year 2006/07 = Oct 2006 for northern regions
        m = (st >= s0 - 1e-9) & (st <= s0 + 9 + 1e-9)
        gt = r["c0"] * reg["area"] / 1000; C = r["C"] * reg["area"] / 1000
        gm = [np.nanmean(v[m]) * reg["area"][m].mean() / 1000 for v in r["G0"].values() if np.mean(~np.isnan(v[m])) >= 0.8]
        disp = np.std(gm, ddof=1) / np.sqrt(len(gm)) if len(gm) > 1 else 0.0
        p = pd.read_csv(f"{g.DATA}/results/hydrological_years/{rid}_{g.REGIONS[rid]}.csv")
        pm = p[(p.start_dates.round(4) >= round(s0, 4) - 1e-6) & (p.start_dates.round(4) <= round(s0, 4) + 9 + 1e-6)]
        rec[rid] = (gt[m].mean(), C[:, m].mean(1), disp, reg["area"][m].mean(), s0, pm.combined_gt.mean(), len(pm))
    def add(name, ids, zg, zci, zmwe):
        v = sum(rec[i][0] for i in ids); ens = sum(rec[i][1] for i in ids); disp = np.sqrt(sum(rec[i][2] ** 2 for i in ids))
        area = sum(rec[i][3] for i in ids); smc = ens.std(); st = np.hypot(smc, disp)
        pub = sum(rec[i][5] for i in ids)
        rows.append(dict(region=name, hydro_window="10 hydrological years starting " + ",".join(sorted({f"{rec[i][4]:.2f}" for i in ids})),
                         recon_gt=v, recon_sigma_ensemble=smc, recon_sigma_groupdisp=disp, recon_sigma_total=st, recon_mwe=v / area * 1000,
                         recon_mwe_sigma=st / area * 1000, published_glambie_same_window_gt=pub, zemp_gt=zg, zemp_ci95=zci, zemp_sigma1_approx=zci / 2, zemp_mwe=zmwe,
                         diff_gt=v - zg, diff_over_combined_sigma=(v - zg) / np.hypot(st, zci / 2) if np.hypot(st, zci / 2) > 0 else np.nan))
    for rid in g.REGIONS:
        zg, zci, zm = ZEMP[rid]
        add(g.REGIONS[rid], [rid], zg, zci, zm)
    sub = [i for i in g.REGIONS if i not in (5, 19)]
    add("total_excl_GRL_ANT (Zemp -267 +/-19, -0.55 +/-0.04)", sub, -267, 19, -0.55)
    add("global_total_19_regions (Zemp Table 1 -332 +/-144, -0.47 +/-0.20)", list(g.REGIONS), -332, 144, -0.47)
    pd.DataFrame(rows).to_csv(f"{OUT}/zemp2019_matched_hydrological_2006_2016.csv", index=False, float_format="%.6g")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 3. DEM(+glaciological) group vs Hugonnet 2021, 2000-2019
def dem_vs_hugonnet():
    m = (starts <= 2019)
    rows = []
    # (a) main and DEM+glaciological-only ensembles
    for name, run in (("main_combination", {}), ("DEM+glaciological group only", {"groups": ("dg",)})):
        res = ra.run_regions(False, ND, seed=17, run=run)
        C, c0 = tot_gt(res)
        rows.append(dict(estimate=name, rate_2000_2019_gt=c0[m].mean(), sigma_ensemble=C[:, m].mean(1).std(),
                         rate_2000_2023_gt=c0.mean(), note="ensemble sigma only (no group dispersion)"))
    # (b) DEM-only (fixed-effect combination of all DEM solutions, no glaciological anomalies) and Hugonnet solution alone
    res0 = ra.run_regions(False, 1)
    dem_tot = np.zeros(24); hug_tot = np.zeros(24); dem_cov = np.zeros(24); hug_cov = np.zeros(24)
    for rid, (reg, r) in res0.items():
        reg_ = reg
        gm = g.group_means(reg_, None, False, False, {})
        dem = gm["dem"][0]
        dem_tot += np.nan_to_num(dem) * reg["area"] / 1000; dem_cov += (~np.isnan(dem)) * reg["area"] / 1000
        hug = [a for a in reg_["ann"] if "Hugonnet" in a["name"]][0]["v"]
        hug_tot += np.nan_to_num(hug) * reg["area"] / 1000; hug_cov += (~np.isnan(hug)) * reg["area"] / 1000
    tot_area = sum(reg["area"] for reg, _ in res0.values()) / 1000
    for name, tot, cov in (("DEM solutions only (weighted fixed-effect mean, no annual variability)", dem_tot, dem_cov),
                           ("Hugonnet et al. 2021 solution alone (sum of 19 regions)", hug_tot, hug_cov)):
        rows.append(dict(estimate=name, rate_2000_2019_gt=tot[m].mean(), sigma_ensemble=np.nan, rate_2000_2023_gt=np.nan,
                         note=f"mean glacier-area coverage 2000-2019 {np.mean((cov / tot_area)[m]):.3f} (1 = all regions all years)"))
    rows.append(dict(estimate="Hugonnet et al. 2021 as published (paper_004)", rate_2000_2019_gt=-267, sigma_ensemble=8,
                     rate_2000_2023_gt=np.nan, note="published -267 +/-16 is a 95% CI; sigma = CI/2"))
    pub = pd.read_csv(f"{g.DATA}/results/calendar_years/0_global.csv")
    rows.append(dict(estimate="published GlaMBIE consensus (dataset)", rate_2000_2019_gt=pub.combined_gt[:20].mean(), sigma_ensemble=np.nan,
                     rate_2000_2023_gt=pub.combined_gt.mean(), note=""))
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/dem_group_vs_hugonnet_2000_2019.csv", index=False, float_format="%.6g")
    return df


# ---------------------------------------------------------------- 4. drop DEM+glaciological
def drop_dg():
    rows = []
    res_m = ra.run_regions(False, 1)
    res_d = {}
    for rid in g.REGIONS:
        reg = g.prepare_region(rid)
        c, G, _, _ = g.combine_once(reg, None, groups=("alt", "grav"))
        if len(G):
            res_d[rid] = (reg, c)
    elig = sorted(res_d)
    # common window: years where every eligible region has a value
    ok = np.all([~np.isnan(res_d[i][1]) for i in elig], axis=0)
    # also give a window excluding regions with short altimetry-only records
    def stats(ids, mask, label):
        a = sum((res_m[i][1]["c0"] * res_m[i][0]["area"] / 1000)[mask] for i in ids).mean()
        b = sum((res_d[i][1] * res_d[i][0]["area"] / 1000)[mask] for i in ids).mean()
        rows.append(dict(set=label, regions=" ".join(str(i) for i in ids), years=f"{int(starts[mask][0])}-{int(starts[mask][-1])} ({mask.sum()} yr)",
                         main_gt=a, without_demdiff_glaciological_gt=b, difference_gt=b - a, ratio=b / a))
    stats(elig, ok, "all regions having altimetry or gravimetry, common valid years")
    big = [i for i in elig if i in (1, 3, 4, 6, 7, 9, 17)]       # regions with gravimetry
    okg = np.all([~np.isnan(res_d[i][1]) for i in big], axis=0)
    stats(big, okg, "regions with gravimetry")
    for i in elig:                                       # per region, own valid years
        mk = ~np.isnan(res_d[i][1])
        if mk.sum() >= 5:
            stats([i], mk, g.REGIONS[i] + " (own valid years)")
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/robustness_drop_demdiff_glaciological.csv", index=False, float_format="%.6g")
    return df


# ---------------------------------------------------------------- 5. group-validation summary
def group_validation_summary():
    v = pd.read_csv(f"{OUT}/validation_groups_vs_published_hydrological.csv")
    s = v.groupby("group").agg(n_regions=("region", "nunique"), mean_bias_gt=("bias_gt", "mean"), median_bias_gt=("bias_gt", "median"),
                               mean_abs_bias_gt=("bias_gt", lambda x: x.abs().mean()), median_rmse_gt=("rmse_gt", "median"),
                               mean_rmse_gt=("rmse_gt", "mean"), median_r=("r_gt", "median"), min_r=("r_gt", "min")).reset_index()
    s.to_csv(f"{OUT}/validation_groups_summary.csv", index=False, float_format="%.4g")
    w = v.pivot(index=["region_id", "region"], columns="group", values=["bias_gt", "rmse_gt", "r_gt"])
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w.reset_index().to_csv(f"{OUT}/validation_groups_by_region_wide.csv", index=False, float_format="%.4g")
    return s


if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    a = accel_variants(); print(a[a.quantity.str.startswith(("diff", "linear", "rate_2000_2023"))].round(2).to_string())
    z = zemp_matched(); print(z.round(2).to_string())
    h = dem_vs_hugonnet(); print(h.round(2).to_string())
    d = drop_dg(); print(d.round(2).to_string())
    print(group_validation_summary().round(2).to_string())
