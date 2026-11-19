"""Measure final float64 predictor adapter against the original timing pilot."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import sys,json,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import joblib,shap
from shap_reliability.estimators import Game,timed_run
with (ROOT/'results/final_precision_pilot.jsonl').open('w') as out:
 for data,budgets in [('german',[128,512,2048]),('diabetes',[32,64,128]),('acs',[64,256,512])]:
  for model in ['logistic','forest','histboost']:
   b=joblib.load(ROOT/f'artifacts/pilot/{data}_{model}.joblib')
   for i in range(2):
    args=(b['model'],b['background'],b['instances'][i],b['groups'])
    for est in ['permutation','kernel']:
     for budget in budgets:
      phi,details=timed_run(Game(*args),est,budget,11000+i)
      row=dict(dataset=data,model=model,instance_index=i,kind='estimator',estimator=est,budget=budget,phi=phi.tolist(),**details)
      out.write(json.dumps(row)+'\n');out.flush()
    if i==0 or data!='german':
      phi,details=timed_run(Game(*args),'exact',0,0)
      row=dict(dataset=data,model=model,instance_index=i,kind='reference',estimator='exact',phi=phi.tolist(),peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,**details)
      out.write(json.dumps(row)+'\n');out.flush()
   print(f'HUTIAN_WAKE: final-precision timing {data}/{model} complete',flush=True)
