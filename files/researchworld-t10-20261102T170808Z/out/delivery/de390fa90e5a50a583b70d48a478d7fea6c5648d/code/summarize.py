#!/usr/bin/env python3
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm

def wilson(k,n):
 z=norm.ppf(.975); p=k/n; c=(p+z*z/(2*n))/(1+z*z/n); r=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
 return c-r,c+r

def summarize(paths,out):
 f=pd.concat([pd.read_parquet(p) for p in paths],ignore_index=True)
 if f.duplicated(['scenario','n','N','rep','seed','method']).any(): raise ValueError('duplicate trials')
 rows=[]; paired=[]
 for key,g in f.groupby(['scenario','n','N','method']):
  k=int(g.covered.sum()); R=len(g); w=g.width.to_numpy(); lo,hi=wilson(k,R)
  rows.append((*key,R,k,k/R,lo,hi,w.mean(),w.std(ddof=1)/np.sqrt(R),np.sqrt(np.mean(((g.lower+g.upper)/2-g.truth)**2))))
 for key,g in f.groupby(['scenario','n','N']):
  wide=g.pivot(index=['rep','seed'],columns='method',values='width')
  for baseline in ['label','ppi++','scalar_unclipped','cf_linear','eb_label','eb_ppi','eb_ppi_full','eb_scalar','clopper_pearson']:
   if baseline not in wide: continue
   for method in wide:
    if method==baseline: continue
    a=wide[method].to_numpy(); b=wide[baseline].to_numpy(); R=len(a); ratio=a.mean()/b.mean()
    # Delta-method SE for ratio of paired means (NOT mean per-trial ratio).
    se=np.std(a-ratio*b,ddof=1)/(np.sqrt(R)*b.mean()); diff=a-b
    paired.append((*key,method,baseline,R,ratio,se,ratio-1.96*se,ratio+1.96*se,diff.mean(),diff.std(ddof=1)/np.sqrt(R)))
 out=Path(out); out.mkdir(parents=True,exist_ok=True)
 pd.DataFrame(rows,columns=['scenario','n','N','method','reps','hits','coverage','coverage_lo','coverage_hi','mean_width','width_mcse','rmse_midpoint']).to_csv(out/'summary.csv',index=False)
 pd.DataFrame(paired,columns=['scenario','n','N','method','baseline','reps','width_ratio','ratio_mcse','ratio_lo','ratio_hi','width_difference','difference_mcse']).to_csv(out/'paired.csv',index=False)
 print(f'{len(f)} trial-method records summarized into {out}')
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('directories',nargs='+'); ap.add_argument('--out',required=True); a=ap.parse_args()
 summarize([p for d in a.directories for p in Path(d).glob('*.parquet')],a.out)
