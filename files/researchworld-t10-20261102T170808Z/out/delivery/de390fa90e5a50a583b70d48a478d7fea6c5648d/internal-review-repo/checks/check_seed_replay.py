"""Replay first/last saved draws per cell and compare every implemented endpoint."""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import beta
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'code'))
from run_experiments import draw,intervals,SCENARIO_IDS,REAL,eb_radius,ALPHA
real={d:(np.load(root/'data'/f'{d}.npz')['Y'],np.load(root/'data'/f'{d}.npz')['Yhat']) for d in REAL}
checked=0;draws=0; max_error=0.
for group in ['synthetic','real','bounded','ratio1']:
 meta=json.loads((root/'results'/group/'metadata.json').read_text())
 for file in sorted((root/'results'/group).glob('*.parquet')):
  f=pd.read_parquet(file)
  for rep in [int(f.rep.min()),int(f.rep.max())]:
   g=f[f.rep==rep]; row=g.iloc[0];n=int(row.n);N=int(row.N);scenario=row.scenario
   rng=np.random.default_rng(np.random.SeedSequence([int(row.seed),SCENARIO_IDS[scenario],n,N//n,rep]))
   y,s,u,truth,bounded=draw(rng,scenario,n,N,real)
   assert truth==row.truth
   result=intervals(y,s,u,bounded,meta['arguments'].get('stress',False))
   if 'clopper_pearson' in set(g.method):
    k=int(y.sum());result['clopper_pearson']=(0 if k==0 else beta.ppf(.025,k,n-k+1),1 if k==n else beta.ppf(.975,k+1,n-k))
   if 'eb_ppi_full' in set(g.method):
    mid=np.mean(y-s)+u.mean(); rad=eb_radius(y-s,2,ALPHA/2)+eb_radius(u,1,ALPHA/2)
    result['eb_ppi_full']=(np.clip(mid-rad,0,1),np.clip(mid+rad,0,1))
   assert set(result)==set(g.method)
   for _,r in g.iterrows():
    error=np.max(np.abs(np.array(result[r.method])-[r.lower,r.upper]));max_error=max(max_error,float(error)); assert np.allclose(result[r.method],[r.lower,r.upper],rtol=1e-12,atol=1e-12),(file,rep,r.method,error)
    checked+=1
   draws+=1
report={'status':'pass','replayed_draw_sets':draws,'trial_method_endpoints_compared':checked,'maximum_absolute_endpoint_difference':max_error}
Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
