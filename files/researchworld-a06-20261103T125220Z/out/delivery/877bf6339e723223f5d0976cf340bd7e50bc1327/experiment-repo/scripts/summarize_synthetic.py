"""Machine-check main synthetic output, export figure-ready values and exact checks."""
import pathlib,json
import numpy as np
import pandas as pd
p=pathlib.Path('results');x=pd.read_json(p/'synthetic-main.jsonl',lines=True)
assert len(x)==288*25
assert len(x[['n','k','rho','spread']].drop_duplicates())==288
assert (x.reps==20000).all()
assert not x.duplicated(['n','k','rho','spread','metric']).any()
assert np.isfinite(x[['mean','mcse']].to_numpy()).all()
x.to_csv(p/'synthetic-summary.csv',index=False,float_format='%.12g')
ref=pd.read_csv(p/'synthetic-exact-null.csv');checks=[]
for metric in ['optimism_reused','coverage_naive','coverage_simultaneous']:
 z=x[(x.rho==0)&(x.spread==0)&(x.metric==metric)].merge(ref[['n','k',metric]],on=['n','k'])
 z['standardized_error']=(z['mean']-z[metric])/z.mcse
 # Family-wise diagnostic threshold; it is not a hypothesis test of the paper's claims.
 assert (z.standardized_error.abs()<5).all()
 checks.append(dict(metric=metric,cells=len(z),max_abs_standardized_error=float(z.standardized_error.abs().max())))
 z.to_csv(p/f'synthetic-exact-check-{metric}.csv',index=False)
rows=[]
for metric in sorted(x.metric.unique()):
 z=x[x.metric==metric]
 rows.append(dict(metric=metric,minimum=float(z['mean'].min()),maximum=float(z['mean'].max()),cells=len(z)))
(p/'synthetic-validation.json').write_text(json.dumps(dict(cells=288,metrics=25,reps_per_cell=20000,exact_checks=checks,metric_ranges=rows,zero_event_warning='A zero empirical event rate has zero plug-in MCSE but is not proof of zero risk; 95% one-sided binomial upper bound is 1-0.05**(1/20000).'),indent=2)+'\n')
print(json.dumps(checks,indent=2))
