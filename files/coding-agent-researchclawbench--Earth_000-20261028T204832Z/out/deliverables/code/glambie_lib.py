"""
Independent re-implementation of a GlaMBIE-style reconciliation of regional
glacier mass-change estimates.

Pipeline per region
  1. read every input solution and classify it into a data group
       DG   : DEM differencing (long-term level) + glaciological (annual variability)
       ALT  : altimetry
       GRAV : gravimetry
       HYB  : hybrid / combined solutions  (held out, used only for validation)
  2. homogenise units to specific mass change (m w.e.) on the regional,
     time-varying glacier area (density 850 +/- 60 kg m-3 for volume data)
  3. homogenise temporal resolution onto the regional hydrological-year grid:
       sub-annual -> annual sums (gaps -> multi-year period records)
       annual     -> kept
       multi-annual -> "period records" downscaled with annual variability
  4. within each group, separate annual variability a_g(y) (additive two-way
     fixed-effects fit of all annually resolved solutions) from the long-term
     level (offsets c_k of each solution / period relative to a_g)
  5. combine groups with a second fixed-effects step (consensus C(y) plus a
     group offset o_g; equal weights by default)
  6. propagate random (year-to-year independent) and systematic (temporally
     correlated) uncertainty components separately.
"""
import glob
import os
import numpy as np
import pandas as pd

DATA = '/work/data/glambie'
RHO = 0.850          # density conversion factor (t m-3 -> m w.e. per m)
SIG_RHO = 0.060
GRACE_GAP = (2017.45, 2018.40)   # GRACE / GRACE-FO gap (data inside are interpolated)
TOL = 1e-3
# representativeness error of glaciological annual variability (m w.e. per year), calibrated
# by leave-one-pentad-out cross-validation against DEM differencing (calibrate_tau.py)
DG_TAU = 0.45

REGIONS = ['1_alaska', '2_western_canada_us', '3_arctic_canada_north', '4_arctic_canada_south',
           '5_greenland_periphery', '6_iceland', '7_svalbard', '8_scandinavia', '9_russian_arctic',
           '10_north_asia', '11_central_europe', '12_caucasus_middle_east', '13_central_asia',
           '14_south_asia_west', '15_south_asia_east', '16_low_latitudes', '17_southern_andes',
           '18_new_zealand', '19_antarctic_and_subantarctic']
SHORT = dict(zip(REGIONS, ['ALA', 'WNA', 'ACN', 'ACS', 'GRL', 'ISL', 'SJM', 'SCA', 'RUA', 'ASN',
                           'CEU', 'CAU', 'ASC', 'ASW', 'ASE', 'TRP', 'SAN', 'NZL', 'ANT']))
GROUPS = ['DG', 'ALT', 'GRAV']
SOURCE2GROUP = {'glaciological': 'DG', 'demdiff': 'DG', 'altimetry': 'ALT',
                'gravimetry': 'GRAV', 'combined': 'HYB'}


def hydro_start(region):
    """Start (fractional year) of the hydrological year used for a region."""
    n = int(region.split('_')[0])
    if n == 16:
        return 0.0      # low latitudes: calendar year
    if n >= 17:
        return 0.25     # southern hemisphere: 1 April
    return 0.75         # northern hemisphere: 1 October


def year_grid(region, first=2000, last=2024):
    """Start dates of hydrological years. NH: 1999.75 ... ; SH: 2000.25 ... ; TRP: 2000.0 ...
    One extra year beyond 2023 is kept (only used for calendar-year conversion)."""
    h = hydro_start(region)
    if h == 0.0:
        starts = np.arange(first, last) + h
    else:
        starts = np.arange(first - 1, last) + h
    return starts


def gravity_snr(region):
    """Signal-to-noise ratio of the gravimetric solutions: |mean| / std of their linear
    mass-change rates over the common GRACE period 2003-2017.4."""
    tr = []
    for ds in read_region_inputs(region):
        if ds['source'] != 'gravimetry':
            continue
        d = ds['data'].dropna(subset=['changes'])
        if len(d) == 1:
            tr.append(d.changes.iloc[0] / (d.end_dates.iloc[0] - d.start_dates.iloc[0]))
            continue
        dd = d[(d.start_dates >= 2002.9) & (d.end_dates <= 2017.4)]
        if len(dd) > 12:
            tr.append(dd.changes.sum() / (dd.end_dates.max() - dd.start_dates.min()))
    tr = np.array(tr)
    if len(tr) < 2:
        return np.nan, tr
    return abs(tr.mean()) / tr.std(ddof=1), tr


def gravimetry_excluded(region, area_km2, snr_min=2.0, area_min=5000.0):
    """Objective rule: gravimetry is used only where (i) the glacier area exceeds the
    effective GRACE footprint scale (>= 5000 km2) and (ii) the independent gravimetric
    solutions agree on the regional rate (SNR = |mean| / inter-solution std >= 2)."""
    snr, _ = gravity_snr(region)
    return (area_km2 < area_min) or not (snr >= snr_min)


class Area:
    """Time-varying regional glacier area (km2), linearly interpolated from the
    GlaMBIE auxiliary area series (RGI 6.0 with regional area-change rates)."""

    def __init__(self, region):
        d = pd.read_csv(f'{DATA}/results/hydrological_years/{region}.csv')
        t = 0.5 * (d.start_dates + d.end_dates)
        self.t = t.values
        self.a = d.glacier_area.values
        p = np.polyfit(self.t, self.a, 1)
        self.p = p

    def __call__(self, t):
        return np.polyval(self.p, np.asarray(t, float))


def read_region_inputs(region):
    out = []
    for f in sorted(glob.glob(f'{DATA}/input/{region}/*.csv')):
        name = os.path.basename(f)[:-4]
        rname = '_'.join(region.split('_')[1:])
        source = name[len(rname) + 1:].split('_')[0]
        d = pd.read_csv(f).sort_values('start_dates').reset_index(drop=True)
        d['unit'] = d.unit.str.lower()
        out.append(dict(file=name, source=source, group=SOURCE2GROUP[source],
                        author=d.author.iloc[0], data=d))
    return out


def to_mwe(d, area):
    """Convert changes/errors to m w.e. ; returns arrays (change, error, density_err_part)."""
    unit = d.unit.iloc[0]
    ch = d.changes.values.astype(float)
    er = d.errors.values.astype(float)
    tm = 0.5 * (d.start_dates.values + d.end_dates.values)
    if unit == 'm':
        c = ch * RHO
        e = er * RHO
        e_rho = np.abs(ch) * SIG_RHO
    elif unit == 'gt':
        A = area(tm)
        c = ch * 1000.0 / A
        e = er * 1000.0 / A
        e_rho = np.zeros_like(c)
    elif unit == 'mwe':
        c, e, e_rho = ch, er, np.zeros_like(ch)
    else:
        raise ValueError(unit)
    return c, e, e_rho


def overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def homogenise(ds, region, area, monthly_err='rms'):
    """Return dict with
         annual : pd.Series indexed by hydro-year start -> mwe
         annual_err : random error of annual values
         periods : list of (t0, t1, mwe, err)  (err incl. density, assumed correlated in period)
         resolution : 'subannual' | 'annual' | 'period'
    """
    d = ds['data'].copy()
    starts = year_grid(region)
    c, e, erho = to_mwe(d, area)
    d['c'], d['e'], d['erho'] = c, e, erho
    dur = (d.end_dates - d.start_dates).values
    res_med = np.median(dur)
    annual, annual_err, periods = {}, {}, []
    is_grav = ds['source'] == 'gravimetry'

    if res_med < 0.2:   # sub-annual (monthly) solution
        # fill isolated missing errors (only change known) with median error
        if d.e.isna().any() and d.c.notna().all():
            d.loc[d.e.isna(), 'e'] = np.nanmedian(d.e)
        flagged = []
        for y0 in starts:
            y1 = y0 + 1
            m = (d.start_dates >= y0 - TOL) & (d.end_dates <= y1 + TOL)
            sub = d[m]
            cov = (sub.end_dates - sub.start_dates).sum()
            if cov < 1 - 0.02:
                continue           # partial year at the edges -> not used
            if sub.c.isna().any():
                flagged.append((y0, None))   # true data gap (NaN) -> unusable
                continue
            val = sub.c.sum()
            if monthly_err == 'rms':
                err = np.sqrt(np.mean(sub.e ** 2))
            else:   # independent monthly errors
                err = np.sqrt(np.sum(sub.e ** 2))
            err = np.sqrt(err ** 2 + (sub.erho.sum()) ** 2)
            if is_grav and overlap(y0, y1, *GRACE_GAP) > 0:
                flagged.append((y0, (val, err)))   # interpolated by provider
                continue
            annual[y0] = val
            annual_err[y0] = err
        # contiguous interpolated (gap) years -> one multi-year period record
        blocks, cur = [], []
        for y0, v in flagged:
            if v is None:
                if cur:
                    blocks.append(cur)
                cur = []
                continue
            if cur and abs(y0 - cur[-1][0] - 1) > TOL:
                blocks.append(cur)
                cur = []
            cur.append((y0, v))
        if cur:
            blocks.append(cur)
        for b in blocks:
            t0 = b[0][0]
            t1 = b[-1][0] + 1
            val = sum(v[0] for _, v in b)
            err = np.sqrt(np.mean([v[1] ** 2 for _, v in b]))
            periods.append((t0, t1, val, err))
        resolution = 'subannual'
    else:
        aligned = np.all(np.abs(dur - 1) < 0.02) and \
            np.all(np.abs(((d.start_dates.values - hydro_start(region)) % 1 + 0.5) % 1 - 0.5) < 0.05)
        if aligned and len(d) >= 3:
            for _, r in d.iterrows():
                y0 = starts[np.argmin(np.abs(starts - r.start_dates))]
                if abs(y0 - r.start_dates) < 0.05 and np.isfinite(r.c):
                    annual[y0] = r.c
                    annual_err[y0] = np.sqrt(r.e ** 2 + r.erho ** 2)
            resolution = 'annual'
        else:
            for _, r in d.iterrows():
                if np.isfinite(r.c):
                    periods.append((r.start_dates, r.end_dates, r.c, np.sqrt(r.e ** 2 + r.erho ** 2)))
            resolution = 'period'
    return dict(annual=pd.Series(annual, dtype=float), annual_err=pd.Series(annual_err, dtype=float),
                periods=periods, resolution=resolution)


def period_weights(t0, t1, starts):
    return np.array([overlap(t0, t1, y, y + 1) for y in starts])


# --------------------------------------------------------------------------
# fixed-effects separation  B_i(y) = a(y) + c_i
# --------------------------------------------------------------------------
def fixed_effects(series, weights, errs=None, n_iter=200):
    """series: list of pd.Series on a common index (NaN = missing).
    Returns a (Series), c (array; weighted mean zero), sigma_a (Series)"""
    M = pd.concat(series, axis=1)
    M.columns = range(len(series))
    W = np.asarray(weights, float)
    c = np.zeros(M.shape[1])
    valid = M.notna()
    for _ in range(n_iter):
        R = M - c
        num = (R * W).sum(axis=1, skipna=True)
        den = (valid * W).sum(axis=1)
        a = num / den.replace(0, np.nan)
        c_new = (M.sub(a, axis=0)).mean(axis=0, skipna=True).values
        c_new = np.nan_to_num(c_new)
        c_new -= np.sum(W * c_new) / W.sum()
        if np.max(np.abs(c_new - c)) < 1e-10:
            c = c_new
            break
        c = c_new
    R = M - c
    a = (R * W).sum(axis=1) / (valid * W).sum(axis=1).replace(0, np.nan)
    sig = None
    if errs is not None:
        E = pd.concat(errs, axis=1)
        E.columns = range(len(errs))
        E = E.reindex(M.index)
        num = ((E * W) ** 2).where(valid).sum(axis=1)
        den = (valid * W).sum(axis=1).replace(0, np.nan)
        sig = np.sqrt(num) / den
    return a, c, sig


def wstd(x, w):
    x, w = np.asarray(x, float), np.asarray(w, float)
    if len(x) < 2:
        return 0.0
    m = np.sum(w * x) / np.sum(w)
    v = np.sum(w * (x - m) ** 2) / np.sum(w)
    neff = np.sum(w) ** 2 / np.sum(w ** 2)
    return np.sqrt(v * neff / (neff - 1))


# --------------------------------------------------------------------------
# regional reconciliation
# --------------------------------------------------------------------------
def reconcile_region(region, opts=None):
    opts = dict(dict(group_weights='equal', within_weights='team', monthly_err='rms',
                     use_grav='auto', drop_groups=(), rho=None, glac_level=False,
                     extend='mean', offset_model='piecewise', tau=DG_TAU), **(opts or {}))
    global RHO
    rho_saved = RHO
    if opts['rho'] is not None:
        RHO = opts['rho']
    area = Area(region)
    starts = year_grid(region)
    idx = pd.Index(starts, name='start')
    A = area(starts + 0.5)
    raw = read_region_inputs(region)
    excl_grav = gravimetry_excluded(region, A[0]) if opts['use_grav'] == 'auto' else (not opts['use_grav'])

    # homogenise all solutions
    sols = []
    for ds in raw:
        h = homogenise(ds, region, area, opts['monthly_err'])
        h.update(ds)
        h['annual'] = h['annual'].reindex(idx)
        h['annual_err'] = h['annual_err'].reindex(idx)
        sols.append(h)
    RHO = rho_saved

    # team weights within group: solutions from the same author share one weight
    for g in GROUPS + ['HYB']:
        gs = [s for s in sols if s['group'] == g]
        for s in gs:
            n_same = sum(1 for t in gs if t['author'] == s['author'] and t['source'] == s['source'])
            s['w'] = 1.0 / n_same if opts['within_weights'] == 'team' else 1.0

    # note: groups listed in drop_groups still provide annual variability to the regional
    # reference (Aref) but are removed from the combination (step C)
    active = [g for g in GROUPS if not (g == 'GRAV' and excl_grav)]
    group_sols = {g: [s for s in sols if s['group'] == g] for g in active}
    group_sols = {g: v for g, v in group_sols.items() if len(v) > 0}
    active = list(group_sols)

    # ---- step A: own annual variability per group --------------------------
    own_a, own_sig, own_mask = {}, {}, {}
    for g, gs in group_sols.items():
        var_s = [s for s in gs if s['annual'].notna().sum() >= 3]
        if var_s:
            a, c, sig = fixed_effects([s['annual'] for s in var_s], [s['w'] for s in var_s],
                                      [s['annual_err'] for s in var_s])
            if g == 'DG':
                sig = np.sqrt(sig ** 2 + opts['tau'] ** 2)
            own_a[g], own_sig[g] = a, sig
            own_mask[g] = a.notna()
        else:
            own_a[g] = pd.Series(np.nan, index=idx)
            own_sig[g] = pd.Series(np.nan, index=idx)
            own_mask[g] = pd.Series(False, index=idx)

    # regional reference variability from all groups' own variability
    ref_groups = [g for g in active if own_mask[g].any()]
    if ref_groups:
        Aref, dref, sref = fixed_effects([own_a[g] for g in ref_groups], [1.0] * len(ref_groups),
                                         [own_sig[g] for g in ref_groups])
    else:
        Aref = pd.Series(np.nan, index=idx)
        sref = Aref.copy()

    groups = {}
    for g, gs in group_sols.items():
        # reference variability for this group: own (if any), else regional, level-matched
        a = own_a[g].copy()
        sa = own_sig[g].copy()
        miss = a.isna()
        if miss.any():
            ov = (~miss) & Aref.notna()
            shift = (a[ov] - Aref[ov]).mean() if ov.any() else 0.0
            a[miss] = Aref[miss] + shift
            sa[miss] = sref[miss]
        # ---- step B: dataset-wise annual series within own coverage ---------
        if g == 'DG':
            lev_s = [s for s in gs if s['source'] == 'demdiff' or
                     (opts['glac_level'] and s['source'] == 'glaciological' and s['author'] != 'WGMS')]
        else:
            lev_s = gs
        series = []
        for s in lev_s:
            val = pd.Series(np.nan, index=idx)
            srand = pd.Series(np.nan, index=idx)
            ssys = pd.Series(np.nan, index=idx)
            use_annual = s['annual'].notna().sum() >= 1 and not (g == 'DG' and s['source'] == 'glaciological'
                                                                    and not opts['glac_level'])
            if use_annual:
                ok = s['annual'].notna()
                val[ok] = s['annual'][ok]
                srand[ok] = s['annual_err'][ok]
                lev = np.sqrt(np.mean(s['annual_err'][ok] ** 2)) / np.sqrt(ok.sum())
                if s['source'] == 'altimetry':
                    lev = np.sqrt(lev ** 2 + (abs(s['annual'][ok].mean()) * SIG_RHO / RHO) ** 2)
                ssys[ok] = lev
            per = []
            for (t0, t1, v, err) in s['periods']:
                w = period_weights(t0, t1, starts)
                if w.sum() < 0.5 or np.any(np.isnan(a.values[w > 0])):
                    continue
                rp = (v - np.sum(w[w > 0] * a.values[w > 0])) / w.sum()
                per.append((w, rp, err / (t1 - t0)))
            if per:
                num = np.zeros(len(idx)); den = np.zeros(len(idx)); snum = np.zeros(len(idx))
                for w, rp, se in per:
                    num += w * rp; den += w; snum += w * se
                cov = den >= 0.5
                if opts['offset_model'] != 'piecewise' and len(per) > 1:
                    pw = np.array([w.sum() for w, _, _ in per])
                    cc = np.sum(pw * np.array([rp for _, rp, _ in per])) / pw.sum()
                    cvals = np.full(len(idx), cc)
                else:
                    cvals = np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)
                svals = np.where(den > 0, snum / np.where(den > 0, den, 1), np.nan)
                fill = cov & val.isna().values
                val[fill] = (a.values + cvals)[fill]
                srand[fill] = sa.values[fill]
                ssys[fill] = svals[fill]
                # DG only: extension beyond DEM coverage with the glaciological variability
                if g == 'DG':
                    pw = np.array([w.sum() for w, _, _ in per])
                    rps = np.array([rp for _, rp, _ in per])
                    ses = np.array([se for _, _, se in per])
                    if opts['extend'] == 'nearest':
                        pos = np.where(den > 0)[0]
                        c_ext = np.array([cvals[pos[np.argmin(np.abs(pos - j))]] for j in range(len(idx))])
                        s_ext = np.array([svals[pos[np.argmin(np.abs(pos - j))]] for j in range(len(idx))])
                    else:
                        c_ext = np.full(len(idx), np.sum(pw * rps) / pw.sum())
                        se_ = np.sqrt(np.sum((pw * ses) ** 2)) / pw.sum()
                        if len(per) > 1:
                            se_ = np.sqrt(se_ ** 2 + wstd(rps, pw) ** 2)
                        s_ext = np.full(len(idx), se_)
                    s['_ext'] = (c_ext, s_ext)
            if val.notna().any() or '_ext' in s:
                series.append(dict(file=s['file'], author=s['author'], w=s['w'], val=val, sr=srand, ss=ssys,
                                   ext=s.pop('_ext', None)))
        if not series:
            continue
        V = pd.concat([o['val'] for o in series], axis=1)
        W = np.array([o['w'] for o in series])
        present = V.notna()
        # DG extension: years with glaciological variability but no DEM coverage
        ext_mask = pd.Series(False, index=idx)
        if g == 'DG':
            need = (~present.any(axis=1)) & own_mask[g]
            if need.any():
                for k, o in enumerate(series):
                    if o['ext'] is None:
                        continue
                    c_ext, s_ext = o['ext']
                    o['val'][need] = (a.values + c_ext)[need.values]
                    o['sr'][need] = sa[need]
                    o['ss'][need] = s_ext[need.values]
                ext_mask = need
                V = pd.concat([o['val'] for o in series], axis=1)
                present = V.notna()
        Wm = present * W
        den = Wm.sum(axis=1).replace(0, np.nan)
        G = (V.fillna(0) * W).sum(axis=1) / den
        SR = pd.concat([o['sr'] for o in series], axis=1)
        SS = pd.concat([o['ss'] for o in series], axis=1)
        if g == 'DG':
            # all DEM series share the same glaciological variability -> correlated
            sig_r = sa.copy()
        else:
            sig_r = np.sqrt(((SR.fillna(0) * W) ** 2).where(present, 0).sum(axis=1)) / den
        sig_s = np.sqrt(((SS.fillna(0) * W) ** 2).where(present, 0).sum(axis=1)) / den
        # structural dispersion between datasets: spread of their mean offsets from the group mean
        d_i, w_i = [], []
        for k, o in enumerate(series):
            m = o['val'].notna() & G.notna()
            if m.sum() >= 1:
                d_i.append((o['val'][m] - G[m]).mean()); w_i.append(o['w'])
        if len(d_i) >= 2:
            neff = np.sum(w_i) ** 2 / np.sum(np.square(w_i))
            sdisp = wstd(d_i, w_i) / np.sqrt(neff)
        else:
            sdisp = 0.0
        sig_s = np.sqrt(sig_s ** 2 + sdisp ** 2)
        cov_mask = G.notna()
        groups[g] = dict(value=G, sig_rand=sig_r.where(cov_mask), sig_sys=sig_s.where(cov_mask),
                         own_var=own_mask[g] & cov_mask, n_level=len(series), offsets=series, a=a,
                         n_present=present.sum(axis=1), ext=ext_mask, sdisp=sdisp)

    # ---- step C: combine groups --------------------------------------------
    groups = {g: v for g, v in groups.items() if g not in opts['drop_groups']}
    gl = list(groups)
    if opts['group_weights'] == 'equal':
        wg = np.ones(len(gl))
    else:   # inverse mean variance
        wg = np.array([1.0 / np.nanmean(groups[g]['sig_rand'] ** 2 + groups[g]['sig_sys'] ** 2) for g in gl])
    Cc, og, _ = fixed_effects([groups[g]['value'] for g in gl], wg)
    vals = pd.concat([groups[g]['value'] for g in gl], axis=1)
    vals.columns = gl
    covered = vals.notna()
    # random component (independent between groups owning their variability)
    sr2 = pd.Series(0.0, index=idx)
    wr = pd.Series(0.0, index=idx)
    for j, g in enumerate(gl):
        m = covered[g] & groups[g]['own_var']
        sr2[m] += (wg[j] * groups[g]['sig_rand'][m]) ** 2
        wr[m] += wg[j]
    sig_rand = np.sqrt(sr2) / wr.replace(0, np.nan)
    # years without any own variability: use the largest group random error
    fill = pd.concat([groups[g]['sig_rand'] for g in gl], axis=1).max(axis=1)
    sig_rand = sig_rand.fillna(fill)
    # extension error for groups not covering a year
    resid_sd = {}
    for j, g in enumerate(gl):
        r = (vals[g] - Cc - og[j])[covered[g]]
        resid_sd[g] = r.std() if len(r) > 2 else np.nan
    ext2 = pd.Series(0.0, index=idx)
    for j, g in enumerate(gl):
        m = ~covered[g]
        if np.isfinite(resid_sd[g]):
            ext2[m] += (wg[j] / wg.sum() * resid_sd[g]) ** 2
    sig_rand = np.sqrt(sig_rand ** 2 + ext2)
    # systematic component
    ss2 = pd.Series(0.0, index=idx)
    for j, g in enumerate(gl):
        s = groups[g]['sig_sys'].copy()
        s = s.fillna(s.mean())     # extended groups keep their mean level error
        ss2 += (wg[j] * s) ** 2
    sig_lev = np.sqrt(ss2) / wg.sum()
    if len(gl) >= 2:
        neff = wg.sum() ** 2 / (wg ** 2).sum()
        sig_struct = wstd(og, wg) / np.sqrt(neff)
    else:
        sig_struct = 0.0
    sig_sys = np.sqrt(sig_lev ** 2 + sig_struct ** 2)
    # year validity: at least one group observes the year
    any_cov = covered.any(axis=1)
    out = pd.DataFrame(dict(start=starts, end=starts + 1, area=A, mwe=Cc.values,
                            sig_rand=sig_rand.values, sig_sys=sig_sys.values,
                            n_groups=covered.sum(axis=1).values), index=idx)
    out['sig'] = np.sqrt(out.sig_rand ** 2 + out.sig_sys ** 2)
    out.loc[~any_cov, ['mwe', 'sig', 'sig_rand', 'sig_sys']] = np.nan
    for g in gl:
        out[f'{g}_mwe'] = groups[g]['value'].values
        out[f'{g}_sig'] = np.sqrt(groups[g]['sig_rand'] ** 2 + groups[g]['sig_sys'] ** 2).values
        out[f'{g}_sig_rand'] = groups[g]['sig_rand'].values
        out[f'{g}_sig_sys'] = groups[g]['sig_sys'].values
        out[f'{g}_ownvar'] = groups[g]['own_var'].values.astype(int)
    out['gt'] = out.mwe * out.area / 1000.0
    out['sig_gt'] = out.sig * out.area / 1000.0
    out['sig_rand_gt'] = out.sig_rand * out.area / 1000.0
    out['sig_sys_gt'] = out.sig_sys * out.area / 1000.0
    meta = dict(region=region, groups=gl, group_offsets=dict(zip(gl, og)), sig_struct=sig_struct,
                excl_grav=excl_grav, group_detail=groups, solutions=sols, Aref=Aref)
    return out, meta


# --------------------------------------------------------------------------
# hydrological -> calendar years
# --------------------------------------------------------------------------
def seasonal_monthly(region, area):
    """Monthly series (m w.e.) from the glaciological sine-wave solution (seasonal shape)."""
    f = glob.glob(f'{DATA}/input/{region}/*GlaciolSineWave*.csv')
    if not f:
        return None
    d = pd.read_csv(f[0])
    c, _, _ = to_mwe(d, area)
    return pd.Series(c, index=np.round(d.start_dates.values * 12).astype(int))   # month index


def to_calendar(region, hy, years=range(2000, 2024)):
    """hy: DataFrame from reconcile_region. Disaggregate each hydrological-year value
    into months with the sine-wave seasonal cycle of that year (additive adjustment of
    the residual spread uniformly), then re-aggregate into calendar years."""
    h = hydro_start(region)
    rows = []
    if h == 0.0:
        for y in years:
            r = hy.loc[float(y)]
            rows.append(dict(year=y, mwe=r.mwe, sig=r.sig, sig_rand=r.sig_rand, sig_sys=r.sig_sys, shift=0.0))
        return pd.DataFrame(rows).set_index('year')
    area = Area(region)
    sw = seasonal_monthly(region, area)
    monthly = {}
    for y0, r in hy.iterrows():
        m0 = int(round(y0 * 12))
        months = list(range(m0, m0 + 12))
        swv = np.array([sw.get(m, np.nan) for m in months])
        if np.isnan(swv).any() or not np.isfinite(r.mwe):
            continue
        adj = (r.mwe - swv.sum()) / 12.0
        for m, v in zip(months, swv):
            monthly[m] = (v + adj, y0)
    for y in years:
        ms = range(y * 12, y * 12 + 12)
        if not all(m in monthly for m in ms):
            rows.append(dict(year=y, mwe=np.nan))
            continue
        val = sum(monthly[m][0] for m in ms)
        # weights of contributing hydrological years
        contrib = {}
        for m in ms:
            contrib[monthly[m][1]] = contrib.get(monthly[m][1], 0) + 1 / 12
        sr = np.sqrt(sum((f * hy.loc[k, 'sig_rand']) ** 2 for k, f in contrib.items()))
        # systematic part: weighted mean (correlated)
        ss = sum(f * hy.loc[k, 'sig_sys'] for k, f in contrib.items())
        # conversion error: 25% of the seasonal shift
        main = max(contrib, key=contrib.get)
        shift = val - hy.loc[main, 'mwe']
        sr = np.sqrt(sr ** 2 + (0.25 * shift) ** 2)
        rows.append(dict(year=y, mwe=val, sig_rand=sr, sig_sys=ss, sig=np.sqrt(sr ** 2 + ss ** 2), shift=shift))
    return pd.DataFrame(rows).set_index('year')
