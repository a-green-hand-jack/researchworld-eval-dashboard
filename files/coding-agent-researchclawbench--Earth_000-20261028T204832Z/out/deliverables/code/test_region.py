import sys; sys.path.insert(0,'/work/code')
import pandas as pd, numpy as np
from glambie_lib import *
pd.set_option('display.width',250)
reg=sys.argv[1]
out,meta=reconcile_region(reg)
print(meta['groups'], meta['group_offsets'], meta['sig_struct'], meta['excl_grav'])
for s in meta['solutions']:
    print(s['group'], s['file'][:50], s['resolution'], s['annual'].notna().sum(), len(s['periods']), round(s['w'],2))
off=pd.read_csv(f'/work/data/glambie/results/hydrological_years/{reg}.csv')
cols=['start','gt','sig_gt','sig_rand_gt','sig_sys_gt','n_groups']+[c for c in out.columns if c.endswith('_mwe')]
o=out[cols].copy()
o['off_gt']=np.nan; o['off_err']=np.nan
for i,r in off.iterrows():
    k=np.argmin(np.abs(o.start-r.start_dates))
    if abs(o.start.iloc[k]-r.start_dates)<0.01:
        o.iloc[k,o.columns.get_loc('off_gt')]=r.combined_gt; o.iloc[k,o.columns.get_loc('off_err')]=r.combined_gt_errors
print(o.round(3).to_string())
cal=to_calendar(reg,out)
print(cal.round(3).T)
