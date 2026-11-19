"""Predeclared finite-rank and exact-zero/replacement scope checks."""
import argparse,hashlib,json,platform,time
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import binom
from benchmark import (METHODS,Predictor,generate,replace_zeros,fit_thresholds,score,
                       quantile,membership)
from summarize import interval,wilson

def rank_experiment(output):
    rows=[]; index=0
    for n in (2,9,19,99,499):
        for alpha in (.05,.1,.2):
            for law in ('uniform','bernoulli'):
                seed=310000+index; index+=1; rng=np.random.default_rng(seed); r=20000
                values=rng.uniform(size=(r,n+1)) if law=='uniform' else rng.binomial(1,.5,size=(r,n+1)).astype(float)
                k=int(np.ceil((n+1)*(1-alpha)))
                q=np.full(r,np.inf) if k>n else np.sort(values[:,:n],axis=1)[:,k-1]
                hits=values[:,n]<=q
                if law=='uniform':
                    conditional=np.minimum(q,1.)
                    expected=min(k/(n+1),1.)
                    expected_var=k*(n+1-k)/((n+1)**2*(n+2)) if k<=n else 0.
                else:
                    conditional=np.where(q==0,.5,1.)
                    p_zero=float(binom.sf(k-1,n,.5)) if k<=n else 0.
                    expected=1-.5*p_zero; expected_var=.25*p_zero*(1-p_zero)
                _,mean,se,lo,hi=interval(conditional)
                hitlo,hithi=wilson(int(hits.sum()),r)
                rows.append(dict(ncal=n,alpha=alpha,law=law,seed=seed,trials=r,rank=k,infinite_threshold=k>n,test_coverage=float(hits.mean()),test_ci_low=hitlo,test_ci_high=hithi,calibration_coverage_mean=mean,calibration_ci_low=lo,calibration_ci_high=hi,calibration_coverage_variance=float(np.var(conditional,ddof=1)),theory_coverage=expected,theory_calibration_variance=expected_var))
                print(json.dumps(dict(check='rank',ncal=n,alpha=alpha,law=law)),flush=True)
    import pandas as pd
    pd.DataFrame(rows).to_csv(output,index=False)

def row_for(method,hits,target,seed,k,eps,g,gc,y,q,radius):
    row=dict(seed=seed,k=k,ncal=499,scenario=target,shift=False,epsilon=eps,alpha=.1,method=method,coverage=float(hits.mean()),n_test=len(hits),zero_component_rate=float((y==0).mean()),boundary_response_rate=float(np.any(y==0,axis=1).mean()),ncal_g0=int(np.sum(gc==0)),ncal_g1=int(np.sum(gc==1)),mean_radius=float(np.mean(radius)) if np.all(np.isfinite(radius)) else None,radius_infinite_fraction=float(np.mean(np.isinf(radius))),radius_status='finite' if np.all(np.isfinite(radius)) else 'infinite',infinite_threshold=bool(np.any(np.isinf(q))),volume_fraction=None)
    for group in (0,1):
        ix=g==group; row[f'coverage_g{group}']=float(hits[ix].mean()); row[f'n_g{group}']=int(ix.sum())
    return row

def boundary_experiment(output):
    raw_methods=('raw_l2','raw_linf','coord_naive','coord_bonferroni')
    clr_methods=('clr_l2','clr_scaled','clr_mondrian')
    with Path(output).open('w') as f:
        for rep in range(2000,2050):
            for k in (3,10):
                # Reinitialize once per dataset, outside epsilon loop for exact pairing.
                seed=900000+rep; rng=np.random.default_rng(seed)
                beta=np.random.default_rng(1729+k).normal(0,.32,(7,k)); beta-=beta.mean(axis=1,keepdims=True)
                xt,yt=generate(rng,1000,k,'zeros',beta)
                xc,yc=generate(rng,499,k,'zeros',beta)
                x,y=generate(rng,5000,k,'zeros',beta)
                for eps in (1e-8,1e-4,1e-2):
                    model=Predictor(xt,replace_zeros(yt,eps)); pc,sc=model.predict(xc); p,s=model.predict(x)
                    yct=replace_zeros(yc,eps); ytest=replace_zeros(y,eps)
                    transformed=fit_thresholds(yct,pc,sc,xc[:,0],.1)
                    for m in METHODS:
                        q=transformed[m]
                        radius=np.asarray(q)[x[:,0].astype(int)] if m=='clr_mondrian' else s*q if m=='clr_scaled' else np.asarray(q)
                        hit=membership(ytest,p,s,x[:,0],m,q)
                        f.write(json.dumps(row_for(m,hit,'zeros_transformed',seed,k,eps,x[:,0],xc[:,0],y,q,radius),allow_nan=False)+'\n')
                    for m in raw_methods:
                        q=quantile(score(yc,pc,sc,m),.1/k if m=='coord_bonferroni' else .1)
                        hit=membership(y,p,s,x[:,0],m,q)
                        f.write(json.dumps(row_for(m,hit,'zeros_original_raw',seed,k,eps,x[:,0],xc[:,0],y,q,np.asarray(q)),allow_nan=False)+'\n')
                    positive=np.all(y>0,axis=1)
                    for m in clr_methods:
                        q=transformed[m]
                        radius=np.asarray(q)[x[:,0].astype(int)] if m=='clr_mondrian' else s*q if m=='clr_scaled' else np.full(len(x),q)
                        # Positive-domain rule, infinity denotes whole-simplex fallback.
                        hit=np.isinf(radius)
                        hit[positive]=membership(y[positive],p[positive],s[positive],x[positive,0],m,q)
                        f.write(json.dumps(row_for(m,hit,'zeros_original_clr_diagnostic',seed,k,eps,x[:,0],xc[:,0],y,q,radius),allow_nan=False)+'\n')
                f.flush(); print(json.dumps(dict(check='boundary',rep=rep,k=k)),flush=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['rank','boundary'],required=True); ap.add_argument('--output',required=True); args=ap.parse_args()
    output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True); start=time.perf_counter()
    if args.mode=='rank': rank_experiment(output)
    else: boundary_experiment(output)
    manifest=dict(mode=args.mode,python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),benchmark_sha256=hashlib.sha256(Path(__file__).with_name('benchmark.py').read_bytes()).hexdigest(),plan='notes/sensitivity_freeze.md',seconds=time.perf_counter()-start)
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)); print('HUTIAN_WAKE: '+args.mode+' sensitivity complete',flush=True)
if __name__=='__main__': main()
