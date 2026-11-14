"""Aggregate random draws and repeated held-out appearances before model bootstrap."""
import json,pathlib
import numpy as np
import pandas as pd
ROOT=pathlib.Path(__file__).resolve().parents[1]
def interval(v,rng):
 a=np.asarray(v,float);b=a[rng.integers(len(a),size=(4000,len(a)))].mean(axis=1)
 return float(a.mean()),float(np.quantile(b,.025)),float(np.quantile(b,.975))
paths=sorted((ROOT/'results').glob('*/model_losses.csv'))
paths += [p for p in (ROOT/'results').glob('*/model_losses.csv.gz') if not p.with_suffix('').exists()]
paths=[p for p in paths if not p.parent.name.startswith('pilot')]
allrows=pd.concat([pd.read_csv(p) for p in paths],ignore_index=True)
# Random query draws do not count as independent new models.
byappearance=allrows.groupby(['dataset','condition','method','k','seed','model'],as_index=False)[['mae','mse','standardized_mse']].mean()
bymodel=byappearance.groupby(['dataset','condition','method','k','model'],as_index=False)[['mae','mse','standardized_mse']].mean()
rng=np.random.default_rng(20261102);summary=[]
for key,g in bymodel.groupby(['dataset','condition','method','k']):
 row=dict(zip(['dataset','condition','method','k'],key));row['unique_test_models']=len(g)
 for col in ['mae','mse','standardized_mse']:
  mean,lo,hi=interval(g[col],rng)
  if col.endswith('mse'):mean,lo,hi=np.sqrt([mean,lo,hi]);col=col.replace('mse','rmse')
  row[col]=mean;row[col+'_lo']=lo;row[col+'_hi']=hi
 seeds=byappearance[(byappearance.dataset==key[0])&(byappearance.condition==key[1])&(byappearance.method==key[2])&(byappearance.k==key[3])].groupby('seed').mae.mean()
 row.update(seed_mae_min=float(seeds.min()),seed_mae_max=float(seeds.max()),n_splits=1 if key[1]=='temporal' else len(seeds),n_seed_runs=len(seeds));summary.append(row)
pd.DataFrame(summary).to_csv(ROOT/'results/summary.csv',index=False)
contrasts=[]
for (dataset,condition,k),g in byappearance[byappearance.k>0].groupby(['dataset','condition','k']):
 pivot=g.pivot(index=['seed','model'],columns='method',values='mae')
 if 'a_opt_covariance' not in pivot:continue
 for other in pivot:
  if other=='a_opt_covariance':continue
  diff=(pivot[other]-pivot.a_opt_covariance).dropna().groupby('model').mean()
  effect,lo,hi=interval(diff,rng)
  contrasts.append(dict(dataset=dataset,condition=condition,k=k,comparator=other,positive_means_a_opt_better=effect,ci_lo=lo,ci_hi=hi,n_models=len(diff)))
pd.DataFrame(contrasts).to_csv(ROOT/'results/paired_effects.csv',index=False)
bymodel.to_csv(ROOT/'results/model_averages.csv',index=False)
meta={'bootstrap_seed':20261102,'bootstrap_replicates':4000,'bootstrap_unit':'unique held-out model name, after averaging query draws and held-out split appearances','estimand':'equal-weight average over distinct evaluated complete model rows','interpretation':'descriptive model-cluster percentile intervals conditional on the observed cohort and fitted split ensemble; model lineages may remain dependent; no population-valid significance claims','sources':[str(p.relative_to(ROOT)) for p in paths]}
(ROOT/'results/uncertainty.json').write_text(json.dumps(meta,indent=2)+'\n')
print(pd.DataFrame(summary).query("method in ['a_opt_covariance','random_covariance','a_opt_mean'] and condition in ['random','provider','fixed_targets']")[['dataset','condition','method','k','mae','mae_lo','mae_hi','unique_test_models']].to_string(index=False))
