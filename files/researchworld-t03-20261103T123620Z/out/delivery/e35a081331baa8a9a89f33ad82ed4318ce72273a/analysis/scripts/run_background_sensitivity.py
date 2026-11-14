"""Separate changed-background arm; requires a complete, audited main panel.

This is not estimator-only repeated-run evidence. Background size and the draw
both change; one draw per size cannot identify a pure size effect. Pilot first.
"""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import argparse,hashlib,json,resource,sys,time,warnings,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import joblib,numpy as np
from shap_reliability.data import load_data
from shap_reliability.estimators import Game,timed_run
from shap_reliability.metrics import run_metrics

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',choices=['acs','diabetes'],required=True);p.add_argument('--model',choices=['logistic','forest','histboost'],required=True);p.add_argument('--pilot',action='store_true');p.add_argument('--output',default='results/background');p.add_argument('--main-results',default='results');args=p.parse_args()
    main_results=ROOT/args.main_results
    manifest=json.loads((main_results/'aggregation_manifest.json').read_text())
    if manifest['status']!='complete' or manifest['n_runs']!=97200:raise ValueError('main evidence is not yet secure')
    cfg=json.loads((ROOT/'configs/main.json').read_text());cell=f'{args.dataset}_{args.model}'
    mainroot=main_results/'main'/cell;meta=json.loads((mainroot/'metadata.json').read_text())
    if meta['signature']!=manifest['signature']:raise ValueError('main source identity mismatch')
    b=joblib.load(ROOT/'artifacts'/f'{cell}_main.joblib');X,_,_,_=load_data(args.dataset)
    n=2 if args.pilot else 12;repeats=2 if args.pilot else 20;budget=cfg['budgets'][args.dataset][1]
    settings=dict(status='pilot' if args.pilot else 'main_background_sensitivity',dataset=args.dataset,model=args.model,n_instances=n,n_repeats=repeats,budgets=[budget],background_sizes=[8,128],background_seed_base=60793,run_seed_base=89273,main_signature=manifest['signature'],scope='one independent training-row draw per size; size and resampling jointly changed; same fitted model/main inputs',normalization_floor=.01,k=3)
    sources={str(q.relative_to(ROOT)):hashlib.sha256(q.read_bytes()).hexdigest() for q in sorted(list((ROOT/'src').rglob('*.py'))+[Path(__file__)])}
    signature=hashlib.sha256(json.dumps(dict(settings=settings,sources=sources),sort_keys=True).encode()).hexdigest()
    out=ROOT/args.output/cell;out.mkdir(parents=True,exist_ok=True)
    if (out/'metadata.json').exists() and json.loads((out/'metadata.json').read_text())['signature']!=signature:raise ValueError('refusing incompatible sensitivity reuse')
    metadata=dict(settings=settings,signature=signature,source_hashes=sources,main_info=b['info'],backgrounds={});start=time.perf_counter();cpu=time.process_time()
    for size in settings['background_sizes']:
        bgseed=[settings['background_seed_base'],cfg['datasets'].index(args.dataset),size]
        ids=np.random.default_rng(np.random.SeedSequence(bgseed)).choice(b['info']['train_ids'],size=size,replace=False)
        bg=b['preprocessor'].transform(X.iloc[ids]).astype(np.float32)
        metadata['backgrounds'][str(size)]=dict(filtered_positions=ids.tolist(),source_ids=X.index.to_numpy()[ids].tolist(),seed_sequence=bgseed)
        (out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        for i in range(n):
            dest=out/f'B{size:03d}_instance_{i:03d}.npz'
            if dest.exists():
                with np.load(dest,allow_pickle=False) as saved:
                    if saved['signature'].item()!=signature:raise ValueError('checkpoint signature mismatch')
                continue
            base=dict(dataset=args.dataset,model=args.model,instance=i,source_id=b['info']['source_explain_ids'][i+cfg['n_pilot_excluded']],background_size=size)
            try:
                gameargs=(b['model'],bg,b['instances'][i+cfg['n_pilot_excluded']],b['groups'])
                g=Game(*gameargs);ref,rd=timed_run(g,'exact',0,0);v=g.values([0,(1<<len(ref))-1])
                if abs(ref.sum()-(v[1]-v[0]))>1e-8:raise ValueError('sensitivity exact efficiency failure')
                rr=dict(base,v_empty=float(v[0]),v_full=float(v[1]),**rd);rows=[];phis=[]
                for e,est in enumerate(cfg['estimators']):
                    for r in range(repeats):
                        seq=[settings['run_seed_base'],cfg['datasets'].index(args.dataset),cfg['models'].index(args.model),size,i,e,r]
                        seed=int(np.random.SeedSequence(seq).generate_state(1,dtype=np.uint32)[0])
                        with warnings.catch_warnings(record=True) as ws:
                            warnings.simplefilter('always');phi,details=timed_run(Game(*gameargs),est,budget,seed)
                        metrics=run_metrics(phi,ref)
                        if not np.isfinite(phi).all() or abs(metrics['efficiency_residual'])>1e-6:raise ValueError('invalid sensitivity attribution')
                        rows.append(dict(base,estimator=est,budget=budget,repeat=r,seed=seed,status='ok',warnings=[str(w.message) for w in ws],**details,**metrics));phis.append(phi)
                with np.load(mainroot/f'instance_{i:03d}.npz',allow_pickle=False) as saved:mainref=saved['reference']
                shift=run_metrics(ref,mainref)
                tmp=dest.with_suffix('.part.npz');np.savez_compressed(tmp,reference=ref,main_reference=mainref,attributions=np.asarray(phis),run_records=np.array(json.dumps(rows)),reference_record=np.array(json.dumps(rr)),reference_shift=np.array(json.dumps(shift)),signature=np.array(signature));tmp.replace(dest)
                print(f'Background completed {cell}/B{size}/{i}',flush=True)
            except Exception as exc:
                with (out/'failures.jsonl').open('a') as f:f.write(json.dumps(dict(base,error=repr(exc),traceback=traceback.format_exc()))+'\n')
                print(f'HUTIAN_WAKE: background failure {cell}/B{size}/{i}: {exc}',flush=True);raise
        print(f'HUTIAN_WAKE: background completed {cell}/B{size}, {n} inputs, {repeats} repeats',flush=True)
    (out/'completion.json').write_text(json.dumps(dict(status='complete',pilot=args.pilot,n_instances=n,n_repeats=repeats,n_backgrounds=2,wall_seconds=time.perf_counter()-start,process_cpu_seconds=time.process_time()-cpu,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2)+'\n')
if __name__=='__main__':main()
