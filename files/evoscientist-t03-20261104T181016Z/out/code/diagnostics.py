"""Frozen background-size, official-library adapter, and uncached-latency diagnostics."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']: os.environ[k]='1'
from pathlib import Path
import argparse, json, time, warnings, traceback
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from run_experiments import ROOT,OUT,DS,MODELS,PS,inputs,path_for,rng_for,design
from shap_audit import *

def background_task(arg):
    ds,model,slot,b=arg; dest=path_for(ds,model,11,slot,f'background_b{b}')
    if dest.exists(): return dict(task=dest.name,b=b,status='exists')
    t=time.process_time(); data,point,c=inputs(ds,model,11,slot,b); d=c.d; c.fill(np.arange(1<<d,dtype=np.uint32)); ref=exact_phi(c.vals,d)
    plans,_=design(ds,model,11,slot,d); attr=np.zeros((2,3,64,d)); ranks=np.empty((3,64),dtype=int)
    for (im,ip,rep),(mm,oo) in plans.items():
        if im==0: ph,r,s=kernel_fit(mm,c(mm),d); ranks[ip,rep]=r
        else: ph=permutation_fit(c(mm),oo,d)
        attr[im,ip,rep]=ph
    np.savez_compressed(dest,dataset=ds,model=model,seed=11,slot=slot,point=point,b=b,d=d,reference=ref,attributions=attr,ranks=ranks,cpu_s=time.process_time()-t,actual_rows=c.game.actual_rows,cache_masks=c.keys,cache_values=c.vals)
    return dict(task=dest.name,b=b,status='done',cpu_s=time.process_time()-t)

def load_cache(ds,model,slot):
    data,point,c=inputs(ds,model,11,slot); main=path_for(ds,model,11,slot)
    if main.exists():
        raw=np.load(main); c.set(raw['cache_masks'],raw['cache_values']); ref=raw['reference']; qualified=bool(raw['qualified'])
    elif c.d<=10:
        c.fill(np.arange(1<<c.d,dtype=np.uint32)); ref=exact_phi(c.vals,c.d); qualified=True
    else: raise RuntimeError('German main reference must exist before diagnostics')
    return c,ref,qualified

def adapter_task(arg):
    ds,model,slot=arg; dest=path_for(ds,model,11,slot,'library')
    if dest.exists(): return dict(task=dest.name,status='exists')
    import shap
    c,ref,qual=load_cache(ds,model,slot); d=c.d; attrs=[]; records=[]; repeats=8 if ds=='german' else 16
    for p in [1,16]:
        for mode in ['default','no_l1']:
            for rep in range(repeats):
                count=[0]; masks_seen=[]
                def fun(z):
                    assert np.all((z==0)|(z==1)), 'Adapter requires exactly binary masks'
                    masks=maskint(z); count[0]+=len(masks); masks_seen.extend(masks.tolist()); return c(masks)
                np.random.seed(int(rng_for(ds,model,11,slot,5,mode=='no_l1',p,rep).integers(0,2**31-1)))
                cpu=time.process_time(); wall=time.perf_counter()
                with warnings.catch_warnings(record=True) as ww:
                    warnings.simplefilter('always'); explainer=shap.KernelExplainer(fun,np.zeros((1,d)),link='identity')
                    kw={} if mode=='default' else dict(l1_reg=0)
                    phi=np.asarray(explainer.shap_values(np.ones((1,d)),nsamples=2*(d-1)*p,silent=True,**kw)).reshape(d)
                attrs.append(phi); met=metrics(phi,ref)
                records.append(dict(dataset=ds,model=model,slot=slot,p=p,mode=mode,rep=rep,requested_cap=2+2*(d-1)*p,adapter_calls=count[0],adapter_unique=len(set(masks_seen)),actual_interior_samples=int(explainer.nsamplesAdded),nonzero=int(np.sum(np.abs(phi)>1e-12)),success=bool(met['success'][0]),error=float(met['error'][0]),qualified=qual,cpu_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,warnings=[str(w.message) for w in ww]))
    np.savez_compressed(dest,attributions=np.array(attrs),reference=ref,records=json.dumps(records),shap_version=shap.__version__,cache_masks=c.keys,cache_values=c.vals)
    return dict(task=dest.name,status='done',records=len(records))

def timing_task(arg):
    ds,model,slot=arg; dest=path_for(ds,model,11,slot,'timing')
    if dest.exists(): return dict(task=dest.name,status='exists')
    data,point,c=inputs(ds,model,11,slot); game=c.game; d=game.d; records=[]
    # Warm-up is explicitly separate, not included in the reported fresh-run latency.
    warmcpu=time.process_time(); warmwall=time.perf_counter(); game.evaluate(np.array([0,(1<<d)-1],dtype=np.uint32)); warmcpu=time.process_time()-warmcpu; warmwall=time.perf_counter()-warmwall
    schedule=[(im,p,rep) for im in [0,1] for p in PS for rep in range(5)]; order=rng_for(ds,model,11,slot,6).permutation(len(schedule))
    for j in order:
        im,p,rep=schedule[j]; rng=rng_for(ds,model,11,slot,6,im,p,rep)
        cpu=time.process_time(); wall=time.perf_counter()
        if im==0: mm=kernel_masks(d,p,rng); oo=None
        else: mm,oo=permutation_masks(d,p,rng)
        vv=game.evaluate(mm) # no memoization, no deduplication
        if im==0: phi,rank,sv=kernel_fit(mm,vv,d)
        else: phi=permutation_fit(vv,oo,d)
        records.append(dict(dataset=ds,model=model,slot=slot,method=['kernel','perm'][im],p=p,rep=rep,requests=len(mm),rows=len(mm)*16,unique_masks=len(np.unique(mm)),cpu_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,efficiency_residual=float(abs(phi.sum()-(vv[1]-vv[0])))))
    np.savez_compressed(dest,records=json.dumps(records),warmcpu=warmcpu,warmwall=warmwall)
    return dict(task=dest.name,status='done',records=len(records))

def main(stage,workers):
    funcs={'background':background_task,'library':adapter_task,'timing':timing_task}
    if stage=='background': tasks=[(ds,m,slot,b) for ds in ['acs','pima'] for m in MODELS for slot in range(8) for b in [4,64]]
    elif stage=='library': tasks=[(ds,m,slot) for ds in DS for m in MODELS for slot in range(2 if ds=='german' else 4)]
    else: tasks=[(ds,m,slot) for ds in DS for m in MODELS for slot in range(2)]
    with ProcessPoolExecutor(max_workers=workers) as pool,(OUT/f'{stage}_task_log.jsonl').open('a') as log:
        fs={pool.submit(funcs[stage],t):t for t in tasks}
        for f in as_completed(fs):
            try: r=f.result()
            except Exception as e: r=dict(task=fs[f],status='error',error=repr(e),traceback=traceback.format_exc())
            log.write(json.dumps(r)+'\n'); log.flush(); print(json.dumps(r),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('stage',choices=['background','library','timing']); ap.add_argument('--workers',type=int,default=4); a=ap.parse_args(); main(a.stage,a.workers)
