"""Result tables, uncertainty aggregation, and validation analyses for the main reconciliation."""
import sys, json
sys.path.insert(0, '/work/code')
import numpy as np
import pandas as pd
from glambie_lib import REGIONS, SHORT, reconcile_region, Area, year_grid, period_weights

OUT = '/work/outputs'
M = f'{OUT}/main'
R = '/work/data/glambie/results'
OCEAN = 362.5e6     # km2 ; 1 mm SLE = 362.5 Gt
pd.set_option('display.width', 220)

cal = {r: pd.read_csv(f'{M}/calendar_{r}.csv', index_col=0).loc[2000:2023] for r in REGIONS}
hyd = {r: pd.read_csv(f'{M}/hydro_{r}.csv') for r in REGIONS}
glob_ = pd.read_csv(f'{M}/calendar_global.csv', index_col=0)


def period_stats(df, y0, y1):
    """Mean rate and its uncertainty over [y0, y1] for one region (random errors independent
    between years, systematic errors fully correlated)."""
    d = df.loc[y0:y1]
    n = len(d)
    cum = d['gt'].sum()
    s_cum = np.sqrt((d.sig_rand_gt ** 2).sum() + d.sig_sys_gt.sum() ** 2)
    cum_m = d.mwe.sum()
    s_cum_m = np.sqrt((d.sig_rand ** 2).sum() + d.sig_sys.sum() ** 2)
    return dict(rate=cum / n, sig_rate=s_cum / n, rate_mwe=cum_m / n, sig_rate_mwe=s_cum_m / n,
                cum=cum, sig_cum=s_cum)


# ---------------------------------------------------------------- regional table
rows = []
for r in REGIONS:
    full = period_stats(cal[r], 2000, 2023)
    a = period_stats(cal[r], 2000, 2011)
    b = period_stats(cal[r], 2012, 2023)
    meta = json.load(open(f'{M}/meta.json'))[r]
    rows.append(dict(region=r, code=SHORT[r], area_2000=cal[r].area.iloc[0], area_2023=cal[r].area.iloc[-1],
                     groups='+'.join(meta['groups']),
                     rate_gt=full['rate'], sig_rate_gt=full['sig_rate'], rate_mwe=full['rate_mwe'],
                     sig_rate_mwe=full['sig_rate_mwe'], cum_gt=full['cum'], sig_cum_gt=full['sig_cum'],
                     rate_0011=a['rate'], sig_0011=a['sig_rate'], rate_1223=b['rate'], sig_1223=b['sig_rate'],
                     mwe_0011=a['rate_mwe'], mwe_1223=b['rate_mwe'],
                     min_year=int(cal[r].mwe.idxmin()), min_mwe=cal[r].mwe.min()))
reg = pd.DataFrame(rows)
tot_cum = reg.cum_gt.sum()
reg['share_pct'] = 100 * reg.cum_gt / tot_cum
reg.to_csv(f'{OUT}/regional_summary.csv', index=False)


# ---------------------------------------------------------------- global
def global_period(y0, y1):
    cum = sum(cal[r].loc[y0:y1, 'gt'].sum() for r in REGIONS)
    s = np.sqrt(sum(period_stats(cal[r], y0, y1)['sig_cum'] ** 2 for r in REGIONS))
    n = y1 - y0 + 1
    area = glob_.loc[y0:y1, 'area'].mean()
    return dict(period=f'{y0}-{y1}', rate=cum / n, sig_rate=s / n, rate_mwe=cum / n * 1000 / area,
                sig_rate_mwe=s / n * 1000 / area, cum=cum, sig_cum=s, sle_mm=-cum / 362.5, sig_sle=s / 362.5)


gp = pd.DataFrame([global_period(*p) for p in [(2000, 2023), (2000, 2011), (2012, 2023), (2000, 2019),
                                                (2000, 2004), (2005, 2009), (2010, 2014), (2015, 2019),
                                                (2006, 2015), (2020, 2023)]])
gp.to_csv(f'{OUT}/global_period_summary.csv', index=False)
print(gp.round(2).to_string())

# global annual table with sea-level equivalent
ga = glob_.loc[2000:2023].copy()
ga['sle_mm'] = -ga['gt'] / 362.5
ga['cum_gt'] = ga['gt'].cumsum()
# cumulative uncertainty through time
cs = []
for y in ga.index:
    cs.append(np.sqrt(sum(period_stats(cal[r], 2000, y)['sig_cum'] ** 2 for r in REGIONS)))
ga['sig_cum_gt'] = cs
ga.to_csv(f'{OUT}/global_annual.csv')

# acceleration: weighted linear trend of annual global mass change (random errors as weights)
yrs = ga.index.values.astype(float)
w = 1 / ga.sig_rand_gt.values ** 2
X = np.vstack([np.ones_like(yrs), yrs - yrs.mean()]).T
cov = np.linalg.inv(X.T @ (X * w[:, None]))
beta = cov @ (X.T @ (w * ga['gt'].values))
res = ga['gt'].values - X @ beta
chi2 = np.sum(w * res ** 2) / (len(yrs) - 2)
se = np.sqrt(np.diag(cov) * max(1, chi2))
ols = np.polyfit(yrs, ga['gt'].values, 1, cov=True)
acc = dict(wls_slope=beta[1], wls_se=se[1], ols_slope=ols[0][0], ols_se=np.sqrt(ols[1][0, 0]),
           diff_periods=gp.set_index('period').loc['2012-2023', 'rate'] - gp.set_index('period').loc['2000-2011', 'rate'],
           sig_diff=np.hypot(gp.set_index('period').loc['2012-2023', 'sig_rate'], gp.set_index('period').loc['2000-2011', 'sig_rate']))
m19 = (yrs <= 2019)
o19 = np.polyfit(yrs[m19], ga['gt'].values[m19], 1, cov=True)
acc['ols_slope_2000_2019'] = o19[0][0]; acc['ols_se_2000_2019'] = np.sqrt(o19[1][0, 0])
og_ = pd.read_csv(f'{R}/calendar_years/0_global.csv')
oo = np.polyfit(og_.start_dates.values, og_.combined_gt.values, 1, cov=True)
acc['official_ols_slope'] = oo[0][0]; acc['official_ols_se'] = np.sqrt(oo[1][0, 0])
acc['pct_increase'] = 100 * acc['diff_periods'] / gp.set_index('period').loc['2000-2011', 'rate']
json.dump({k: float(v) for k, v in acc.items()}, open(f'{OUT}/acceleration.json', 'w'), indent=1)
print('acceleration', {k: round(v, 2) for k, v in acc.items()})

# ---------------------------------------------------------------- comparison with official GlaMBIE
comp = []
og = pd.read_csv(f'{R}/calendar_years/0_global.csv'); og.index = og.start_dates.astype(int)
for r in REGIONS + ['global']:
    if r == 'global':
        m = ga; o = og
    else:
        m = cal[r]
        o = pd.read_csv(f'{R}/calendar_years/{r}.csv'); o.index = o.start_dates.astype(int)
    o = o.loc[2000:2023]
    d = m['gt'] - o.combined_gt
    dm = m.mwe - o.combined_mwe
    z = d / np.sqrt(m.sig_gt ** 2 + o.combined_gt_errors ** 2)
    comp.append(dict(region=SHORT.get(r, 'GLOBAL'), mine_rate=m['gt'].mean(), official_rate=o.combined_gt.mean(),
                     diff_rate=d.mean(), mine_mwe=m.mwe.mean(), official_mwe=o.combined_mwe.mean(), diff_mwe=dm.mean(),
                     r=np.corrcoef(m['gt'], o.combined_gt)[0, 1], rmse_gt=np.sqrt((d ** 2).mean()),
                     rmse_mwe=np.sqrt((dm ** 2).mean()), mean_sig_mine=m.sig_gt.mean(),
                     mean_sig_official=o.combined_gt_errors.mean(), frac_within_1sig=(np.abs(z) < 1).mean()))
comp = pd.DataFrame(comp)
comp.to_csv(f'{OUT}/comparison_official.csv', index=False)
print(comp.round(3).to_string())

# ---------------------------------------------------------------- leave-one-group-out
logo = []
for r in REGIONS:
    full, meta = reconcile_region(r)
    gl = meta['groups']
    if len(gl) < 2:
        continue
    for g in gl:
        wo, _ = reconcile_region(r, dict(drop_groups=(g,)))
        own = full[f'{g}_mwe']
        own_s = full[f'{g}_sig']
        m = own.notna() & wo.mwe.notna()
        # mean over the common years with partially correlated errors: use group random/systematic split
        n = m.sum()
        d = (own[m] - wo.mwe[m]).mean()
        s_own = np.sqrt((full[f'{g}_sig_rand'][m] ** 2).sum() / n ** 2 + full[f'{g}_sig_sys'][m].mean() ** 2)
        s_wo = np.sqrt((wo.sig_rand[m] ** 2).sum() / n ** 2 + wo.sig_sys[m].mean() ** 2)
        z = d / np.hypot(s_own, s_wo)
        ra = np.corrcoef(own[m], wo.mwe[m])[0, 1]
        da = own[m] - wo.mwe[m]
        za = da / np.sqrt(own_s[m] ** 2 + wo.sig[m] ** 2)
        logo.append(dict(region=SHORT[r], group=g, n_years=int(n), mean_diff_mwe=d, sig_diff=np.hypot(s_own, s_wo),
                         z_mean=z, r_annual=ra, rms_z_annual=np.sqrt(np.mean(za ** 2)),
                         frac_annual_within_1sig=np.mean(np.abs(za) < 1)))
logo = pd.DataFrame(logo)
logo.to_csv(f'{OUT}/leave_one_group_out.csv', index=False)
print(logo.round(3).to_string())
print('LOGO: rms z_mean = %.2f ; median r = %.2f ; median rms_z_annual = %.2f; mean frac within 1 sigma = %.2f' % (
    np.sqrt(np.mean(logo.z_mean ** 2)), logo.r_annual.median(), logo.rms_z_annual.median(), logo.frac_annual_within_1sig.mean()))

# ---------------------------------------------------------------- hybrid (held-out) comparison
hyb = []
for r in REGIONS:
    full, meta = reconcile_region(r)
    for s in meta['solutions']:
        if s['group'] != 'HYB':
            continue
        if s['annual'].notna().sum() >= 3:
            a = s['annual']
            m = a.notna() & full.mwe.notna()
            d = (a[m] - full.mwe[m])
            hyb.append(dict(region=SHORT[r], author=s['author'], file=s['file'], kind='annual', n=int(m.sum()),
                            hybrid_mean=a[m].mean(), recon_mean=full.mwe[m].mean(), diff=d.mean(),
                            r=np.corrcoef(a[m], full.mwe[m])[0, 1], rmse=np.sqrt((d ** 2).mean())))
        for (t0, t1, v, e) in s['periods']:
            wts = period_weights(t0, t1, full.start.values)
            if wts.sum() < 0.9 * (t1 - t0):
                continue
            rec = np.nansum(wts * full.mwe.values) / (t1 - t0)
            hyb.append(dict(region=SHORT[r], author=s['author'], file=s['file'], kind=f'period {t0:.1f}-{t1:.1f}', n=1,
                            hybrid_mean=v / (t1 - t0), recon_mean=rec, diff=v / (t1 - t0) - rec, r=np.nan, rmse=np.nan,
                            sig_hybrid=e / (t1 - t0)))
hyb = pd.DataFrame(hyb)
hyb.to_csv(f'{OUT}/hybrid_comparison.csv', index=False)
print(hyb.round(3).to_string())
print(hyb.groupby('author')[['diff', 'r', 'rmse']].agg(['mean', 'median', 'count']).round(3))

# ---------------------------------------------------------------- literature comparison (global)
lit = pd.DataFrame([
    dict(study='Hugonnet et al. (2021)', period='2000-2004', value=-227, sig95=25),
    dict(study='Hugonnet et al. (2021)', period='2005-2009', value=-257, sig95=22),
    dict(study='Hugonnet et al. (2021)', period='2010-2014', value=-284, sig95=23),
    dict(study='Hugonnet et al. (2021)', period='2000-2019', value=-267, sig95=16),
    dict(study='Zemp et al. (2019)', period='2006-2015', value=-332, sig95=144),
])
gpi = gp.set_index('period')
lit['this_study'] = [gpi.loc[p, 'rate'] for p in lit.period]
lit['this_study_sig95'] = [1.96 * gpi.loc[p, 'sig_rate'] for p in lit.period]
og_rates = {p: og.loc[int(p[:4]):int(p[5:]), 'combined_gt'].mean() for p in lit.period}
lit['glambie_official'] = [og_rates[p] for p in lit.period]
lit.to_csv(f'{OUT}/literature_comparison.csv', index=False)
print(lit.round(1).to_string())

# Zemp 2019 regional 2006-2016 (m w.e./yr)
zemp = dict(ALA=-0.85, WNA=-0.83, ACN=-0.57, ACS=-0.57, GRL=-0.63, ISL=-0.50, SJM=-0.47, SCA=-0.49, RUA=-0.47,
            ASN=-0.37, CEU=-0.87, CAU=-0.90, ASC=-0.15, ASW=-0.03, ASE=-0.35, TRP=-1.03, SAN=-1.18, NZL=-0.68, ANT=-0.11)
zr = pd.DataFrame([dict(code=SHORT[r], zemp2019=zemp[SHORT[r]], this_study=cal[r].loc[2006:2015, 'mwe'].mean(),
                        official=pd.read_csv(f'{R}/calendar_years/{r}.csv').set_index('start_dates').loc[2006.0:2015.0, 'combined_mwe'].mean())
                   for r in REGIONS])
zr.to_csv(f'{OUT}/zemp2019_regional_comparison.csv', index=False)
print(zr.round(2).to_string())
