#!/usr/bin/env python3
"""Add exact binomial baseline using sufficient count stored in label-only midpoint.
Only binary-outcome datasets are selected; no claim for nonbinary labels.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import beta
BINARY={'bernoulli_quadratic','rare_binary','galaxies','forest','alphafold'}
for directory in __import__('sys').argv[1:]:
 for p in Path(directory).glob('*.parquet'):
  f=pd.read_parquet(p)
  if f.scenario.iloc[0] not in BINARY or 'clopper_pearson' in set(f.method): continue
  g=f[f.method=='label'].copy(); n=g.n.to_numpy(); raw=n*(g.lower+g.upper).to_numpy()/2; k=np.rint(raw).astype(int)
  if not np.allclose(k,raw,atol=1e-8): raise ValueError('cannot recover binomial counts')
  lo=np.zeros(len(g)); hi=np.ones(len(g)); a=k>0; b=k<n
  lo[a]=beta.ppf(.025,k[a],n[a]-k[a]+1); hi[b]=beta.ppf(.975,k[b]+1,n[b]-k[b])
  g['method']='clopper_pearson'; g['lower']=lo; g['upper']=hi; g['width']=hi-lo; g['covered']=(lo<=g.truth)&(g.truth<=hi)
  pd.concat([f,g],ignore_index=True).to_parquet(p,index=False)
  print('added exact binary interval',p,flush=True)
