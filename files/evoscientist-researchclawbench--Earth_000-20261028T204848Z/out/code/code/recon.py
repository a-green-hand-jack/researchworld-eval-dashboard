"""
Reconciliation of multi-method glacier mass-change estimates (GlaMBIE input data).

Independent re-implementation of a GlaMBIE-style "trend + annual-variability" combination:

  1. Homogenisation      : every dataset row -> specific mass change (m w.e.) on a monthly grid
  2. Within data group   : annual variability (fixed-effects fit of annual-resolving datasets) is
                           calibrated to the long-term level of every dataset (trend rows and annual rows)
  3. Between data groups : regional annual variability + (constant) group offsets combined
                           with inverse-variance (default) or equal weights
  4. Unit conversion     : m w.e. -> Gt with time-varying regional glacier area
  5. Calendar years      : hydrological -> calendar years using monthly seasonal cycle
  6. Global              : sum of regions, errors in quadrature

Everything is driven by a config dict so that sensitivity experiments can be run.
"""
import glob, os
import numpy as np
import pandas as pd

DATA = 'data/glambie/input'
RES = 'data/glambie/results'

RHO_ICE = 850.0       # kg m-3, Huss (2013) volume-to-mass conversion
SIG_RHO = 60.0        # kg m-3
RHO_W = 997.0         # kg m-3, water density used for m w.e. <-> Gt (GlaMBIE convention)

REGIONS = {1: 'alaska', 2: 'western_canada_us', 3: 'arctic_canada_north', 4: 'arctic_canada_south',
           5: 'greenland_periphery', 6: 'iceland', 7: 'svalbard', 8: 'scandinavia', 9: 'russian_arctic',
           10: 'north_asia', 11: 'central_europe', 12: 'caucasus_middle_east', 13: 'central_asia',
           14: 'south_asia_west', 15: 'south_asia_east', 16: 'low_latitudes', 17: 'southern_andes',
           18: 'new_zealand', 19: 'antarctic_and_subantarctic'}
LABELS = {1: 'Alaska', 2: 'Western Canada & US', 3: 'Arctic Canada North', 4: 'Arctic Canada South',
          5: 'Greenland Periphery', 6: 'Iceland', 7: 'Svalbard & Jan Mayen', 8: 'Scandinavia',
          9: 'Russian Arctic', 10: 'North Asia', 11: 'Central Europe', 12: 'Caucasus & Middle East',
          13: 'Central Asia', 14: 'South Asia West', 15: 'South Asia East', 16: 'Low Latitudes',
          17: 'Southern Andes', 18: 'New Zealand', 19: 'Antarctic & Subantarctic'}

# hydrological-year start (fraction of calendar year): NH 1 Oct, tropics 1 Jan, SH 1 Apr
def hy_start(rid):
    if rid == 16:
        return 0.0
    if rid in (17, 18, 19):
        return 0.25
    return 0.75

# Regions where satellite gravimetry is not used for the consensus (see report):
# small glacier area (< ~10,000 km2, below GRACE resolution / leakage dominated), adjacency to ice sheets
# (5, 19), strong non-glacial hydrological / GIA signals (2, 13-15).
GRAV_EXCLUDED = {2, 5, 8, 10, 11, 12, 13, 14, 15, 16, 18, 19}

GROUP_OF_SOURCE = {'altimetry': 'altimetry', 'gravimetry': 'gravimetry', 'demdiff': 'demdiff_and_glaciological',
                   'glaciological': 'demdiff_and_glaciological', 'combined': 'hybrid'}

DEFAULT_CFG = dict(
    group_weighting='equal',      # 'invvar' | 'equal'   (between data groups)
    offset_mode='constant',       # 'constant' | 'yearwise'
    exclude_groups=(),            # e.g. ('gravimetry',)
    include_hybrid=False,         # use hybrid ("combined") datasets as 4th data group
    grav_everywhere=False,        # ignore GRAV_EXCLUDED
    exclude_glac_level=True,      # glaciological data only provide variability (not level)
    calendar_seasonal='yearly',   # 'yearly' | 'linear'
    rho=RHO_ICE,
)

K_RANGE = np.arange(1999, 2024)   # hydrological years indexed by their start year (k + s)


# ----------------------------------------------------------------------------------------------- area
def region_area_model():
    """Linear area model A(t) per region from the GlaMBIE area convention (RGI 6.0 + regional
    area-change rates); taken from the 'glacier_area' column of the result files (auxiliary data)."""
    rows = []
    for rid, name in REGIONS.items():
        d = pd.read_csv(f'{RES}/calendar_years/{rid}_{name}.csv')
        p = np.polyfit(d.start_dates.values, d.glacier_area.values, 1)
        rows.append(dict(region_id=rid, slope=p[0], a2000=np.polyval(p, 2000.0),
                         resid=np.abs(np.polyval(p, d.start_dates) - d.glacier_area).max()))
    return pd.DataFrame(rows).set_index('region_id')


AREA = None
def area(rid, t):
    global AREA
    if AREA is None:
        AREA = region_area_model()
    r = AREA.loc[rid]
    return r.a2000 + r.slope * (np.asarray(t) - 2000.0)


def mean_area(rid, t0, t1):
    return area(rid, 0.5 * (t0 + t1))  # linear model -> mean = value at midpoint


# ----------------------------------------------------------------------------------------- loading
def list_datasets(rid):
    name = REGIONS[rid]
    out = []
    for f in sorted(glob.glob(f'{DATA}/{rid}_{name}/*.csv')):
        base = os.path.basename(f)[:-4]
        rest = base[len(name) + 1:]
        src = rest.split('_')[0]
        out.append(dict(file=f, source=src, dataset=rest[len(src) + 1:], group=GROUP_OF_SOURCE[src]))
    return out


def to_mwe(df, rid, rho=RHO_ICE):
    """Convert changes/errors of a dataset to m w.e."""
    unit = df.unit.iloc[0].lower()
    c = df.changes.values.astype(float); e = df.errors.values.astype(float)
    if unit == 'm':
        mwe = c * rho / RHO_W
        err = np.sqrt((e * rho / RHO_W) ** 2 + (c * SIG_RHO / RHO_W) ** 2)
    elif unit == 'mwe':
        mwe, err = c, e
    elif unit == 'gt':
        A = mean_area(rid, df.start_dates.values, df.end_dates.values)
        mwe = c * 1e3 / (A * RHO_W / 1e3) / 1e3 * 1e3  # Gt -> m w.e. : Gt*1e12 kg / (A km2*1e6 m2 * rho_w)
        mwe = c * 1e12 / (A * 1e6 * RHO_W)
        err = e * 1e12 / (A * 1e6 * RHO_W)
    else:
        raise ValueError(unit)
    out = pd.DataFrame(dict(m0=np.round(df.start_dates.values * 12).astype(int),
                            m1=np.round(df.end_dates.values * 12).astype(int), mwe=mwe, err=err))
    out = out[(out.m1 > out.m0) & np.isfinite(out.mwe) & np.isfinite(out.err)]
    return out.reset_index(drop=True)


# ------------------------------------------------------------------------------ seasonal cycle
def seasonal_cycle(rid):
    """Year-specific and climatological monthly seasonal anomaly (zero-sum per HY) from the
    UZH glaciological sine-wave dataset (Zemp et al.). Returns dict month_index -> anomaly (m w.e.)
    and climatology array (12,) indexed by month-in-HY. Low latitudes: no seasonality."""
    s = hy_start(rid)
    f = glob.glob(f'{DATA}/{rid}_{REGIONS[rid]}/*GlaciolSineWave*.csv')
    if not f:
        return {}, np.zeros(12)
    d = to_mwe(pd.read_csv(f[0]), rid)
    d = d[d.m1 - d.m0 == 1]
    mon = dict(zip(d.m0, d.mwe))
    anom = {}
    clim = []
    for k in range(1990, 2030):
        ms = int(round((k + s) * 12)) + np.arange(12)
        if all(m in mon for m in ms):
            v = np.array([mon[m] for m in ms]); a = v - v.mean()
            for m, x in zip(ms, a):
                anom[m] = x
            clim.append(a)
    clim = np.mean(clim, axis=0) if clim else np.zeros(12)
    return anom, clim


def seas_anom(rid, months, anom, clim):
    s = hy_start(rid)
    out = []
    for m in months:
        if m in anom:
            out.append(anom[m])
        else:
            j = int((m - int(round(s * 12))) % 12)
            out.append(clim[j])
    return np.array(out)


# ------------------------------------------------------------------------------ dataset -> rows
def process_dataset(ds, rid, cfg, anom, clim):
    """Returns dict with 'annual' (Series k -> (value, err)) if annual-resolving,
    and/or 'trend' list of rows {m0,m1,mwe_corr,err,L} (seasonally corrected)."""
    raw = pd.read_csv(ds['file'])
    d = to_mwe(raw, rid, cfg['rho'])
    s = hy_start(rid)
    dur = (d.m1 - d.m0)
    out = dict(annual=None, trend=[])
    if dur.median() <= 12:
        # annual-resolving: aggregate monthly / annual rows to hydrological years
        mon_val, mon_err = {}, {}
        for r in d.itertuples():
            n = r.m1 - r.m0
            for m in range(int(r.m0), int(r.m1)):
                mon_val[m] = r.mwe / n
                mon_err[m] = r.err   # epoch-type error, carried as is (see report)
        # flag gap-filled (linearly interpolated) months: runs of >=3 identical monthly changes
        flagged = set()
        if (dur == 1).all():
            ms_sorted = sorted(mon_val)
            run = [ms_sorted[0]]
            for a, b in zip(ms_sorted[:-1], ms_sorted[1:]):
                if b == a + 1 and abs(mon_val[b] - mon_val[a]) <= 2e-3 * max(abs(mon_val[a]), 1e-9):
                    run.append(b)
                else:
                    if len(run) >= 3:
                        flagged.update(run)
                    run = [b]
            if len(run) >= 3:
                flagged.update(run)
        recs, gap_hy = {}, []
        for k in K_RANGE:
            ms = int(round((k + s) * 12)) + np.arange(12)
            if all(m in mon_val for m in ms):
                v = sum(mon_val[m] for m in ms)
                if (dur == 12).all():
                    e = mon_err[ms[0]]
                else:
                    e = np.sqrt(np.mean([mon_err[m] ** 2 for m in ms]))
                if any(m in flagged for m in ms):
                    gap_hy.append((k, v, e))     # year affected by gap interpolation
                else:
                    recs[k] = (v, e)
        if len(recs):
            out['annual'] = pd.DataFrame(recs, index=['v', 'e']).T
        # gap-affected years -> multi-year level constraint (total preserved, timing not resolved)
        blocks = []
        for k, v, e in gap_hy:
            if blocks and blocks[-1][-1][0] == k - 1:
                blocks[-1].append((k, v, e))
            else:
                blocks.append([(k, v, e)])
        for b in blocks:
            m0 = int(round((b[0][0] + s) * 12)); m1 = int(round((b[-1][0] + 1 + s) * 12))
            out['trend'].append(dict(m0=m0, m1=m1, mwe=sum(x[1] for x in b),
                                     err=np.sqrt(np.mean([x[2] ** 2 for x in b])), L=len(b)))
        out['n_flagged'] = len(flagged)
        # rows that do not align with HY grid and are long are ignored (none in practice)
    else:
        for r in d.itertuples():
            months = np.arange(int(r.m0), int(r.m1))
            corr = r.mwe - seas_anom(rid, months, anom, clim).sum()
            out['trend'].append(dict(m0=r.m0, m1=r.m1, mwe=corr, err=r.err, L=(r.m1 - r.m0) / 12.0))
    return out


def hy_weights(rid, m0, m1):
    """fraction of each hydrological year k (in K_RANGE) covered by [m0, m1) months -> array"""
    s = hy_start(rid)
    w = np.zeros(len(K_RANGE))
    for i, k in enumerate(K_RANGE):
        a = int(round((k + s) * 12)); b = a + 12
        w[i] = max(0, min(b, m1) - max(a, m0)) / 12.0
    return w


# ---------------------------------------------------------------- fixed-effects variability
def fixed_effects(series, weights=None, use_err=True):
    """series: list of DataFrames indexed by k with cols v,e. Model v_ik = c_i + u_k.
    Weighted LS (1/e^2 * team weight). Returns u (Series over covered k), sigma_u."""
    ks = sorted(set().union(*[set(s.index) for s in series]))
    if not ks:
        return None, None
    kidx = {k: j for j, k in enumerate(ks)}
    n_i, n_k = len(series), len(ks)
    rows, y, w = [], [], []
    for i, s in enumerate(series):
        tw = 1.0 if weights is None else weights[i]
        for k, r in s.iterrows():
            x = np.zeros(n_i + n_k); x[i] = 1; x[n_i + kidx[k]] = 1
            rows.append(x); y.append(r.v); w.append(tw / r.e ** 2 if use_err else tw)
    X = np.array(rows); y = np.array(y); w = np.array(w)
    # constraint sum(u)=0 -> append heavy row
    xc = np.zeros(n_i + n_k); xc[n_i:] = 1
    X = np.vstack([X, xc]); y = np.append(y, 0); w = np.append(w, 1e6 * w.max())
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    u = pd.Series(beta[n_i:], index=ks)
    # uncertainty of u_k: inverse-variance combination of contributing datasets
    sig = {}
    for k in ks:
        ws = [(1.0 if weights is None else weights[i]) / (s.loc[k, 'e'] ** 2 if use_err else 1.0) for i, s in enumerate(series) if k in s.index]
        wn = [1.0 if weights is None else weights[i] for i, s in enumerate(series) if k in s.index]
        # effective error of a weighted mean with normalised weights
        es = [s.loc[k, 'e'] for i, s in enumerate(series) if k in s.index]
        W = np.array(ws); E = np.array(es)
        sig[k] = np.sqrt(np.sum((W / W.sum()) ** 2 * E ** 2))
    return u, pd.Series(sig)


def team_of(ds):
    return ds['dataset'].split('_')[-3] if ds['dataset'].endswith('et_al') else ds['dataset']


# -------------------------------------------------------------------------- region pipeline
def run_region(rid, cfg=None):
    cfg = {**DEFAULT_CFG, **(cfg or {})}
    s = hy_start(rid)
    anom, clim = seasonal_cycle(rid)
    dss = list_datasets(rid)
    used = []
    for ds in dss:
        g = ds['group']
        if g == 'hybrid' and not cfg['include_hybrid']:
            continue
        if g in cfg['exclude_groups']:
            continue
        if ds['source'] == 'gravimetry' and rid in GRAV_EXCLUDED and not cfg['grav_everywhere']:
            continue
        p = process_dataset(ds, rid, cfg, anom, clim)
        used.append({**ds, **p, 'team': ds['file'].split('_')[-3] if False else ds['dataset']})
    # team key: author (last part of file name) -> equal weight per author within group
    for u in used:
        u['team'] = pd.read_csv(u['file'], nrows=1).author.iloc[0]
    groups = sorted(set(u['group'] for u in used))

    # ---------- regional variability (all annual-resolving datasets, team-normalised weights)
    # annual-resolving datasets with < 3 years carry no usable variability information
    ann = [u for u in used if u['annual'] is not None and len(u['annual']) >= 3]
    def team_weights(lst):
        cnt = {}
        for u in lst:
            cnt[(u['group'], u['team'])] = cnt.get((u['group'], u['team']), 0) + 1
        ng = {}
        for (g, t) in cnt:
            ng[g] = ng.get(g, 0) + 1
        return [1.0 / cnt[(u['group'], u['team'])] / ng[u['group']] for u in lst]
    UE = cfg['group_weighting'] == 'invvar'
    vR, svR = fixed_effects([u['annual'] for u in ann], team_weights(ann), UE)
    # extend over K_RANGE if needed (fill missing years with 0 anomaly and large error)
    vR = vR.reindex(K_RANGE); svR = svR.reindex(K_RANGE)

    group_res = {}
    for g in groups:
        members = [u for u in used if u['group'] == g]
        gann = [u for u in members if u['annual'] is not None and len(u['annual']) >= 3]
        own_var = False
        if gann:
            vg, svg = fixed_effects([u['annual'] for u in gann], team_weights(gann), UE)
            vg = vg.reindex(K_RANGE); svg = svg.reindex(K_RANGE)
            own_var = vg.notna().sum() >= 3
            # fill years without own variability with regional variability (aligned)
            ov = vg.notna() & vR.notna()
            off = (vg[ov] - vR[ov]).mean() if ov.any() else 0.0
            fill = vg.isna()
            vg[fill] = vR[fill] + off; svg[fill] = svR[fill]
        else:
            vg, svg = vR.copy(), svR.copy()
        # ---------- level constraints (rows) per team
        rows = []   # each: team, weights over K, beta, sigma_annual
        for u in members:
            is_glac = u['source'] == 'glaciological'
            if is_glac and cfg['exclude_glac_level']:
                continue
            if u['annual'] is not None:
                for k, r in u['annual'].iterrows():
                    i = int(np.where(K_RANGE == k)[0][0])
                    w = np.zeros(len(K_RANGE)); w[i] = 1
                    rows.append(dict(team=u['team'], w=w, beta=r.v - vg.iloc[i], sig=r.e, trend=False))
            for t in u['trend']:
                w = hy_weights(rid, t['m0'], t['m1'])
                if w.sum() < 0.5 or np.isnan(vg.values[w > 0]).any():
                    continue
                beta = (t['mwe'] - np.nansum(w * vg.values)) / w.sum()
                rows.append(dict(team=u['team'], w=w, beta=beta, sig=t['err'] / np.sqrt(max(t['L'], 1.0)),
                                 rate_sig=t['err'] / t['L'], trend=True))
        teams = sorted(set(r['team'] for r in rows))
        B = np.full(len(K_RANGE), np.nan); SB = np.full(len(K_RANGE), np.nan); cov = np.zeros(len(K_RANGE))
        ftrend = np.zeros(len(K_RANGE))
        for i in range(len(K_RANGE)):
            tb, ts, tt = [], [], []
            for t in teams:
                rr = [r for r in rows if r['team'] == t and r['w'][i] > 0]
                if not rr:
                    continue
                ww = np.array([r['w'][i] for r in rr])
                tb.append(np.sum(ww * [r['beta'] for r in rr]) / ww.sum())
                ts.append(np.sqrt(np.sum((ww / ww.sum()) ** 2 * np.array([r['sig'] for r in rr]) ** 2)))
                tt.append(np.mean([r['trend'] for r in rr]))
                cov[i] = max(cov[i], ww.max())
            if tb:
                tb, ts = np.array(tb), np.array(ts)
                B[i] = tb.mean()
                prop = np.sqrt(np.sum(ts ** 2)) / len(tb)
                emp = tb.std(ddof=1) / np.sqrt(len(tb)) if len(tb) > 1 else 0.0
                SB[i] = max(prop, emp)
                ftrend[i] = np.mean(tt)
        covered = ~np.isnan(B)
        if not covered.any():
            continue
        # years without level coverage: use mean offset of all teams (constant extrapolation)
        team_mean = []
        for t in teams:
            rr = [r for r in rows if r['team'] == t]
            ww = np.array([r['w'].sum() for r in rr])
            team_mean.append(np.sum(ww * [r['beta'] for r in rr]) / ww.sum())
        Bfill = np.mean(team_mean)
        SBfill = np.nanmax(SB)
        if cfg.get('extrap', 'nearest') == 'nearest':
            idx_c = np.where(covered)[0]
            for i in np.where(~covered)[0]:
                j = idx_c[np.argmin(np.abs(idx_c - i))]
                B[i] = B[j]; SB[i] = max(SB[j], SBfill)
        else:
            B[~covered] = Bfill; SB[~covered] = SBfill
        x = vg.values + B
        sx = np.sqrt(SB ** 2 + ftrend * svg.values ** 2 + (~covered) * svg.values ** 2)
        valid = ~np.isnan(x)
        group_res[g] = pd.DataFrame(dict(k=K_RANGE, mwe=x, err=sx, covered=covered, cov=cov,
                                         own_var=own_var, n_teams=len(teams), valid=valid)).set_index('k')

    # ---------- regional combination
    var_groups = [g for g in group_res if group_res[g].own_var.iloc[0]]
    if not var_groups:
        var_groups = list(group_res)
    if cfg['offset_mode'] == 'constant':
        # regional variability from groups with own variability (fixed effects on group series)
        series = [group_res[g].loc[group_res[g].valid, ['mwe', 'err']].rename(columns={'mwe': 'v', 'err': 'e'})
                  for g in var_groups]
        for i, g in enumerate(var_groups):  # only years with genuine group coverage for variability
            series[i] = series[i][group_res[g].loc[series[i].index, 'covered'] | (group_res[g].loc[series[i].index, 'own_var'])]
        u, su = fixed_effects(series, None, UE)
        u = u.reindex(K_RANGE); su = su.reindex(K_RANGE)
        offs, soffs, names = [], [], []
        for g, gr in group_res.items():
            m = gr.covered & gr.valid & u.notna().values
            if m.sum() == 0:
                continue
            wcov = gr.loc[m, 'cov'].values
            o = np.sum(wcov * (gr.loc[m, 'mwe'].values - u[m.values].values)) / wcov.sum()
            # error of the long-term mean: annual errors partially correlated -> use mean error / sqrt(n_eff)
            n_eff = max(1.0, wcov.sum() / 3.0)   # assume ~3-yr decorrelation
            so = np.sqrt(np.mean(gr.loc[m, 'err'].values ** 2)) / np.sqrt(n_eff)
            offs.append(o); soffs.append(so); names.append(g)
        offs, soffs = np.array(offs), np.array(soffs)
        wts = 1 / soffs ** 2 if cfg['group_weighting'] == 'invvar' else np.ones_like(offs)
        wts = wts / wts.sum()
        O = np.sum(wts * offs)
        sO_prop = np.sqrt(np.sum(wts ** 2 * soffs ** 2))
        sO_disc = np.sqrt(np.sum(wts * (offs - O) ** 2)) if len(offs) > 1 else 0.0
        sO = np.sqrt(sO_prop ** 2 + sO_disc ** 2)
        comb = u.values + O
        scomb = np.sqrt(su.values ** 2 + sO ** 2)
        s_rand = su.values.copy(); s_sys = np.full(len(K_RANGE), sO)
        meta = dict(offsets=dict(zip(names, offs)), offset_err=dict(zip(names, soffs)),
                    weights=dict(zip(names, wts)), O=O, sO_disc=sO_disc, sO_prop=sO_prop)
    else:  # yearwise weighted mean of group series where covered
        comb = np.full(len(K_RANGE), np.nan); scomb = np.full(len(K_RANGE), np.nan)
        s_sys = np.zeros(len(K_RANGE))
        for i in range(len(K_RANGE)):
            xs, es = [], []
            for g, gr in group_res.items():
                if gr.valid.iloc[i] and (gr.covered.iloc[i] or len(group_res) == 1):
                    xs.append(gr.mwe.iloc[i]); es.append(gr.err.iloc[i])
            if not xs:
                gs = [gr for gr in group_res.values() if gr.valid.iloc[i]]
                xs = [gr.mwe.iloc[i] for gr in gs]; es = [gr.err.iloc[i] for gr in gs]
            if not xs:
                continue
            xs, es = np.array(xs), np.array(es)
            wts = 1 / es ** 2 if cfg['group_weighting'] == 'invvar' else np.ones_like(xs)
            wts = wts / wts.sum()
            comb[i] = np.sum(wts * xs)
            disc = np.sqrt(np.sum(wts * (xs - comb[i]) ** 2)) if len(xs) > 1 else 0
            scomb[i] = np.sqrt(np.sum(wts ** 2 * es ** 2) + disc ** 2)
        meta = {}
        s_rand = scomb.copy()
    A = area(rid, K_RANGE + s + 0.5)
    out = pd.DataFrame(dict(k=K_RANGE, start=K_RANGE + s, end=K_RANGE + s + 1, area=A, mwe=comb, mwe_err=scomb,
                            err_rand=s_rand, err_sys=s_sys))
    out['gt'] = out.mwe * out.area * 1e6 * RHO_W / 1e12
    out['gt_err'] = out.mwe_err * out.area * 1e6 * RHO_W / 1e12
    for g, gr in group_res.items():
        out[g + '_mwe'] = np.where(gr.valid.values, gr.mwe.values, np.nan)
        out[g + '_err'] = gr.err.values
        out[g + '_covered'] = gr.covered.values
        out[g + '_ownvar'] = gr.own_var.values
    out = out.set_index('k')
    return out, dict(meta=meta, used=[(u['source'], u['dataset'], u['team'], u['annual'] is not None, len(u['trend'])) for u in used],
                     anom=anom, clim=clim)


# ------------------------------------------------------------------------- calendar years
def to_calendar(rid, hy, anom, clim, cfg=None):
    """Convert hydrological-year series (index k) to calendar years 2000..2023 via monthly series:
    month value = b_k/12 + seasonal anomaly (year-specific from glaciological sine wave if available)."""
    cfg = {**DEFAULT_CFG, **(cfg or {})}
    s = hy_start(rid)
    mval, merr, mrand, msys = {}, {}, {}, {}
    for k, r in hy.iterrows():
        if np.isnan(r.mwe):
            continue
        ms = int(round((k + s) * 12)) + np.arange(12)
        sa = seas_anom(rid, ms, anom, clim) if cfg['calendar_seasonal'] == 'yearly' else np.zeros(12)
        for m, a in zip(ms, sa):
            mval[m] = r.mwe / 12 + a
            merr[m] = r.mwe_err / 12
            mrand[m] = r.err_rand / 12
            msys[m] = r.err_sys / 12
    rows = []
    for Y in range(2000, 2024):
        ms = np.arange(Y * 12, Y * 12 + 12)
        if not all(m in mval for m in ms):
            rows.append(dict(year=Y, mwe=np.nan, mwe_err=np.nan, err_rand=np.nan, err_sys=np.nan)); continue
        v = sum(mval[m] for m in ms)
        e = sum(merr[m] for m in ms)  # fully correlated within a HY, linear (conservative)
        rows.append(dict(year=Y, mwe=v, mwe_err=e, err_rand=sum(mrand[m] for m in ms),
                         err_sys=sum(msys[m] for m in ms)))
    c = pd.DataFrame(rows)
    c['area'] = area(rid, c.year + 0.5)
    c['gt'] = c.mwe * c.area * 1e6 * RHO_W / 1e12
    c['gt_err'] = c.mwe_err * c.area * 1e6 * RHO_W / 1e12
    c['gt_err_rand'] = c.err_rand * c.area * 1e6 * RHO_W / 1e12
    c['gt_err_sys'] = c.err_sys * c.area * 1e6 * RHO_W / 1e12
    return c.set_index('year')


def run_all(cfg=None, regions=None):
    regions = regions or list(REGIONS)
    hy, cal, meta = {}, {}, {}
    for rid in regions:
        h, m = run_region(rid, cfg)
        hy[rid] = h; meta[rid] = m
        cal[rid] = to_calendar(rid, h, m['anom'], m['clim'], cfg)
    glob_ = pd.DataFrame(index=range(2000, 2024))
    glob_['gt'] = sum(cal[r]['gt'] for r in regions)
    glob_['gt_err'] = np.sqrt(sum(cal[r].gt_err ** 2 for r in regions))
    glob_['gt_err_rand'] = np.sqrt(sum(cal[r].gt_err_rand ** 2 for r in regions))
    glob_['gt_err_sys'] = np.sqrt(sum(cal[r].gt_err_sys ** 2 for r in regions))
    glob_['area'] = sum(cal[r].area for r in regions)
    glob_['mwe'] = glob_['gt'] * 1e12 / (glob_.area * 1e6 * RHO_W)
    glob_['mwe_err'] = glob_.gt_err * 1e12 / (glob_.area * 1e6 * RHO_W)
    return hy, cal, glob_, meta
