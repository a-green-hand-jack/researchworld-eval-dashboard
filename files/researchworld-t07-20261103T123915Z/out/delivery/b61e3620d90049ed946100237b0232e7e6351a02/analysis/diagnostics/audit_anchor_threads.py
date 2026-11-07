"""Bounded source-only thread-count sensitivity of the one GSM loss mismatch."""
import json,pathlib
import numpy as np
from threadpoolctl import threadpool_limits
from benchsmall.pipeline import Study,check_freeze
from benchsmall.estimators import anchor_estimator,ridge_estimator
root=pathlib.Path(__file__).resolve().parents[1];check_freeze(root);study=Study(root)
x,ss=study.data('gsm','main');source=x[ss['train']];validation=x[ss['validation']];rows=[]
for threads in [1,2,1,2]:
 with threadpool_limits(limits=threads):
  est=anchor_estimator(source,30,study.selection_seed('gsm',30,'correctness-anchor'));losses=[]
  for alpha in study.cfg['alpha_grid']:
   fit=ridge_estimator(source,est.items,alpha)
   losses.append([alpha,float(np.abs(fit.predict(validation[:,est.items])-validation.mean(1)).mean())])
  rows.append({'threads':threads,'items':est.items.tolist(),'weights':est.weights.tolist(),'losses':losses})
(root/'results/study/source_anchor_thread_diagnostic.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
print([(r['threads'],r['losses'][1][1]) for r in rows])
