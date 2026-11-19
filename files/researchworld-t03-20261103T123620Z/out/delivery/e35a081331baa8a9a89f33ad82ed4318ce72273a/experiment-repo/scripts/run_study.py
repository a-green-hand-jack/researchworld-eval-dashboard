"""Checkpoint a complete fixed-game panel. Managed resource runner, no network.

One job per dataset/model is independent. Each completed input is atomically
committed to an NPZ checkpoint; a rerun verifies the configuration and source
hashes before skipping it. Failed inputs remain explicit and stop the job.
"""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import sys,argparse,json,hashlib,time,resource,traceback,warnings,subprocess,platform
SCRIPT_WALL_START=time.monotonic()
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import joblib,shap
from shap_reliability.models import prepare
from shap_reliability.estimators import Game,timed_run
from shap_reliability.metrics import run_metrics

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--model',required=True);p.add_argument('--config',default='configs/main.json');p.add_argument('--output',default='results/main');p.add_argument('--limit',type=int)
    args=p.parse_args(); cfg=json.loads((ROOT/args.config).read_text())
    if cfg['status']!='frozen':raise ValueError('main configuration is not frozen')
    dataset=args.dataset;model=args.model; cell=f'{dataset}_{model}'
    data_manifest=json.loads((ROOT/'data/manifest.json').read_text())
    record=data_manifest[dataset]
    with (ROOT/record['file']).open('rb') as raw:
        actual_data_sha=hashlib.file_digest(raw,'sha256').hexdigest()
    if actual_data_sha!=record['sha256']:raise ValueError('actual raw data differ from the recorded source version')
    out=ROOT/args.output/cell;out.mkdir(parents=True,exist_ok=True)
    sources={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(list((ROOT/'src').rglob('*.py'))+[ROOT/'scripts/run_study.py',ROOT/'scripts/fetch_data.py'])}
    signature=hashlib.sha256(json.dumps(dict(config=cfg,sources=sources),sort_keys=True).encode()).hexdigest()
    code_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    meta_path=out/'metadata.json'
    if meta_path.exists():
        old=json.loads(meta_path.read_text())
        if old['signature']!=signature:raise ValueError('refusing checkpoint reuse across configuration/source changes')
        bundle=joblib.load(ROOT/'artifacts'/f'{cell}_main.joblib')
    else:
        bundle=prepare(dataset,model,seed=cfg['model_seed'],background_size=cfg['background_size'],n_instances=cfg['n_instances']+cfg['n_pilot_excluded'],training_cap=cfg['training_cap'])
        (ROOT/'artifacts').mkdir(exist_ok=True);joblib.dump(bundle,ROOT/'artifacts'/f'{cell}_main.joblib')
        metadata=dict(hardware={'platform':platform.platform(),'affinity_cpus':len(os.sched_getaffinity(0)),'thread_limits':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']},'cpu_model':next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),'unknown')},config=cfg,signature=signature,source_hashes=sources,code_revision=code_revision,info=bundle['info'],data_manifest=json.loads((ROOT/'data/manifest.json').read_text()),library_versions={k:__import__('importlib.metadata',fromlist=['version']).version(k) for k in ['numpy','scipy','pandas','scikit-learn','shap','folktables','joblib']})
        meta_path.write_text(json.dumps(metadata,indent=2)+'\n')
    n=cfg['n_instances'] if args.limit is None else min(args.limit,cfg['n_instances'])
    print(f'Start {cell}; n={n}; signature={signature}',flush=True)
    for local in range(n):
        dest=out/f'instance_{local:03d}.npz'
        if dest.exists():continue
        i=local+cfg['n_pilot_excluded']; source_id=bundle['info']['source_explain_ids'][i]
        base=dict(dataset=dataset,model=model,instance=local,source_id=source_id,background_size=cfg['background_size'])
        try:
            game_args=(bundle['model'],bundle['background'],bundle['instances'][i],bundle['groups'])
            print(f'Reference {cell}/{local}',flush=True)
            refgame=Game(*game_args)
            ref,refdetails=timed_run(refgame,'exact',0,0)
            endpoints=refgame.values([0,(1<<len(ref))-1])
            if abs(ref.sum()-(endpoints[1]-endpoints[0]))>1e-8:raise ValueError('reference efficiency check failed')
            refrecord=dict(base,reference_method='exact_empirical_coalition_enumeration',n_coalitions=1<<len(ref),v_empty=float(endpoints[0]),v_full=float(endpoints[1]),**refdetails)
            # Free the German million-coalition cache before stochastic calls.
            del refgame
            rows=[]; phis=[]
            for e,est in enumerate(cfg['estimators']):
              for b,budget in enumerate(cfg['budgets'][dataset]):
                for r in range(cfg['n_repeats']):
                    # Independent SeedSequences across all estimator/budget/case cells.
                    seq=np.random.SeedSequence([cfg['run_seed_base'],cfg['datasets'].index(dataset),cfg['models'].index(model),local,e,b,r])
                    seed=int(seq.generate_state(1,dtype=np.uint32)[0])
                    with warnings.catch_warnings(record=True) as ws:
                        warnings.simplefilter('always')
                        phi,details=timed_run(Game(*game_args),est,budget,seed)
                    if not np.all(np.isfinite(phi)):raise ValueError('nonfinite attribution')
                    metrics=run_metrics(phi,ref,k=cfg['k'],denominator_floor=cfg['normalization_floor'])
                    if abs(metrics['efficiency_residual'])>1e-6:raise ValueError('stochastic efficiency check failed')
                    row=dict(base,estimator=est,budget=budget,repeat=r,seed=seed,warnings=[str(w.message) for w in ws],status='ok',**details,**metrics)
                    rows.append(row);phis.append(phi)
            tmp=dest.with_suffix('.part.npz')
            np.savez_compressed(tmp,reference=ref,attributions=np.asarray(phis),run_records=np.array(json.dumps(rows)),reference_record=np.array(json.dumps(refrecord)),signature=np.array(signature))
            tmp.replace(dest)
            print(f'Completed {cell}/{local}; peak_rss_kib={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}',flush=True)
            if (local+1)%10==0 or local==n-1:print(f'HUTIAN_WAKE: main completed {cell} {local+1}/{n} inputs',flush=True)
        except Exception as exc:
            with (out/'failures.jsonl').open('a') as f:f.write(json.dumps(dict(base,error=repr(exc),traceback=traceback.format_exc()))+'\n')
            print(f'HUTIAN_WAKE: main failure {cell}/{local}: {exc}',flush=True)
            raise
    (out/'completion.json').write_text(json.dumps(dict(status='complete',n_completed=n,wall_seconds=time.monotonic()-SCRIPT_WALL_START,process_total_cpu_seconds=time.process_time(),peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2)+'\n')
if __name__=='__main__':main()
