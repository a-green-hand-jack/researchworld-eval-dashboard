#!/usr/bin/env python3
"""Replay fixed seed draws to give unit-PPI EB baseline all n labels (no tuning needed)."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from run_experiments import SCENARIO_IDS,REAL,draw,eb_radius,ALPHA
real={d:(np.load('data/'+d+'.npz')['Y'],np.load('data/'+d+'.npz')['Yhat']) for d in REAL}
bounded={'bernoulli_quadratic','rare_binary','bounded_quadratic',*REAL}
for directory in sys.argv[1:]:
 for p in Path(directory).glob('*.parquet'):
  f=pd.read_parquet(p); d=f.scenario.iloc[0]
  if d not in bounded or 'eb_ppi_full' in set(f.method): continue
  g=f[f.method=='label'].copy()
  lowers=[]; uppers=[]
  for row in g.itertuples():
   n=int(row.n); N=int(row.N); rep=int(row.rep); seed=int(row.seed)
   rng=np.random.default_rng(np.random.SeedSequence([seed,SCENARIO_IDS[d],n,N//n,rep]))
   y,s,u,truth,_=draw(rng,d,n,N,real)
   if abs(y.mean()-(row.lower+row.upper)/2)>1e-10: raise ValueError('seed replay mismatch')
   a=np.mean(y-s)+u.mean(); radius=eb_radius(y-s,2,ALPHA/2)+eb_radius(u,1,ALPHA/2)
   lo=float(np.clip(a-radius,0,1)); hi=float(np.clip(a+radius,0,1))
   lowers.append(lo); uppers.append(hi)
  g['method']='eb_ppi_full'; g['lower']=lowers; g['upper']=uppers
  g['width']=g.upper-g.lower; g['covered']=(g.lower<=g.truth)&(g.truth<=g.upper)
  pd.concat([f,g],ignore_index=True).to_parquet(p,index=False)
  print('added full-label unit-PPI EB',p,flush=True)
