"""Exact independent equal-quality null references; no simulation or approximations."""
import pathlib
import numpy as np
import pandas as pd
from scipy.stats import binom
from run_synthetic import cp_table
rows=[]
for n in [16,32,64,128,256,512]:
 for k in [1,2,4,8,16,32,64,128]:
  x=np.arange(n+1);cdf=binom.cdf(x,n,.4)**k
  mass=np.diff(np.r_[0.,cdf]);assert abs(mass.sum()-1)<1e-12
  lo,hi=cp_table(n,.05);slo,shi=cp_table(n,.05/k)
  rows.append(dict(n=n,k=k,rho=0.,spread=0.,optimism_reused=float(np.dot(mass,x/n-.4)),coverage_naive=float(mass[(lo<=.4)&(.4<=hi)].sum()),coverage_simultaneous=float(mass[(slo<=.4)&(.4<=shi)].sum())))
p=pathlib.Path('results/synthetic-exact-null.csv');pd.DataFrame(rows).to_csv(p,index=False)
print('Wrote exact 48-cell independent null reference to',p)
