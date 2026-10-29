"""Run the full reconstruction: regional/global series, group series, period rates, validation, robustness.
Usage: python run_all.py [--ndraw 1000] [--out ../outputs]"""
import argparse, os, time, warnings
import numpy as np, pandas as pd
import glambie_recon as g

warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--ndraw", type=int, default=1000)
ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs"))
ap.add_argument("--skip-robustness", action="store_true")
args = ap.parse_args()
OUT = os.path.abspath(args.out)
os.makedirs(OUT, exist_ok=True)
GROUPNAME = {"alt": "altimetry", "grav": "gravimetry", "dg": "demdiff_glaciological"}
PERIODS = {"2000-2011": (2000, 2011), "2012-2023": (2012, 2023), "2000-2023": (2000, 2023), "2000-2019": (2000, 2019),
           "2000-2004": (2000, 2004), "2005-2009": (2005, 2009), "2010-2014": (2010, 2014), "2015-2019": (2015, 2019),
           "2020-2023": (2020, 2023)}


def run_regions(hydro, ndraw, seed=0, prep=None, run=None, regions=None):
    res = {}
    for rid in (regions or g.REGIONS):
        reg = g.prepare_region(rid, hydro=hydro, **(prep or {}))
        r = _run(reg, ndraw, seed, run or {})
        res[rid] = (reg, r)
    return res


def _run(reg, ndraw, seed, run):
    groups = run.get("groups")
    if groups is not None and len(g.combine_once(reg, None, **run)[1]) == 0:   # dropped group was the only one: keep all
        run = {k: v for k, v in run.items() if k != "groups"}
    r = g.run_region(reg, ndraw=ndraw, seed=seed, **run)
    return r


def table_regional(res, hydro):
    rows = []
    for rid, (reg, r) in res.items():
        gt = r["c0"] * reg["area"] / 1000
        mc = r["C"].std(0) * reg["area"] / 1000
        dp = r["disp"] * reg["area"] / 1000
        for k, s in enumerate(reg["starts"]):
            tot = np.hypot(mc[k], dp[k])
            rows.append(dict(region_id=rid, region=g.REGIONS[rid], start_dates=s, end_dates=s + 1, area_km2=reg["area"][k],
                             mwe=gt[k] / reg["area"][k] * 1000, mwe_err=tot / reg["area"][k] * 1000, gt=gt[k], gt_err=tot,
                             gt_err_mc=mc[k], gt_err_groupdisp=dp[k], n_groups=int(r["nG"][k]),
                             level_gt=r["L0"][k] * reg["area"][k] / 1000, annual_variability_gt=r["AV0"][k] * reg["area"][k] / 1000))
    return pd.DataFrame(rows)


def add_global(df, res):
    """Global = sum of regions; regional ensembles are independent, group-dispersion terms add in quadrature."""
    C = sum(r["C"] * reg["area"] / 1000 for reg, r in res.values())
    c0 = sum(r["c0"] * reg["area"] / 1000 for reg, r in res.values())
    dp = np.sqrt(sum((r["disp"] * reg["area"] / 1000) ** 2 for reg, r in res.values()))
    area = sum(reg["area"] for reg, r in res.values())
    mc = C.std(0)
    tot = np.hypot(mc, dp)
    starts = next(iter(res.values()))[0]["starts"]
    rows = [dict(region_id=0, region="global", start_dates=s, end_dates=s + 1, area_km2=area[k], mwe=c0[k] / area[k] * 1000,
                 mwe_err=tot[k] / area[k] * 1000, gt=c0[k], gt_err=tot[k], gt_err_mc=mc[k], gt_err_groupdisp=dp[k],
                 n_groups=np.nan, level_gt=np.nan, annual_variability_gt=np.nan) for k, s in enumerate(starts)]
    return pd.concat([pd.DataFrame(rows), df], ignore_index=True), C, c0


def period_rates(res, C_glob, c0_glob, starts):
    """Mean annual rates (Gt/yr, m w.e./yr) per region and global for each period; uncertainty = ensemble std
    (annual errors correlated as in the inputs) plus inter-group dispersion of the period means."""
    rows = []
    items = [(rid, g.REGIONS[rid], res[rid]) for rid in res] + [(0, "global", None)]
    store = {}
    for rid, name, rr in items:
        if rr is None:
            reg_area = sum(reg["area"] for reg, r in res.values()); C = C_glob; c0 = c0_glob
            dispf = None
        else:
            reg, r = rr; reg_area = reg["area"]; C = r["C"] * reg["area"] / 1000; c0 = r["c0"] * reg["area"] / 1000
        for pn, (a, b) in PERIODS.items():
            m = (starts >= a - 1e-9) & (starts <= b + 1e-9)
            rate = c0[m].mean(); dr = C[:, m].mean(1)
            area_m = reg_area[m].mean()
            # inter-group dispersion of the period mean (groups covering >= 80 % of the period)
            if rr is None:
                disp = np.sqrt(sum(store[(rid2, pn)][3] ** 2 for rid2 in res))
            else:
                reg, r = rr
                gm = [np.nanmean(v[m]) * reg["area"][m].mean() / 1000 for v in r["G0"].values() if np.mean(~np.isnan(v[m])) >= 0.8]
                disp = np.std(gm, ddof=1) / np.sqrt(len(gm)) if len(gm) > 1 else 0.0
            mc = dr.std()
            store[(rid, pn)] = (rate, mc, None, disp)
            rows.append(dict(region_id=rid, region=name, period=pn, n_years=int(m.sum()), rate_gt=rate, rate_gt_err=np.hypot(mc, disp),
                             rate_gt_err_mc=mc, rate_gt_err_groupdisp=disp, rate_mwe=rate / area_m * 1000,
                             rate_mwe_err=np.hypot(mc, disp) / area_m * 1000))
    return pd.DataFrame(rows), store


def accel(res, C_glob, c0_glob, starts, store):
    rows = []
    for rid in [0] + list(res):
        if rid == 0:
            C, c0, nm = C_glob, c0_glob, "global"
        else:
            reg, r = res[rid]; C = r["C"] * reg["area"] / 1000; c0 = r["c0"] * reg["area"] / 1000; nm = g.REGIONS[rid]
        m1 = (starts >= 2000) & (starts <= 2011); m2 = (starts >= 2012) & (starts <= 2023)
        d = c0[m2].mean() - c0[m1].mean(); dd = C[:, m2].mean(1) - C[:, m1].mean(1)
        disp = np.hypot(store[(rid, "2000-2011")][3], store[(rid, "2012-2023")][3])
        # linear trend in annual Gt (acceleration, Gt/yr per decade)
        t = starts - starts.mean()
        slope = lambda y: (t * (y - y.mean(axis=-1, keepdims=True))).sum(-1) / (t ** 2).sum() * 10
        s0, sd = slope(c0), slope(C)
        rows.append(dict(region_id=rid, region=nm, d_rate_2012_2023_minus_2000_2011_gt=d, d_rate_err=np.hypot(dd.std(), disp),
                         d_rate_err_mc=dd.std(), trend_gt_per_yr_per_decade=s0, trend_err=sd.std()))
    return pd.DataFrame(rows)


def cumulative_table(res, C_glob, c0_glob, starts, store):
    """Cumulative mass change since the start of 2000 (Gt) with ensemble sigma (covariance-aware) and the group-dispersion term
    (the 2000-2023 inter-group dispersion of the mean rate times elapsed years, i.e. a rate-type systematic error)."""
    rows = []
    for rid in [0] + list(res):
        if rid == 0:
            C, c0, nm = C_glob, c0_glob, "global"
        else:
            reg, r = res[rid]; C = r["C"] * reg["area"] / 1000; c0 = r["c0"] * reg["area"] / 1000; nm = g.REGIONS[rid]
        cc, CC = np.cumsum(c0), np.cumsum(C, 1)
        dc = store[(rid, "2000-2023")][3] * np.arange(1, len(starts) + 1)
        for k, s in enumerate(starts):
            mc = CC[:, k].std()
            rows.append(dict(region_id=rid, region=nm, end_dates=s + 1, cum_gt=cc[k], cum_gt_err_mc=mc, cum_gt_err_groupdisp=dc[k],
                             cum_gt_err=np.hypot(mc, dc[k]), cum_sle_mm=-cc[k] / 362.5))
    return pd.DataFrame(rows)


def group_table(res):
    rows = []
    for rid, (reg, r) in res.items():
        for k, v in r["G0"].items():
            sd = np.nanstd(r["GD"][k], 0)
            for j, s in enumerate(reg["starts"]):
                if np.isnan(v[j]):
                    continue
                n = sum(1 for a in reg["ann"] if {"alt": "alt", "grav": "grav", "dg": None}.get(k) == a["sub"] or
                        (k == "dg" and a["sub"] in ("dem", "av")) if not np.isnan(a["v"][j]))
                rows.append(dict(region_id=rid, region=g.REGIONS[rid], group=GROUPNAME[k], start_dates=s, end_dates=s + 1,
                                 mwe=v[j], mwe_err=sd[j], gt=v[j] * reg["area"][j] / 1000, gt_err=sd[j] * reg["area"][j] / 1000,
                                 n_solutions=n))
    return pd.DataFrame(rows)


def solution_table(res):
    rows = []
    for rid, (reg, r) in res.items():
        for a in reg["ann"]:
            for j, s in enumerate(reg["starts"]):
                if np.isnan(a["v"][j]):
                    continue
                rows.append(dict(region_id=rid, region=g.REGIONS[rid], solution=a["name"], source=a["source"],
                                 group={"alt": "altimetry", "grav": "gravimetry"}.get(a["sub"], "demdiff_glaciological"),
                                 start_dates=s, end_dates=s + 1, mwe=a["v"][j], mwe_err=a["err"][j],
                                 gt=a["v"][j] * reg["area"][j] / 1000, annual_resolved=a["annual"]))
    return pd.DataFrame(rows)


def inventory():
    rows = []
    for rid in g.REGIONS:
        used = {a["name"] for a in g.prepare_region(rid)["ann"]}
        for s in g.load_solutions(rid):
            d = s["df"]
            rows.append(dict(region_id=rid, region=g.REGIONS[rid], file=s["name"], source=s["source"], unit=s["unit"], n_rows=len(d),
                             first_start=d.start_dates.min(), last_end=d.end_dates.max(), median_interval_yr=float(np.median(d.end_dates - d.start_dates)),
                             used_in_main_run=s["name"] in used,
                             excluded_reason="" if s["name"] in used else "region not eligible for this data group (see README)"))
    return pd.DataFrame(rows)


def validation(df, pubdir, label, res, hydro):
    rows, yr = [], []
    for rid in ([0] if not hydro else []) + list(g.REGIONS):
        nm = "global" if rid == 0 else g.REGIONS[rid]
        p = pd.read_csv(f"{g.DATA}/results/{pubdir}/{rid}_{nm}.csv")
        p["start_dates"] = p.start_dates.round(4)
        m = df[df.region_id == rid].assign(start_dates=lambda x: x.start_dates.round(4)).merge(p, on="start_dates", suffixes=("", "_pub"))
        d = m["gt"] - m.combined_gt
        z = d / np.hypot(m["gt_err"], m.combined_gt_errors)
        dm = m["mwe"] - m.combined_mwe
        rows.append(dict(year_type=label, region_id=rid, region=nm, n_years=len(m), mean_gt=m["gt"].mean(), mean_gt_pub=m.combined_gt.mean(),
                         bias_gt=d.mean(), rmse_gt=np.sqrt((d ** 2).mean()), r_gt=np.corrcoef(m["gt"], m.combined_gt)[0, 1],
                         bias_mwe=dm.mean(), rmse_mwe=np.sqrt((dm ** 2).mean()), r_mwe=np.corrcoef(m["mwe"], m.combined_mwe)[0, 1],
                         frac_within_1sigma=(z.abs() <= 1).mean(), frac_within_2sigma=(z.abs() <= 2).mean(),
                         mean_err_gt=m["gt_err"].mean(), mean_err_gt_pub=m.combined_gt_errors.mean(),
                         cum_diff_gt=d.sum(), cum_err_gt=np.sqrt((m["gt_err"] ** 2).sum()) ))
        m["diff_gt"] = d; m["z"] = z; m["year_type"] = label
        yr.append(m[["year_type", "region_id", "region", "start_dates", "gt", "gt_err", "combined_gt", "combined_gt_errors", "mwe", "mwe_err",
                     "combined_mwe", "combined_mwe_errors", "diff_gt", "z"]].rename(columns={"gt": "gt_recon", "gt_err": "gt_err_recon",
                     "combined_gt": "gt_pub", "combined_gt_errors": "gt_err_pub", "mwe": "mwe_recon", "mwe_err": "mwe_err_recon",
                     "combined_mwe": "mwe_pub", "combined_mwe_errors": "mwe_err_pub"}))
    return pd.DataFrame(rows), pd.concat(yr)


def group_validation(res_h):
    """Reconstructed group series versus published per-group hydrological-year series."""
    rows = []
    cols = {"alt": "altimetry", "grav": "gravimetry", "dg": "demdiff_and_glaciological"}
    for rid, (reg, r) in res_h.items():
        p = pd.read_csv(f"{g.DATA}/results/hydrological_years/{rid}_{g.REGIONS[rid]}.csv")
        p = p.set_index(p.start_dates.round(4))
        for k, v in r["G0"].items():
            pg = np.array([p[cols[k] + "_gt"].get(round(s, 4), np.nan) for s in reg["starts"]])
            mine = v * reg["area"] / 1000
            ok = ~np.isnan(pg) & ~np.isnan(mine)
            if ok.sum() < 3:
                continue
            rows.append(dict(region_id=rid, region=g.REGIONS[rid], group=GROUPNAME[k], n_years=int(ok.sum()), mean_gt=mine[ok].mean(),
                             mean_gt_pub=pg[ok].mean(), bias_gt=(mine[ok] - pg[ok]).mean(), rmse_gt=np.sqrt(((mine - pg)[ok] ** 2).mean()),
                             r_gt=np.corrcoef(mine[ok], pg[ok])[0, 1]))
    return pd.DataFrame(rows)


def main():
    t0 = time.time()
    # ---- main run: calendar years and hydrological years
    res_c = run_regions(False, args.ndraw)
    df_c = table_regional(res_c, False)
    df_c, C_g, c0_g = add_global(df_c, res_c)
    starts_c = next(iter(res_c.values()))[0]["starts"]
    df_c.to_csv(f"{OUT}/regional_calendar_years.csv", index=False, float_format="%.6g")
    res_h = run_regions(True, max(200, args.ndraw // 4), seed=7)
    df_h = table_regional(res_h, True)
    df_h.to_csv(f"{OUT}/regional_hydrological_years.csv", index=False, float_format="%.6g")
    print("main done", time.time() - t0, flush=True)
    group_table(res_c).to_csv(f"{OUT}/group_series_calendar.csv", index=False, float_format="%.6g")
    group_table(res_h).to_csv(f"{OUT}/group_series_hydrological.csv", index=False, float_format="%.6g")
    solution_table(res_c).to_csv(f"{OUT}/solution_annual_calendar.csv", index=False, float_format="%.6g")
    inventory().to_csv(f"{OUT}/input_inventory.csv", index=False)
    pr, store = period_rates(res_c, C_g, c0_g, starts_c)
    cumulative_table(res_c, C_g, c0_g, starts_c, store).to_csv(f"{OUT}/cumulative_calendar_years.csv", index=False, float_format="%.6g")
    pr.to_csv(f"{OUT}/period_rates.csv", index=False, float_format="%.6g")
    accel(res_c, C_g, c0_g, starts_c, store).to_csv(f"{OUT}/acceleration.csv", index=False, float_format="%.6g")
    # ---- validation
    v1, y1 = validation(df_c, "calendar_years", "calendar", res_c, False)
    v2, y2 = validation(df_h, "hydrological_years", "hydrological", res_h, True)
    pd.concat([v1, v2]).to_csv(f"{OUT}/validation_vs_published.csv", index=False, float_format="%.6g")
    pd.concat([y1, y2]).to_csv(f"{OUT}/validation_vs_published_by_year.csv", index=False, float_format="%.6g")
    group_validation(res_h).to_csv(f"{OUT}/validation_groups_vs_published_hydrological.csv", index=False, float_format="%.6g")
    # published period rates (from the published calendar series) next to ours
    rows = []
    for rid in [0] + list(g.REGIONS):
        nm = "global" if rid == 0 else g.REGIONS[rid]
        p = pd.read_csv(f"{g.DATA}/results/calendar_years/{rid}_{nm}.csv")
        for pn, (a, b) in PERIODS.items():
            m = (p.start_dates >= a) & (p.start_dates <= b)
            rows.append(dict(region_id=rid, region=nm, period=pn, rate_gt_pub=p.combined_gt[m].mean(), rate_mwe_pub=p.combined_mwe[m].mean(),
                             rate_gt_err_pub_annual_rss=np.sqrt((p.combined_gt_errors[m] ** 2).sum()) / m.sum()))
    pp = pd.DataFrame(rows).merge(pr[["region_id", "period", "rate_gt", "rate_gt_err", "rate_mwe", "rate_mwe_err"]], on=["region_id", "period"])
    pp["diff_gt"] = pp.rate_gt - pp.rate_gt_pub
    pp["diff_over_recon_err"] = pp.diff_gt / pp.rate_gt_err
    pp.to_csv(f"{OUT}/period_rates_vs_published.csv", index=False, float_format="%.6g")
    print("validation done", time.time() - t0, flush=True)
    if args.skip_robustness:
        return
    # ---- robustness (central estimates only unless stated)
    scen = {
        "main": ({}, {}),
        "drop_altimetry": ({}, {"groups": ("grav", "dg")}),
        "drop_gravimetry": ({}, {"groups": ("alt", "dg")}),
        "only_demdiff_glaciological": ({}, {"groups": ("dg",)}),
        "hybrids_excluded": ({"hybrid_in_dg": False}, {}),
        "wgms_beta_excluded": ({"exclude": lambda s: "WGMS-beta" in s["name"]}, {}),
        "no_group_eligibility_rules": ({"eligibility": False}, {}),
        "plain_mean_no_weights": ({}, {"plain_mean": True}),
        "smoothing_window_3": ({}, {"win": 3}),
        "smoothing_window_7": ({}, {"win": 7}),
        "tau_0.05": ("TAU", 0.05), "tau_0.5": ("TAU", 0.5), "density_0.90": ("RHO", 0.90), "density_0.80": ("RHO", 0.80),
        "no_bootstrap_MC_only": ({}, {"bootstrap": False}),
        "errors_fully_correlated_in_time_per_solution": ("CORR", "solution"),
    }
    rows = []
    for name, (prep, run) in scen.items():
        old = None
        if isinstance(prep, str):                       # module-level parameter scenario
            pname, pval = prep, run
            old = (pname, getattr(g, pname)); setattr(g, pname, pval); prep, run = {}, {}
        nd = args.ndraw // 4 if name in ("main", "no_bootstrap_MC_only", "errors_fully_correlated_in_time_per_solution") else 1
        rs = run_regions(False, nd, seed=3, prep=prep, run=run)
        _, C, c0 = add_global(table_regional(rs, False), rs)
        for pn in ("2000-2023", "2000-2011", "2012-2023"):
            a, b = PERIODS[pn]; m = (starts_c >= a) & (starts_c <= b)
            rate = c0[m].mean(); sd = C[:, m].mean(1).std() if nd > 1 else np.nan
            rows.append(dict(scenario=name, period=pn, global_rate_gt=rate, mc_err=sd))
        rr = {g.REGIONS[rid]: (r["c0"] * reg["area"] / 1000)[(starts_c >= 2000)].mean() for rid, (reg, r) in rs.items()}
        for k, v in rr.items():
            rows.append(dict(scenario=name, period="2000-2023_region:" + k, global_rate_gt=v, mc_err=np.nan))
        if old is not None:
            setattr(g, old[0], old[1])
        print("robustness", name, time.time() - t0, flush=True)
    rb = pd.DataFrame(rows).rename(columns={"global_rate_gt": "rate_gt"})
    rb.to_csv(f"{OUT}/robustness_scenarios.csv", index=False, float_format="%.6g")
    # alternative uncertainty assumption for the global trend: regional group-dispersion fully correlated / no dispersion
    rows = []
    for pn in ("2000-2023", "2000-2011", "2012-2023"):
        sub = pr[pr.period == pn]
        glob = sub[sub.region_id == 0].iloc[0]
        regs = sub[sub.region_id > 0]
        rows.append(dict(period=pn, rate_gt=glob.rate_gt, err_mc=glob.rate_gt_err_mc, err_disp_independent=glob.rate_gt_err_groupdisp,
                         err_disp_fully_correlated=regs.rate_gt_err_groupdisp.sum(),
                         err_total_independent=glob.rate_gt_err,
                         err_total_correlated=np.hypot(glob.rate_gt_err_mc, regs.rate_gt_err_groupdisp.sum())))
    pd.DataFrame(rows).to_csv(f"{OUT}/robustness_global_uncertainty.csv", index=False, float_format="%.6g")
    print("all done", time.time() - t0)


if __name__ == "__main__":
    main()
