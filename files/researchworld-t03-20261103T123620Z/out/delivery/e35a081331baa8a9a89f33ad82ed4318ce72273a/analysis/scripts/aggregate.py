"""Aggregate completed panels; never substitute pilot or incomplete checkpoints."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import sys,argparse,json,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np,pandas as pd
from scipy.stats import norm
from audit_panel import audit
from shap_reliability.metrics import run_metrics,pairwise_metrics,cluster_bootstrap

RATE_METRICS={'top1_match','signed_top1_match','topk_overlap','signed_topk_overlap','topk_jaccard','topk_exact_match','sign_agreement'}
NUMERIC_METRICS=['absolute_l1_error','nl1_error','top1_match','signed_top1_match','topk_overlap','signed_topk_overlap','topk_jaccard','topk_exact_match','sign_agreement','abs_rank_spearman','error_success_0p1','error_success_0p2','error_success_0p4','joint_success_0p1','joint_success_0p2','joint_success_0p4','strict_joint_success_0p1','strict_joint_success_0p2','strict_joint_success_0p4','tie_aware_joint_success_0p2','prediction_rows','wall_seconds','cpu_seconds']

def wilson(count,total):
    z=norm.ppf(.975);p=count/total;denom=1+z*z/total
    center=(p+z*z/(2*total))/denom;half=z*np.sqrt(p*(1-p)/total+z*z/(4*total*total))/denom
    return float(center-half),float(center+half)

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',default='results/main');p.add_argument('--output',default='results');p.add_argument('--allow-partial',action='store_true');args=p.parse_args()
    root=ROOT/args.input;output=ROOT/args.output;output.mkdir(parents=True,exist_ok=True)
    audit_result=audit(root,args.allow_partial)
    (output/'panel_audit.json').write_text(json.dumps(audit_result,indent=2)+'\n')
    runrows=[];refs=[];models=[];pairrows=[];meanrows=[];completions=[];signatures=set()
    for cell in sorted(root.iterdir()):
        if not cell.is_dir():continue
        meta=json.loads((cell/'metadata.json').read_text());cfg=meta['config'];signatures.add(meta['signature'])
        data,model=meta['info']['version'],meta['info']['model']
        paths=sorted(cell.glob('instance_[0-9][0-9][0-9].npz'))
        if len(paths)!=cfg['n_instances']:raise ValueError(f'incomplete panel: {cell}, {len(paths)}/{cfg["n_instances"]}')
        comp=json.loads((cell/'completion.json').read_text());completions.append(dict(cell=cell.name,**comp))
        info=meta['info'];modelrow={k:v for k,v in info.items() if not isinstance(v,(list,dict))};modelrow['dataset']=cell.name.rsplit('_',1)[0];models.append(modelrow)
        for path in paths:
            a=np.load(path,allow_pickle=False)
            if a['signature'].item()!=meta['signature']:raise ValueError('checkpoint signature mismatch')
            rows=json.loads(a['run_records'].item());refrecord=json.loads(a['reference_record'].item());ref=a['reference'];phis=a['attributions'];order=np.argsort(-np.abs(ref),kind='stable');k=cfg['k'];scale=float(abs(ref).sum());tol=cfg['sign_tie_tolerance']
            gap1=float(abs(ref[order[0]])-abs(ref[order[1]]));gapk=float(abs(ref[order[k-1]])-abs(ref[order[k]]))
            refs.append(dict(refrecord,reference_l1=scale,reference_efficiency_residual=float(ref.sum()-(refrecord['v_full']-refrecord['v_empty'])),top1_gap_absolute=gap1,topk_gap_absolute=gapk,top1_numerical_tie=gap1<=2*tol,topk_boundary_numerical_tie=gapk<=2*tol,selected_sign_numerical_ambiguity=bool(np.any(abs(ref[order[:k]])<=tol)),n_active_sign_features=int((abs(ref)>=.01*max(scale,.01)).sum()),top3_l1_share=float(abs(ref[order[:k]]).sum()/scale) if scale else float('nan'),low_signal=scale<.01))
            if len(rows)!=len(cfg['estimators'])*len(cfg['budgets'][refrecord['dataset']])*cfg['n_repeats']:raise ValueError('run denominator mismatch')
            for row in rows:
                row['warnings']=json.dumps(row['warnings']);runrows.append(row)
            local=pd.DataFrame(rows)
            for (est,budget),group in local.groupby(['estimator','budget'],sort=True):
                idx=group.index.to_numpy();vecs=phis[idx];base={k:rows[idx[0]][k] for k in ['dataset','model','instance','source_id','background_size']};base.update(estimator=est,budget=int(budget))
                pairrows.append(dict(base,**pairwise_metrics(vecs,ref)))
                meanrows.append(dict(base,n_averaged=len(idx),total_prediction_rows=int(group['prediction_rows'].sum()),**run_metrics(vecs.mean(axis=0),ref)))
    if len(signatures)!=1:raise ValueError('main cells do not share source/config signature')
    expected={f'{d}_{m}' for d in cfg['datasets'] for m in cfg['models']}
    observed={x['cell'] for x in completions}
    if observed!=expected and not args.allow_partial:raise ValueError(f'missing entire model cells: {sorted(expected-observed)}')
    runs=pd.DataFrame(runrows);runs.to_parquet(output/'run_metrics.parquet',index=False)
    pd.DataFrame(refs).to_csv(output/'reference_diagnostics.csv',index=False)
    pd.DataFrame(models).to_csv(output/'model_diagnostics.csv',index=False)
    pd.DataFrame(meanrows).to_csv(output/'averaged_run_metrics.csv',index=False)
    pairs=pd.DataFrame(pairrows);pairs.to_csv(output/'instance_repeatability.csv',index=False)
    pd.DataFrame(completions).to_csv(output/'job_costs.csv',index=False)
    aggregate=[];strata=[];case=[];paired=[];assess=[];floor_sensitivity=[]
    keys=['dataset','model','estimator','budget','background_size']
    for key,group in runs.groupby(keys,sort=True):
        base=dict(zip(keys,key));ordered=group.sort_values(['instance','repeat']);n=ordered['instance'].nunique();r=ordered['repeat'].nunique()
        refpanel=pd.DataFrame(refs);rp=refpanel[(refpanel['dataset']==base['dataset'])&(refpanel['model']==base['model'])]
        assess.append(dict(base,n_instances=n,n_runs=len(group),n_exact_references=len(rp),n_failed_runs=0,n_unresolved_references=0,n_top1_numerical_ties=int(rp['top1_numerical_tie'].sum()),n_topk_boundary_numerical_ties=int(rp['topk_boundary_numerical_tie'].sum()),n_selected_sign_ambiguous=int(rp['selected_sign_numerical_ambiguity'].sum()),n_low_signal=int(rp['low_signal'].sum()),n_active_sign_assessable=int((rp['n_active_sign_features']>0).sum()),primary_denominator='all exact-reference instances, including numerical ties and weak signals; stable raw-index tie rule'))
        for floor in [.001,.01,.05]:
            nl1=ordered['absolute_l1_error'].to_numpy()/np.maximum(ordered['reference_l1'].to_numpy(),floor)
            success=((nl1<=.2)&(ordered['signed_topk_overlap'].to_numpy()>=2/3)).astype(float)
            for name,vals in [('nl1_error',nl1),('joint_success_0p2',success)]:
                floor_sensitivity.append(dict(base,normalization_floor=floor,metric=name,**cluster_bootstrap(vals.reshape(n,r),n_bootstrap=cfg['n_bootstrap'],seed=cfg['bootstrap_seed'],bounded_01=name=='joint_success_0p2')))
        if len(ordered)!=n*r:raise ValueError('ragged successful-run panel')
        for metric in NUMERIC_METRICS:
            values=ordered[metric].to_numpy().reshape(n,r)
            aggregate.append(dict(base,metric=metric,**cluster_bootstrap(values,n_bootstrap=cfg['n_bootstrap'],seed=cfg['bootstrap_seed'],bounded_01=metric in RATE_METRICS or 'success_' in metric)))
        for instance,g in group.groupby('instance'):
            s=int(g['joint_success_0p2'].sum());lo,hi=wilson(s,len(g))
            case.append(dict(base,instance=int(instance),source_id=int(g['source_id'].iloc[0]),successes=s,n_repeats=len(g),success_rate=s/len(g),wilson_low=lo,wilson_high=hi,reference_l1=g['reference_l1'].iloc[0],top1_gap_normalized=g['top1_gap_normalized'].iloc[0],topk_gap_normalized=g['topk_gap_normalized'].iloc[0],low_signal=g['low_signal'].iloc[0],near_tie_top1=g['near_tie_top1'].iloc[0]))
        for label,mask in [('near_top1_tie',group['near_tie_top1']==1),('separated_top1',group['near_tie_top1']==0),('low_signal',group['low_signal']==1),('nonlow_signal',group['low_signal']==0)]:
            g=group[mask].sort_values(['instance','repeat']);nn=g['instance'].nunique()
            for metric in ['joint_success_0p2','top1_match','nl1_error']:
                if nn>=2:stats=cluster_bootstrap(g[metric].to_numpy().reshape(nn,r),n_bootstrap=cfg['n_bootstrap'],seed=cfg['bootstrap_seed'],bounded_01=metric in RATE_METRICS or 'success_' in metric)
                else:stats=dict(estimate=float(g[metric].mean()) if nn else float('nan'),ci_low=float('nan'),ci_high=float('nan'),n_instances=nn,n_repeats=r,n_bootstrap=0,interval='insufficient instances for interval')
                strata.append(dict(base,stratum=label,metric=metric,**stats))
    # Paired instance contrasts. Runs have independent seeds, so their index pairing
    # is arbitrary; each case contrast is the difference of the two run means.
    for (data,model,bg),g in runs.groupby(['dataset','model','background_size']):
        panels={key:gg.sort_values(['instance','repeat']) for key,gg in g.groupby(['estimator','budget'])}
        for a,b in itertools.combinations(sorted(panels),2):
            if a[0]!=b[0] and a[1]!=b[1]:continue
            ga,gb=panels[a],panels[b]
            if not np.array_equal(ga['instance'],gb['instance']):raise ValueError('unpaired instance contrast')
            n=ga['instance'].nunique();r=ga['repeat'].nunique()
            for metric in ['joint_success_0p2','nl1_error','top1_match']:
                val=(ga[metric].to_numpy()-gb[metric].to_numpy()).reshape(n,r)
                paired.append(dict(dataset=data,model=model,background_size=bg,estimator_a=a[0],budget_a=a[1],estimator_b=b[0],budget_b=b[1],metric=metric,contrast='a_minus_b',**cluster_bootstrap(val,n_bootstrap=cfg['n_bootstrap'],seed=cfg['bootstrap_seed'])))
    pd.DataFrame(assess).to_csv(output/'assessability_counts.csv',index=False)
    pd.DataFrame(floor_sensitivity).to_csv(output/'floor_sensitivity.csv',index=False)
    pd.DataFrame(aggregate).to_csv(output/'aggregate_metrics.csv',index=False)
    pd.DataFrame(strata).to_csv(output/'stratified_metrics.csv',index=False)
    pd.DataFrame(case).to_csv(output/'instance_success.csv',index=False)
    pd.DataFrame(paired).to_csv(output/'paired_contrasts.csv',index=False)
    # Pairwise summaries are inferred over independent instances, never seed pairs.
    pa=[]
    for key,g in pairs.groupby(keys,sort=True):
      for metric in ['pairwise_top1_agreement','pairwise_normalized_l1','pairwise_run_normalized_l1','pairwise_signed_topk_overlap','pairwise_topk_overlap','pairwise_joint_agreement_0p2','modal_top1_share']:
        pa.append(dict(zip(keys,key),metric=metric,**cluster_bootstrap(g[metric].to_numpy()[:,None],n_bootstrap=cfg['n_bootstrap'],seed=cfg['bootstrap_seed'],bounded_01='normalized_l1' not in metric)))
    pd.DataFrame(pa).to_csv(output/'aggregate_repeatability.csv',index=False)
    (output/'aggregation_manifest.json').write_text(json.dumps(dict(status='complete' if observed==expected else 'partial_debug',n_runs=len(runs),n_reference_inputs=len(refs),n_model_cells=len(models),signature=next(iter(signatures)),source='results/main/*/instance_*.npz',failed_runs_in_denominator=0,intervals='pointwise; no multiple-comparison adjustment; conditional on fixed split/model/background'),indent=2)+'\n')
    print(f'Aggregated {len(runs)} actual calls, {len(refs)} exact references, {len(models)} fitted models',flush=True)
if __name__=='__main__':main()
