"""Additional timing at genuinely stochastic per-dataset budgets."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']: os.environ[k]='1'
import sys,json,resource
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import joblib,shap
from shap_reliability.estimators import Game,timed_run
ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'results/budget_pilot.jsonl').open('a') as out:
 for data,budgets in [('german',[128,512,2048]),('diabetes',[32,64,128]),('acs',[64,256,512])]:
  for model in ['logistic','forest','histboost']:
   b=joblib.load(ROOT/f'artifacts/pilot/{data}_{model}.joblib')
   for i in range(2):
    for est in ['permutation','kernel']:
     for budget in budgets:
      phi,details=timed_run(Game(b['model'],b['background'],b['instances'][i],b['groups']),est,budget,11000+i)
      r=dict(dataset=data,model=model,instance_index=i,estimator=est,budget=budget,phi=phi.tolist(),peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,**details)
      out.write(json.dumps(r)+'\n');out.flush()
   print(f'HUTIAN_WAKE: three-budget timing complete {data}/{model}',flush=True)
