import sys; sys.path.insert(0,'./code')
from glambie_recon import *
import pickle
inp=load_inputs()
YEARS=list(range(2000,2024))
reg={}; res={}
for rid in range(1,20):
    res[rid]=reconcile_region(rid,inp); reg[rid]=annualise(res[rid]); reg[rid]['region_id']=rid; reg[rid]['region']=REGNAME[rid]
R=pd.concat(reg.values(),ignore_index=True)
off=pd.concat([official(r).assign(region_id=r) for r in range(1,20)],ignore_index=True)
off['year']=np.round(off.start_dates).astype(int)
R=R.merge(off[['region_id','year','combined_gt','combined_gt_errors','combined_mwe','combined_mwe_errors']].rename(columns=lambda c:c.replace('combined','off')if c.startswith('combined') else c),on=['region_id','year'])
R.to_csv('./outputs/regional_annual.csv',index=False)
# global
g=R.groupby('year').agg(gt=('gt','sum'),gt_off=('off_gt','sum'),area=('area','sum'))
g['gt_err_quad']=R.groupby('year').gt_err.apply(lambda x:np.sqrt((x**2).sum()))
g['gt_err_lin']=R.groupby('year').gt_err.sum()
og=official(0); og['year']=np.round(og.start_dates).astype(int); og=og.set_index('year')
g['gt_official_global']=og.combined_gt; g['gt_err_official']=og.combined_gt_errors
g['mwe']=g['gt']/g['area']*1e3; g['mwe_official']=og.combined_mwe
g['slr_mm']=-g['gt']/362.5
g.to_csv('./outputs/global_annual.csv')
pickle.dump(res,open('./outputs/res.pkl','wb'))
print(g.round(3).to_string())
print('Total 2000-2023 Gt mine %.0f  official-global %.0f  sum-of-official-regions %.0f'%(g['gt'].sum(),g['gt_official_global'].sum(),g['gt_off'].sum()))
print('corr global annual',np.corrcoef(g['gt'],g['gt_official_global'])[0,1],'rmse',np.sqrt(((g['gt']-g['gt_official_global'])**2).mean()))
