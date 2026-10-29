"""Additional statistics for the report: correlated-error bounds, period rates, and comparison numbers."""
import sys, os, pickle, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import glambie_lib as L

OUT = os.path.join(L.ROOT, 'outputs')
M = pickle.load(open(os.path.join(OUT, 'main_results.pkl'), 'rb'))
cal, glob_ = M['cal'], M['glob']
allc = pd.concat(cal.values())
allc = allc[(allc.start_dates >= 2000) & (allc.start_dates <= 2023)]
st = {}
# cumulative error: (i) independent in time and space, (ii) fully correlated in time within a region
e_ind = np.sqrt((allc.gt_err ** 2).sum())
e_corr = np.sqrt((allc.groupby('region_id').gt_err.sum() ** 2).sum())
st['cum_err_independent_gt'] = float(e_ind)
st['cum_err_time_correlated_gt'] = float(e_corr)
st['cum_gt'] = float(allc['gt'].sum())
st['mean_rate_err_time_correlated'] = float(e_corr / 24)
og = pd.read_csv(os.path.join(L.RES, 'calendar_years', '0_global.csv'))
og = og[(og.start_dates >= 2000) & (og.start_dates <= 2023)]
g = glob_[(glob_.start_dates >= 2000) & (glob_.start_dates <= 2023)].set_index('start_dates')
o = og.set_index('start_dates')
periods = [(2000, 2004), (2005, 2009), (2010, 2014), (2015, 2019), (2020, 2023), (2000, 2011), (2012, 2023), (2000, 2023)]
rows = []
for a, b in periods:
    s = g.loc[a:b]; so = o.loc[a:b]
    rows.append(dict(period=f'{a}-{b}', ours_gt=s['gt'].mean(), ours_err=np.sqrt((s.gt_err ** 2).sum()) / len(s),
                     ours_mwe=s.mwe.mean(), ours_mwe_err=np.sqrt((s.mwe_err ** 2).sum()) / len(s),
                     glambie_gt=so.combined_gt.mean(), glambie_mwe=so.combined_mwe.mean(),
                     ours_sle_mm_yr=-s['gt'].mean() / 362.5))
per = pd.DataFrame(rows)
per.to_csv(os.path.join(OUT, 'global_period_rates.csv'), index=False)
st['ratio_2023_to_2000_2011_mean'] = float(g.loc[2023, 'gt'] / g.loc[2000:2011, 'gt'].mean())
st['n_years_below_-350'] = int((g['gt'] < -350).sum())
st['years_below_-350'] = [int(y) for y in g.index[g['gt'] < -350]]
# share of loss by region type
pol = [3, 4, 5, 7, 9, 19]
st['share_polar_and_peripheral'] = float(allc[allc.region_id.isin(pol)]['gt'].sum() / allc['gt'].sum())
st['share_alaska'] = float(allc[allc.region_id == 1]['gt'].sum() / allc['gt'].sum())
st['share_top5'] = float(allc.groupby('region_id')['gt'].sum().nsmallest(5).sum() / allc['gt'].sum())
# area weighted annual correlation with GlaMBIE
st['global_annual_r'] = float(np.corrcoef(g['gt'], o.combined_gt)[0, 1])
json.dump(st, open(os.path.join(OUT, 'extra_stats.json'), 'w'), indent=2)
pd.set_option('display.width', 200)
print(json.dumps(st, indent=1)); print(per.round(3).to_string())
# compact global table for report
gt = glob_[(glob_.start_dates >= 2000) & (glob_.start_dates <= 2023)][['start_dates', 'gt', 'gt_err', 'mwe', 'mwe_err']]
gt = gt.merge(og[['start_dates', 'combined_gt', 'combined_gt_errors']], on='start_dates')
gt.to_csv(os.path.join(OUT, 'global_table_for_report.csv'), index=False)
print(gt.round(2).to_string())
