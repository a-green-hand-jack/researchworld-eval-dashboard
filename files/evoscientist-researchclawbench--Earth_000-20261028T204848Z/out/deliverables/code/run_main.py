"""Main driver: runs the reconciliation (main configuration + sensitivity variants),
derives structural uncertainty, writes all intermediate products to outputs/."""
import sys, os, json, warnings
sys.path.insert(0, 'code')
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import recon
from recon import REGIONS, LABELS

OUT = 'outputs'
for d in ['hydrological_years', 'calendar_years', 'variants']:
    os.makedirs(f'{OUT}/{d}', exist_ok=True)

VARIANTS = {
    'main': {},
    'invvar_weights': {'group_weighting': 'invvar'},
    'yearwise_offsets': {'offset_mode': 'yearwise'},
    'mean_offset_extrapolation': {'extrap': 'mean'},
    'linear_calendar': {'calendar_seasonal': 'linear'},
    'rho_790': {'rho': 790.0},
    'rho_910': {'rho': 910.0},
    'no_altimetry': {'exclude_groups': ('altimetry',)},
    'no_gravimetry': {'exclude_groups': ('gravimetry',)},
    'no_demdiff_glac': {'exclude_groups': ('demdiff_and_glaciological',)},
    'gravimetry_everywhere': {'grav_everywhere': True},
    'with_hybrids': {'include_hybrid': True},
}
# methodological-choice ensemble used for the structural uncertainty
STRUCT = ['main', 'invvar_weights', 'yearwise_offsets', 'mean_offset_extrapolation']

results = {}
for name, cfg in VARIANTS.items():
    regions = list(REGIONS)
    hy, cal, gl, meta = {}, {}, None, {}
    for rid in regions:
        try:
            h, m = recon.run_region(rid, cfg)
            if np.isnan(h.mwe.values).all():
                raise ValueError('empty')
            hy[rid] = h; meta[rid] = m
            cal[rid] = recon.to_calendar(rid, h, m['anom'], m['clim'], cfg)
        except Exception as e:          # region has no data left in this variant (e.g. leave-one-group-out)
            hy[rid] = None; cal[rid] = None; meta[rid] = None
    results[name] = dict(hy=hy, cal=cal, meta=meta)
    print('ran', name, 'regions available:', sum(c is not None for c in cal.values()))

years = np.arange(2000, 2024)

def global_from(cal, fallback=None):
    tot = pd.Series(0.0, index=years); n = 0
    for rid in REGIONS:
        c = cal[rid] if cal[rid] is not None else (fallback[rid] if fallback else None)
        x = c.loc[years, 'gt']
        if fallback is not None:
            x = x.fillna(fallback[rid].loc[years, 'gt'])
        tot += x
    return tot

# ------------------------------------------------------------------ structural uncertainty
main = results['main']
reg_struct_gt = {}
for rid in REGIONS:
    arr = np.array([results[v]['cal'][rid].loc[years, 'gt'].values for v in STRUCT])
    reg_struct_gt[rid] = arr.std(axis=0, ddof=1)

# ------------------------------------------------------------------ write main products
regional_rows = []
for rid, name in REGIONS.items():
    h = main['hy'][rid].copy()
    h.to_csv(f'{OUT}/hydrological_years/{rid}_{name}.csv')
    c = main['cal'][rid].loc[years].copy()
    c['gt_err_struct'] = reg_struct_gt[rid]
    c['gt_err_total'] = np.sqrt(c.gt_err ** 2 + c.gt_err_struct ** 2)
    fac = c.area * 1e6 * recon.RHO_W / 1e12
    c['mwe_err_struct'] = c.gt_err_struct / fac
    c['mwe_err_total'] = c.gt_err_total / fac
    c.to_csv(f'{OUT}/calendar_years/{rid}_{name}.csv')
    main['cal'][rid] = c

def cum_err(c, sl=slice(None), col='gt'):
    """uncertainty of the cumulative change: random part in quadrature, systematic & structural linearly"""
    cc = c.loc[sl]
    r = np.sqrt(np.sum(cc[f'{col}_err_rand' if col == 'gt' else 'err_rand'] ** 2))
    s = np.sum(cc[f'{col}_err_sys' if col == 'gt' else 'err_sys'])
    st = np.sum(cc[f'{col}_err_struct'])
    return np.sqrt(r ** 2 + s ** 2 + st ** 2)

glob_rows = []
G = pd.DataFrame(index=years)
G['gt'] = sum(main['cal'][r]['gt'] for r in REGIONS)
G['area'] = sum(main['cal'][r]['area'] for r in REGIONS)
for comp in ['gt_err_rand', 'gt_err_sys', 'gt_err_struct', 'gt_err', 'gt_err_total']:
    G[comp] = np.sqrt(sum(main['cal'][r][comp] ** 2 for r in REGIONS))
fac = G.area * 1e6 * recon.RHO_W / 1e12
G['mwe'] = G['gt'] / fac
G['mwe_err'] = G.gt_err / fac
G['mwe_err_total'] = G.gt_err_total / fac
G['sle_mm'] = -G['gt'] / 362.5
G['sle_mm_err'] = G.gt_err_total / 362.5
G.index.name = 'year'
G.to_csv(f'{OUT}/global_calendar_years.csv')

def period_stats(c, y0, y1):
    sl = slice(y0, y1); n = y1 - y0 + 1
    cum = c.loc[sl, 'gt'].sum(); e = cum_err(c, sl)
    return cum, e, cum / n, e / n

official = {}
for rid, name in REGIONS.items():
    o = pd.read_csv(f'{recon.RES}/calendar_years/{rid}_{name}.csv')
    o.index = np.floor(o.start_dates + 1e-6).astype(int)
    official[rid] = o.loc[years]
og = pd.read_csv(f'{recon.RES}/calendar_years/0_global.csv'); og.index = np.floor(og.start_dates + 1e-6).astype(int)
official[0] = og.loc[years]

for rid, name in REGIONS.items():
    c = main['cal'][rid]
    cum, e, rate, erate = period_stats(c, 2000, 2023)
    _, _, r1, e1 = period_stats(c, 2000, 2011)
    _, _, r2, e2 = period_stats(c, 2012, 2023)
    a = c.area.mean()
    o = official[rid]
    groups = [g for g in ['altimetry', 'gravimetry', 'demdiff_and_glaciological'] if g + '_mwe' in main['hy'][rid]]
    regional_rows.append(dict(region_id=rid, region=LABELS[rid], area_2000_km2=c.loc[2000, 'area'],
        n_groups=len(groups), groups='+'.join(g[:4] for g in groups),
        n_datasets=len(main['meta'][rid]['used']),
        rate_gt=rate, rate_gt_err=erate, rate_mwe=rate * 1e12 / (a * 1e6 * recon.RHO_W), rate_mwe_err=erate * 1e12 / (a * 1e6 * recon.RHO_W),
        cum_gt=cum, cum_gt_err=e, rate_2000_2011=r1, err_2000_2011=e1, rate_2012_2023=r2, err_2012_2023=e2,
        off_rate_gt=o.combined_gt.mean(), off_rate_mwe=o.combined_mwe.mean(),
        r_vs_official=np.corrcoef(c.mwe, o.combined_mwe)[0, 1],
        rmsd_vs_official_mwe=np.sqrt(np.mean((c.mwe - o.combined_mwe) ** 2)),
        mean_err_mwe=c.mwe_err_total.mean(), off_mean_err_mwe=o.combined_mwe_errors.mean()))
RS = pd.DataFrame(regional_rows)
RS.to_csv(f'{OUT}/regional_summary.csv', index=False)

# global cumulative: regional cumulative errors combined in quadrature
def global_period(y0, y1):
    sl = slice(y0, y1); n = y1 - y0 + 1
    cum = G.loc[sl, 'gt'].sum()
    e = np.sqrt(sum(cum_err(main['cal'][r], sl) ** 2 for r in REGIONS))
    return cum, e, cum / n, e / n
gsum = {}
for (y0, y1) in [(2000, 2023), (2000, 2011), (2012, 2023), (2000, 2019), (2006, 2016), (2000, 2009), (2010, 2019)]:
    cum, e, rate, erate = global_period(y0, y1)
    ocum = official[0].loc[y0:y1, 'combined_gt'].sum()
    gsum[f'{y0}-{y1}'] = dict(cum_gt=cum, cum_err=e, rate_gt=rate, rate_err=erate,
                              sle_mm=-cum / 362.5, sle_err=e / 362.5, official_cum_gt=ocum, official_rate=ocum / (y1 - y0 + 1))
area_mean = G.area.mean()
gsum['2000-2023']['rate_mwe'] = gsum['2000-2023']['rate_gt'] * 1e12 / (area_mean * 1e6 * recon.RHO_W)
gsum['2000-2023']['rate_mwe_err'] = gsum['2000-2023']['rate_err'] * 1e12 / (area_mean * 1e6 * recon.RHO_W)

# acceleration (OLS on annual series; MC over random errors)
rng = np.random.default_rng(42)
def accel(series, err_rand, y0, y1):
    sl = slice(y0, y1); x = np.arange(y0, y1 + 1); y = series.loc[sl].values; er = err_rand.loc[sl].values
    p = np.polyfit(x, y, 1)
    res = y - np.polyval(p, x); se = np.sqrt(np.sum(res ** 2) / (len(x) - 2) / np.sum((x - x.mean()) ** 2))
    mc = [np.polyfit(x, y + rng.normal(0, er), 1)[0] for _ in range(2000)]
    return dict(slope_gt_per_yr2=p[0], slope_se=se, slope_mc_sd=np.std(mc),
                slope_per_decade=10 * p[0], slope_per_decade_err=10 * np.sqrt(se ** 2 + np.std(mc) ** 2))
gsum['acceleration_2000_2023'] = accel(G['gt'], G.gt_err_rand, 2000, 2023)
gsum['acceleration_2000_2019'] = accel(G['gt'], G.gt_err_rand, 2000, 2019)
gsum['acceleration_official_2000_2023'] = accel(official[0].combined_gt, official[0].combined_gt_errors * 0, 2000, 2023)
gsum['ratio_2012_2023_vs_2000_2011'] = gsum['2012-2023']['rate_gt'] / gsum['2000-2011']['rate_gt']
gsum['official_ratio_2012_2023_vs_2000_2011'] = official[0].loc[2012:2023, 'combined_gt'].mean() / official[0].loc[2000:2011, 'combined_gt'].mean()
gsum['validation_global'] = dict(r=float(np.corrcoef(G['gt'], official[0].combined_gt)[0, 1]),
                                 rmsd_gt=float(np.sqrt(np.mean((G['gt'] - official[0].combined_gt) ** 2))),
                                 bias_gt=float(np.mean(G['gt'] - official[0].combined_gt)),
                                 frac_years_within_combined_unc=float(np.mean(np.abs(G['gt'] - official[0].combined_gt) <
                                     np.sqrt(G.gt_err_total ** 2 + official[0].combined_gt_errors ** 2))))
json.dump(gsum, open(f'{OUT}/global_summary.json', 'w'), indent=2, default=float)

# ------------------------------------------------------------------ variants summary
vrows = []
for v in VARIANTS:
    cal = results[v]['cal']
    gl = global_from(cal, fallback=main['cal'])
    nmiss = sum(cal[r] is None for r in REGIONS)
    row = dict(variant=v, regions_missing_filled_with_main=nmiss, global_rate_2000_2023=gl.mean(),
               global_cum=gl.sum(), r_vs_main=np.corrcoef(gl, G['gt'])[0, 1], r_vs_official=np.corrcoef(gl, official[0].combined_gt)[0, 1],
               diff_vs_main_pct=100 * (gl.sum() - G['gt'].sum()) / abs(G['gt'].sum()))
    vrows.append(row)
    pd.DataFrame({rid: (cal[rid].loc[years, 'gt'] if cal[rid] is not None else np.nan) for rid in REGIONS}).assign(global_gt=gl).to_csv(f'{OUT}/variants/{v}_calendar_gt.csv')
VS = pd.DataFrame(vrows); VS.to_csv(f'{OUT}/variants_summary.csv', index=False)

# leave-one-group-out per region (only regions where the group exists and >=2 groups)
logo = []
for rid in REGIONS:
    groups = [g for g in ['altimetry', 'gravimetry', 'demdiff_and_glaciological'] if g + '_mwe' in main['hy'][rid]]
    if len(groups) < 2:
        continue
    base = main['cal'][rid].loc[years, 'mwe']
    for g, v in [('altimetry', 'no_altimetry'), ('gravimetry', 'no_gravimetry'), ('demdiff_and_glaciological', 'no_demdiff_glac')]:
        if g not in groups or results[v]['cal'][rid] is None:
            continue
        alt = results[v]['cal'][rid].loc[years, 'mwe']
        mk = alt.notna().values
        if mk.sum() < 3:
            continue
        logo.append(dict(region_id=rid, region=LABELS[rid], left_out=g, n_years=int(mk.sum()), main_rate_mwe=base[mk].mean(), logo_rate_mwe=alt[mk].mean(),
                         diff_mwe=alt[mk].mean() - base[mk].mean(), r=np.corrcoef(base[mk], alt[mk])[0, 1],
                         main_err=main['cal'][rid].loc[years, 'mwe_err_total'].mean()))
pd.DataFrame(logo).to_csv(f'{OUT}/leave_one_group_out.csv', index=False)

# ------------------------------------------------------------------ data-group agreement
agree = []
for rid in REGIONS:
    h = main['hy'][rid]
    groups = [g for g in ['altimetry', 'gravimetry', 'demdiff_and_glaciological'] if g + '_mwe' in h]
    if len(groups) < 2:
        continue
    common = np.all([h[g + '_covered'].values for g in groups], axis=0)
    n = common.sum()
    if n < 3:
        continue
    stats = {}
    for g in groups:
        x = h.loc[common, g + '_mwe']; e = h.loc[common, g + '_err']
        stats[g] = (x.mean(), np.sqrt(np.mean(e ** 2)) / np.sqrt(max(1, n / 3.0)))
    comb = h.loc[common, 'mwe'].mean()
    for g in groups:
        agree.append(dict(region_id=rid, region=LABELS[rid], group=g, n_common_years=n, first=h.index[common].min(),
                          last=h.index[common].max(), mean_mwe=stats[g][0], err_mwe=stats[g][1], combined_mean=comb,
                          z=(stats[g][0] - comb) / stats[g][1]))
pd.DataFrame(agree).to_csv(f'{OUT}/group_agreement.csv', index=False)

# dataset usage table
use = []
for rid in REGIONS:
    for (src, ds, team, ann, ntr) in main['meta'][rid]['used']:
        use.append(dict(region_id=rid, source=src, dataset=ds, team=team, annual_resolving=ann, n_trend_rows=ntr))
pd.DataFrame(use).to_csv(f'{OUT}/datasets_used_main.csv', index=False)

print(RS[['region_id', 'region', 'rate_gt', 'rate_gt_err', 'rate_mwe', 'off_rate_gt', 'r_vs_official']].round(3).to_string())
print(json.dumps({k: v for k, v in gsum.items()}, indent=1, default=float)[:3000])
print(VS.round(3).to_string())
