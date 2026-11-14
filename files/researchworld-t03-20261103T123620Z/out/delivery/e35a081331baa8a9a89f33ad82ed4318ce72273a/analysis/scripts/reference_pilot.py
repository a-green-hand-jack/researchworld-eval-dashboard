"""Measure full German coalition enumeration; no extrapolated result as evidence."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']: os.environ[k]='1'
import sys,json,resource,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import joblib,numpy as np
from shap_reliability.estimators import Game,timed_run
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'results/reference_pilot.jsonl'
for model in ['logistic','forest','histboost']:
    b=joblib.load(ROOT/f'artifacts/pilot/german_{model}.joblib')
    print(f'Start exact German reference pilot {model}',flush=True)
    phi,details=timed_run(Game(b['model'],b['background'],b['instances'][0],b['groups']),'exact',0,0)
    row=dict(dataset='german',model=model,instance_index=0,source_id=b['info']['explain_ids'][0],phi=phi.tolist(),peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,**details)
    with out.open('a') as f:f.write(json.dumps(row)+'\n')
    print(json.dumps(row),flush=True)
    print(f'HUTIAN_WAKE: exact German pilot complete {model}',flush=True)
