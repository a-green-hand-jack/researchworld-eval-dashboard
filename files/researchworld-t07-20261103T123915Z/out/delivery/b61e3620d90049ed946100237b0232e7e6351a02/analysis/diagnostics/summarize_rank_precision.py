"""Quantify precision effects on finite-benchmark rank means and contrasts."""
import pathlib
import pandas as pd
from benchsmall.metrics import paired_interval
root=pathlib.Path(__file__).resolve().parents[1];out=root/'results/study'
r=pd.read_parquet(out/'rank_precision_repeats.parquet');r=r[r.scenario=='main'];metrics=['spearman','kendall_tau_b']
macro=r.groupby(['decimals','budget','repeat','method'])[metrics].mean().reset_index()
macro.to_csv(out/'rank_precision_macro_repeats.csv',index=False)
rows=[]
for (decimals,k),g in macro.groupby(['decimals','budget']):
 for metric in metrics:
  pivot=g.pivot(index='repeat',columns='method',values=metric)
  for ref in ['random_mean','source_difference','ridge','aipw_paper']:
   rows.append({'decimals':int(decimals),'budget':int(k),'metric':metric,'method':'crossfit_difference','reference':ref,**paired_interval(pivot.crossfit_difference-pivot[ref])})
table=pd.DataFrame(rows);table.to_csv(out/'rank_precision_macro_contrasts.csv',index=False)
keys=['budget','metric','method','reference'];base=table[table.decimals==12].set_index(keys);deltas=[]
for decimals in [10,14]:
 x=table[table.decimals==decimals].set_index(keys)
 for metric in metrics:
  a=x[x.index.get_level_values('metric')==metric];b=base.loc[a.index]
  deltas.append({'decimals':decimals,'metric':metric,'max_abs_macro_contrast_change':float(abs(a.difference-b.difference).max()),'max_abs_low_endpoint_change':float(abs(a.ci_low-b.ci_low).max()),'max_abs_high_endpoint_change':float(abs(a.ci_high-b.ci_high).max())})
pd.DataFrame(deltas).to_csv(out/'rank_precision_conclusion_sensitivity.csv',index=False)
print(pd.DataFrame(deltas).to_string(index=False))
