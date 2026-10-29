"""Validation and robustness analyses:
 (a) comparison with hybrid estimates (not used in the consensus),
 (b) leave-one-group-out (LOGO) consistency / uncertainty calibration,
 (c) sensitivity of global totals to methodological choices,
 (d) comparison with literature benchmarks, (e) trend / acceleration analysis.
"""
import sys, os, pickle, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import glambie_lib as L

OUT = os.path.join(L.ROOT, 'outputs')
M = pickle.load(open(os.path.join(OUT, 'main_results.pkl'), 'rb'))
res, cal, glob_ = M['res'], M['cal'], M['glob']
rng = np.random.default_rng(42)
summary = {}
YRS = np.arange(2000, 2024)

# ------------------------------------------------------------------ (a) hybrids
hyb_rows, hyb_cal = [], {}
for rid, r in res.items():
    for ds in r['datasets']:
        if ds['group'] != 'hybrid':
            continue
        if ds['kind'] == 'annual':
            v, e = ds['hy'], ds['hy_err']
            ok = np.isfinite(v) & np.isfinite(r['mwe'])
            ok &= (r['starts'] >= 1999.7) & (r['starts'] < 2024)
            if ok.sum() < 3:
                continue
            hyb_rows.append(dict(region_id=rid, dataset=ds['name'], kind='annual', n=int(ok.sum()),
                                 start=r['starts'][ok].min(), end=r['starts'][ok].max() + 1,
                                 hybrid_mean=np.mean(v[ok]), ours_mean=np.mean(r['mwe'][ok]),
                                 r=np.corrcoef(v[ok], r['mwe'][ok])[0, 1],
                                 rmse=np.sqrt(np.mean((v[ok] - r['mwe'][ok]) ** 2))))
            key = ds['name'].split('_')[0]
            if key in ('DUS-combined', 'Huss'):
                rr = dict(rid=rid, starts=r['starts'], mwe=v, err=e)
                c = L.to_calendar(rr, YRS)
                hyb_cal.setdefault(key, {})[rid] = c
        else:  # single-period trends (e.g. Colgan, Miles): compare period means
            for sk, tk, xk, ek in zip(ds['start'], ds['end'], ds['x'], ds['e']):
                # our mean over the same period using monthly-uniform HY values
                w = np.clip(np.minimum(r['starts'] + 1, tk) - np.maximum(r['starts'], sk), 0, 1)
                ok = (w > 0) & np.isfinite(r['mwe'])
                ours = np.sum(w[ok] * r['mwe'][ok]) / (tk - sk)
                hyb_rows.append(dict(region_id=rid, dataset=ds['name'], kind='trend', n=1, start=sk, end=tk,
                                     hybrid_mean=xk / (tk - sk), ours_mean=ours, r=np.nan, rmse=np.nan))
hyb = pd.DataFrame(hyb_rows)
hyb.to_csv(os.path.join(OUT, 'validation_hybrid_regional.csv'), index=False)
# global hybrid series (regions with complete coverage)
ghyb = {}
for key, d in hyb_cal.items():
    if len(d) < 19:
        continue
    a = pd.concat(d.values())
    g = a.groupby('start_dates').agg(gt=('gt', 'sum'), n=('gt', lambda x: np.isfinite(x).sum()))
    ghyb[key] = g
gh = glob_[['start_dates', 'gt', 'gt_err']].copy()
for key, g in ghyb.items():
    gh = gh.merge(g[['gt']].rename(columns={'gt': key + '_gt'}), left_on='start_dates', right_index=True, how='left')
gh.to_csv(os.path.join(OUT, 'validation_hybrid_global.csv'), index=False)
summary['hybrid_global'] = {}
for key in ghyb:
    m = gh[np.isfinite(gh[key + '_gt'])]
    if key == 'Huss':
        m = m[m.start_dates <= 2020]
    summary['hybrid_global'][key] = dict(years=f'{int(m.start_dates.min())}-{int(m.start_dates.max())}',
                                         ours_mean=float(m['gt'].mean()), hybrid_mean=float(m[key + '_gt'].mean()),
                                         r=float(np.corrcoef(m['gt'], m[key + '_gt'])[0, 1]),
                                         rmse=float(np.sqrt(np.mean((m['gt'] - m[key + '_gt']) ** 2))))

# ------------------------------------------------------------------ (b) LOGO
logo = []
for rid, r in res.items():
    G = r['groups']
    if len(G) < 2:
        continue
    for g in G:
        others = [h for h in G if h != g]
        V = np.array([G[h]['mwe'] for h in others]); E = np.array([G[h]['err'] for h in others])
        ok = np.isfinite(V) & np.isfinite(E)
        n = ok.sum(0)
        with np.errstate(all='ignore'):
            cm = np.where(n > 0, np.nansum(np.where(ok, V, 0), 0) / n, np.nan)
            ce = np.where(n > 0, np.sqrt(np.nansum(np.where(ok, E ** 2, 0), 0)) / n, np.nan)
        z = (G[g]['mwe'] - cm) / np.sqrt(G[g]['err'] ** 2 + ce ** 2)
        for a, zz, gv, cv in zip(r['starts'], z, G[g]['mwe'], cm):
            if np.isfinite(zz) and 1999.7 <= a < 2024:
                logo.append(dict(region_id=rid, group=g, hy_start=a, z=zz, diff=gv - cv))
logo = pd.DataFrame(logo)
logo.to_csv(os.path.join(OUT, 'validation_logo.csv'), index=False)
summary['logo'] = dict(n=int(len(logo)), sd_z=float(logo.z.std()), mean_z=float(logo.z.mean()),
                       frac_within_1sigma=float((logo.z.abs() < 1).mean()),
                       frac_within_2sigma=float((logo.z.abs() < 2).mean()),
                       by_group={g: dict(n=int(len(d)), sd_z=float(d.z.std()), mean_z=float(d.z.mean()),
                                         mean_diff=float(d['diff'].mean()),
                                         frac1=float((d.z.abs() < 1).mean()))
                                 for g, d in logo.groupby('group')})

# ------------------------------------------------------------------ (c) sensitivity
def global_stats(g):
    g = g[(g.start_dates >= 2000) & (g.start_dates <= 2023)]
    g19 = g[g.start_dates <= 2019]
    return dict(total_gt=float(g['gt'].sum()), total_err=float(np.sqrt((g.gt_err ** 2).sum())),
                mean_gt=float(g['gt'].mean()), mean_2000_2019=float(g19['gt'].mean()),
                mean_mwe=float(g.mwe.mean()))

variants = {
    'Main (equal-weight groups)': None,
    'Inverse-variance weighting of groups': dict(group_weighting='ivw'),
    'Inverse-variance weighting within groups': dict(within_weighting='ivw'),
    'Gravimetry used in all regions': dict(grav_all=True),
    'Hybrid estimates as 4th group': dict(use_hybrid=True),
    'Density 800 kg m-3': dict(density=0.80),
    'Density 900 kg m-3': dict(density=0.90),
    'DEM extrapolation: nearest-period offset': dict(ext_mode='nearest'),
    'Sub-annual errors as epoch noise': dict(hr_err='epoch'),
}
sens = []
for name, opt in variants.items():
    if opt is None:
        st = global_stats(glob_)
    else:
        _, _, g = L.run_all(opt)
        st = global_stats(g)
    st['variant'] = name
    sens.append(st); print(name, round(st['total_gt'], 1), round(st['mean_gt'], 1))
# drop-one-group variants (only where other groups remain)
for drop in L.GROUPS:
    cals = {}
    for rid in range(1, 20):
        r = L.process_region(rid, dict(drop_group=drop))
        if not np.isfinite(r['mwe']).any() or (rid in res and len(res[rid]['groups']) == 1):
            r = res[rid]
        else:
            # where the dropped group was the only one in a given year, fall back to main estimate
            r['mwe'] = np.where(np.isfinite(r['mwe']), r['mwe'], res[rid]['mwe'])
            r['err'] = np.where(np.isfinite(r['err']), r['err'], res[rid]['err'])
        cals[rid] = L.to_calendar(r)
    a = pd.concat(cals.values())
    g = a.groupby('start_dates').agg(glacier_area=('glacier_area', 'sum'), gt=('gt', 'sum'),
                                     gt_err=('gt_err', lambda x: np.sqrt((x ** 2).sum()))).reset_index()
    g['mwe'] = g['gt'] / g['glacier_area'] * 1000
    st = global_stats(g); st['variant'] = f'Without {drop} group (where replaceable)'
    sens.append(st); print(st['variant'], round(st['total_gt'], 1))
sens = pd.DataFrame(sens)
sens.to_csv(os.path.join(OUT, 'sensitivity_global.csv'), index=False)

# ------------------------------------------------------------------ (d) literature
g = glob_.set_index('start_dates')
def pmean(a, b):
    s = g.loc[a:b]
    return float(s['gt'].mean()), float(np.sqrt((s.gt_err ** 2).sum()) / len(s))
lit = [
    ('Hugonnet et al. (2021) 2000-2019', 2000, 2019, -267, 16 / 2),
    ('Hugonnet et al. (2021) 2000-2004', 2000, 2004, -227, 25 / 2),
    ('Hugonnet et al. (2021) 2005-2009', 2005, 2009, -257, 22 / 2),
    ('Hugonnet et al. (2021) 2010-2014', 2010, 2014, -284, 23 / 2),
    ('Hugonnet et al. (2021) 2015-2018', 2015, 2018, -292, 24 / 2),
    ('Zemp et al. (2019) 2006-2016', 2006, 2016, -335, 144),
]
og = pd.read_csv(os.path.join(L.RES, 'calendar_years', '0_global.csv')).set_index('start_dates')
litrows = []
for name, a, b, v, e in lit:
    m, me = pmean(a, b)
    o = og.loc[a:b]
    litrows.append(dict(reference=name, period=f'{a}-{b}', ref_gt_yr=v, ref_err_1sigma=e, ours_gt_yr=m, ours_err=me,
                        glambie2024_gt_yr=float(o.combined_gt.mean()),
                        z=(m - v) / np.sqrt(me ** 2 + e ** 2)))
lit = pd.DataFrame(litrows)
lit.to_csv(os.path.join(OUT, 'validation_literature.csv'), index=False)

# ------------------------------------------------------------------ (e) trends / acceleration
def trend_mc(y, s, t, nmc=5000):
    X = np.c_[np.ones_like(t), t - t.mean()]
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ beta
    se_ols = np.sqrt(resid @ resid / (len(y) - 2) / ((t - t.mean()) ** 2).sum())
    sl = []
    for _ in range(nmc):
        yy = y + rng.normal(0, s)
        sl.append(np.linalg.lstsq(X, yy, rcond=None)[0][1])
    se_meas = np.std(sl)
    # lag-1 autocorrelation of residuals for effective sample size
    r1 = np.corrcoef(resid[:-1], resid[1:])[0, 1]
    neff = len(y) * (1 - r1) / (1 + r1) if r1 > 0 else len(y)
    se_ar = se_ols * np.sqrt((len(y) - 2) / max(neff - 2, 1))
    return dict(slope=float(beta[1]), se_ols=float(se_ols), se_meas=float(se_meas), r1=float(r1),
                se_total=float(np.sqrt(max(se_ar, se_ols) ** 2 + se_meas ** 2)))

gg = glob_[(glob_.start_dates >= 2000) & (glob_.start_dates <= 2023)]
tr = trend_mc(gg['gt'].values, gg.gt_err.values, gg.start_dates.values)
trm = trend_mc(gg.mwe.values, gg.mwe_err.values, gg.start_dates.values)
summary['global_trend_gt_per_yr2'] = tr
summary['global_trend_mwe_per_yr2'] = trm
ogg = og.loc[2000:2023]
summary['glambie2024_trend_gt_per_yr2'] = trend_mc(ogg.combined_gt.values, ogg.combined_gt_errors.values, ogg.index.values.astype(float))
p1 = gg[gg.start_dates <= 2011]; p2 = gg[gg.start_dates >= 2012]
summary['two_period'] = dict(p1_mean=float(p1['gt'].mean()), p1_err=float(np.sqrt((p1.gt_err ** 2).sum()) / len(p1)),
                             p2_mean=float(p2['gt'].mean()), p2_err=float(np.sqrt((p2.gt_err ** 2).sum()) / len(p2)))
tp = summary['two_period']
tp['increase_pct'] = 100 * (tp['p2_mean'] / tp['p1_mean'] - 1)
reg_tr = []
for rid, c in cal.items():
    c = c[(c.start_dates >= 2000) & (c.start_dates <= 2023)]
    t = trend_mc(c['gt'].values, c.gt_err.values, c.start_dates.values, nmc=1000)
    tm = trend_mc(c.mwe.values, c.mwe_err.values, c.start_dates.values, nmc=1000)
    reg_tr.append(dict(region_id=rid, region=L.REGION_NAMES[rid], slope_gt=t['slope'], se_gt=t['se_total'],
                       slope_mwe=tm['slope'], se_mwe=tm['se_total'],
                       p1_mwe=c.mwe[c.start_dates <= 2011].mean(), p2_mwe=c.mwe[c.start_dates >= 2012].mean()))
reg_tr = pd.DataFrame(reg_tr)
reg_tr.to_csv(os.path.join(OUT, 'regional_trends.csv'), index=False)

# extremes
gg2 = gg.sort_values('gt')
summary['most_negative_years'] = gg2[['start_dates', 'gt', 'gt_err']].head(5).to_dict('records')
summary['least_negative_years'] = gg2[['start_dates', 'gt', 'gt_err']].tail(3).to_dict('records')

# uncertainty budget: share of global variance from each region (2000-2023 total)
allc = pd.concat(cal.values())
allc = allc[(allc.start_dates >= 2000) & (allc.start_dates <= 2023)]
budget = allc.groupby('region_id').apply(lambda d: (d.gt_err ** 2).sum())
budget = (budget / budget.sum()).sort_values(ascending=False)
summary['variance_share'] = {L.REGION_NAMES[k]: float(v) for k, v in budget.items()}

json.dump(summary, open(os.path.join(OUT, 'validation_summary.json'), 'w'), indent=2, default=float)
pd.set_option('display.width', 250)
print(hyb.round(3).to_string()); print(json.dumps(summary, indent=1, default=float)); print(sens.round(1).to_string()); print(lit.round(2).to_string())
print(reg_tr.round(3).to_string())
