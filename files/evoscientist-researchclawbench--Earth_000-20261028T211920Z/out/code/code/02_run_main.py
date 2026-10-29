"""Run the main reconciliation and write regional/global time series to outputs/."""
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import glambie_lib as L

OUT = os.path.join(L.ROOT, 'outputs')
os.makedirs(os.path.join(OUT, 'hydrological_years'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'calendar_years'), exist_ok=True)

res, cal, glob_ = L.run_all()

# ---- hydrological-year tables (per group + combined)
long_rows = []
for rid, r in res.items():
    df = pd.DataFrame(dict(start_dates=r['starts'], end_dates=r['starts'] + 1, glacier_area=r['area']))
    df['combined_mwe'] = r['mwe']; df['combined_mwe_errors'] = r['err']
    df['combined_gt'] = r['mwe'] * r['area'] / 1000; df['combined_gt_errors'] = r['err'] * r['area'] / 1000
    df['n_groups'] = r['ngroups']; df['intergroup_sd_mwe'] = r['spread']
    for g, v in r['groups'].items():
        df[g + '_mwe'] = v['mwe']; df[g + '_mwe_errors'] = v['err']; df[g + '_n'] = v['n']
        df[g + '_gt'] = v['mwe'] * r['area'] / 1000; df[g + '_gt_errors'] = v['err'] * r['area'] / 1000
    df = df[np.isfinite(df.combined_mwe)]
    df.to_csv(os.path.join(OUT, 'hydrological_years', f'{rid}_{L.REGION_NAMES[rid].replace(" ", "_").replace("&", "and")}.csv'), index=False)
    for ds in r['datasets']:
        if 'hy' not in ds:
            continue
        for a, v, e, x in zip(r['starts'], ds['hy'], ds['hy_err'], ds.get('extrap', np.zeros(len(r['starts'])))):
            if np.isfinite(v):
                long_rows.append(dict(region_id=rid, method=ds['method'], group=ds['group'], dataset=ds['name'],
                                      kind=ds['kind'], var_source=ds.get('var_source', ''), hy_start=a, mwe=v,
                                      mwe_err=e, extrap_years=x))
pd.DataFrame(long_rows).to_csv(os.path.join(OUT, 'dataset_annual_series_long.csv'), index=False)

# ---- calendar years
allc = []
for rid, c in cal.items():
    c.to_csv(os.path.join(OUT, 'calendar_years', f'{rid}_{L.REGION_NAMES[rid].replace(" ", "_").replace("&", "and")}.csv'), index=False)
    allc.append(c)
allc = pd.concat(allc)
allc.to_csv(os.path.join(OUT, 'regional_calendar_all.csv'), index=False)
glob_.to_csv(os.path.join(OUT, 'global_calendar.csv'), index=False)

with open(os.path.join(OUT, 'main_results.pkl'), 'wb') as f:
    pickle.dump(dict(res=res, cal=cal, glob=glob_), f)

# ---- summary table: 2000-2023 regional rates
rows = []
for rid, c in cal.items():
    c = c[(c.start_dates >= 2000) & (c.start_dates <= 2023)]
    n = len(c)
    rows.append(dict(region_id=rid, region=L.REGION_NAMES[rid], area_2000=c.glacier_area.iloc[0],
                     mean_mwe_yr=c.mwe.mean(), mean_mwe_yr_err=np.sqrt((c.mwe_err ** 2).sum()) / n,
                     mean_gt_yr=c["gt"].mean(), mean_gt_yr_err=np.sqrt((c.gt_err ** 2).sum()) / n,
                     cum_mwe=c.mwe.sum(), cum_mwe_err=np.sqrt((c.mwe_err ** 2).sum()),
                     cum_gt=c["gt"].sum(), cum_gt_err=np.sqrt((c.gt_err ** 2).sum()),
                     rate_2000_2011_gt=c["gt"][c.start_dates < 2012].mean(), rate_2012_2023_gt=c["gt"][c.start_dates >= 2012].mean()))
g = glob_[(glob_.start_dates >= 2000) & (glob_.start_dates <= 2023)]
n = len(g)
rows.append(dict(region_id=0, region='Global', area_2000=g.glacier_area.iloc[0], mean_mwe_yr=g.mwe.mean(),
                 mean_mwe_yr_err=np.sqrt((g.mwe_err ** 2).sum()) / n, mean_gt_yr=g["gt"].mean(),
                 mean_gt_yr_err=np.sqrt((g.gt_err ** 2).sum()) / n, cum_mwe=g.mwe.sum(),
                 cum_mwe_err=np.sqrt((g.mwe_err ** 2).sum()), cum_gt=g["gt"].sum(), cum_gt_err=np.sqrt((g.gt_err ** 2).sum()),
                 rate_2000_2011_gt=g["gt"][g.start_dates < 2012].mean(), rate_2012_2023_gt=g["gt"][g.start_dates >= 2012].mean()))
summ = pd.DataFrame(rows)
summ['cum_sle_mm'] = -summ.cum_gt / 362.5
summ['cum_sle_mm_err'] = summ.cum_gt_err / 362.5
summ.to_csv(os.path.join(OUT, 'summary_rates_2000_2023.csv'), index=False)
pd.set_option('display.width', 250)
print(summ.round(3).to_string())
print(glob_.round(3).to_string())
