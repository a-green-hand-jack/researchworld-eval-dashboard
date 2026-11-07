"""Adjacent-rank heterogeneity and cluster sandwich standard errors.
Not a bootstrap substitute or calibrated simultaneous confidence procedure.
"""
import json,time
import numpy as np,pandas as pd
from scipy.special import expit
from datasets import primary,ROOT
from bt import fit,order,influence,aggregate,hessian
from run_study import threshold
out=ROOT/'results/diagnostics';out.mkdir(parents=True,exist_ok=True)
rows=[]
for d in primary():
 start=time.perf_counter();a,b,y,names=d.arrays();m=len(names);t,_=fit(a,b,y,m);i,j,n,w=aggregate(a,b,y,m)
 H=hessian(t,i,j,n,1.);inv=np.linalg.inv(H)
 groups,code=np.unique(d.frame.cluster.astype(str),return_inverse=True)
 S=np.zeros((len(groups),m));r=y-expit(t[a]-t[b]);np.add.at(S,(code,a),r);np.add.at(S,(code,b),-r)
 S-=S.mean(axis=0);cov=inv@(S.T@S)@inv*len(groups)/(len(groups)-1)
 o=order(t)
 for rank in range(m-1):
  pair=(o[rank],o[rank+1]);c=np.zeros(m);c[pair[0]]=1;c[pair[1]]=-1
  indices,gain,_=influence(a,b,y,t,pair=pair);gap=float(c@t);cap=min(len(indices),int(.05*len(y)))
  gains=np.cumsum(gain[indices[:cap]]);lin=int(np.searchsorted(gains,gap)+1);lin=lin if lin<=cap else None
  # Search a successful prefix and verify its neighboring endpoint.
  def refit_margin(k):
   z=y.copy();ix=indices[:k];z[ix]=1-z[ix];u,_=fit(a,b,z,m,init=t)
   return float(u[pair[0]]-u[pair[1]])
  found=None;found_margin=None
  if cap and refit_margin(cap)<-1e-10:
   lo=0;hi=cap
   while hi-lo>1:
    mid=(lo+hi)//2
    if refit_margin(mid)<-1e-10:hi=mid
    else:lo=mid
   found=hi;found_margin=refit_margin(hi)
  sd=float(np.sqrt(max(0,c@cov@c)))
  rows.append(dict(dataset=d.name,N=len(y),rank=rank+1,upper=names[pair[0]],lower=names[pair[1]],gap=gap,sandwich_sd=sd,gap_over_sd=gap/sd,linear_k=lin,found_k=found,found_fraction=None if found is None else found/len(y),found_margin=found_margin))
 print(d.name,'adjacent contrasts',m-1,'seconds',round(time.perf_counter()-start,3),flush=True)
pd.DataFrame(rows).to_csv(out/'adjacent_pairs.csv',index=False)
print('HUTIAN_WAKE: adjacent-rank diagnostics complete',flush=True)
