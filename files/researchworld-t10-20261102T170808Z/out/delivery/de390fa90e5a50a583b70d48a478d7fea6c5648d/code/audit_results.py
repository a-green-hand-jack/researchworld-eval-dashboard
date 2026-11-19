#!/usr/bin/env python3
"""Validate all published trial records and expose unstable fit tails."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
ap=argparse.ArgumentParser(); ap.add_argument('directories',nargs='+'); a=ap.parse_args()
rows=[]; total=0
for d in a.directories:
 meta=json.loads((Path(d)/'metadata.json').read_text()); expected=meta['arguments']['reps']
 for p in Path(d).glob('*.parquet'):
  f=pd.read_parquet(p); total+=len(f)
  assert np.isfinite(f[['truth','lower','upper','width']].to_numpy()).all(),str(p)
  assert (f.width>=0).all(),str(p)
  assert np.allclose(f.width,f.upper-f.lower),str(p)
  assert (f.covered==((f.lower<=f.truth)&(f.truth<=f.upper))).all(),str(p)
  assert not f.duplicated(['scenario','n','N','rep','seed','method']).any(),str(p)
  assert (f.groupby('method').size()==expected).all(),str(p)
  for method,g in f.groupby('method'):
   q=np.quantile(g.width,[.5,.9,.99,.999,1]); rows.append((g.scenario.iloc[0],g.n.iloc[0],g.N.iloc[0],method,*q))
pd.DataFrame(rows,columns=['scenario','n','N','method','width_median','width_p90','width_p99','width_p999','width_max']).to_csv('results/tail_diagnostics.csv',index=False)
Path('results/audit.json').write_text(json.dumps({'trial_method_records':total,'status':'pass','checks':['finite numeric records','nonnegative width','endpoint/width identity','coverage recomputed from truth','unique trial-method keys','repetition count per cell-method']},indent=2))
print('audit passed',total,'trial-method records',flush=True)
