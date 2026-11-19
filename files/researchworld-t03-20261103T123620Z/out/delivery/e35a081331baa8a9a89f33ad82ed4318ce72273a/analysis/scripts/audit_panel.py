"""Independent vector/denominator/provenance audit of saved panel checkpoints.

No model predictions are rerun. --allow-partial is for development only.
--allow-incomplete audits an atomic-checkpoint snapshot, always labeled in_progress.
"""
import argparse,hashlib,itertools,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def audit(root,allow_partial=False,allow_incomplete=False):
    cells=sorted(p for p in root.iterdir() if p.is_dir())
    if not cells:raise ValueError('no panel cells')
    signatures=set();n_runs=n_refs=0;seeds=set();failures=[];max_ref_eff=max_run_eff=max_metric_delta=0.;exhaustive=warnings=0;cell_summaries=[];pending_metadata=[]
    for cell in cells:
        if not (cell/'metadata.json').exists():
            if allow_incomplete:
                pending_metadata.append(cell.name);continue
            raise ValueError('missing model metadata')
        meta=json.loads((cell/'metadata.json').read_text());cfg=meta['config'];signatures.add(meta['signature'])
        signature=hashlib.sha256(json.dumps(dict(config=cfg,sources=meta['source_hashes']),sort_keys=True).encode()).hexdigest()
        if signature!=meta['signature']:raise ValueError('metadata signature is not reproducible')
        for source,digest in meta['source_hashes'].items():
            if hashlib.sha256((ROOT/source).read_bytes()).hexdigest()!=digest:raise ValueError(f'delivered source differs from executing source: {source}')
        if cfg['status']!='frozen':raise ValueError('unfrozen config')
        dataset,model=cell.name.rsplit('_',1)
        complete=(cell/'completion.json').exists()
        if complete:
            comp=json.loads((cell/'completion.json').read_text())
            if comp['status']!='complete' or comp['n_completed']!=cfg['n_instances']:raise ValueError('incomplete job')
        elif not allow_incomplete:raise ValueError('incomplete job')
        cell_reference_cpu=cell_stochastic_cpu=0.
        paths=sorted(cell.glob('instance_[0-9][0-9][0-9].npz'))
        expected_n=len(paths) if allow_incomplete else cfg['n_instances']
        if expected_n>cfg['n_instances'] or [p.name for p in paths]!=[f'instance_{i:03d}.npz' for i in range(expected_n)]:raise ValueError('missing/extra panel indices')
        if (cell/'failures.jsonl').exists():failures.extend(json.loads(s) for s in (cell/'failures.jsonl').read_text().splitlines())
        for i,path in enumerate(paths):
            with np.load(path,allow_pickle=False) as a:
                ref=a['reference'];phis=a['attributions'];rr=json.loads(a['reference_record'].item());rows=json.loads(a['run_records'].item())
                if a['signature'].item()!=signature:raise ValueError('checkpoint signature mismatch')
            n=len(rows);d=len(ref);n_runs+=n;n_refs+=1
            cell_reference_cpu+=rr['cpu_seconds'];cell_stochastic_cpu+=sum(r['cpu_seconds'] for r in rows)
            if phis.shape!=(n,d) or not np.isfinite(phis).all() or not np.isfinite(ref).all():raise ValueError('invalid attribution array')
            expected=list(itertools.product(cfg['estimators'],cfg['budgets'][dataset],range(cfg['n_repeats'])))
            if [(r['estimator'],r['budget'],r['repeat']) for r in rows]!=expected:raise ValueError('run keys not exactly the configured grid')
            source_id=meta['info']['source_explain_ids'][i+cfg['n_pilot_excluded']]
            for r in [rr,*rows]:
                if (r['dataset'],r['model'],r['instance'],r['source_id'],r['background_size'])!=(dataset,model,i,source_id,cfg['background_size']):raise ValueError('identity mismatch')
            if rr['n_coalitions']!=2**d or rr['reference_method']!='exact_empirical_coalition_enumeration' or not rr['exhaustive']:raise ValueError('non-exact reference')
            re=abs(ref.sum()-(rr['v_full']-rr['v_empty']));max_ref_eff=max(max_ref_eff,re)
            if re>1e-8:raise ValueError('reference efficiency violation')
            ae=np.abs(phis-ref).sum(axis=1);nl1=ae/max(np.abs(ref).sum(),cfg['normalization_floor'])
            ref_top=np.argsort(-np.abs(ref),kind='stable')[:cfg['k']]
            orders=np.argsort(-np.abs(phis),axis=1,kind='stable')[:,:cfg['k']]
            overlap=np.array([sum(j in ref_top and np.sign(p[j])==np.sign(ref[j]) for j in order)/len(ref_top) for p,order in zip(phis,orders)])
            success=(nl1<=cfg['primary_l1_cutoff'])&(overlap>=cfg['primary_signed_topk_overlap'])
            for key,values in [('absolute_l1_error',ae),('nl1_error',nl1),('signed_topk_overlap',overlap),('joint_success_0p2',success)]:
                delta=float(np.max(np.abs(np.array([r[key] for r in rows])-values)));max_metric_delta=max(max_metric_delta,delta)
                if delta>1e-12:raise ValueError(f'saved metric differs from vectors: {key}')
            eff=np.abs(phis.sum(axis=1)-ref.sum());max_run_eff=max(max_run_eff,float(eff.max()))
            if eff.max()>1e-6:raise ValueError('run efficiency violation')
            for r in rows:
                seq=[cfg['run_seed_base'],cfg['datasets'].index(dataset),cfg['models'].index(model),i,cfg['estimators'].index(r['estimator']),cfg['budgets'][dataset].index(r['budget']),r['repeat']]
                seed=int(np.random.SeedSequence(seq).generate_state(1,dtype=np.uint32)[0])
                if seed!=r['seed']:raise ValueError('seed provenance mismatch')
                if seed in seeds:raise ValueError('legacy RNG seed collision')
                seeds.add(seed)
                if r['status']!='ok' or r['prediction_rows']<=0 or r['cpu_seconds']<0:raise ValueError('invalid status/cost')
                if r['estimator']=='kernel' and r.get('kernel_design_rank',0)!=r.get('kernel_design_columns',0):raise ValueError('rank deficient kernel solve')
                exhaustive+=bool(r['exhaustive']);warnings+=len(r['warnings'])
        cell_summaries.append(dict(cell=cell.name,n_checkpointed_inputs=len(paths),n_configured_inputs=cfg['n_instances'],completion_record_present=complete,exact_reference_cpu_seconds=cell_reference_cpu,stochastic_cpu_seconds=cell_stochastic_cpu))
    expected_cells={f'{d}_{m}' for d in cfg['datasets'] for m in cfg['models']};observed={p.name for p in cells}
    if observed!=expected_cells and not (allow_partial or allow_incomplete):raise ValueError(f'incomplete matrix: {sorted(expected_cells-observed)}')
    if len(signatures)!=1:raise ValueError('mixed source/config signatures')
    return dict(status='in_progress' if allow_incomplete else ('complete' if observed==expected_cells else 'partial_debug'),cells=cell_summaries,pending_metadata_cells=pending_metadata,n_model_cells=len(cell_summaries),n_reference_inputs=n_refs,n_runs=n_runs,n_unique_seeds=len(seeds),max_reference_efficiency_residual=max_ref_eff,max_run_efficiency_residual=max_run_eff,max_saved_metric_difference=max_metric_delta,exhaustive_stochastic_calls=exhaustive,warning_messages=warnings,recorded_failed_attempts=len(failures),failures=failures,signature=next(iter(signatures)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',default='results/main');p.add_argument('--output',default='results/panel_audit.json');p.add_argument('--allow-partial',action='store_true');p.add_argument('--allow-incomplete',action='store_true');a=p.parse_args()
    result=audit(ROOT/a.input,a.allow_partial,a.allow_incomplete);out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
