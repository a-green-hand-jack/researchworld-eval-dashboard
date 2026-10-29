"""Numerical checks; synthetic examples here are tests, never empirical evidence."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import itertools
import numpy as np,pandas as pd
from scipy.optimize import minimize
from bt import Data

def main():
 rng=np.random.default_rng(174);rows=[]
 for a,b in itertools.combinations('abcd',2):
  for _ in range(2):rows.append({'a':a,'b':b,'y':float(rng.integers(2)),'cluster':str(len(rows))})
 d=Data('test',pd.DataFrame(rows));t=d.fit();i,j=np.argsort(-t)[:2]
 def f(v):
  z=d.X@v
  return np.sum(d.count*np.logaddexp(0,z)-d.wins*z)+.001*np.dot(v,v)/2
 res=minimize(f,np.zeros(d.m),method='BFGS',tol=1e-8)
 assert np.max(np.abs(t-(res.x-res.x.mean())))<1e-5
 r=int(d.dec[0]);eps=1e-4;w=d.wins.copy();w[d.edge[r]]+=eps*(1-2*d.y[r]);tt=d.fit(wins=w,start=t)
 assert abs(((t[i]-t[j])-(tt[i]-tt[j]))/eps-d.influence(t,i,j)[r])<1e-4
 exact=d.balanced_radius(i,j);best=None
 for k in range(1,len(d.dec)+1):
  for ids in itertools.combinations(d.dec,k):
   v=d.fit(wins=d.edited_wins(ids),start=t)
   if v[i]<v[j]-1e-8:best=k;break
  if best is not None:break
 assert best==exact,(best,exact)
 # A non-balanced example must reject use of the exact formula.
 dd=Data('imbalanced',pd.concat([d.frame,d.frame.iloc[:1]],ignore_index=True))
 try:dd.balanced_radius(0,2)
 except ValueError:pass
 else:raise AssertionError('balance check failed')
 print('PASS: independent optimizer, finite differences, exhaustive balanced radius, unbalanced rejection')
if __name__=='__main__':main()
