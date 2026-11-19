"""Create checkable quantitative evidence inputs; no paper/figure prose generation."""
import hashlib,json,pathlib
import numpy as np
import pandas as pd
from benchsmall.metrics import paired_interval
root=pathlib.Path(__file__).resolve().parents[1];out=root/'results/study'
read=lambda n:pd.read_csv(out/n)
macro=read('macro_repeats.csv');contrasts=read('paired_contrasts.csv');metrics=read('metrics.csv');robustness=read('robustness_contrasts.csv');collisions=read('response_collisions.csv')
quantities=['mae_pp','rmse_pp','spearman','kendall_tau_b','bias_pp']
macro_summary=[]
for (k,method),g in macro.groupby(['budget','method']):
 r={'budget':int(k),'method':method}
 for metric in quantities:
  r[metric]=paired_interval(g[metric]);r[metric]['defined_benchmarks_min']=int(g[metric+'_n_benchmarks'].min());r[metric]['defined_benchmarks_max']=int(g[metric+'_n_benchmarks'].max())
 macro_summary.append(r)
point_counts=[]
for (k,metric,method,ref),g in contrasts[(contrasts.benchmark!='MACRO13')&(contrasts.scenario=='main')].groupby(['budget','metric','method','reference']):
 valid=g[g.n_valid>0];negative=metric in ['mae_pp','rmse_pp']
 point_counts.append({'budget':int(k),'metric':metric,'method':method,'reference':ref,'n_benchmarks':len(g),'n_defined':len(valid),
  'method_lower':int((valid.difference<0).sum()),'method_higher':int((valid.difference>0).sum()),
  'interval_below_zero':int((valid.ci_high<0).sum()),'interval_above_zero':int((valid.ci_low>0).sum())})
pattern=[]
for (b,scenario),g in collisions.groupby(['benchmark','scenario']):
 pattern.append({'benchmark':b,'scenario':scenario,'n_targets':len(g),'n_patterns':g.response_pattern.nunique(),'n_source_matches':int(g.source_match.sum()),'max_target_pattern_multiplicity':int(g.target_pattern_multiplicity.max())})
# Small-source/family macro effects use paired benchmark cells from the same draw.
robust_macro=[];primary=metrics[(metrics.evaluation_subset=='primary')&(metrics.budget==30)]
for method,g in primary.groupby('method'):
 for metric in quantities:
  pivot=g.pivot(index=['benchmark','repeat'],columns='scenario',values=metric)
  for condition,reference in [('source25','main'),('source50','main'),('family_excluded','family_reference')]:
   if condition not in pivot or reference not in pivot:continue
   delta=(pivot[condition]-pivot[reference]).groupby(level='repeat').agg(difference='mean',n_benchmarks='count')
   robust_macro.append({'method':method,'metric':metric,'condition':condition,'reference':reference,
    'n_benchmarks_min':int(delta.n_benchmarks.min()),'n_benchmarks_max':int(delta.n_benchmarks.max()),**paired_interval(delta.difference)})
inputs=['macro_repeats.csv','paired_contrasts.csv','metrics.csv','robustness_contrasts.csv','response_collisions.csv','scoring_provenance.json','fit_diagnostics.csv','prediction_integrity.csv']
manifest={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in inputs}
def clean(x):
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 if isinstance(x,list):return [clean(v) for v in x]
 if isinstance(x,(np.integer,)):return int(x)
 if isinstance(x,(float,np.floating)) and not np.isfinite(x):return None
 return x
report={'purpose':'Analysis evidence inputs, all planned conditions retained; directions are method-minus-reference; error units percentage points',
 'uncertainty':'Conditional fixed-pool item-draw Monte Carlo mean intervals, not future-target/draw prediction coverage; exploratory counts across comparisons have no multiplicity correction',
 'input_sha256':manifest,'macro_means':macro_summary,'candidate_macro_contrasts':contrasts[(contrasts.benchmark=='MACRO13')&(contrasts.method=='crossfit_difference')].to_dict('records'),
 'benchmark_effect_counts':point_counts,'response_collision_counts':pattern,'robustness_macro':robust_macro,
 'failure_diagnostics':{'source_fit_count':len(read('fit_diagnostics.csv')),'nonconverged_source_fits':int((~read('fit_diagnostics.csv').converged).sum()),'prediction_integrity':read('prediction_integrity.csv').to_dict('records')}}
(out/'evidence_numbers.json').write_text(json.dumps(clean(report),indent=2,sort_keys=True,allow_nan=False)+'\n')
pd.DataFrame(robust_macro).to_csv(out/'robustness_macro.csv',index=False)
print('Generated checkable macro, heterogeneity, collision and robustness evidence with input hashes.',flush=True)
