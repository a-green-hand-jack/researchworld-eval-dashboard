"""Validate full main-export identities, interval transformation and MCSE contracts."""
import json,pathlib
import numpy as np
import pandas as pd
from finite_population import hypergeom_interval

root=pathlib.Path('results/real');scope=json.loads(pathlib.Path('provenance/real-scope-tier-c.json').read_text());d=np.load('results/real-main.npz');ids=d['candidate_ids'].tolist();S=d['scores'][d['pools']=='search'];A=d['scores'][d['pools']=='audit'];p=json.loads((root/'primary-result.json').read_text());candidate=ids.index(p['candidate_id']);count=int(S[:,candidate].sum());m=len(A);N=12032-len(S)
assert S.shape==(256,4) and A.shape==(512,4) and np.isin(d['scores'],[0,1]).all()
assert ids==sorted(scope['active_candidate_ids']) and count==int(S.sum(axis=0).max())==p['search_successes']
assert p['audit_successes']==int(A[:,candidate].sum()) and np.isclose(p['reused_minus_audit'],S[:,candidate].mean()-A[:,candidate].mean())
assert p['design_count']==2 and p['per_design_alpha']==.025 and p['actual_cache_calls']==6144 and p['analysis_cache_responses']==3072
assert np.allclose(p['exact_audit_interval'],hypergeom_interval(p['audit_successes'],m,N,.025))
total=hypergeom_interval(count,len(S),12032,.025/4);assert np.allclose(p['exact_simultaneous_remaining_interval'],np.clip((12032*np.array(total)-count)/N,0,1))
assert np.allclose(p['exact_gap_interval'],[count/len(S)-p['exact_audit_interval'][1],count/len(S)-p['exact_audit_interval'][0]])
x=pd.read_csv(root/'cache-calibration.csv');y=pd.read_csv(root/'conditional-selection.csv');expected={(n,k) for n in scope['n_grid'] for k in scope['k_grid']}
assert set(map(tuple,x[['n','k']].drop_duplicates().to_numpy()))==set(map(tuple,y[['n','k']].drop_duplicates().to_numpy()))==expected
assert len(x)==15*25 and len(y)==15*18 and (x.reps==20000).all() and (y.reps==20000).all()
assert not x.duplicated(['n','k','metric']).any() and not y.duplicated(['n','k','metric']).any()
checks=0
for frame in [x,y]:
 for row in frame.itertuples():
  assert np.isfinite(row.mean) and np.isfinite(row.mcse) and row.mcse>=0
  if row.metric.startswith(('coverage_','false_superiority_')) or row.metric in ['selection_is_default','naive_superiority_claim_frequency','simultaneous_superiority_claim_frequency','naive_claim_audit_sign_disagreement','simultaneous_claim_audit_sign_disagreement','apparent_point_gain_audit_sign_disagreement']:
   assert 0<=row.mean<=1 and np.isclose(row.mean*row.reps,round(row.mean*row.reps),atol=1e-7)
   assert np.isclose(row.mcse,np.sqrt(row.mean*(1-row.mean)/(row.reps-1)),atol=1e-12);checks+=1
weights=pd.read_csv(root/'selection-frequencies.csv');assert np.allclose(weights.groupby(['n','k']).full_selection_frequency.sum(),1)
for row in y[y.metric=='full_selected_audit_accuracy'].itertuples():
 w=weights[(weights.n==row.n)&(weights.k==row.k)].set_index('candidate_id').loc[ids].full_selection_frequency.to_numpy();assert np.isclose(row.mean,w@A.mean(axis=0))
for name in ['candidate-correlation.csv','candidate-covariance.csv']:
 frame=pd.read_csv(root/name,index_col=0);assert frame.index.tolist()==ids and [int(c) for c in frame.columns]==ids
b=pd.read_json(root/'bootstrap-main.jsonl',lines=True);assert len(b)==2000 and set(b.n)=={64,256} and (b.k==4).all() and b.groupby('n').bootstrap.nunique().eq(1000).all()
bias=x[x.metric.str.startswith('bias_')];z=np.abs(bias['mean']/bias.mcse);assert z.max()<5,'Investigate an unexpected independent/split calibration bias before delivery'
summary=dict(status='PASS',matrix_questions=768,matrix_candidates=4,cells=15,reps=20000,probability_metric_mcse_checks=checks,bootstrap_records=2000,max_absolute_zero_bias_mcse=float(z.max()),warning='Diagnostics support implementation and target accounting; they are not proofs of population coverage or additional model runs.')
(root/'validation.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
