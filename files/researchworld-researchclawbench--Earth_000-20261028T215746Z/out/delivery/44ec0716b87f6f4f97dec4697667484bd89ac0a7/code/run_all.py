"""Reproduce the reconciled 2000-2023 regional and global glacier mass change.

Usage (from the workspace root):  python code/run_all.py [--data data/glambie]
Writes outputs/reconciliation/ and outputs/validation/.
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "analysis"))
import homogenise as H  # noqa: E402
import reconcile as R   # noqa: E402

GT_PER_MM = 362.5
# regions where GlaMBIE retained gravimetry in its consensus (data/glambie/
# results: non-empty gravimetry_gt columns); elsewhere glacier signals are
# small relative to GRACE leakage from ice sheets, hydrology and the spatial
# resolution (~300 km)
GRAV_REGIONS = {1, 3, 4, 6, 7, 9, 17}
PERIOD = (2000, 2023)

VARIANTS = {
    "main": {},
    "equal_weights": {"weighting": "equal"},
    "independent_group_errors": {"errors": "independent"},
    "glaciological_UZH_with_trend": {"uzh_trend": True},
    "gravimetry_all_regions": {"grav": "all"},
    "no_gravimetry": {"grav": "none"},
    "no_altimetry": {"drop": "altimetry"},
    "no_demdiff_glaciological": {"drop": "demdiff_and_glaciological"},
    "with_hybrid_group": {"hybrid": True},
    "density_800": {"rho": 800.0},
    "density_900": {"rho": 900.0},
}


def rnum(region):
    return int(region.split("_")[0])


def run_variant(data_dir, cfg, subs_cache):
    rho = cfg.get("rho", 850.0)
    if rho not in subs_cache:
        H.RHO = rho
        subs_cache[rho] = H.load_inputs(data_dir)
        H.RHO = 850.0
    subs = subs_cache[rho]
    regions = H.region_list(data_dir)
    grp_rows, reg_h, reg_c, diag = [], [], [], []
    for region in regions:
        h0 = H.hydro_start(region)
        area = H.load_area(data_dir, region)
        rs = [s for s in subs if s["region"] == region]
        dg = R.solve_group([s for s in rs if s["group"] ==
                            "demdiff_and_glaciological"], h0,
                           abs_labels=("SineWave",) if cfg.get("uzh_trend") else ())
        groups = {"demdiff_and_glaciological": dg}
        for g in ("altimetry", "gravimetry"):
            gs = [s for s in rs if s["group"] == g]
            if g == "gravimetry":
                mode = cfg.get("grav", "glambie")
                if mode == "none" or (mode == "glambie" and
                                      rnum(region) not in GRAV_REGIONS):
                    gs = []
            groups[g] = R.solve_group(gs, h0, borrow=dg) if gs else None
        if cfg.get("hybrid"):
            groups["combined"] = R.solve_group(
                [s for s in rs if s["group"] == "combined"], h0, borrow=dg)
        groups = {k: v for k, v in groups.items() if v is not None}
        for k, v in groups.items():
            diag.append(dict(region=region, group=k, birge=v.attrs.get("birge"),
                             tau_mwe=v.attrs.get("tau"),
                             n_level_submissions=v.attrs.get("n_level"),
                             first_year=int(v.year.min()), last_year=int(v.year.max())))
        for k, v in groups.items():
            v = v.copy()
            v.attrs = {}
            v["region"], v["group"] = region, k
            grp_rows.append(v)
        use = {k: v for k, v in groups.items() if k != cfg.get("drop")}
        for v in use.values():
            v.attrs = {}
        cons = R.combine_groups(use, cfg.get("weighting", "iv"),
                                  cfg.get("errors", "dependent"))
        if cfg.get("drop"):
            # leave-one-group-out: years the remaining groups do not cover
            # keep the full combination, so that global sums stay complete
            full = R.combine_groups(groups, cfg.get("weighting", "iv"),
                                      cfg.get("errors", "dependent"))
            miss = full[~full.year.isin(cons.year)]
            cons = pd.concat([cons, miss.assign(groups="fallback:" + miss.groups)]
                             ).sort_values("year").reset_index(drop=True)
        cons["region"] = region
        b = np.array([H.hydro_bounds(int(y), h0) for y in cons.year]).reshape(-1, 2)
        cons["start_dates"], cons["end_dates"] = b[:, 0], b[:, 1]
        reg_h.append(cons)
        sine = [s for s in rs if s["source"] == "glaciological" and
                "SineWave" in s["label"]]
        cal = R.hydro_to_calendar(cons, sine[0]["native"] if sine else None,
                                  region)
        cal["region"] = region
        cal["glacier_area"] = area(cal.year + 0.5)
        reg_c.append(cal)
    grp = pd.concat(grp_rows, ignore_index=True)
    reg_h = pd.concat(reg_h, ignore_index=True)
    reg_c = pd.concat(reg_c, ignore_index=True)
    for df in (grp, reg_h):
        mid = []
        for _, r in df.iterrows():
            a, b = H.hydro_bounds(int(r.year), H.hydro_start(r.region))
            mid.append(H.load_area(data_dir, r.region)(0.5 * (a + b)))
        df["glacier_area"] = mid
    for df in (grp, reg_h, reg_c):
        df["gt"] = df.mwe * df.glacier_area / 1000.0
        df["gt_err"] = df.mwe_err * df.glacier_area / 1000.0
    reg_c = reg_c[(reg_c.year >= PERIOD[0]) & (reg_c.year <= PERIOD[1])]
    glob_ = reg_c.groupby("year").agg(
        n_regions=("region", "nunique"), glacier_area=("glacier_area", "sum"),
        gt=("gt", "sum"),
        gt_err=("gt_err", lambda e: np.sqrt(np.sum(e ** 2)))).reset_index()
    glob_["mwe"] = glob_["gt"] * 1000 / glob_.glacier_area
    glob_["mwe_err"] = glob_["gt_err"] * 1000 / glob_.glacier_area
    glob_["sle_mm"] = -glob_["gt"] / GT_PER_MM
    glob_["sle_mm_err"] = glob_["gt_err"] / GT_PER_MM
    return dict(subs=subs, groups=grp, hydro=reg_h, calendar=reg_c,
                global_=glob_, diag=pd.DataFrame(diag))


def period_stats(df, y0, y1, col="gt"):
    d = df[(df.year >= y0) & (df.year <= y1)]
    n = len(d)
    tot = d[col].sum()
    e_ind = np.sqrt(np.sum(d[col + "_err"] ** 2))
    e_cor = d[col + "_err"].sum()
    return dict(n_years=n, total=tot, total_err=e_ind,
                total_err_correlated=e_cor, rate=tot / n,
                rate_err=e_ind / n, rate_err_correlated=e_cor / n)


def summaries(res):
    rows = []
    cal, gl = res["calendar"], res["global_"]
    for region, d in cal.groupby("region", sort=False):
        r = dict(region=region,
                 glacier_area_2000=float(d.glacier_area.iloc[0]))
        for lab, (a, b) in {"2000_2023": PERIOD, "2000_2011": (2000, 2011),
                            "2012_2023": (2012, 2023)}.items():
            sg, sm = period_stats(d, a, b, "gt"), period_stats(d, a, b, "mwe")
            r[f"rate_gt_{lab}"], r[f"rate_gt_err_{lab}"] = sg["rate"], sg["rate_err"]
            r[f"rate_mwe_{lab}"], r[f"rate_mwe_err_{lab}"] = sm["rate"], sm["rate_err"]
            if lab == "2000_2023":
                r["cumulative_gt"], r["cumulative_gt_err"] = sg["total"], sg["total_err"]
                r["cumulative_mwe"], r["cumulative_mwe_err"] = sm["total"], sm["total_err"]
        rows.append(r)
    reg = pd.DataFrame(rows)
    reg["share_of_global_loss_pct"] = 100 * reg.cumulative_gt / reg.cumulative_gt.sum()
    g = {}
    for lab, (a, b) in {"2000_2023": PERIOD, "2000_2011": (2000, 2011),
                        "2012_2023": (2012, 2023)}.items():
        g[lab] = {"gt": period_stats(gl, a, b, "gt"),
                  "mwe": period_stats(gl, a, b, "mwe"),
                  "sle_mm": period_stats(gl.assign(sle_mm_err=gl.sle_mm_err), a, b, "sle_mm")}
    # linear acceleration of annual global mass change (Gt yr-2), WLS
    x, y, w = gl.year.values, gl["gt"].values, 1 / gl.gt_err.values ** 2
    X = np.vstack([np.ones_like(x), x - x.mean()]).T
    cov = np.linalg.inv(X.T @ (X * w[:, None]))
    beta = cov @ X.T @ (w * y)
    resid = y - X @ beta
    s2 = max(1.0, np.sum(w * resid ** 2) / (len(y) - 2))
    g["linear_trend_gt_per_yr2"] = {"slope": beta[1],
                                    "slope_err": np.sqrt(cov[1, 1] * s2),
                                    "per_decade": 10 * beta[1],
                                    "per_decade_err": 10 * np.sqrt(cov[1, 1] * s2)}
    return reg, g


def compare(ours, ref, key, cols=("mwe", "gt")):
    out = {}
    m = ours.merge(ref, on=key, suffixes=("", "_ref"))
    for c in list(m.columns):
        if c != key:
            m[c] = pd.to_numeric(m[c], errors="coerce")
    for c in cols:
        d = m[c] - m[c + "_ref"]
        out[f"n_{c}"] = int(d.notna().sum())
        out[f"bias_{c}"] = d.mean()
        out[f"rmse_{c}"] = np.sqrt(np.mean(d ** 2))
        out[f"r_{c}"] = np.corrcoef(m[c], m[c + "_ref"])[0, 1] if len(m) > 2 else np.nan
        comb = np.sqrt(m[c + "_err"] ** 2 + m[c + "_err_ref"] ** 2)
        out[f"frac_within_1sigma_{c}"] = float(np.mean(np.abs(d) <= comb))
        out[f"mean_err_{c}"] = m[c + "_err"].mean()
        out[f"mean_err_ref_{c}"] = m[c + "_err_ref"].mean()
    return out, m


def load_reference(data_dir):
    hy, ca = [], []
    for region in H.region_list(data_dir):
        for sub, lst in (("hydrological_years", hy), ("calendar_years", ca)):
            r = pd.read_csv(os.path.join(data_dir, "results", sub, region + ".csv"))
            r["region"] = region
            lst.append(r)
    g = pd.read_csv(os.path.join(data_dir, "results", "calendar_years", "0_global.csv"))
    return pd.concat(hy, ignore_index=True), pd.concat(ca, ignore_index=True), g


def year_of(df, region_col="region"):
    """Label of reference rows, matching ours (see homogenise.hydro_bounds)."""
    return np.floor(df.start_dates + 0.5).astype(int)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join("data", "glambie"))
    ap.add_argument("--out", default="outputs")
    a = ap.parse_args()
    od_r = os.path.join(a.out, "reconciliation")
    od_v = os.path.join(a.out, "validation")
    os.makedirs(od_r, exist_ok=True)
    os.makedirs(od_v, exist_ok=True)
    cache = {}
    results = {k: run_variant(a.data, v, cache) for k, v in VARIANTS.items()}
    res = results["main"]

    # ---- inventory of inputs
    inv = pd.DataFrame([{k: s[k] for k in ("region", "source", "group", "label",
                         "file", "unit", "n_rows", "native_dt", "resolved", "t0",
                         "t1", "trend_mwe", "trend_mwe_err")} for s in res["subs"]])
    inv["used_in_consensus"] = (inv.group != "combined") & ~(
        (inv.group == "gravimetry") & ~inv.region.map(rnum).isin(GRAV_REGIONS))
    inv["role"] = np.where(inv.source == "glaciological", "annual variability only",
                  np.where(inv.group == "combined", "comparison only (hybrid)",
                  np.where(inv.resolved, "annual series", "multi-year trend")))
    inv.loc[~inv.used_in_consensus & (inv.group == "gravimetry"), "role"] = \
        "excluded (gravimetry outside retained regions)"
    inv.to_csv(os.path.join(od_r, "inputs_inventory.csv"), index=False)

    # ---- main series
    cols = ["region", "year", "start_dates", "end_dates", "glacier_area", "mwe",
            "mwe_err", "gt", "gt_err"]
    grp = res["groups"].copy()
    b = [H.hydro_bounds(int(r.year), H.hydro_start(r.region)) for _, r in grp.iterrows()]
    grp["start_dates"], grp["end_dates"] = [x[0] for x in b], [x[1] for x in b]
    grp = grp[(grp.end_dates > 2000) & (grp.start_dates < 2024.5)]
    grp[["region", "group", "year", "start_dates", "end_dates", "glacier_area",
         "mwe", "mwe_err", "gt", "gt_err", "n_resolved", "n_trend",
         "borrowed"]].to_csv(os.path.join(od_r, "group_series_hydrological_years.csv"),
                             index=False)
    hy = res["hydro"]
    hy = hy[(hy.end_dates > 2000) & (hy.start_dates < 2024.5)]
    hy[cols + ["n_groups", "groups"]].to_csv(
        os.path.join(od_r, "regional_hydrological_years.csv"), index=False)
    ca = res["calendar"].copy()
    ca["start_dates"], ca["end_dates"] = ca.year.astype(float), ca.year + 1.0
    ca[cols].to_csv(os.path.join(od_r, "regional_calendar_years.csv"), index=False)
    gl = res["global_"]
    gl.to_csv(os.path.join(od_r, "global_calendar_years.csv"), index=False)
    res["diag"].to_csv(os.path.join(od_r, "group_diagnostics.csv"), index=False)
    reg_sum, glob_sum = summaries(res)
    reg_sum.to_csv(os.path.join(od_r, "summary_regional.csv"), index=False)

    # hybrid submissions as annual series (comparison only)
    hyb = []
    for s in res["subs"]:
        if s["group"] == "combined" and len(s["annual"]):
            d = s["annual"].copy()
            d["region"], d["label"] = s["region"], s["label"]
            hyb.append(d)
    hyb = pd.concat(hyb, ignore_index=True)
    hyb.to_csv(os.path.join(od_r, "hybrid_submissions_hydrological_years.csv"),
               index=False)

    # ---- validation against the published GlaMBIE results
    rh, rc, rg = load_reference(a.data)
    rh["year"], rc["year"], rg["year"] = year_of(rh), year_of(rc), year_of(rg)
    ren = {"combined_mwe": "mwe", "combined_mwe_errors": "mwe_err",
           "combined_gt": "gt", "combined_gt_errors": "gt_err"}
    rows, pairs = [], []
    for region in H.region_list(a.data):
        for lev, ours, ref in (("hydrological", hy, rh), ("calendar", ca, rc)):
            o = ours[(ours.region == region)][["year", "mwe", "mwe_err", "gt", "gt_err"]]
            r = ref[ref.region == region].rename(columns=ren)[["year", "mwe", "mwe_err", "gt", "gt_err"]]
            o = o[(o.year >= 2000) & (o.year <= 2023)]
            st, m = compare(o, r, "year")
            st.update(region=region, level=lev, rate_mwe=m.mwe.mean(),
                      rate_mwe_ref=m.mwe_ref.mean(), rate_gt=m["gt"].mean(),
                      rate_gt_ref=m.gt_ref.mean())
            rows.append(st)
            m["region"], m["level"] = region, lev
            pairs.append(m)
    vs = pd.DataFrame(rows)
    vs.to_csv(os.path.join(od_v, "vs_glambie_regional.csv"), index=False)
    pd.concat(pairs).to_csv(os.path.join(od_v, "vs_glambie_regional_pairs.csv"), index=False)
    gst, gm = compare(gl[["year", "mwe", "mwe_err", "gt", "gt_err"]],
                      rg.rename(columns=ren)[["year", "mwe", "mwe_err", "gt", "gt_err"]], "year")
    gm.to_csv(os.path.join(od_v, "vs_glambie_global_pairs.csv"), index=False)
    # per data group
    grows = []
    for g in R.GROUPS:
        refc = rh.rename(columns={f"{g}_mwe": "mwe_r", f"{g}_mwe_errors": "err_r"})
        for region in H.region_list(a.data):
            o = grp[(grp.region == region) & (grp.group == g)]
            r = refc[refc.region == region][["year", "mwe_r", "err_r"]].dropna()
            m = o.merge(r, on="year")
            if not len(m):
                grows.append(dict(region=region, group=g, n=0, ours_n=len(o), ref_n=len(r)))
                continue
            d = m.mwe - m.mwe_r
            grows.append(dict(region=region, group=g, n=len(m), ours_n=len(o), ref_n=len(r),
                              bias_mwe=d.mean(), rmse_mwe=np.sqrt(np.mean(d ** 2)),
                              r_mwe=np.corrcoef(m.mwe, m.mwe_r)[0, 1] if len(m) > 2 else np.nan,
                              mean_err=m.mwe_err.mean(), mean_err_ref=m.err_r.mean()))
    pd.DataFrame(grows).to_csv(os.path.join(od_v, "vs_glambie_groups.csv"), index=False)

    # ---- agreement between data groups (hydrological years, common years)
    ag = []
    for region, d in grp.groupby("region", sort=False):
        piv = d.pivot(index="year", columns="group", values="mwe")
        pe = d.pivot(index="year", columns="group", values="mwe_err")
        gs = [g for g in R.GROUPS if g in piv]
        for i in range(len(gs)):
            for j in range(i + 1, len(gs)):
                ok = piv[[gs[i], gs[j]]].dropna().index
                if not len(ok):
                    continue
                diff = piv.loc[ok, gs[i]] - piv.loc[ok, gs[j]]
                se = np.sqrt(pe.loc[ok, gs[i]] ** 2 + pe.loc[ok, gs[j]] ** 2)
                # mean-rate difference over common years; error of the mean
                # with errors treated as independent between years
                mdiff = diff.mean()
                mse = np.sqrt(np.sum(se ** 2)) / len(ok)
                ag.append(dict(region=region, group_a=gs[i], group_b=gs[j],
                               n_years=len(ok), first=int(ok.min()), last=int(ok.max()),
                               mean_rate_diff_mwe=mdiff, mean_rate_diff_err=mse,
                               z=mdiff / mse,
                               r_annual=np.corrcoef(piv.loc[ok, gs[i]], piv.loc[ok, gs[j]])[0, 1] if len(ok) > 2 else np.nan,
                               rms_annual_diff=np.sqrt(np.mean(diff ** 2)),
                               frac_annual_within_1sigma=float(np.mean(np.abs(diff) <= se))))
    pd.DataFrame(ag).to_csv(os.path.join(od_v, "group_agreement.csv"), index=False)

    # ---- hybrid submissions versus consensus (common hydrological years)
    hr = []
    for (region, lab), d in hyb.groupby(["region", "label"], sort=False):
        m = d.merge(hy[hy.region == region][["year", "mwe", "mwe_err"]], on="year",
                    suffixes=("", "_cons"))
        m = m[(m.year >= 2000) & (m.year <= 2023)]
        if len(m) < 2:
            continue
        dd = m.mwe - m.mwe_cons
        hr.append(dict(region=region, label=lab, n_years=len(m), first=int(m.year.min()),
                       last=int(m.year.max()), mean_rate=m.mwe.mean(),
                       mean_rate_cons=m.mwe_cons.mean(), mean_rate_diff=dd.mean(),
                       r_annual=np.corrcoef(m.mwe, m.mwe_cons)[0, 1] if len(m) > 2 else np.nan,
                       rms_annual_diff=np.sqrt(np.mean(dd ** 2))))
    pd.DataFrame(hr).to_csv(os.path.join(od_v, "hybrid_vs_consensus.csv"), index=False)

    # ---- sensitivity of global and regional results to method choices
    sens, sreg = [], []
    for k, r in results.items():
        rs, gs_ = summaries(r)
        sens.append(dict(variant=k, **{f"rate_gt_{p}": gs_[p]["gt"]["rate"] for p in ("2000_2023", "2000_2011", "2012_2023")},
                         rate_gt_err_2000_2023=gs_["2000_2023"]["gt"]["rate_err"],
                         cumulative_gt=gs_["2000_2023"]["gt"]["total"],
                         cumulative_gt_err=gs_["2000_2023"]["gt"]["total_err"],
                         rate_mwe_2000_2023=gs_["2000_2023"]["mwe"]["rate"],
                         trend_gt_per_decade=gs_["linear_trend_gt_per_yr2"]["per_decade"]))
        rs = rs[["region", "rate_mwe_2000_2023", "rate_mwe_err_2000_2023", "rate_gt_2000_2023"]].copy()
        rs["variant"] = k
        sreg.append(rs)
    pd.DataFrame(sens).to_csv(os.path.join(od_v, "sensitivity_global.csv"), index=False)
    pd.concat(sreg).to_csv(os.path.join(od_v, "sensitivity_regional.csv"), index=False)

    # ---- combined structural + random uncertainty of the headline numbers
    # random: quadrature of annual errors (main run). structural: SD of the
    # central values over alternative configurations. Excluded from the
    # structural set: density variants (density error already propagated in
    # the random part) and independent_group_errors (same central values).
    STRUCT = ["equal_weights", "glaciological_UZH_with_trend",
              "gravimetry_all_regions", "no_gravimetry", "with_hybrid_group",
              "no_altimetry", "no_demdiff_glaciological"]
    STRUCT_CHOICES = STRUCT[:5]          # without leave-one-group-out
    sums = {k: summaries(r)[1] for k, r in results.items()}
    comb = {"definition": {
        "random": "annual 1-sigma errors of the main run combined in quadrature",
        "structural": "sample SD (ddof=1) of the main and alternative-configuration central values",
        "combined": "sqrt(random^2 + structural^2)",
        "structural_set": ["main"] + STRUCT,
        "structural_set_choices_only": ["main"] + STRUCT_CHOICES,
        "excluded": "density_800/900 (density error already in random part), "
                    "independent_group_errors (identical central values)",
        "half_range": "half of (max - min) over the same set, for reference"}}
    gl_main = results["main"]["global_"]
    area_mean = {lab: gl_main[(gl_main.year >= a_) & (gl_main.year <= b_)].glacier_area.mean()
                 for lab, (a_, b_) in {"2000_2023": PERIOD, "2000_2011": (2000, 2011),
                                       "2012_2023": (2012, 2023)}.items()}

    def quantity(get, rand):
        out = {"value": get(sums["main"]), "random": rand}
        for tag, vs in (("", STRUCT), ("_choices_only", STRUCT_CHOICES)):
            vals = np.array([get(sums[k]) for k in ["main"] + vs])
            sd = float(np.std(vals, ddof=1))
            out["structural_sd" + tag] = sd
            out["half_range" + tag] = float((vals.max() - vals.min()) / 2)
            out["combined" + tag] = float(np.hypot(rand, sd))
        return out

    for lab in ("2000_2023", "2000_2011", "2012_2023"):
        for unit in ("gt", "mwe"):
            comb[f"rate_{unit}_{lab}"] = quantity(
                lambda g, l=lab, u=unit: g[l][u]["rate"], sums["main"][lab][unit]["rate_err"])
    for unit in ("gt", "mwe"):
        comb[f"cumulative_{unit}_2000_2023"] = quantity(
            lambda g, u=unit: g["2000_2023"][u]["total"], sums["main"]["2000_2023"][unit]["total_err"])
        comb[f"cumulative_{unit}_2000_2023"]["random_correlated_bound"] = \
            sums["main"]["2000_2023"][unit]["total_err_correlated"]
    comb["sle_mm_2000_2023"] = quantity(
        lambda g: g["2000_2023"]["sle_mm"]["total"], sums["main"]["2000_2023"]["sle_mm"]["total_err"])
    for unit in ("gt", "mwe"):
        r1 = sums["main"]["2000_2011"][unit]["rate_err"]
        r2 = sums["main"]["2012_2023"][unit]["rate_err"]
        comb[f"rate_difference_{unit}_2012_2023_minus_2000_2011"] = quantity(
            lambda g, u=unit: g["2012_2023"][u]["rate"] - g["2000_2011"][u]["rate"],
            float(np.hypot(r1, r2)))
    comb["per_variant"] = {k: {"rate_gt_2000_2023": v["2000_2023"]["gt"]["rate"],
                               "rate_gt_2000_2011": v["2000_2011"]["gt"]["rate"],
                               "rate_gt_2012_2023": v["2012_2023"]["gt"]["rate"],
                               "cumulative_gt_2000_2023": v["2000_2023"]["gt"]["total"]}
                           for k, v in sums.items()}

    # ---- trend of annual global mass change with error- and AR(1)-aware errors
    x = gl_main.year.values.astype(float)
    y = gl_main["gt"].values
    e = gl_main.gt_err.values
    n = len(y)
    X = np.vstack([np.ones(n), x - x.mean()]).T
    tr = {}
    # (a) OLS with AR(1)-adjusted effective sample size
    bo, *_ = np.linalg.lstsq(X, y, rcond=None)
    ro = y - X @ bo
    rho_o = float(np.corrcoef(ro[:-1], ro[1:])[0, 1])
    s2 = np.sum(ro ** 2) / (n - 2)
    se_ols = float(np.sqrt(s2 / np.sum((x - x.mean()) ** 2)))
    neff = n * (1 - rho_o) / (1 + rho_o) if rho_o > 0 else n
    infl = np.sqrt((n - 2) / max(neff - 2, 1.0)) if rho_o > 0 else 1.0
    tr["ols"] = {"slope_gt_per_yr2": bo[1], "slope_err": se_ols, "lag1_residual_autocorr": rho_o,
                 "n": n, "n_eff_ar1": neff, "slope_err_ar1": se_ols * infl}
    # (b) WLS with the annual 1-sigma errors, Birge-scaled, AR(1)-adjusted
    w = 1 / e ** 2
    cov = np.linalg.inv(X.T @ (X * w[:, None]))
    bw = cov @ X.T @ (w * y)
    rw = (y - X @ bw) / e
    rho_w = float(np.corrcoef(rw[:-1], rw[1:])[0, 1])
    birge = float(np.sqrt(np.sum(rw ** 2) / (n - 2)))
    se_w = float(np.sqrt(cov[1, 1]))
    neff_w = n * (1 - rho_w) / (1 + rho_w) if rho_w > 0 else n
    infl_w = np.sqrt((n - 2) / max(neff_w - 2, 1.0)) if rho_w > 0 else 1.0
    tr["wls"] = {"slope_gt_per_yr2": bw[1], "slope_err_stated_errors": se_w,
                 "birge_ratio": birge, "lag1_residual_autocorr": rho_w, "n_eff_ar1": neff_w,
                 "slope_err": se_w * max(1.0, birge) * infl_w,
                 "note": "slope_err = stated-error WLS error x max(1, Birge) x AR(1) inflation"}
    # (c) Monte Carlo: perturb annual values within errors (independent, and
    #     with a fully correlated common component), refit OLS
    rng = np.random.default_rng(42)
    nmc = 20000
    sl_ind = np.empty(nmc)
    for i in range(nmc):
        yy = y + rng.normal(0, e)
        sl_ind[i] = np.linalg.lstsq(X, yy, rcond=None)[0][1]
    tr["monte_carlo"] = {"n_draws": nmc, "slope_sd_measurement_only": float(np.std(sl_ind)),
                         "slope_err_total": float(np.hypot(np.std(sl_ind), se_ols * infl)),
                         "note": "measurement-only SD from perturbing annual values with their 1-sigma "
                                 "(independent years; a common offset does not change the slope); "
                                 "total adds the AR(1)-adjusted OLS residual error in quadrature"}
    sl_var = np.array([summaries(results[k])[1]["linear_trend_gt_per_yr2"]["slope"]
                       for k in ["main"] + STRUCT])
    tr["structural_sd_slope"] = float(np.std(sl_var, ddof=1))
    tr["recommended"] = {
        "slope_gt_per_yr2": bw[1],
        "slope_err": float(np.hypot(se_w * max(1.0, birge) * infl_w, tr["structural_sd_slope"])),
        "per_decade": 10 * bw[1],
        "per_decade_err": 10 * float(np.hypot(se_w * max(1.0, birge) * infl_w,
                                              tr["structural_sd_slope"])),
        "definition": "WLS slope; error = AR(1)- and Birge-adjusted WLS error combined in "
                      "quadrature with the structural SD of the slope over the variant set"}
    for k in ("ols", "wls"):
        tr[k]["per_decade"] = 10 * tr[k]["slope_gt_per_yr2"]
    tr["ols"]["per_decade_err_ar1"] = 10 * tr["ols"]["slope_err_ar1"]
    tr["wls"]["per_decade_err"] = 10 * tr["wls"]["slope_err"]
    comb["trend_of_annual_global_mass_change"] = tr
    with open(os.path.join(od_v, "headline_uncertainty.json"), "w") as f:
        json.dump(comb, f, indent=1, default=float)

    # ---- prior global estimates (values quoted from related_work papers)
    prior = [  # (source, period, Gt/yr, err, where)
        ("Hugonnet et al. 2021", 2000, 2004, -227, 25, "Table 1"),
        ("Hugonnet et al. 2021", 2005, 2009, -257, 22, "Table 1"),
        ("Hugonnet et al. 2021", 2010, 2014, -284, 23, "Table 1"),
        ("Hugonnet et al. 2021", 2015, 2018, -292, 24, "Table 1 (2015-2018)"),
        ("Hugonnet et al. 2021", 2000, 2019, -267, 16, "abstract (2000-2019)"),
        ("Zemp et al. 2019", 2006, 2016, -335, 144, "abstract (2006-2016)"),
    ]
    pr = []
    rgg = rg.rename(columns=ren)
    for src, y0, y1, v, e, where in prior:
        o = period_stats(gl, y0, y1)
        p = period_stats(rgg, y0, y1)
        pr.append(dict(source=src, first_year=y0, last_year=y1, prior_rate_gt=v,
                       prior_rate_gt_err=e, where=where, ours_rate_gt=o["rate"],
                       ours_rate_gt_err=o["rate_err"], glambie_rate_gt=p["rate"],
                       glambie_rate_gt_err=p["rate_err"],
                       diff_ours_minus_prior=o["rate"] - v,
                       z=(o["rate"] - v) / np.hypot(o["rate_err"], e)))
    pd.DataFrame(pr).to_csv(os.path.join(od_v, "prior_estimates.csv"), index=False)

    ref_sum = {lab: {"gt": period_stats(rgg, a_, b_, "gt"), "mwe": period_stats(rgg, a_, b_, "mwe")}
               for lab, (a_, b_) in {"2000_2023": PERIOD, "2000_2011": (2000, 2011),
                                     "2012_2023": (2012, 2023)}.items()}
    summary = {"ours": glob_sum, "glambie_published": ref_sum,
               "global_vs_glambie_annual": gst,
               "n_submissions": int(len(inv)),
               "n_submissions_by_source": inv.source.value_counts().to_dict(),
               "n_used_in_consensus": int(inv.used_in_consensus.sum()),
               "conventions": {"density_kg_m3": "850 +- 60", "gt_per_mm_sle": GT_PER_MM,
                               "errors": "1 sigma",
                               "period_errors": "annual errors combined in quadrature (independent years); *_correlated = linear sum"}}
    with open(os.path.join(a.out, "reconciliation", "summary_global.json"), "w") as f:
        json.dump(summary, f, indent=1, default=float)
    print(json.dumps({"ours": glob_sum["2000_2023"]["gt"], "ref": ref_sum["2000_2023"]["gt"],
                      "global_vs_ref": gst}, indent=1, default=float))


if __name__ == "__main__":
    main()
