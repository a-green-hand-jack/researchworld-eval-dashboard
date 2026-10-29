import sys; sys.path.insert(0,'./code')
import pandas as pd, glob, os, numpy as np
B='./data/glambie/results/hydrological_years/'
for f in sorted(glob.glob(B+'*.csv'),key=lambda x:int(os.path.basename(x).split('_')[0])):
    d=pd.read_csv(f)
    s=os.path.basename(f)[:-4]
    out=[]
    for g in ['altimetry','gravimetry','demdiff_and_glaciological']:
        c=d[g+'_gt']; ok=c.notna()
        out.append('%s:%d (%.2f-%.2f)'%(g[:4],ok.sum(),d.start_dates[ok].min() if ok.any() else 0, d.end_dates[ok].max() if ok.any() else 0))
    print(s,'area %.0f'%d.glacier_area.mean(),' | '.join(out), 'N=',len(d), d.start_dates.min(), d.end_dates.max())
