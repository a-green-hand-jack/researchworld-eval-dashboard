"""Audit final evidence; derive MC diagnostics and paired epsilon sensitivity."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from summarize import interval

root=Path('results'); main=pd.read_json(root/'main.jsonl',lines=True); weighted=pd.read_json(root/'weighted.jsonl',lines=True)
prior=pd.read_json(root/'prior_scores.jsonl',lines=True) if (root/'prior_scores.jsonl').exists() else pd.DataFrame()
frame=pd.concat([main,weighted,prior],ignore_index=True)
keys=['seed','k','ncal','scenario','shift','epsilon','alpha']
assert len(main)==11200 and len(weighted)==1600
assert not frame.duplicated(keys+['method']).any()
assert (frame.groupby(['k','ncal','scenario','shift','method']).size()==100).all()
assert (frame.ncal_g0+frame.ncal_g1==frame.ncal).all()
assert (frame.n_g0+frame.n_g1==frame.n_test).all() and (frame.n_test==5000).all()
a=main[(main.method=='clr_l2')&(~main['shift'])].merge(weighted[~weighted['shift']],on=keys,suffixes=('_core','_oracle'))
for metric in ['coverage','coverage_g0','coverage_g1','volume_fraction']:
    assert np.array_equal(a[metric+'_core'].fillna(-1),a[metric+'_oracle'].fillna(-1)),metric
assert len(a)==800
if not prior.empty:
    assert len(prior)==3200
    tv=main[(main.k==3)&(main.method=='raw_linf')].merge(prior[(prior.k==3)&(prior.method=='tv')],on=keys,suffixes=('_core','_tv'))
    for metric in ['coverage','coverage_g0','coverage_g1','volume_fraction']:
        assert np.array_equal(tv[metric+'_core'].fillna(-1),tv[metric+'_tv'].fillna(-1)),metric
    assert len(tv)==800
# A conservative SE bound for the paired area difference, allowing arbitrary
# positive/negative dependence between two methods' common-candidate estimates.
mc=[]
pairs=[('clr_scaled','clr_l2'),('clr_mondrian','clr_l2'),('raw_l2','clr_l2'),('raw_linf','clr_l2'),('coord_bonferroni','coord_naive'),('clr_weighted','clr_l2'),('clr_weighted','clr_mondrian'),('tv','raw_l2'),('tv','raw_linf'),('tv','clr_l2'),('kl_forward','raw_l2'),('kl_forward','raw_linf'),('kl_forward','clr_l2')]
for cellkeys,cell in frame[frame.k==3].groupby(['k','ncal','scenario','shift']):
    for m1,m2 in pairs:
        if m1 not in cell.method.values or m2 not in cell.method.values: continue
        x=cell[cell.method==m1].set_index('seed');y=cell[cell.method==m2].set_index('seed')
        n,mean,se,lo,hi=interval(x.volume_fraction-y.volume_fraction)
        bound=float(np.sqrt(np.sum((x.volume_mc_se_conditional+y.volume_mc_se_conditional)**2))/n)
        mc.append(dict(zip(['k','ncal','scenario','shift'],cellkeys))|dict(method_a=m1,method_b=m2,n_rep=n,mean_area_difference=mean,ci_low=lo,ci_high=hi,candidate_mc_se_upper_bound=bound,candidate_resolution_ratio=abs(mean)/bound if bound else None,resolution_reason='exact_duplicate' if (m1=='tv' and m2=='raw_linf') or (m1=='clr_weighted' and m2=='clr_l2' and not cellkeys[-1]) else 'paired_interval_includes_zero' if lo<=0<=hi else 'candidate_MC_unresolved' if abs(mean)<=2*bound else 'resolved',ordering_resolved=bool((lo>0 or hi<0) and abs(mean)>2*bound)))
pd.DataFrame(mc).to_csv(root/'main_summary/area_precision.csv',index=False)
# Epsilon contrast is paired on the same original dataset, not pooled across eps.
boundary=pd.read_json(root/'boundary.jsonl',lines=True)
assert len(boundary)==4200
assert (boundary.groupby(['k','scenario','epsilon','method']).size()==50).all()
epsilon_rows=[]
for cellkeys,cell in boundary.groupby(['k','scenario','method']):
    for metric in ['coverage','coverage_g0','coverage_g1']:
        pivot=cell.pivot(index='seed',columns='epsilon',values=metric)
        for eps in (1e-4,1e-2):
            n,mean,se,lo,hi=interval(pivot[eps]-pivot[1e-8])
            epsilon_rows.append(dict(zip(['k','scenario','method'],cellkeys))|dict(epsilon_a=eps,epsilon_b=1e-8,metric=metric,n_rep=n,mean_difference=mean,se=se,ci_low=lo,ci_high=hi))
pd.DataFrame(epsilon_rows).to_csv(root/'boundary_summary/epsilon_contrasts.csv',index=False)
prevalence=boundary.drop_duplicates(['seed','k'])
zero_rows=[]
for k,cell in prevalence.groupby('k'):
    for metric in ['zero_component_rate','boundary_response_rate']:
        n,mean,se,lo,hi=interval(cell[metric]);zero_rows.append(dict(k=k,metric=metric,n_rep=n,mean=mean,se=se,ci_low=lo,ci_high=hi))
pd.DataFrame(zero_rows).to_csv(root/'boundary_summary/zero_prevalence.csv',index=False)
# A deterministic inverse image is exactly the measured transformed event.
bs=pd.read_csv(root/'boundary_summary/summary.csv')
pullback=bs[(bs.scenario=='zeros_transformed')&bs.method.isin(['clr_l2','clr_scaled','clr_mondrian'])&bs.metric.isin(['coverage','coverage_g0','coverage_g1'])].copy()
pullback['scenario']='zeros_original_pullback'
pullback['provenance']='Exact event identity: Y in T_epsilon inverse(C) iff T_epsilon(Y) in C; copied from measured transformed coverage, no new simulation.'
pullback.to_csv(root/'boundary_summary/pullback_equivalence.csv',index=False)
rank=pd.read_csv(root/'rank_checks.csv')
# All theoretical rank targets retained, including any pointwise interval misses.
rank['mean_minus_theory']=rank.calibration_coverage_mean-rank.theory_coverage
rank['variance_ratio']=rank.calibration_coverage_variance/rank.theory_calibration_variance.replace(0,np.nan)
rank.to_csv(root/'rank_checks.csv',index=False)
manifest=dict(audit='passed',main_rows=len(main),oracle_rows=len(weighted),boundary_rows=len(boundary),prior_score_rows=len(prior),tv_k3_exact_equivalence_rows=800 if len(prior) else 0,main_cells=160 if len(prior) else 128,main_replications_per_cell=100,boundary_replications_per_cell=50,test_points_per_environment=5000,area_anchors=32,area_candidates_per_anchor=8192,weighted_iid_exact_equivalence_rows=len(a),main_infinite_threshold_records=int(frame.infinite_threshold.sum()),main_zero_area_record_count=int((frame.volume_fraction==0).sum()),main_area_candidate_se_max=float(frame.volume_mc_se_conditional.max()),rank_cells=len(rank),rank_trials_per_cell=20000,failed_resource_runs=[],exclusions='pilot seeds only; no main/extension/boundary replications excluded; finite radius summary omitted whenever any infinity; high-dimensional area intentionally unmeasured',compute=dict(core_job='job-290563a3e6',core_resource_wall_seconds=116.110,core_cpu_seconds=124.165104,extension_job='job-e0323225a2',extensions_resource_wall_seconds=43.878,extensions_cpu_seconds=45.080784),source_versions='Core and extension raw-file manifests retain their exact source SHA256; final scripts remain algorithmically compatible with all recorded measurements.')
if len(prior):
    manifest['compute']['prior_score_job']='job-e4f5364687'
    manifest['compute']['prior_score_resource_ran_seconds']=44.498
    manifest['compute']['prior_score_cpu_seconds']=45.631351
    manifest['compute']['prior_score_cell_wall_seconds_sum']=float(pd.read_json(root/'prior_scores.timings.jsonl',lines=True).seconds.sum())
(root/'audit.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
