import sys; sys.path.insert(0,'./code')
from glambie_recon import *
import pickle
inp=load_inputs()
ann={}; res={}
for rid in range(1,20):
    r=reconcile_region(rid,inp); res[rid]=r; ann[rid]=annualise(r)
    o=official(rid); o=o.assign(year=np.round(o.start_dates).astype(int)).set_index('year')
    a=ann[rid].set_index('year')
    print(rid,REGNAME[rid],'mine %.3f  off %.3f  corr %.2f rmse %.3f'%(a.mwe.mean(),o.combined_mwe.mean(),np.corrcoef(a.mwe,o.combined_mwe.loc[a.index])[0,1],np.sqrt(((a.mwe-o.combined_mwe.loc[a.index])**2).mean())))
pickle.dump(ann,open('./outputs/ann.pkl','wb'))
