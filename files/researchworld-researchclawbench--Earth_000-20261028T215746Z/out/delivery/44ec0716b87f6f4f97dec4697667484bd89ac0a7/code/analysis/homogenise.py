"""Read and homogenise the GlaMBIE input submissions.

Every submission is converted to specific mass change (m w.e.) and total mass
change (Gt) on its own native periods, then resampled to annual values on the
regional hydrological year (or kept as a single multi-year trend when the
submission has no sub-period resolution).
"""
import glob
import os
import re

import numpy as np
import pandas as pd

RHO = 850.0       # kg m-3, volume-to-mass conversion density (Huss 2013)
RHO_ERR = 60.0    # kg m-3
SOURCES = ["glaciological", "demdiff", "altimetry", "gravimetry", "combined"]
# data groups of the consensus; hybrid ("combined") submissions are kept apart
GROUP_OF = {"glaciological": "demdiff_and_glaciological",
            "demdiff": "demdiff_and_glaciological",
            "altimetry": "altimetry", "gravimetry": "gravimetry",
            "combined": "combined"}


def region_list(data_dir):
    d = sorted(os.listdir(os.path.join(data_dir, "input")))
    d = [x for x in d if re.match(r"^\d+_", x)]
    return sorted(d, key=lambda s: int(s.split("_")[0]))


def hydro_start(region):
    """Fractional month offset of the hydrological year (GlaMBIE convention):
    1 Oct in the northern hemisphere, 1 Apr in the southern, 1 Jan in the
    low latitudes."""
    n = int(region.split("_")[0])
    if n == 16:
        return 0.0
    if n in (17, 18, 19):
        return 0.25
    return 0.75


def hydro_bounds(y, h0):
    """Hydrological year labelled y: 1 Oct (y-1) - 1 Oct y in the north,
    1 Apr y - 1 Apr (y+1) in the south, calendar year y in the low latitudes
    (the labelling of the GlaMBIE result files)."""
    if h0 >= 0.5:
        return y - 1 + h0, y + h0
    return y + h0, y + 1 + h0


def load_area(data_dir, region):
    """Time-varying glacier area (km2) of a region, from the GlaMBIE result
    files (RGI 6.0 area with regional area-change rates). Returns a function
    of decimal year (linear interpolation / extrapolation)."""
    rows = []
    for sub in ("hydrological_years", "calendar_years"):
        f = os.path.join(data_dir, "results", sub, region + ".csv")
        r = pd.read_csv(f)
        rows.append(pd.DataFrame({"t": 0.5 * (r.start_dates + r.end_dates),
                                  "a": r.glacier_area}))
    a = pd.concat(rows).groupby("t").a.mean().sort_index()
    t, v = a.index.values, a.values
    slope = np.polyfit(t, v, 1)[0]

    def area(x):
        x = np.asarray(x, float)
        y = np.interp(x, t, v)
        y = np.where(x < t[0], v[0] + slope * (x - t[0]), y)
        y = np.where(x > t[-1], v[-1] + slope * (x - t[-1]), y)
        return y
    return area


def parse_name(region, path):
    name = os.path.basename(path)[:-4]
    for s in SOURCES:
        tag = "_" + s + "_"
        if tag in name:
            rest = name.split(tag, 1)[1]
            return s, rest
    raise ValueError(path)


def to_mwe_gt(df, area):
    """Add mwe, mwe_err, gt, gt_err columns for each native period."""
    unit = df.unit.str.lower().iloc[0]
    amid = area(0.5 * (df.start_dates + df.end_dates))
    if unit == "m":     # elevation change -> m w.e. with density uncertainty
        mwe = df.changes * RHO / 1000.0
        err = np.sqrt((df.errors * RHO / 1000.0) ** 2 +
                      (df.changes * RHO_ERR / 1000.0) ** 2)
        gt, gte = mwe * amid / 1000.0, err * amid / 1000.0
    elif unit == "mwe":
        mwe, err = df.changes, df.errors
        gt, gte = mwe * amid / 1000.0, err * amid / 1000.0
    elif unit == "gt":
        gt, gte = df.changes, df.errors
        mwe, err = gt * 1000.0 / amid, gte * 1000.0 / amid
    else:
        raise ValueError(unit)
    out = df[["start_dates", "end_dates"]].copy()
    out["mwe"], out["mwe_err"], out["gt"], out["gt_err"] = mwe, err, gt, gte
    return out


def interval_change(native, t0, t1, col="mwe"):
    """Change over [t0, t1] from a contiguous series of native increments,
    with linear interpolation inside native periods. Returns (value, error,
    covered) where covered says the series spans the interval.

    Error model: for sub-annual (monthly) series the stated errors are
    treated as epoch (anomaly) noise, so the error of a change between two
    epochs is the rms of the increment errors in the interval and does not
    accumulate with the number of months. For annual or longer native
    periods the errors are independent per period and add in quadrature."""
    s, e = native.start_dates.values, native.end_dates.values
    if t0 < s[0] - 1e-6 or t1 > e[-1] + 1e-6:
        return np.nan, np.nan, False
    ov = np.clip(np.minimum(e, t1) - np.maximum(s, t0), 0, None)
    frac = ov / (e - s)
    v = native[col].values
    er = native[col + "_err"].values
    m = frac > 0
    if np.isnan(v[m]).any():
        return np.nan, np.nan, False
    val = np.sum(frac[m] * v[m])
    dt = np.median(e - s)
    if dt < 0.9:
        err = np.sqrt(np.mean(er[m] ** 2)) if m.any() else np.nan
    else:
        err = np.sqrt(np.sum((frac[m] * er[m]) ** 2))
    return val, err, True


def load_inputs(data_dir):
    """Return list of dicts, one per submission, with native series in
    m w.e./Gt and annual hydrological-year series where resolvable."""
    subs = []
    for region in region_list(data_dir):
        area = load_area(data_dir, region)
        h0 = hydro_start(region)
        for f in sorted(glob.glob(os.path.join(data_dir, "input", region,
                                               "*.csv"))):
            src, label = parse_name(region, f)
            raw = pd.read_csv(f)
            nat = to_mwe_gt(raw, area)
            dt = (nat.end_dates - nat.start_dates).median()
            resolved = len(nat) > 1 and dt <= 1.01
            ann = []
            if resolved:
                for y in range(1990, 2025):
                    a, b = hydro_bounds(y, h0)
                    v, e, ok = interval_change(nat, a, b)
                    if ok:
                        ann.append((y, a, b, v, e))
            ann = pd.DataFrame(ann, columns=["year", "start", "end", "mwe", "mwe_err"])
            if len(ann):
                ar = area(0.5 * (ann.start + ann.end))
                ann["gt"], ann["gt_err"] = ann.mwe * ar / 1000, ann.mwe_err * ar / 1000
            t0, t1 = nat.start_dates.iloc[0], nat.end_dates.iloc[-1]
            tot, tot_e, _ = interval_change(nat, t0, t1)
            if not resolved:
                tot_e = np.sqrt(np.sum(nat.mwe_err ** 2))
            subs.append(dict(region=region, source=src, group=GROUP_OF[src],
                             label=label, file=os.path.relpath(f, data_dir),
                             unit=raw.unit.iloc[0], n_rows=len(raw),
                             native_dt=dt, resolved=resolved, t0=t0, t1=t1,
                             trend_mwe=tot / (t1 - t0),
                             trend_mwe_err=tot_e / (t1 - t0),
                             native=nat, annual=ann))
    return subs
