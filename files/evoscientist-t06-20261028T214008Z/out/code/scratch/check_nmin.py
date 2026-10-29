import sys; sys.path.insert(0,'code')
import numpy as np, pandas as pd
from lbrobust import data as D
p=pd.read_csv('results/e1_pairs.csv')
nm={'Arena-55k':'arena55k','Arena-140k':'arena140k','MT-Bench-Human':'mt_human','MT-Bench-GPT4':'mt_gpt4'}
rows=[]
for ds,g in p.groupby('dataset'):
    d=D.load(nm.get(ds, ds.replace('NBA-','nba')))
    cnt=np.bincount(d.i,weights=d.n,minlength=d.K)+np.bincount(d.j,weights=d.n,minlength=d.K)
    g=g.copy(); g['nmin']=np.minimum(cnt[g.hi],cnt[g.lo]); rows.append(g)
q=pd.concat(rows); q['grp']=q.dataset.where(~q.dataset.str.startswith('NBA'),'NBA')
q['ratio']=q.neff_drop/q.nmin
q['kz']=q.drop_best/(q.z*np.sqrt(q.nmin))
print(q.groupby('grp')[['ratio','kz']].describe().round(3).to_string())
x=q[(q.z>0.5)]
b=np.polyfit(np.log(x.z*np.sqrt(x.nmin)),np.log(x.drop_best.clip(lower=0.5)),1); print('loglog slope/intercept',b)
print('corr log', np.corrcoef(np.log(x.z*np.sqrt(x.nmin)),np.log(x.drop_best.clip(lower=0.5)))[0,1], 'corr klin', np.corrcoef(np.log(x.klin_drop),np.log(x.drop_best.clip(lower=0.5)))[0,1])
