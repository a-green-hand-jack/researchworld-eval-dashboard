"""All-cell10/12/14-decimal rank sensitivity and common-shift invariance."""
import pathlib
import numpy as np,pandas as pd
from scipy.stats import rankdata,kendalltau
from benchsmall.pipeline import Study,check_freeze
from benchsmall.data import load_benchmark
root=pathlib.Path(__file__).resolve().parents[1];check_freeze(root);study=Study(root);out=study.out;records=[]
for b,bb in study.splits.items():
 x,unused,unused2=load_benchmark(root,b);truth=x.mean(1)
 for scenario in bb['scenarios']:
  df=pd.read_parquet(out/'predictions'/b/f'{scenario}.parquet')
  for (k,repeat,method),g in df.groupby(['budget','repeat','method']):
   for decimals in [10,12,14]:
    y=np.round(truth[g.target_row],decimals);p=np.round(g.predicted_score.to_numpy(),decimals)
    valid=len(np.unique(y))>1 and len(np.unique(p))>1
    records.append({'benchmark':b,'scenario':scenario,'budget':int(k),'repeat':int(repeat),'method':method,'decimals':decimals,
     'spearman':float(np.corrcoef(rankdata(y),rankdata(p))[0,1]) if valid else float('nan'),
     'kendall_tau_b':float(kendalltau(y,p,variant='b').statistic) if valid else float('nan'),
     'prediction_unique_scores':len(np.unique(p))})
table=pd.DataFrame(records);table.to_parquet(out/'rank_precision_repeats.parquet',index=False)
keys=['benchmark','scenario','budget','repeat','method'];ref=table[table.decimals==12].set_index(keys);rows=[]
for decimals in [10,14]:
 check=table[table.decimals==decimals].set_index(keys)
 for metric in ['spearman','kendall_tau_b']:
  delta=check[metric]-ref[metric]
  rows.append({'decimals':decimals,'metric':metric,'n_cells':len(delta),'n_defined_pairs':int(delta.notna().sum()),'n_changed_above_1e_12':int((abs(delta)>1e-12).sum()),'max_abs_difference':float(abs(delta).max()),'n_changed_unique_score_counts':int((check.prediction_unique_scores!=ref.prediction_unique_scores).sum())})
base=ref.reset_index();aa=base[base.method=='random_mean'].set_index(keys[:-1]);bb=base[base.method=='source_difference'].set_index(keys[:-1])
for metric in ['spearman','kendall_tau_b']:
 np.testing.assert_allclose(aa[metric],bb[metric],atol=1e-12,rtol=0,equal_nan=True)
assert np.array_equal(aa.prediction_unique_scores,bb.prediction_unique_scores)
pd.DataFrame(rows).to_csv(out/'rank_precision_sensitivity.csv',index=False)
print('HUTIAN_WAKE: all-cell rank precision sensitivity and constant-shift invariance complete',flush=True)
