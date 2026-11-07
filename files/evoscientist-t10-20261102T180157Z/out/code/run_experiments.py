"""Run fixed-budget paired repeated-sampling experiments. See todos.md.
Example: OPENBLAS_NUM_THREADS=1 python run_experiments.py --reps 2000 --jobs 4
"""
from __future__ import annotations
import argparse, hashlib, json, os, platform, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm
from methods import all_intervals

ROOT=Path(__file__).resolve().parent
BASE_SEED=20261102
SCENARIOS=['linear','quadratic','step','null','rare','galaxies','forest']

def conditional_mean(name,s):
    if name=='linear': return .1+.8*s
    if name=='quadratic': return .02+.96*(2*s-1)**2
    if name=='step': return .01+.98*(s>.5)
    if name=='null': return np.full_like(s,.5)
    if name=='rare': return np.full_like(s,.01)
    raise ValueError(name)

def moments(name):
    if name=='linear': return .5,.25,.64/12,.8/12
    if name=='quadratic': return .34,.34*.66,.96**2*(1/5-1/9),0.
    if name=='step': return .5,.25,.98**2/4,.98/8
    if name=='null': return .5,.25,0.,0.
    if name=='rare': return .01,.0099,0.,0.
    raise ValueError(name)

def wilson(k,n):
    z=norm.ppf(.975); p=k/n; den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return mid-half,mid+half

def run_cell(config):
    name,n,ratio,reps,tag=config
    N=n*ratio; sid=SCENARIOS.index(name)
    rng=np.random.default_rng(np.random.SeedSequence([BASE_SEED,sid,n,ratio]))
    t0=time.perf_counter(); is_real=name in ['galaxies','forest']
    data=np.load(ROOT/'data'/f'{name}.npz') if is_real else None
    mu=float(data['Y'].mean()) if is_real else moments(name)[0]
    records=[]
    for rep in range(reps):
        if is_real:
            # Independent WITH-replacement draws from the empirical population.
            # Evaluator never gives the unlabeled labels to interval construction.
            il=rng.integers(0,len(data['Y']),n)
            iu=rng.integers(0,len(data['Y']),N)
            y=data['Y'][il]; sl=data['Yhat'][il]; su=data['Yhat'][iu]
            out,idx=all_intervals(y,sl,su)
        else:
            sl=rng.uniform(size=n); su=rng.uniform(size=N)
            ml=conditional_mean(name,sl); m_u=conditional_mean(name,su)
            y=rng.binomial(1,ml)
            out,idx=all_intervals(y,sl,su,ml,m_u)
        for method,(lo,hi,raw) in out.items():
            records.append((name,n,N,ratio,tag,rep,method,mu,lo,hi,hi-lo,raw,int(lo<=mu<=hi),idx if method=='eb_select' else -1))
    df=pd.DataFrame.from_records(records,columns=['scenario','n','N','ratio','grid','rep','method','truth','lower','upper','width','raw_width','covered','selected'])
    stem=f'{name}_n{n}_r{ratio}'
    path=ROOT/'results'/'raw'/f'{stem}.csv.gz'; path.parent.mkdir(exist_ok=True,parents=True)
    df.to_csv(path,index=False,compression='gzip',float_format='%.12g')
    pp=df[df.method=='ppipp'].sort_values('rep').width.to_numpy()
    summary=[]
    for method,g in df.groupby('method',sort=False):
        g=g.sort_values('rep'); w=g.width.to_numpy(); b=g.covered.sum()
        low,high=wilson(b,reps); rat=w.mean()/pp.mean() if pp.mean()>0 else np.nan
        infl=(w-rat*pp)/pp.mean()
        summary.append(dict(scenario=name,n=n,N=N,ratio=ratio,grid=tag,method=method,
            reps=reps,truth=mu,coverage=b/reps,cov_lo=low,cov_hi=high,
            width=w.mean(),width_se=w.std(ddof=1)/np.sqrt(reps),
            raw_width=g.raw_width.mean(),width_ratio_ppipp=rat,
            ratio_se=infl.std(ddof=1)/np.sqrt(reps),
            paired_diff=(w-pp).mean(),paired_diff_se=(w-pp).std(ddof=1)/np.sqrt(reps),
            seconds=time.perf_counter()-t0))
    print(stem,'done',round(time.perf_counter()-t0,2),'sec',flush=True)
    return summary

def manifest():
    meta={'base_seed':BASE_SEED,'python':platform.python_version(),'platform':platform.platform(),
          'cpu_count':os.cpu_count(),'date_utc':'2026-11-02','sampling':'independent iid; empirical data with replacement',
          'data_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*.npz')}}
    for name in ['numpy','scipy','pandas','matplotlib','sklearn','ppi_py']:
        mod=__import__(name); meta[name]=getattr(mod,'__version__','0.2.3 (package metadata)')
    return meta

def main():
    p=argparse.ArgumentParser(); p.add_argument('--reps',type=int,default=2000)
    p.add_argument('--jobs',type=int,default=4); p.add_argument('--smoke',action='store_true')
    a=p.parse_args(); t=time.perf_counter()
    core=[(name,n,10,a.reps,'core') for name in SCENARIOS for n in [100,500,2000]]
    stress=[(name,30,10,a.reps,'stress') for name in SCENARIOS[:5]]
    stress += [(name,500,r,a.reps,'stress') for name in ['linear','quadratic','rare'] for r in [1,100]]
    cells=[('linear',100,10,a.reps,'smoke'),('quadratic',100,10,a.reps,'smoke'),('galaxies',100,10,a.reps,'smoke')] if a.smoke else core+stress
    (ROOT/'results'/'raw').mkdir(exist_ok=True,parents=True)
    meta=manifest(); meta['cells']=cells; meta['jobs']=a.jobs
    (ROOT/'results'/'config.json').write_text(json.dumps(meta,indent=2))
    if a.jobs==1:
        summaries=[run_cell(c) for c in cells]
    else:
        with ProcessPoolExecutor(max_workers=a.jobs) as pool:
            summaries=list(pool.map(run_cell,cells))
    df=pd.DataFrame([s for group in summaries for s in group])
    df.to_csv(ROOT/'results'/'summary.csv',index=False)
    analytic=[]
    for name in SCENARIOS[:5]:
        mu,vy,vm,cov=moments(name)
        for ratio in [1,10,100]:
            r=1/ratio; scalar=vy-cov*cov/(1/12*(1+r)); opt=vy-vm/(1+r)
            analytic.append(dict(scenario=name,ratio=ratio,truth=mu,variance_y=vy,var_conditional_mean=vm,
                nvar_scalar=scalar,nvar_score_oracle=opt,oracle_width_ratio=np.sqrt(opt/scalar)))
    pd.DataFrame(analytic).to_csv(ROOT/'results'/'oracle.csv',index=False)
    meta['wall_seconds']=time.perf_counter()-t; meta['total_repetitions']=sum(c[3] for c in cells)
    (ROOT/'results'/'config.json').write_text(json.dumps(meta,indent=2))
    print('TOTAL',meta['wall_seconds'],'seconds',flush=True)

if __name__=='__main__': main()
