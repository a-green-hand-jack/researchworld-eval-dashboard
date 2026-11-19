"""Audit every expected prediction/access cell before retrospective truth scoring."""
import hashlib,itertools,json,pathlib
import numpy as np
import pandas as pd
from benchsmall.pipeline import Study,check_freeze,read,write
root=pathlib.Path(__file__).resolve().parents[1];check_freeze(root);study=Study(root)
manifest={};rows=[]
for b,bb in study.splits.items():
 for scenario,ss in bb['scenarios'].items():
  path=study.out/'predictions'/b/f'{scenario}.parquet'
  assert path.exists(),path
  df=pd.read_parquet(path);selections=read(path.with_suffix('.selections.json'));access=read(path.with_suffix('.access.json'))
  methods=study.cfg['methods'] if scenario=='main' else study.cfg['robustness_methods'];budgets=study.cfg['budgets'] if scenario=='main' else [30]
  keys=['budget','repeat','method','target_row'];expected=set(itertools.product(budgets,range(20),methods,ss['target']))
  assert set(df[keys].itertuples(index=False,name=None))==expected and not df.duplicated(keys).any()
  assert 'true_score' not in df and np.isfinite(df.predicted_score).all()
  assert set(df.n_items)=={bb['n_items']} and set(df.n_history)=={len(ss['history'])}
  assert all(df.original_row==df.target_row.map(dict(enumerate(bb['deduplicated_original_rows']))))
  assert len(selections)==len(methods)*len(budgets)*20 and len(access)==len(budgets)*20
  for (k,repeat,method),g in df.groupby(['budget','repeat','method']):
   key=f'{scenario}:{b}:{k}:{repeat}:{method}';assert set(g.selection_key)=={key}
   items=selections[key]['items'];want=0 if method=='source_prior' else k
   assert len(items)==len(set(items))==want and set(g.observed_items)=={want}
   assert all(0<=j<bb['n_items'] for j in items) and np.allclose(g.observed_fraction,want/bb['n_items'])
   assert items==access[f'{k}:{repeat}'][method]
   if 'anchor' not in method and method!='source_prior':assert items==study.items[b]['final'][repeat]['items'][:k]
   if 'anchor' in method:
    assert items==selections[f'{scenario}:{b}:{k}:0:{method}']['items']
  for suffix in ['.parquet','.selections.json','.access.json','.timings.parquet']:
   file=path.with_suffix(suffix);manifest[str(file.relative_to(root))]=hashlib.sha256(file.read_bytes()).hexdigest()
  rows.append({'benchmark':b,'scenario':scenario,'prediction_rows':len(df),'cells':len(methods)*len(budgets)*20,'reserved_targets':len(ss['target']),'duplicate_cells':0,'nonfinite_predictions':0,'budget_violations':0,'truth_present':False})
pd.DataFrame(rows).to_csv(study.out/'prediction_integrity.csv',index=False)
write(study.out/'prescore_artifact_manifest.json',manifest)
print('HUTIAN_WAKE: target-blind prediction/access integrity passed for all '+str(len(rows))+' scenarios',flush=True)
