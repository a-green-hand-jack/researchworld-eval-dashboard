"""Isolate fixed-alpha AIPW formula effects algebraically from frozen outputs.

With an unpenalized intercept code=mU, and paper(alpha10)=(k/N)*yS+(1-k/N)*mU.
This diagnostic adds no fit, observations, tuning or primary-method selection.
"""
import pathlib
import numpy as np,pandas as pd
from benchsmall.metrics import paired_interval
from rank_metrics import metrics
root=pathlib.Path(__file__).resolve().parents[1];out=root/'results/study';records=[];contrast=[];predictions=[]
for path in sorted((out/'predictions').glob('*/*.parquet')):
 if path.name.endswith('.timings.parquet'):continue
 df=pd.read_parquet(path);b=df.benchmark.iloc[0];scenario=df.scenario.iloc[0]
 scored=pd.read_parquet(out/'scored_predictions.parquet',filters=[('benchmark','==',b),('scenario','==',scenario)],columns=['budget','repeat','method','target_row','true_score'])
 truth=scored.drop_duplicates('target_row').set_index('target_row').true_score
 for (k,repeat),g in df.groupby(['budget','repeat']):
  pivot=g.pivot(index='target_row',columns='method',values='predicted_score');fraction=k/g.n_items.iloc[0]
  code=pivot.aipw_code;paper10=fraction*pivot.random_mean+(1-fraction)*code;y=truth.loc[pivot.index]
  predictions.append(pd.DataFrame({'benchmark':b,'scenario':scenario,'budget':int(k),'repeat':int(repeat),'target_row':pivot.index.to_numpy(),'alpha':10.,'budget_fraction':fraction,'code_score':code.to_numpy(),'random_mean_score':pivot.random_mean.to_numpy(),'paper_alpha10_score':paper10.to_numpy(),'true_score':y.to_numpy()}))
  code_metric=metrics(y.to_numpy(),code.to_numpy());paper_metric=metrics(y.to_numpy(),paper10.to_numpy())
  r={'benchmark':b,'scenario':scenario,'budget':int(k),'repeat':int(repeat),'alpha':10.,'max_abs_prediction_difference_pp':float(np.abs(code-paper10).max()*100)}
  for metric in ['mae_pp','rmse_pp','spearman','kendall_tau_b','bias_pp']:
   r['code_'+metric]=code_metric[metric];r['paper_alpha10_'+metric]=paper_metric[metric];r['difference_'+metric]=code_metric[metric]-paper_metric[metric]
  records.append(r)
pd.concat(predictions,ignore_index=True).to_parquet(out/'aipw_formula_predictions.parquet',index=False)
table=pd.DataFrame(records);table.to_csv(out/'aipw_formula_repeats.csv',index=False)
for (b,scenario,k),g in table.groupby(['benchmark','scenario','budget']):
 for metric in ['mae_pp','rmse_pp','spearman','kendall_tau_b','bias_pp']:
  contrast.append({'benchmark':b,'scenario':scenario,'budget':int(k),'metric':metric,'method':'aipw_code_alpha10','reference':'aipw_paper_alpha10_reconstructed',**paired_interval(g['difference_'+metric])})
pd.DataFrame(contrast).to_csv(out/'aipw_formula_contrasts.csv',index=False)
print('Saved fixed-alpha same-fit AIPW formula diagnostics without new fitting/observations.',flush=True)
