"""Add exact binary / Hoeffding comparators using exactly the original draws.
This avoids recomputing already-completed, unchanged inference procedures.
The current experiment.py generates these baselines directly on a fresh run.
"""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import json,time
import numpy as np
import pandas as pd
from experiment import sample
from methods import hoeffding,exact_binomial
ROOT=Path(__file__).resolve().parents[1]
t=time.perf_counter();out=[]
for p in sorted((ROOT/'results/raw').glob('*.json')):
    meta=json.loads(p.read_text())
    if meta['kind']=='ablation':continue
    f=p.with_suffix('.csv.gz');df=pd.read_csv(f);present=set(df.method)
    needed=[]
    if 'Hoeffding' not in present:needed.append('Hoeffding')
    binary=meta['kind']=='real' or not meta['case'].endswith('_cont')
    if binary and 'Exact-binomial' not in present:needed.append('Exact-binomial')
    if not needed:continue
    pop=None
    if meta['kind']=='real':
        z=np.load(ROOT/'data'/f"{meta['case']}.npz");pop=(z['Y'],z['Yhat'])
    rng=np.random.default_rng(meta['seed']);rows=[]
    for r in range(meta['reps']):
        y,sl,su=sample(meta['case'],meta['n'],meta['N'],rng,pop)
        for m in needed:
            lo,hi=(hoeffding(y) if m=='Hoeffding' else exact_binomial(y))
            rows.append((r,m,lo,hi,int(lo<=meta['theta']<=hi),hi-lo))
    new=pd.DataFrame(rows,columns=df.columns)
    df=pd.concat([df,new],ignore_index=True).sort_values(['rep','method'])
    df.to_csv(f,index=False,float_format='%.12g',compression={'method':'gzip','mtime':0})
    out.append(dict(cell=p.stem,added=needed));print(out[-1],flush=True)
(ROOT/'logs/augment.json').write_text(json.dumps(dict(wall_seconds=time.perf_counter()-t,cells=out),indent=2))
