import sys; sys.path.insert(0,'/work/code')
import pandas as pd, numpy as np
from glambie_lib import REGIONS, SHORT
tag = sys.argv[1] if len(sys.argv)>1 else 'main'
R='/work/data/glambie/results'
rows=[]
for r in REGIONS:
    mine=pd.read_csv(f'/work/outputs/{tag}/calendar_{r}.csv',index_col=0)
    off=pd.read_csv(f'{R}/calendar_years/{r}.csv'); off.index=off.start_dates.astype(int)
    offh=pd.read_csv(f'{R}/hydrological_years/{r}.csv')
    used=[g for g in ['altimetry','gravimetry','demdiff_and_glaciological'] if offh[g+'_gt'].notna().any()]
    m=mine.loc[2000:2023]; o=off.loc[2000:2023]
    d=m['gt']-o.combined_gt
    rows.append(dict(region=SHORT[r], mine=m['gt'].mean(), off=o.combined_gt.mean(), diff=d.mean(),
      mine_mwe=m.mwe.mean(), off_mwe=o.combined_mwe.mean(),
      rmse_ann=np.sqrt((d**2).mean()), r=np.corrcoef(m['gt'],o.combined_gt)[0,1],
      sig_mine=m.sig_gt.mean(), sig_off=o.combined_gt_errors.mean(), off_groups='/'.join(u[:4] for u in used)))
df=pd.DataFrame(rows)
pd.set_option('display.width',200)
print(df.round(3).to_string())
g=pd.read_csv(f'/work/outputs/{tag}/calendar_global.csv',index_col=0)
og=pd.read_csv(f'{R}/calendar_years/0_global.csv'); og.index=og.start_dates.astype(int)
print('global mean mine %.1f official %.1f ; cum %.0f vs %.0f; r=%.3f rmse=%.1f'%(g['gt'].mean(),og.combined_gt.mean(),g['gt'].sum(),og.combined_gt.sum(),
   np.corrcoef(g['gt'],og.combined_gt)[0,1], np.sqrt(((g['gt']-og.combined_gt)**2).mean())))
print(pd.DataFrame({'mine':g['gt'],'off':og.combined_gt,'sig':g.sig_gt,'sig_off':og.combined_gt_errors}).round(1).T.to_string())
