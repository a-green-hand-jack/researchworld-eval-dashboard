"""Independent delivered-record/summary consistency check; no experiments are rerun."""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm
root=Path(sys.argv[1]); out=Path(sys.argv[2])
summary=pd.read_csv(root/'results/summary.csv')
paired=pd.read_csv(root/'results/paired.csv')
files=0; trial_records=0; checked_summaries=0; checked_pairs=0
for group in ['synthetic','real','bounded','ratio1']:
 for path in sorted((root/'results'/group).glob('*.parquet')):
  f=pd.read_parquet(path); files+=1; trial_records+=len(f)
  assert np.isfinite(f[['truth','lower','upper','width']]).all().all()
  assert (f.width>=0).all() and np.allclose(f.width,f.upper-f.lower)
  assert (f.covered==((f.lower<=f.truth)&(f.truth<=f.upper))).all()
  assert not f.duplicated(['scenario','n','N','rep','seed','method']).any()
  scenario=f.scenario.iloc[0]; n=int(f.n.iloc[0]); N=int(f.N.iloc[0])
  ss=summary[(summary.scenario==scenario)&(summary.n==n)&(summary.N==N)]
  assert set(ss.method)==set(f.method)
  for _,row in ss.iterrows():
   g=f[f.method==row.method]; k=int(g.covered.sum()); R=len(g); z=norm.ppf(.975); p=k/R
   c=(p+z*z/(2*R))/(1+z*z/R); half=z*np.sqrt(p*(1-p)/R+z*z/(4*R*R))/(1+z*z/R)
   a=np.array([R,k,p,c-half,c+half,g.width.mean(),g.width.std(ddof=1)/R**.5])
   b=row[['reps','hits','coverage','coverage_lo','coverage_hi','mean_width','width_mcse']].to_numpy(dtype=float)
   assert np.allclose(a,b,rtol=1e-10,atol=1e-13),(path,row.method)
   checked_summaries+=1
  wide=f.pivot(index=['rep','seed'],columns='method',values='width'); assert not wide.isna().any().any()
  pp=paired[(paired.scenario==scenario)&(paired.n==n)&(paired.N==N)]
  for _,row in pp.iterrows():
   a=wide[row.method].to_numpy(); b=wide[row.baseline].to_numpy(); R=len(a)
   r=a.mean()/b.mean(); se=np.std(a-r*b,ddof=1)/(R**.5*b.mean()); diff=a-b
   vals=[R,r,se,r-1.96*se,r+1.96*se,diff.mean(),np.std(diff,ddof=1)/R**.5]
   expected=row[['reps','width_ratio','ratio_mcse','ratio_lo','ratio_hi','width_difference','difference_mcse']].to_numpy(dtype=float)
   assert np.allclose(vals,expected,rtol=1e-10,atol=1e-13),(path,row.method,row.baseline)
   checked_pairs+=1
assert checked_summaries==len(summary) and checked_pairs==len(paired)
report={'status':'pass','trial_files':files,'trial_method_records':trial_records,'summary_rows_recomputed':checked_summaries,'paired_rows_recomputed':checked_pairs,'strong_baseline_rows':paired[paired.baseline.isin(['eb_ppi_full','clopper_pearson'])].groupby('baseline').size().to_dict()}
out.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report))
