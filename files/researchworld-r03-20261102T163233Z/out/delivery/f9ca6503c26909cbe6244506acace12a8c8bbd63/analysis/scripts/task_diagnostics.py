"""Task and model error diagnostics from saved, leakage-safe model splits."""
import json,pathlib
import numpy as np
import pandas as pd
from methods import moments,predict
ROOT=pathlib.Path(__file__).resolve().parents[1]
x=pd.read_csv(ROOT/'data/mteb.csv',index_col=0)
splits=json.load(open(ROOT/'results/mteb_random/splits.json'))
# Full-cohort correlations are descriptive, never reused as training inputs.
x.corr(min_periods=20).to_csv(ROOT/'results/mteb_descriptive_correlation.csv')
mask=x.notna().to_numpy(float)
pd.DataFrame(mask.T@mask,index=x.columns,columns=x.columns).to_csv(ROOT/'results/mteb_pair_counts.csv')
rows=[]
for split in splits:
 train=x.loc[split['train_names']].to_numpy();test=x.loc[split['test_names']].to_numpy();mu,cov=moments(train,split['alpha']);post=cov.copy();q=[];remain=list(range(len(x.columns)))
 for step in range(16):
  gain=np.sum(post[:,remain]**2,axis=0)/np.maximum(np.diag(post)[remain],1e-12);j=remain[int(np.argmax(gain))];q.append(j);remain.remove(j)
  post-=np.outer(post[:,j],post[j,:])/max(post[j,j],1e-12);post=(post+post.T)/2
 for k in [1,2,4,8,16]:
  for kind in ['covariance','ridge']:
   pp=predict(mu,cov,test,q[:k],kind=kind,train=train,ridge=split['ridge'])
   for j,t in enumerate(x.columns):
    rows.append(dict(seed=split['seed'],k=k,method=kind,task=t,queried=j in q[:k],mae=float(np.abs(pp[:,j]-test[:,j]).mean()),n_models=len(test)))
pd.DataFrame(rows).to_csv(ROOT/'results/mteb_task_errors.csv',index=False)
print('Task diagnostics saved',flush=True)
