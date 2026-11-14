"""Audit and summarize the separate changed-background arm, never main data."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np,pandas as pd
from shap_reliability.metrics import run_metrics,cluster_bootstrap

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',default='results/background');p.add_argument('--output',default='results/background_sensitivity');p.add_argument('--allow-pilot',action='store_true');p.add_argument('--main-results',default='results');a=p.parse_args()
    root=ROOT/a.input;out=ROOT/a.output;out.mkdir(parents=True,exist_ok=True)
    rows=[];references=[];shifts=[];costs=[];main_signatures=set();seen_seeds=set();cells=set();failed_attempts=[];warning_count=0
    cfg=json.loads((ROOT/'configs/main.json').read_text())
    main_manifest=json.loads((ROOT/a.main_results/'aggregation_manifest.json').read_text())
    if main_manifest['status']!='complete':raise ValueError('main evidence is not complete')
    for cell in sorted(p for p in root.iterdir() if p.is_dir()):
        meta=json.loads((cell/'metadata.json').read_text());s=meta['settings'];comp=json.loads((cell/'completion.json').read_text());cells.add(cell.name);main_signatures.add(s['main_signature'])
        expected_sig=hashlib.sha256(json.dumps(dict(settings=s,sources=meta['source_hashes']),sort_keys=True).encode()).hexdigest()
        if expected_sig!=meta['signature']:raise ValueError('metadata signature mismatch')
        for source,digest in meta['source_hashes'].items():
            if hashlib.sha256((ROOT/source).read_bytes()).hexdigest()!=digest:raise ValueError('delivered sensitivity source mismatch')
        if s['main_signature']!=main_manifest['signature']:raise ValueError('wrong main evidence identity')
        mainroot=ROOT/a.main_results/'main'/cell.name
        mainmeta=json.loads((mainroot/'metadata.json').read_text())
        if meta['main_info']!=mainmeta['info']:raise ValueError('changed main model/input provenance')
        expected_n=2 if s['status']=='pilot' else 12;expected_r=2 if s['status']=='pilot' else 20
        if (s['n_instances'],s['n_repeats'],s['background_sizes'],s['budgets'])!=(expected_n,expected_r,[8,128],[cfg['budgets'][s['dataset']][1]]):raise ValueError('changed planned sensitivity grid')
        for size in s['background_sizes']:
            bgseq=[60793,cfg['datasets'].index(s['dataset']),size]
            ids=np.random.default_rng(np.random.SeedSequence(bgseq)).choice(mainmeta['info']['train_ids'],size=size,replace=False).tolist()
            if meta['backgrounds'][str(size)]['filtered_positions']!=ids or meta['backgrounds'][str(size)]['seed_sequence']!=bgseq:raise ValueError('background is not the recorded training-only draw')
        if s['status']!='main_background_sensitivity' and not a.allow_pilot:raise ValueError('pilot is not main background evidence')
        if comp['status']!='complete' or comp['n_instances']!=expected_n or comp['n_repeats']!=expected_r or comp['n_backgrounds']!=2:raise ValueError('incomplete sensitivity cell')
        paths=sorted(cell.glob('B*_instance_*.npz'))
        if len(paths)!=s['n_instances']*len(s['background_sizes']):raise ValueError('incomplete background panel')
        costs.append(dict(dataset=s['dataset'],model=s['model'],**comp))
        if (cell/'failures.jsonl').exists():failed_attempts.extend(json.loads(x) for x in (cell/'failures.jsonl').read_text().splitlines())
        for size in s['background_sizes']:
            for i in range(s['n_instances']):
                with np.load(cell/f'B{size:03d}_instance_{i:03d}.npz',allow_pickle=False) as v:
                    if v['signature'].item()!=expected_sig:raise ValueError('checkpoint signature mismatch')
                    ref=v['reference'];mainref=v['main_reference'];phis=v['attributions'];records=json.loads(v['run_records'].item());rr=json.loads(v['reference_record'].item())
                if phis.shape!=(2*s['n_repeats'],len(ref)) or len(ref)!=mainmeta['info']['n_features'] or not np.isfinite(phis).all() or not np.isfinite(ref).all():raise ValueError('invalid sensitivity vectors')
                with np.load(mainroot/f'instance_{i:03d}.npz',allow_pickle=False) as main:
                    if not np.array_equal(mainref,main['reference']):raise ValueError('wrong main reference')
                    mainrr=json.loads(main['reference_record'].item())
                expected_source=mainmeta['info']['source_explain_ids'][i+cfg['n_pilot_excluded']]
                if rr['source_id']!=expected_source or abs(rr['v_full']-mainrr['v_full'])>1e-12:raise ValueError('changed explained input/prediction')
                expected=[(e,r) for e in ['permutation','kernel'] for r in range(s['n_repeats'])]
                if [(r['estimator'],r['repeat']) for r in records]!=expected:raise ValueError('sensitivity run grid mismatch')
                if abs(ref.sum()-(rr['v_full']-rr['v_empty']))>1e-8 or not rr['exhaustive'] or rr['unique_coalitions']!=2**len(ref):raise ValueError('invalid exact changed-game reference')
                base=dict(dataset=s['dataset'],model=s['model'],background_size=size,instance=i,source_id=rr['source_id'])
                references.append(dict(rr,reference_l1=float(abs(ref).sum()),efficiency_residual=float(ref.sum()-(rr['v_full']-rr['v_empty']))))
                shifts.append(dict(base,comparison='changed_exact_reference_vs_main_B32_exact_reference',**run_metrics(ref,mainref)))
                for phi,r in zip(phis,records):
                    if (r['dataset'],r['model'],r['background_size'],r['instance'],r['source_id'])!=(s['dataset'],s['model'],size,i,rr['source_id']):raise ValueError('identity mismatch')
                    metrics=run_metrics(phi,ref)
                    for key in ['nl1_error','joint_success_0p2','signed_topk_overlap']:
                        if abs(metrics[key]-r[key])>1e-12:raise ValueError('saved sensitivity metric mismatch')
                    seq=[89273,cfg['datasets'].index(s['dataset']),cfg['models'].index(s['model']),size,i,cfg['estimators'].index(r['estimator']),r['repeat']]
                    expected_seed=int(np.random.SeedSequence(seq).generate_state(1,dtype=np.uint32)[0])
                    if r['seed']!=expected_seed or r['budget']!=s['budgets'][0]:raise ValueError('sensitivity seed/budget mismatch')
                    if r['estimator']=='kernel' and r.get('kernel_design_rank',0)!=r.get('kernel_design_columns',0):raise ValueError('sensitivity Kernel rank deficiency')
                    warning_count+=len(r['warnings'])
                    if r['seed'] in seen_seeds:raise ValueError('sensitivity legacy seed collision')
                    seen_seeds.add(r['seed'])
                    if r['status']!='ok' or abs(metrics['efficiency_residual'])>1e-6:raise ValueError('failed sensitivity run')
                    r['warnings']=json.dumps(r['warnings']);rows.append(r)
    if not a.allow_pilot and cells!={f'{d}_{m}' for d in ['acs','diabetes'] for m in ['logistic','forest','histboost']}:raise ValueError('missing entire sensitivity cell')
    if len(main_signatures)!=1:raise ValueError('mixed main source identity')
    runs=pd.DataFrame(rows);runs.to_parquet(out/'run_metrics.parquet',index=False)
    pd.DataFrame(references).to_csv(out/'reference_diagnostics.csv',index=False);shift=pd.DataFrame(shifts);shift.to_csv(out/'reference_shift.csv',index=False);pd.DataFrame(costs).to_csv(out/'job_costs.csv',index=False)
    stats=[];shiftstats=[]
    for key,g in runs.groupby(['dataset','model','background_size','estimator','budget']):
        base=dict(zip(['dataset','model','background_size','estimator','budget'],key));g=g.sort_values(['instance','repeat']);n=g['instance'].nunique();r=g['repeat'].nunique()
        if len(g)!=n*r:raise ValueError('ragged sensitivity panel')
        for metric in ['joint_success_0p2','nl1_error','absolute_l1_error','signed_topk_overlap','top1_match','prediction_rows','cpu_seconds','wall_seconds']:
            stats.append(dict(base,metric=metric,**cluster_bootstrap(g[metric].to_numpy().reshape(n,r),bounded_01=metric in ['joint_success_0p2','signed_topk_overlap','top1_match'])))
    for key,g in shift.groupby(['dataset','model','background_size']):
        for metric in ['nl1_error','absolute_l1_error','signed_topk_overlap','top1_match','joint_success_0p2']:
            shiftstats.append(dict(zip(['dataset','model','background_size'],key),metric=metric,**cluster_bootstrap(g[metric].to_numpy()[:,None],bounded_01=metric in ['signed_topk_overlap','top1_match','joint_success_0p2'])))
    pd.DataFrame(stats).to_csv(out/'aggregate_metrics.csv',index=False);pd.DataFrame(shiftstats).to_csv(out/'aggregate_reference_shift.csv',index=False)
    manifest=dict(status='pilot_debug' if a.allow_pilot else 'complete',n_runs=len(runs),n_reference_inputs=len(references),n_model_cells=len(cells),n_unique_seeds=len(seen_seeds),n_captured_warning_messages=warning_count,n_failed_attempts=len(failed_attempts),failed_attempts=failed_attempts,main_signature=next(iter(main_signatures)),scope='conditional changed-background check; one draw per size confounds size and resampling; no German/model-refit/general background-variance claim',intervals='pointwise independent-instance cluster; actual n_instances/n_repeats recorded per row; finite boundary guard; fixed trained models/each background draw',cost_scope='cell process/wall timers start after imports/bundle/data loading; resource-reported job spend is retained separately and may undershoot process timers due to sampling; peak RSS is whole process')
    (out/'aggregation_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)
if __name__=='__main__':main()
