#!/usr/bin/env python3
"""Paired fixed-predictor mean inference; all seeds and draw-level results recorded."""
import argparse, json, time, os, platform
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm, t

ALPHA=.05
Z=norm.ppf(1-ALPHA/2)
SYNTHETIC=['linear','quadratic','sigmoid','no_signal','heavy_tail','bernoulli_quadratic','rare_binary']
REAL=['galaxies','forest','alphafold']
SCENARIO_IDS={d:i for i,d in enumerate(SYNTHETIC+REAL+['bounded_quadratic'])}
SCENARIO_IDS['null']=SCENARIO_IDS['no_signal']  # Alias preserves original follow-up CLI and seeds.

def basis(s, degree=3):
    return np.polynomial.legendre.legvander(2*s-1,degree)[:,1:]

def coef(x,y):
    # Fixed-dimensional centered least squares; singular directions use Moore-Penrose.
    xc=x-x.mean(0); yc=y-y.mean()
    return np.linalg.lstsq(xc,yc,rcond=1e-10)[0]

def wald(y,sl,su,b):
    r=y-sl@np.atleast_1d(b); h=su@np.atleast_1d(b)
    est=r.mean()+h.mean()
    se=np.sqrt(r.var(ddof=0)/len(y)+h.var(ddof=0)/len(su))
    return est-Z*se,est+Z*se

def crossfit(y,x,u,degree):
    n=len(y); N=len(u); h=np.zeros(n); hu=np.zeros(N)
    # Equal deterministic folds, independent because observations are iid.
    cut=n//2
    for idx,train in [(np.arange(cut),np.arange(cut,n)),(np.arange(cut,n),np.arange(cut))]:
        b=coef(x[train,:degree],y[train])/(1+n/N)
        h[idx]=x[idx,:degree]@b
        hu+=(len(idx)/n)*(u[:,:degree]@b)
    est=y.mean()-h.mean()+hu.mean()
    # Out-of-fold residual and averaged unlabeled influence variances.
    se=np.sqrt((y-h).var(ddof=0)/n+hu.var(ddof=0)/N)
    return est-Z*se,est+Z*se

def eb_radius(a,span,delta):
    # Two-sided empirical Bernstein, via two applications of Maurer-Pontil Thm 4.
    k=len(a); z=np.log(4/delta)
    return np.sqrt(2*a.var(ddof=1)*z/k)+7*span*z/(3*(k-1))

def finite_sample(y,s,u,x,xu):
    n=len(y); N=len(u); k=max(10,n//4); m=n-k
    ans={}
    a=y.mean(); r=eb_radius(y,1,ALPHA)
    ans['eb_label']=(np.clip(a-r,0,1),np.clip(a+r,0,1))
    for name in ['eb_ppi','eb_scalar','eb_cubic']:
        if name=='eb_ppi': hl=s[k:]; hu=u; c=1.
        elif name=='eb_scalar':
            # Training-only clipping means known ranges do not depend on evaluation labels.
            b=float(np.clip(coef(s[:k,None],y[:k])[0],0,1))/(1+m/N)
            hl=b*s[k:]; hu=b*u; c=b
        else:
            b=coef(x[:k],y[:k]); intercept=y[:k].mean()-x[:k].mean(0)@b
            c=1/(1+m/N)
            hl=c*np.clip(intercept+x[k:]@b,0,1)
            hu=c*np.clip(intercept+xu@b,0,1)
        resid=y[k:]-hl; a=resid.mean()+hu.mean()
        r=eb_radius(resid,1+c,ALPHA/2)+eb_radius(hu,c,ALPHA/2)
        ans[name]=(np.clip(a-r,0,1),np.clip(a+r,0,1))
    return ans

def draw(rng,scenario,n,N,real):
    if scenario in REAL:
        y,s=real[scenario]; il=rng.integers(len(y),size=n); iu=rng.integers(len(y),size=N)
        return y[il],s[il],s[iu],float(y.mean()),True
    s=rng.uniform(size=n); u=rng.uniform(size=N)
    if scenario=='linear': y=.2+.8*s+rng.normal(0,.2,n); mu=.6
    elif scenario=='quadratic': y=(2*s-1)**2+rng.normal(0,.15,n); mu=1/3
    elif scenario=='sigmoid': y=1/(1+np.exp(-12*(s-.5)))+rng.normal(0,.15,n); mu=.5
    elif scenario in ['null','no_signal']: y=.4+rng.normal(0,.2,n); mu=.4
    elif scenario=='heavy_tail': y=(2*s-1)**2+rng.standard_t(3,n)*.15; mu=1/3
    elif scenario=='bernoulli_quadratic': y=rng.binomial(1,.05+.9*(2*s-1)**2); mu=.35
    elif scenario=='bounded_quadratic': y=.025+.95*(2*s-1)**2+rng.uniform(-.025,.025,n); mu=.025+.95/3
    elif scenario=='rare_binary': y=rng.binomial(1,.01,size=n); mu=.01
    return y,s,u,mu,scenario in ['bernoulli_quadratic','rare_binary','bounded_quadratic']

def intervals(y,s,u,bounded,stress=False):
    n=len(y); N=len(u); x=basis(s); xu=basis(u)
    ans={'label':wald(y,x[:,:1],xu[:,:1],0), 'ppi':wald(y,x[:,:1],xu[:,:1],.5)}
    # Reproduce ppi-python 0.2.3 scalar tuning, including ddof conventions and clipping.
    cov=np.mean((y-y.mean())*(s-s.mean()))
    den=(1+n/N)*np.var(np.r_[s,u],ddof=1)
    b=cov/den if den>0 else 0
    ans['ppi++']=wald(y,x[:,:1],xu[:,:1],np.clip(b,0,1)/2)
    # Legendre first coordinate is 2*s-1, so coefficients on s must be divided by 2.
    ans['scalar_unclipped']=wald(y,x[:,:1],xu[:,:1],b/2)
    ans['cf_linear']=crossfit(y,x,xu,1)
    ans['cf_cubic']=crossfit(y,x,xu,3)
    ans['plugin_cubic']=wald(y,x,xu,coef(x,y)/(1+n/N))
    if stress:
        xp=basis(s,12); up=basis(u,12)
        ans['cf_degree12']=crossfit(y,xp,up,12)
        ans['plugin_degree12']=wald(y,xp,up,coef(xp,y)/(1+n/N))
    if bounded: ans.update(finite_sample(y,s,u,x,xu))
    return ans

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--group',choices=['synthetic','real','all'],default='all'); ap.add_argument('--reps',type=int,default=5000); ap.add_argument('--ns',type=int,nargs='+',default=[100,500,2000]); ap.add_argument('--ratio',type=int,default=10); ap.add_argument('--seed',type=int,default=20261102); ap.add_argument('--out',default='results/main'); ap.add_argument('--scenarios',nargs='+',choices=list(SCENARIO_IDS)); ap.add_argument('--stress',action='store_true'); args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    real={d:(np.load('data/'+d+'.npz')['Y'],np.load('data/'+d+'.npz')['Yhat']) for d in REAL} if args.group!='synthetic' else {}
    scenarios=SYNTHETIC if args.group=='synthetic' else REAL if args.group=='real' else SYNTHETIC+REAL
    if args.scenarios: scenarios=args.scenarios
    start=time.perf_counter()
    meta={'arguments':vars(args),'numpy':np.__version__,'pandas':pd.__version__,'python':platform.python_version(),'alpha':ALPHA,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    (out/'metadata.json').write_text(json.dumps(meta,indent=2))
    for d in scenarios:
        for n in args.ns:
            N=args.ratio*n; rows=[]
            # Scenario ordinal stable across group selection and future additions.
            sid=SCENARIO_IDS[d]
            for rep in range(args.reps):
                seed=np.random.SeedSequence([args.seed,sid,n,args.ratio,rep]); rng=np.random.default_rng(seed)
                y,s,u,truth,bounded=draw(rng,d,n,N,real)
                for method,(lo,hi) in intervals(y,s,u,bounded,args.stress).items():
                    rows.append(('no_signal' if d=='null' else d,n,N,rep,args.seed,method,truth,lo,hi,hi-lo,lo<=truth<=hi))
            frame=pd.DataFrame(rows,columns=['scenario','n','N','rep','seed','method','truth','lower','upper','width','covered'])
            frame.to_parquet(out/f'{d}_n{n}.parquet',index=False)
            print(f'completed {d} n={n} reps={args.reps} elapsed={time.perf_counter()-start:.2f}s',flush=True)
    meta['elapsed_seconds']=time.perf_counter()-start
    (out/'metadata.json').write_text(json.dumps(meta,indent=2))
    print('HUTIAN_WAKE: experiment group complete '+str(out),flush=True)

if __name__=='__main__': main()
