"""
Core library for reconciling GlaMBIE input datasets into regional and global
glacier mass-change time series (2000-2023).

Pipeline (per region):
  1. Homogenise units   : elevation change [m] -> m w.e. (density 850 +/- 60 kg m-3);
                          Gt -> m w.e. using the (time-varying) regional glacier area.
  2. Temporal homogenisation on a monthly grid:
       * "annual-resolution" datasets (interval <= 1 yr) -> cumulative series ->
         hydrological-year (HY) changes;
       * "trend" datasets (interval > 1 yr) -> temporally downscaled to annual
         resolution by adding an annual-variability reference (anomalies) and
         re-calibrating each period so that the period total is preserved exactly.
  3. Data-group solutions (altimetry, gravimetry, DEM differencing + glaciological):
       arithmetic mean of the datasets available in each year.
  4. Regional consensus  : mean of the data-group solutions (equal weights by default).
  5. Conversion to Gt and from hydrological to calendar years (seasonal correction
     derived from the monthly glaciological sine-wave series of the region).
  6. Global aggregate    : sum of 19 regions, errors added in quadrature.
Hybrid ("combined") estimates are excluded from the consensus and kept for validation.
"""
import os, glob
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(ROOT, 'data/glambie/input')
RES = os.path.join(ROOT, 'data/glambie/results')

DENSITY, DENSITY_ERR = 0.85, 0.06            # volume-to-mass conversion (Huss 2013)
T0, T1 = 1990.0, 2027.0                      # monthly grid limits
NM = int(round((T1 - T0) * 12))
TGRID = T0 + np.arange(NM + 1) / 12.0        # month boundaries

# Regions where gravimetry is considered reliable (large glacier area and no dominant
# leakage from ice sheets (RGI 5, 19) or terrestrial hydrology / groundwater (RGI 2, 13-15)).
GRAV_REGIONS = {1, 3, 4, 6, 7, 9, 17}
GROUPS = ['altimetry', 'gravimetry', 'demdiff_glac']
REGION_NAMES = {1: 'Alaska', 2: 'Western Canada & US', 3: 'Arctic Canada North', 4: 'Arctic Canada South',
                5: 'Greenland Periphery', 6: 'Iceland', 7: 'Svalbard & Jan Mayen', 8: 'Scandinavia',
                9: 'Russian Arctic', 10: 'North Asia', 11: 'Central Europe', 12: 'Caucasus & Middle East',
                13: 'Central Asia', 14: 'South Asia West', 15: 'South Asia East', 16: 'Low Latitudes',
                17: 'Southern Andes', 18: 'New Zealand', 19: 'Antarctic & Subantarctic'}


def m_idx(t):
    return int(round((t - T0) * 12))


def hy_offset(rid):
    """Start of the hydrological year (fraction of calendar year)."""
    if rid == 16:
        return 0.0
    if rid in (17, 18, 19):
        return 0.25
    return 0.75


def region_dirs():
    out = {}
    for d in sorted(glob.glob(os.path.join(IN, '*_*'))):
        if os.path.isdir(d):
            rid = int(os.path.basename(d).split('_')[0])
            out[rid] = d
    return out


def load_area(rid):
    """Regional glacier area per hydrological year (RGI6 + area-change rates, as used by GlaMBIE).
    Returns function area(t) [km2] with linear interpolation / extrapolation."""
    d = region_dirs()[rid]
    f = os.path.join(RES, 'hydrological_years', os.path.basename(d) + '.csv')
    h = pd.read_csv(f)
    tm = (h.start_dates.values + h.end_dates.values) / 2
    a = h.glacier_area.values
    p = np.polyfit(tm, a, 1)

    def area(t):
        t = np.asarray(t, dtype=float)
        return np.where((t >= tm[0]) & (t <= tm[-1]), np.interp(t, tm, a), np.polyval(p, t))
    return area


def load_region_datasets(rid):
    """Load and unit-homogenise all datasets of a region (values in m w.e.)."""
    d = region_dirs()[rid]
    rname = os.path.basename(d).split('_', 1)[1]
    area = load_area(rid)
    out = []
    for f in sorted(glob.glob(os.path.join(d, '*.csv'))):
        base = os.path.basename(f)[:-4]
        rest = base[len(rname) + 1:]
        method = rest.split('_')[0]
        name = rest[len(method) + 1:]
        df = pd.read_csv(f)
        unit = str(df.unit.iloc[0]).lower()
        df = df[np.isfinite(df.changes)].copy()
        df['errors'] = df.errors.abs()
        if df.errors.isna().all():
            df['errors'] = 0.0
        df['errors'] = df.errors.fillna(df.errors.median())
        x, e = df.changes.values.astype(float), df.errors.values.astype(float)
        if unit == 'm':      # elevation change -> m w.e.
            e = np.sqrt((DENSITY * e) ** 2 + (DENSITY_ERR * x) ** 2)
            x = DENSITY * x
        elif unit == 'gt':   # Gt -> m w.e.
            A = area((df.start_dates.values + df.end_dates.values) / 2)
            x = x / A * 1000.0
            e = e / A * 1000.0
        elif unit != 'mwe':
            raise ValueError(unit)
        s, t = df.start_dates.values, df.end_dates.values
        dt = t - s
        kind = 'annual' if np.median(dt) <= 1.0 + 1e-3 else 'trend'
        group = {'glaciological': 'demdiff_glac', 'demdiff': 'demdiff_glac', 'altimetry': 'altimetry',
                 'gravimetry': 'gravimetry', 'combined': 'hybrid'}[method]
        out.append(dict(raw=df.changes.values.astype(float), rid=rid, method=method, group=group, name=name, unit=unit, kind=kind,
                        start=s, end=t, x=x, e=e, author=df.author.iloc[0]))
    return out


def hy_starts(rid, first=1998, last=2025):
    return np.arange(first, last + 1) + hy_offset(rid)


EXT_MODE = 'mean'   # offset used for extrapolating DEM series: nearest period or record mean
HR_ERR = 'rms'   # error model for sub-annual series: 'rms' or 'epoch' (see report)


def annual_from_highres(ds, starts):
    """HY changes (m w.e.) and errors from a dataset with <=1-yr resolution."""
    s, t, x, e = ds['start'], ds['end'], ds['x'], ds['e']
    tb = np.r_[s[0], t]
    # handle (rare) gaps: build cumulative on the union of boundaries
    cum = np.r_[0.0, np.cumsum(x)]
    tb_c = tb.copy()
    # if gaps exist (start != previous end), interpolation bridges them linearly
    if not np.allclose(s[1:], t[:-1], atol=1e-3):
        tb_c = np.r_[s[0], t]
    vals, errs = np.full(len(starts), np.nan), np.full(len(starts), np.nan)
    cover = np.full(len(starts), np.nan)
    # monthly error representation: each month inherits the error of the interval covering it
    for i, a in enumerate(starts):
        b = a + 1.0
        if a < tb_c[0] - 1e-3 or b > tb_c[-1] + 1e-3:
            continue
        vals[i] = np.interp(b, tb_c, cum) - np.interp(a, tb_c, cum)
        # error: RMS of interval errors weighted by temporal overlap with the year
        ov = np.clip(np.minimum(t, b) - np.maximum(s, a), 0, None)
        frac = ov / np.maximum(t - s, 1e-9)        # fraction of each interval inside the year
        w = ov / ov.sum()
        cover[i] = ov.sum()
        # monthly intervals: RMS; annual intervals: overlap-weighted quadrature
        long = (t - s) > 0.5
        if long.any() and (~long).sum() == 0:
            errs[i] = np.sqrt(np.sum((frac * e) ** 2))
        else:
            errs[i] = np.sqrt(np.sum(w * e ** 2))
            if HR_ERR == 'epoch':
                # sub-annual errors treated as independent epoch noise: annual change error
                # = sqrt(2) * RMS / sqrt(number of sub-annual epochs in the year)
                nep = max(int(round(ov.sum() / np.median(t - s))), 1)
                errs[i] *= np.sqrt(2.0 / nep)
    # --- detect data gaps filled by linear interpolation (>=3 identical consecutive monthly
    #     changes, e.g. GRACE/GRACE-FO gap 2017-2018) and flag affected years
    gapflag = (cover < 0.9) & (np.median(t - s) < 0.1)
    if np.median(t - s) < 0.1 and ds['method'] != 'glaciological' and len(x) > 3:
        same = np.r_[False, np.isclose(ds['raw'][1:], ds['raw'][:-1], rtol=1e-6, atol=1e-9)]
        filled = np.zeros(len(x), bool)
        run = 0
        for k in range(len(x)):
            run = run + 1 if same[k] else 0
            if run >= 2:                       # 3 identical values in a row
                filled[k - run:k + 1] = True
        if filled.any():
            for i, a in enumerate(starts):
                inside = (s >= a - 1e-3) & (t <= a + 1 + 1e-3) & filled
                if inside.sum() >= 2:
                    gapflag[i] = True
    ds['gapflag'] = gapflag
    return vals, errs


def fill_gaps(ds, ref, ref_err):
    """Re-distribute changes over blocks of gap-affected years: the block total (constrained by
    the observed epochs bracketing the gap) is kept, the split between years follows the
    annual-variability reference."""
    g = ds.get('gapflag')
    if g is None or not g.any():
        return
    v, e = ds['hy'], ds['hy_err']
    idx = np.where(g & np.isfinite(v))[0]
    blocks, cur = [], []
    for i in idx:
        if cur and i != cur[-1] + 1:
            blocks.append(cur); cur = []
        cur.append(i)
    if cur:
        blocks.append(cur)
    for b in blocks:
        b = np.array(b)
        T = v[b].sum()
        c = (T - ref[b].sum()) / len(b)
        v[b] = ref[b] + c
        e[b] = np.sqrt(e[b] ** 2 + ref_err[b] ** 2)


def monthly_ref(ref_annual, starts):
    """Spread annual reference anomalies (per HY) uniformly over months of the grid."""
    r = np.zeros(NM)
    has = np.zeros(NM, bool)
    for a, v in zip(starts, ref_annual):
        if np.isfinite(v):
            i0 = m_idx(a)
            if 0 <= i0 and i0 + 12 <= NM:
                r[i0:i0 + 12] = v / 12.0
                has[i0:i0 + 12] = True
    return r, has


def calibrate_trend(ds, ref_m, starts, extend=False, min_months=6):
    """Temporal downscaling of a trend dataset with an annual-variability reference.

    Within each period k the monthly series is ref_m + c_k, with c_k chosen so that the
    period sum equals the observed change T_k exactly. Returns HY values/errors and a
    flag (0 = observed period, >0 = years of extrapolation)."""
    s, t, x, e = ds['start'], ds['end'], ds['x'], ds['e']
    mon = np.full(NM, np.nan)
    rate_err = np.full(NM, np.nan)        # m w.e. per year
    for sk, tk, xk, ek in zip(s, t, x, e):
        i0, i1 = m_idx(sk), m_idx(tk)
        n = i1 - i0
        if n <= 0:
            continue
        ck = (xk - ref_m[i0:i1].sum()) / n
        mon[i0:i1] = ref_m[i0:i1] + ck
        rate_err[i0:i1] = ek / (n / 12.0)
    covered = np.isfinite(mon)
    i_first, i_last = np.where(covered)[0][[0, -1]]
    L = (i_last - i_first + 1) / 12.0
    # mean offset over the whole record (for extension / filling)
    c_all = np.nansum(mon[covered] - ref_m[covered]) / covered.sum()
    off_m = mon - ref_m
    c_first, c_last = off_m[i_first], off_m[i_last]
    rerr_all = np.sqrt(np.nanmean(rate_err[covered] ** 2))
    vals = np.full(len(starts), np.nan)
    errs = np.full(len(starts), np.nan)
    extrap = np.full(len(starts), np.nan)
    for i, a in enumerate(starts):
        i0 = m_idx(a)
        if i0 < 0 or i0 + 12 > NM:
            continue
        cov = covered[i0:i0 + 12]
        nc = cov.sum()
        mid = i0 + 6
        c_near = c_all if EXT_MODE == 'mean' else (c_first if mid < i_first else c_last)
        if nc >= min_months:
            seg = np.where(cov, mon[i0:i0 + 12], ref_m[i0:i0 + 12] + c_near)
            vals[i] = seg.sum()
            errs[i] = np.sqrt(np.nanmean(np.where(cov, rate_err[i0:i0 + 12], rerr_all) ** 2))
            extrap[i] = 0.0
        elif extend:
            vals[i] = (ref_m[i0:i0 + 12] + c_near).sum()
            # distance (yr) from the calibration window
            dist = (i_first - mid) / 12.0 if mid < i_first else (mid - i_last) / 12.0
            dist = max(dist, 0.5)
            errs[i] = rerr_all * np.sqrt(1.0 + dist / L)
            extrap[i] = dist
    return vals, errs, extrap


def combine_mean(vals, errs):
    """Arithmetic mean over datasets (axis 0) with error = propagated (independent) + spread."""
    V = np.asarray(vals, float); E = np.asarray(errs, float)
    ok = np.isfinite(V) & np.isfinite(E)
    n = ok.sum(0)
    with np.errstate(invalid='ignore', divide='ignore'):
        mean = np.where(n > 0, np.nansum(np.where(ok, V, 0), 0) / n, np.nan)
        prop = np.sqrt(np.nansum(np.where(ok, E ** 2, 0), 0)) / n
        dev = np.where(ok, V - mean, 0)
        sd = np.sqrt(np.where(n > 1, (dev ** 2).sum(0) / np.maximum(n - 1, 1), 0))
        err = np.sqrt(prop ** 2 + sd ** 2 / np.maximum(n, 1))
    err = np.where(n > 0, err, np.nan)
    return mean, err, n


def combine_ivw(vals, errs):
    V = np.asarray(vals, float); E = np.asarray(errs, float)
    ok = np.isfinite(V) & np.isfinite(E) & (E > 0)
    w = np.where(ok, 1 / np.where(ok, E, 1) ** 2, 0)
    n = ok.sum(0)
    with np.errstate(invalid='ignore', divide='ignore'):
        mean = np.where(n > 0, (w * np.where(ok, V, 0)).sum(0) / w.sum(0), np.nan)
        err = np.where(n > 0, 1 / np.sqrt(w.sum(0)), np.nan)
    return mean, err, n


def process_region(rid, opts=None):
    """Full per-region pipeline. Returns dict with per-dataset, per-group and combined HY series."""
    o = dict(ext_mode='mean', hr_err='rms', group_weighting='mean', use_hybrid=False, grav_all=False, density=None,
             drop_group=None, drop_dataset=None, within_weighting='mean')
    if opts:
        o.update(opts)
    global DENSITY, HR_ERR, EXT_MODE
    dens0 = DENSITY
    HR_ERR = o['hr_err']; EXT_MODE = o['ext_mode']
    if o['density']:
        DENSITY = o['density']
    try:
        dsets = load_region_datasets(rid)
    finally:
        DENSITY = dens0
    starts = hy_starts(rid)
    ny = len(starts)
    area = load_area(rid)
    A = area(starts + 0.5)

    # --- annual-resolution series for every high-res dataset
    for ds in dsets:
        if ds['kind'] == 'annual':
            ds['hy'], ds['hy_err'] = annual_from_highres(ds, starts)
    # --- variability references
    def anomalies(sel, ref_years=None):
        an = []; ae = []
        for ds in sel:
            v = ds['hy'].copy()
            if np.isfinite(v).sum() < 5:
                continue
            if ref_years is not None:
                m = np.isin(np.round(starts, 2), np.round(ref_years, 2)) & np.isfinite(v)
                mu = np.nanmean(v[m]) if m.sum() >= 5 else np.nanmean(v)
            else:
                mu = np.nanmean(v)
            an.append(v - mu); ae.append(np.where(np.isfinite(v), ds['hy_err'], np.nan))
        if not an:
            return None, None
        an = np.array(an); ae = np.array(ae)
        with np.errstate(all='ignore'):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                nn = np.isfinite(an).sum(0)
                err = np.sqrt(np.nansum(ae ** 2, 0)) / np.maximum(nn, 1)
                err = np.where(nn > 0, err, np.nan)
                return np.nanmean(an, 0), err
    glac = [d for d in dsets if d['method'] == 'glaciological' and d['kind'] == 'annual']
    glac_ref, glac_err = anomalies(glac, ref_years=np.arange(2000, 2020) + hy_offset(rid))
    if glac_ref is None:
        glac_ref = np.full(ny, np.nan); glac_err = np.full(ny, np.nan)
    glac_err = np.where(np.isfinite(glac_err), glac_err, np.nanmean(glac_err) if np.isfinite(glac_err).any() else 0.0)
    glac_avail = np.isfinite(glac_ref)
    if not glac_avail.any():
        glac_avail[:] = True
    glac_ref = np.nan_to_num(glac_ref)
    # repair interpolated data gaps in non-glaciological high-resolution series
    for ds in dsets:
        if ds['kind'] == 'annual' and ds['method'] != 'glaciological':
            fill_gaps(ds, glac_ref, glac_err)
    group_ref = {}
    for g in ['altimetry', 'gravimetry']:
        sel = [d for d in dsets if d['group'] == g and d['kind'] == 'annual']
        group_ref[g] = anomalies(sel)
    glac_m, _ = monthly_ref(glac_ref, starts)

    # --- downscale trend datasets
    for ds in dsets:
        if ds['kind'] != 'trend':
            continue
        ref_m = glac_m
        ref_err = glac_err.copy()
        ds['var_source'] = 'glaciological'
        gr, gre = group_ref.get(ds['group'], (None, None))
        if gr is not None:
            gm, has = monthly_ref(gr, starts)
            i0, i1 = m_idx(ds['start'].min()), m_idx(ds['end'].max())
            if has[i0:i1].mean() >= 0.8:
                ref_m = np.where(has, gm, glac_m)
                ref_err = np.where(np.isfinite(gr), gre, glac_err)
                ds['var_source'] = ds['group']
        extend = ds['group'] == 'demdiff_glac'
        ds['hy'], ds['hy_err'], ds['extrap'] = calibrate_trend(ds, ref_m, starts, extend=extend)
        ds['hy_err'] = np.sqrt(ds['hy_err'] ** 2 + np.nan_to_num(ref_err) ** 2)   # + variability-reference error
        if extend:
            bad = ~glac_avail & (ds['extrap'] > 0)
            ds['hy'][bad] = np.nan; ds['hy_err'][bad] = np.nan; ds['extrap'][bad] = np.nan

    # --- group solutions
    groups = {}
    for g in GROUPS:
        if o['drop_group'] == g:
            continue
        if g == 'gravimetry' and not (o['grav_all'] or rid in GRAV_REGIONS):
            continue
        if g == 'demdiff_glac':
            sel = [d for d in dsets if d['method'] == 'demdiff']    # glaciological -> variability only
        else:
            sel = [d for d in dsets if d['group'] == g]
        if o['drop_dataset']:
            sel = [d for d in sel if d['name'] != o['drop_dataset']]
        if not sel:
            continue
        V = np.array([d['hy'] for d in sel]); E = np.array([d['hy_err'] for d in sel])
        if g == 'demdiff_glac':
            # use extrapolated values only where no dataset has observational coverage
            X = np.array([d.get('extrap', np.zeros(ny)) for d in sel])
            Xn = np.nan_to_num(X, nan=99)
            observed = Xn == 0
            anyobs = observed.any(0)
            # where no observation: keep only the least-extrapolated datasets (within 1 yr)
            nearest = Xn <= (Xn.min(0)[None, :] + 1.0)
            keep = np.where(anyobs[None, :], observed, nearest)
            V = np.where(keep, V, np.nan)
            E = np.where(keep, E, np.nan)
        if o['within_weighting'] == 'ivw':
            m, e, n = combine_ivw(V, E)
        else:
            m, e, n = combine_mean(V, E)
        groups[g] = dict(mwe=m, err=e, n=n, members=[d['name'] for d in sel])
    if o['use_hybrid']:
        sel = [d for d in dsets if d['group'] == 'hybrid' and d['kind'] == 'annual']
        if sel:
            m, e, n = combine_mean(np.array([d['hy'] for d in sel]), np.array([d['hy_err'] for d in sel]))
            groups['hybrid'] = dict(mwe=m, err=e, n=n, members=[d['name'] for d in sel])

    GV = np.array([groups[g]['mwe'] for g in groups]).reshape(-1, ny)
    GE = np.array([groups[g]['err'] for g in groups]).reshape(-1, ny)
    if o['group_weighting'] == 'ivw':
        cm, ce, cn = combine_ivw(GV, GE)
    else:
        ok = np.isfinite(GV) & np.isfinite(GE)
        cn = ok.sum(0)
        with np.errstate(all='ignore'):
            cm = np.where(cn > 0, np.nansum(np.where(ok, GV, 0), 0) / cn, np.nan)
            ce = np.where(cn > 0, np.sqrt(np.nansum(np.where(ok, GE ** 2, 0), 0)) / cn, np.nan)
    with np.errstate(all='ignore'):
        ok = np.isfinite(GV)
        spread = np.array([np.std(GV[ok[:, j], j], ddof=1) if ok[:, j].sum() > 1 else np.nan for j in range(ny)])
    return dict(rid=rid, starts=starts, area=A, datasets=dsets, groups=groups,
                mwe=cm, err=ce, ngroups=cn, spread=spread, glac_ref=glac_ref)


def sinewave_sums(rid):
    """HY and calendar-year sums of the monthly glaciological sine-wave series (m w.e.)."""
    d = region_dirs()[rid]
    f = glob.glob(os.path.join(d, '*SineWave*'))
    if not f:
        return None
    z = pd.read_csv(f[0])
    tb = np.r_[z.start_dates.values[0], z.end_dates.values]
    cum = np.r_[0, np.cumsum(z.changes.values)]

    def S(a):
        if a < tb[0] - 1e-3 or a + 1 > tb[-1] + 1e-3:
            return np.nan
        return np.interp(a + 1, tb, cum) - np.interp(a, tb, cum)
    return S


def to_calendar(res, years=np.arange(2000, 2024)):
    """Convert HY series to calendar years: time-weighted HY combination plus a
    year-specific seasonal correction from the monthly sine-wave glaciological series."""
    rid = res['rid']; off = hy_offset(rid)
    starts = np.round(res['starts'], 3)
    H = dict(zip(starts, res['mwe'])); HE = dict(zip(starts, res['err']))
    S = sinewave_sums(rid)
    area = load_area(rid)
    rows = []
    for Y in years:
        if off == 0:
            v, e = H.get(round(float(Y), 3), np.nan), HE.get(round(float(Y), 3), np.nan)
        else:
            a, b = round(Y - (1 - off), 3), round(Y + off, 3)
            wa = 1 - off if off == 0.75 else off
            wa = {0.75: 0.75, 0.25: 0.25}[off]
            ha, hb = H.get(a, np.nan), H.get(b, np.nan)
            ea, eb = HE.get(a, np.nan), HE.get(b, np.nan)
            if S is not None:
                sa, sb, cY = S(a), S(b), S(float(Y))
                if not np.isfinite(hb):          # last year: assume persistence of residual
                    hb, eb = sb + (ha - sa), ea
                if not np.isfinite(ha):
                    ha, ea = sa + (hb - sb), eb
                v = cY + wa * (ha - sa) + (1 - wa) * (hb - sb)
            else:
                if not np.isfinite(hb):
                    hb, eb = ha, ea
                v = wa * ha + (1 - wa) * hb
            e = wa * ea + (1 - wa) * eb
        Ar = float(area(Y + 0.5))
        rows.append(dict(start_dates=float(Y), end_dates=float(Y + 1), glacier_area=Ar, region_id=rid,
                         region=REGION_NAMES[rid], mwe=v, mwe_err=e, gt=v * Ar / 1000, gt_err=e * Ar / 1000))
    return pd.DataFrame(rows)


def run_all(opts=None, regions=range(1, 20)):
    res = {rid: process_region(rid, opts) for rid in regions}
    cal = {rid: to_calendar(r) for rid, r in res.items()}
    allc = pd.concat(cal.values())
    g = allc.groupby('start_dates').agg(glacier_area=('glacier_area', 'sum'), gt=('gt', 'sum'),
                                        gt_err=('gt_err', lambda x: np.sqrt((x ** 2).sum())))
    g['mwe'] = g['gt'] / g['glacier_area'] * 1000
    g['mwe_err'] = g['gt_err'] / g['glacier_area'] * 1000
    g = g.reset_index()
    g['end_dates'] = g.start_dates + 1
    return res, cal, g
