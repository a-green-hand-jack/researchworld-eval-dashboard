"""Check anchor reproduction against immutable original target-budget outputs.

No tuning or primary-artifact replacement. New source-only selections are
compared first; target responses are read only if their items match exactly.
"""
import argparse,hashlib,json,pathlib,time
import numpy as np
import pandas as pd
from benchsmall.pipeline import Study,check_freeze
from benchsmall.estimators import anchor_estimator,ridge_estimator
from benchsmall.mirt import MIRTModel
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--benchmarks',nargs='+');p.add_argument('--repetitions',type=int,default=1);args=p.parse_args()
check_freeze(root);study=Study(root);rows=[];development=[];start=time.perf_counter()
for b in args.benchmarks or study.splits:
 x,ss=study.data(b,'main');source=x[ss['train']];validation=x[ss['validation']];history=x[ss['history']]
 selections=json.loads((study.out/'predictions'/b/'main.selections.json').read_text())
 predictions=pd.read_parquet(study.out/'predictions'/b/'main.parquet')
 chosen=json.loads((study.out/'development'/b/'main.json').read_text())['selection']
 for repeat in range(args.repetitions):
  if b=='gsm':
   est=anchor_estimator(source,30,study.selection_seed(b,30,'correctness-anchor'))
   losses=[]
   for a in study.cfg['alpha_grid']:
    fitted=ridge_estimator(source,est.items,a)
    losses.append([a,float(np.abs(fitted.predict(validation[:,est.items])-validation.mean(1)).mean())])
   development.append({'benchmark':b,'budget':30,'repetition':repeat,'items':est.items.tolist(),'weights':est.weights.tolist(),'losses':losses,'metadata':est.metadata})
  for k in study.cfg['budgets']:
   d=chosen[str(k)]['parameters']['mirt_dimension'];z=np.load(study.out/'fits'/b/'main'/f'refit_d{d}.npz')
   model=MIRTModel(dimension=d);model.a=z['a'];model.b=z['b'];model.theta=z['theta']
   for method,est in [('anchor_mean',anchor_estimator(history,k,study.selection_seed(b,k,'correctness-anchor'))),('mirt_anchor_mean',model.anchor_estimator(k,study.selection_seed(b,k,'mirt-anchor')))]:
    key=f'main:{b}:{k}:0:{method}';old=selections[key];equal=old['items']==est.items.tolist()
    r={'benchmark':b,'budget':k,'method':method,'repetition':repeat,'items_exactly_equal':equal,'items':est.items.tolist(),'original_items':old['items'],'weights':est.weights.tolist()}
    if equal:
     saved=predictions[(predictions.budget==k)&(predictions['repeat']==0)&(predictions.method==method)].sort_values('target_row')
     fresh=est.predict(x[np.ix_(saved.target_row.to_numpy(),est.items)])
     r['same_budget_prediction_max_abs_difference']=float(abs(fresh-saved.predicted_score.to_numpy()).max())
    rows.append(r)
record={'scope':'Retrospective reproducibility audit; no tuning, new target items or primary artifact changes','elapsed_seconds':time.perf_counter()-start,'final_anchor_checks':rows,'gsm_development_repeated_checks':development}
out=study.out/'anchor_reproduction_audit.json';out.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print('HUTIAN_WAKE: anchor reproduction audit complete '+str(len(rows))+' final-anchor checks',flush=True)
