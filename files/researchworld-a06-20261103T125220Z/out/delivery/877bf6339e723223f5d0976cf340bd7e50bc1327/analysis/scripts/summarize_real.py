"""Validate complete frozen calibration grid and export values with logical costs.

No plot rendering; all fresh audit and empirical-cache targets stay separate.
"""
import argparse,json,pathlib
import numpy as np
import pandas as pd


def main():
 p=argparse.ArgumentParser();p.add_argument('--scope',required=True);p.add_argument('--cache-calibration',required=True);p.add_argument('--out-dir',required=True);a=p.parse_args()
 scope=json.loads(pathlib.Path(a.scope).read_text());x=pd.read_json(a.cache_calibration,lines=True)
 expected={(n,k) for n in scope['n_grid'] for k in scope['k_grid']}
 assert set(map(tuple,x[['n','k']].drop_duplicates().to_numpy()))==expected
 assert (x.reps==scope['cache_calibration_reps']).all()
 assert (x.target=='fixed_empirical_cache_iid_with_replacement').all()
 assert (x.population_questions==scope['search_questions']+scope['audit_questions']).all()
 assert not x.duplicated(['n','k','metric']).any()
 metrics=set(x.metric);assert len(metrics)==25
 assert all(set(g.metric)==metrics for _,g in x.groupby(['n','k']))
 assert np.isfinite(x[['mean','mcse']].to_numpy()).all() and (x.mcse>=0).all()
 for metric in metrics:
  if metric.startswith(('coverage_','false_superiority_')):
   assert x[x.metric==metric]['mean'].between(0,1).all()
 out=pathlib.Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 x.to_csv(out/'cache-calibration.csv',index=False)
 budgets=[]
 for n,k in sorted(expected):
  ns=n//2;nh=n-ns;cs=max(1,n*k//(k+1));ch=n*k-cs*k
  for method,search,audit in [('naive_reuse',n,0),('simultaneous_reuse',n,0),('independent_audit',n,n),('split_question_budget',ns,nh),('split_call_budget',cs,ch)]:
   budgets.append(dict(n=n,k=k,method=method,selection_questions=search,report_only_questions=audit,total_question_draws=search+audit,logical_selection_model_calls=search*k,logical_report_model_calls=audit,logical_total_model_calls=search*k+audit,new_model_calls_for_cached_resampling=0,target='selected configuration under this protocol; smaller split search can select a different identity',cost_type='logical cost of a hypothetical uncached protocol, not extra inference actually performed'))
 pd.DataFrame(budgets).to_csv(out/'cache-protocol-budgets.csv',index=False)
 summary=dict(cells=len(expected),metrics=len(metrics),reps_per_cell=scope['cache_calibration_reps'],zero_event_one_sided_95_upper_bound=1-.05**(1/scope['cache_calibration_reps']),warning='All calibration truth is the known empirical cache distribution. MCSE is conditional Monte Carlo error. A zero empirical error rate is not proof of zero risk.')
 (out/'cache-validation.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary))
if __name__=='__main__':main()
