"""Fresh complete ACS logistic path and strict endpoint/efficiency preflight."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import sys,time,json,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np,shap
from shap_reliability.models import prepare
from shap_reliability.estimators import Game,timed_run
start=time.perf_counter();cpu=time.process_time()
b=prepare('acs','logistic',n_instances=62)
args=(b['model'],b['background'],b['instances'][0],b['groups'])
g=Game(*args);ref,refdetail=timed_run(g,'exact',0,0);v=g.values([0,1023]);residual=float(ref.sum()-(v[1]-v[0]))
if abs(residual)>1e-8:raise ValueError(('strict reference efficiency failed',residual))
phi,details=timed_run(Game(*args),'kernel',2048,27182)
err=float(np.max(abs(phi-ref)))
if err>1e-12:raise ValueError(('exhaustive estimator mismatch',err))
rows=[]
for est in ['permutation','kernel']:
 for budget in [64,256,512]:
  phi,d=timed_run(Game(*args),est,budget,27183)
  efficiency=float(phi.sum()-(v[1]-v[0]))
  if abs(efficiency)>1e-6:raise ValueError((est,budget,'efficiency',efficiency))
  rows.append(dict(estimator=est,budget=budget,efficiency_residual=efficiency,**d))
record=dict(status='pass',dataset='acs',model='logistic',n_rows=b['info']['n_rows'],n_train=b['info']['n_train'],n_test=b['info']['n_test'],n_transformed_features=b['info']['transformed_features'],background_size=32,reference_efficiency_residual=residual,exhaustive_kernel_max_absolute_error=err,reference_tolerance=1e-8,peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,total_wall_seconds=time.perf_counter()-start,total_cpu_seconds=time.process_time()-cpu,stochastic_checks=rows)
(ROOT/'results/acs_preflight.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
