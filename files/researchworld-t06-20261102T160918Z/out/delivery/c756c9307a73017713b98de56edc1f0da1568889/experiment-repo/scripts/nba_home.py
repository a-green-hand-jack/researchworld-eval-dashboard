"""Home-advantage nuisance-variable sensitivity for the NBA season panel."""
import numpy as np,pandas as pd,json,time
from scipy.special import expit
from datasets import nba,ROOT
from bt import order
out=ROOT/'results/nba_home';out.mkdir(parents=True,exist_ok=True);rows=[]
for year in range(2006,2016):
 start=time.perf_counter();d=nba(year);a,b,y,names=d.arrays();m=len(names);N=len(y)
 X=np.zeros((N,m+1));X[np.arange(N),a]=1;X[np.arange(N),b]=-1;X[:,-1]=d.frame.home
 def fit(z,w=None,t0=None):
  w=np.ones(N) if w is None else w;t=np.zeros(m+1) if t0 is None else t0.copy()
  for iteration in range(50):
   p=expit(X@t);g=X.T@(w*(p-z))+t;H=X.T@((w*p*(1-p))[:,None]*X)+np.eye(m+1)
   if max(abs(g))<1e-8:break
   step=np.linalg.solve(H,g);t-=step;t[:m]-=t[:m].mean()
  assert max(abs(g))<1e-7
  return t,H,float(max(abs(g)))
 t,H,grad=fit(y);pair=order(t[:m])[:2];c=np.zeros(m+1);c[pair[0]]=1;c[pair[1]]=-1;gap=float(c@t)
 gain=-(1-2*y)*(X@np.linalg.solve(H,c));ix=np.flatnonzero(gain>1e-14);ix=ix[np.argsort(-gain[ix],kind='stable')];cap=min(len(ix),int(.05*N))
 def margin(k):
  z=y.copy();z[ix[:k]]=1-z[ix[:k]];u,_,_=fit(z,t0=t);return float(c@u)
 k=None;lo=0;hi=cap
 if margin(cap)<-1e-10:
  while hi-lo>1:
   mid=(hi+lo)//2
   if margin(mid)<-1e-10:hi=mid
   else:lo=mid
  k=hi
 rng=np.random.default_rng(20261102+year);groups,code=np.unique(d.frame.cluster,return_inverse=True);margins=[]
 for rep in range(300):
  counts=rng.multinomial(len(groups),np.full(len(groups),1/len(groups)));u,_,_=fit(y,counts[code],t);margins.append(c@u)
 rows.append(dict(dataset=d.name,N=N,leader=names[pair[0]],runner=names[pair[1]],home_logit=t[-1],gap=gap,gap_low=np.quantile(margins,.025),gap_high=np.quantile(margins,.975),attack_k=k,attack_fraction=None if k is None else k/N,gradient_max=grad,seconds=time.perf_counter()-start))
 print(d.name,rows[-1],flush=True)
pd.DataFrame(rows).to_csv(out/'audits.csv',index=False)
print('HUTIAN_WAKE: home-adjusted NBA diagnostic complete',flush=True)
