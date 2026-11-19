"""Paired repeated-sampling experiments. Run from /work or any working directory."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[k]='1'
import argparse,json,time,platform,resource
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import pandas as pd
from scipy.integrate import quad
from methods import all_intervals,dictionary,phi,coefficient,wald

ROOT=Path(__file__).resolve().parents[1]
CASES=['linear_cont','quadratic_cont','linear_binary','quadratic_binary','threshold_binary','null_binary','binary_score','rare_binary']

def conditional_mean(case,s):
    t=2*s-1
    if case=='linear_cont':return .5+.4*t
    if case=='quadratic_cont':return .1+.8*t*t
    if case=='linear_binary':return .5+.45*t
    if case=='quadratic_binary':return .05+.9*t*t
    if case=='threshold_binary':return .05+.9*(s>.7)
    if case=='null_binary':return np.full_like(s,.5)
    if case=='rare_binary':return np.full_like(s,.005)
    if case=='binary_score':return .1+.8*s
    raise KeyError(case)

def sample(case,n,N,rng,population=None):
    if population is not None:
        yp,sp=population;idx=rng.integers(0,len(yp),size=n+N)
        return yp[idx[:n]],sp[idx[:n]],sp[idx[n:]]
    s=rng.binomial(1,.5,size=n+N).astype(float) if case=='binary_score' else rng.random(n+N)
    m=conditional_mean(case,s[:n])
    y=m+rng.uniform(-.03,.03,size=n) if case.endswith('_cont') else rng.binomial(1,m).astype(float)
    return y,s[:n],s[n:]

def theory(case,n,N,population=None):
    if population is not None:
        y,s=population;muy=y.mean();vy=y.var();p=phi(s,3);pc=p-p.mean(0)
        sig=pc.T@pc/len(y);c=pc.T@(y-muy)/len(y)
        q1=c[0]**2/sig[0,0] if sig[0,0]>0 else 0
        q3=c@np.linalg.pinv(sig,hermitian=True)@c
        return dict(theta=muy,varY=vy,explained1=q1,explained3=q3,varM=None)
    if case=='binary_score':
        return dict(theta=.5,varY=.25,explained1=.16,explained3=.16,varM=.16)
    # Exact integration of piecewise polynomial functions; explicit break at threshold.
    def integ(f):return sum(quad(f,a,b,epsabs=1e-12)[0] for a,b in [(0,.7),(.7,1)])
    m=lambda s:float(conditional_mean(case,np.array([s]))[0])
    mu=integ(m);vm=integ(lambda s:(m(s)-mu)**2)
    vy=vm+.03**2/3 if case.endswith('_cont') else mu*(1-mu)
    cs=np.array([integ(lambda s,k=k:(m(s)-mu)*phi(np.array([s]),3)[0,k]) for k in range(3)])
    qs=cs**2*np.array([3,5,7])
    return dict(theta=mu,varY=vy,explained1=qs[0],explained3=qs.sum(),varM=vm)

def run_cell(task):
    kind,case,n,ratio,reps,seed,outdir=task
    start=time.perf_counter();start_cpu=time.process_time();N=int(n*ratio)
    rng=np.random.default_rng(seed)
    pop=None
    if kind=='real':
        z=np.load(ROOT/'data'/f'{case}.npz');pop=(z['Y'],z['Yhat'])
    th=theory(case,n,N,pop)
    records=[]
    for r in range(reps):
        y,sl,su=sample(case,n,N,rng,pop)
        if kind=='ablation':
            intervals={f'CV{d}':dictionary(y,sl,su,d) for d in [1,2,3,7,15]}
        else:intervals=all_intervals(y,sl,su,binary=(pop is not None or not case.endswith('_cont')))
        for method,(lo,hi) in intervals.items():
            records.append((r,method,lo,hi,int(lo<=th['theta']<=hi)))
    df=pd.DataFrame(records,columns=['rep','method','lo','hi','covered'])
    df['width']=df.hi-df.lo
    assert np.isfinite(df[['lo','hi','width']]).all().all()
    assert (df.width>=0).all()
    name=f'{kind}_{case}_n{n}_r{ratio:g}'
    df.to_csv(ROOT/outdir/(name+'.csv.gz'),index=False,float_format='%.12g',compression={'method':'gzip','mtime':0})
    elapsed=time.perf_counter()-start
    meta=dict(kind=kind,case=case,n=n,N=N,reps=reps,seed=seed,seconds=elapsed,
              cpu_seconds=time.process_time()-start_cpu,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,**th)
    (ROOT/outdir/(name+'.json')).write_text(json.dumps(meta,indent=2))
    return meta

def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',choices=['main','ablation','ratio','finite','smoke'],default='main')
    p.add_argument('--reps',type=int,default=5000);p.add_argument('--workers',type=int,default=4)
    p.add_argument('--outdir',default='results/raw');args=p.parse_args()
    (ROOT/args.outdir).mkdir(parents=True,exist_ok=True)
    if args.suite=='main':
        cells=[('synthetic',c,n,10.) for c in CASES for n in [200,800]]
        cells += [('real',c,n,10.) for c in ['galaxies','forest','alphafold'] for n in [200,800]]
    elif args.suite=='ablation':
        cells=[('ablation',c,n,10.) for c in ['linear_cont','quadratic_cont','null_binary'] for n in [50,200,800]]
    elif args.suite=='ratio':
        cells=[('synthetic',c,800,r) for c in ['linear_cont','quadratic_cont','null_binary'] for r in [.25,1.,4.,40.]]
    elif args.suite=='finite':
        cells=[('synthetic',c,n,10.) for c in ['quadratic_cont','null_binary','rare_binary'] for n in [3200,12800]]
    else:cells=[('synthetic',c,200,10.) for c in CASES]+[('real','forest',200,10.)]
    # Stable experiment-level seeds independent of scheduling and suite order.
    import hashlib
    tasks=[]
    for k,c,n,r in cells:
        key=f'{k}/{c}/{n}/{r:g}'
        seed=int.from_bytes(hashlib.sha256(('fixed-score-20261102/'+key).encode()).digest()[:8],'little')
        tasks.append((k,c,n,r,args.reps,seed,args.outdir))
    t=time.perf_counter();out=[]
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures={ex.submit(run_cell,t):t for t in tasks}
        for f in as_completed(futures):
            a=f.result();out.append(a);print(json.dumps(a),flush=True)
    log=dict(suite=args.suite,reps=args.reps,workers=args.workers,wall_seconds=time.perf_counter()-t,
             python=platform.python_version(),platform=platform.platform(),tasks=out)
    (ROOT/'logs'/f'run_{args.suite}.json').write_text(json.dumps(log,indent=2))
if __name__=='__main__':main()
