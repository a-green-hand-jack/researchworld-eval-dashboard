"""Test numerical identity after fixing input/output dtypes for every predictor."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import joblib,numpy as np,shap
from shap_reliability.estimators import Game,timed_run
rows=[]
for d in ['acs','diabetes']:
 for m in ['logistic','forest','histboost']:
  b=joblib.load(ROOT/f'artifacts/pilot/{d}_{m}.joblib')
  for i in range(2):
   args=(b['model'],b['background'],b['instances'][i],b['groups'])
   ref,_=timed_run(Game(*args),'exact',0,0)
   phi,detail=timed_run(Game(*args),'kernel',2048,12500+i)
   diff=float(np.max(abs(ref-phi)))
   if diff>1e-12:raise ValueError((d,m,i,diff))
   rows.append(dict(dataset=d,model=m,instance_index=i,max_absolute_error=diff,kernel_design_condition=detail['kernel_design_condition'],kernel_design_rank=detail['kernel_design_rank']))
(ROOT/'results/common_game_validation.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS: all 12 real-data exhaustive Kernel/direct games agree to 1e-12; maximum error',max(r['max_absolute_error'] for r in rows))
