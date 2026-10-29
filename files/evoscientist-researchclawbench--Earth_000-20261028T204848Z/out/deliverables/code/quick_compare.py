import sys; sys.path.insert(0,'code')
import recon, pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
cfg = eval(sys.argv[1]) if len(sys.argv)>1 else {}
hy,cal,gl,meta=recon.run_all(cfg)
rows=[]
for rid in recon.REGIONS:
    o=pd.read_csv(f"data/glambie/results/calendar_years/{rid}_{recon.REGIONS[rid]}.csv")
    o['year']=np.floor(o.start_dates+1e-6).astype(int); o=o.set_index('year').loc[2000:2023]
    c=cal[rid].loc[2000:2023]
    m=c.mwe.notna()
    rows.append(dict(rid=rid, n=m.sum(), my_mean=c.mwe[m].mean(), off_mean=o.combined_mwe[m].mean(), r=np.corrcoef(c.mwe[m],o.combined_mwe[m])[0,1],
        rmsd=np.sqrt(((c.mwe[m]-o.combined_mwe[m])**2).mean()), my_err=c.mwe_err[m].mean(), off_err=o.combined_mwe_errors[m].mean(),
        my_gt=c['gt'][m].sum(), off_gt=o.combined_gt[m].sum()))
df=pd.DataFrame(rows); print(df.round(3).to_string())
o=pd.read_csv("data/glambie/results/calendar_years/0_global.csv")
print('global my', gl['gt'].sum().round(1), 'official', o.combined_gt.sum().round(1), 'r', np.corrcoef(gl['gt'], o.combined_gt)[0,1].round(3), 'rmsd', np.sqrt(((gl['gt'].values-o.combined_gt.values)**2).mean()).round(1))
print(pd.DataFrame({'my':gl['gt'].values,'my_e':gl['gt_err'].values,'off':o.combined_gt.values,'off_e':o.combined_gt_errors.values},index=gl.index).round(1).T.to_string())
