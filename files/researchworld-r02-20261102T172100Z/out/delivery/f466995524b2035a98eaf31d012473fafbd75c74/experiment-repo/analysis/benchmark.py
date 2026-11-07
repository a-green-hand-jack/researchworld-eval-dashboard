"""Compositional-response split conformal benchmark; no external datasets."""
import argparse, hashlib, itertools, json, platform, time
from pathlib import Path
import numpy as np
import scipy
from scipy.special import softmax,xlogy

METHODS = ('raw_l2','raw_linf','clr_l2','clr_scaled','clr_mondrian','coord_naive','coord_bonferroni')

def clr(y):
    z = np.log(y)
    return z-z.mean(axis=-1,keepdims=True)

def quantile(scores, alpha):
    n=len(scores); k=int(np.ceil((n+1)*(1-alpha)))
    if k>n:
        return np.full(scores.shape[1:],np.inf)
    return np.sort(scores,axis=0)[k-1]

def weighted_quantile(scores,weights,test_weight,alpha):
    """Quantile of calibration weighted scores plus test weight at infinity."""
    order=np.argsort(scores); ordered=np.asarray(scores)[order]
    cumulative=np.cumsum(np.asarray(weights)[order])
    target=(1-alpha)*(np.sum(weights)+test_weight)
    index=np.searchsorted(cumulative,target,side='left')
    return np.inf if index>=len(ordered) else ordered[index]

def features(x):
    g=x[:,0]; z=x[:,1:]
    return np.column_stack((np.ones(len(x)),g,z,z[:,0]*z[:,1],z[:,0]**2))

def generate(rng,n,k,scenario,beta,shift=False):
    prob=.8 if shift else .2
    x=np.column_stack((rng.binomial(1,prob,n),rng.normal(size=(n,3))))
    mu=features(x)@beta
    if scenario=='homogeneous':
        scale=np.full(n,.45)
    elif scenario in ('heterogeneous','zeros'):
        scale=np.where(x[:,0]==0,.18,.95)*np.exp(.15*x[:,1])
    else:
        raise ValueError(scenario)
    # Anisotropy has fixed trace and is shared across scenarios.
    axis=np.linspace(.65,1.35,k); axis=axis/np.sqrt(np.mean(axis**2))
    y=softmax(mu+scale[:,None]*rng.normal(size=(n,k))*axis,axis=1)
    if scenario=='zeros':
        # Measurement censoring, not a latent true zero; preserve row sums.
        y=np.where(y<.025,0,y); y=y/y.sum(axis=1,keepdims=True)
    return x,y

def replace_zeros(y,eps):
    return np.maximum(y,eps)/np.maximum(y,eps).sum(axis=-1,keepdims=True)

class Predictor:
    def __init__(self,x,y):
        phi=features(x); target=clr(y)
        # Ridge intercept is unpenalized; tiny regularizer is predeclared.
        reg=np.eye(phi.shape[1])*1e-3; reg[0,0]=0
        self.beta=np.linalg.solve(phi.T@phi+reg,phi.T@target)
        resid=target-phi@self.beta
        lognorm=np.log(np.maximum(np.sum(resid**2,axis=1),1e-12))
        self.scale_beta=np.linalg.solve(phi.T@phi+reg,phi.T@lognorm)
    def predict(self,x):
        phi=features(x)
        return softmax(phi@self.beta,axis=1),np.exp(np.clip(phi@self.scale_beta/2,-12,12))

def score(y,p,s,method):
    if method=='tv':
        r=np.abs(y-p)
        # On the 3-simplex TV equals max residual; canonicalize the duplicate
        # to preserve exact matched memberships despite floating roundoff.
        return np.max(r,axis=-1) if y.shape[-1]==3 else .5*np.sum(r,axis=-1)
    if method=='kl_forward':
        if np.any(p<=0): raise ValueError('Forward KL requires a positive predictor')
        return np.maximum(0.,np.sum(xlogy(y,y)-xlogy(y,p),axis=-1))
    if method=='raw_l2': return np.linalg.norm(y-p,axis=-1)
    if method in ('raw_linf','coord_naive','coord_bonferroni'): return np.abs(y-p) if method.startswith('coord') else np.max(np.abs(y-p),axis=-1)
    d=np.linalg.norm(clr(y)-clr(p),axis=-1)
    return d/s if method=='clr_scaled' else d

def fit_thresholds(y,p,s,g,alpha,target_shift=False):
    out={}
    for m in METHODS+('clr_weighted','tv','kl_forward'):
        a=alpha/y.shape[1] if m=='coord_bonferroni' else alpha
        v=score(y,p,s,m)
        if m=='clr_weighted':
            weights=np.where(g==1,4.,.25) if target_shift else np.ones(len(g))
            test_weights=[.25,4.] if target_shift else [1.,1.]
            out[m]=[weighted_quantile(v,weights,w,a) for w in test_weights]
        else:
            out[m]=[quantile(v[g==i],a) for i in (0,1)] if m=='clr_mondrian' else quantile(v,a)
    return out

def membership(y,p,s,g,m,q):
    v=score(y,p,s,m)
    if m in ('clr_mondrian','clr_weighted'):
        limit=np.asarray(q)[g.astype(int)]
    else: limit=q
    hit=v<=limit
    return np.all(hit,axis=-1) if m.startswith('coord') else hit

def run_rep(seed,k,ncal,scenario,alpha=.1,ntrain=1000,ntest=2000,nvolume=4096,nanchors=32,epsilon=1e-6,methods=METHODS):
    started=time.perf_counter(); rng=np.random.default_rng(seed)
    # Fixed coefficients depend on K only; all replications estimate same DGP.
    beta=np.random.default_rng(1729+k).normal(0,.32,(7,k)); beta-=beta.mean(axis=1,keepdims=True)
    xt,yt=generate(rng,ntrain,k,scenario,beta)
    xc,yc=generate(rng,ncal,k,scenario,beta)
    if scenario=='zeros': yt=replace_zeros(yt,epsilon); yc=replace_zeros(yc,epsilon)
    model=Predictor(xt,yt); pc,sc=model.predict(xc)
    rows=[]
    for shift in (False,True):
        thresholds=fit_thresholds(yc,pc,sc,xc[:,0],alpha,target_shift=shift)
        x,y=generate(rng,ntest,k,scenario,beta,shift)
        zero_component_rate=float((y==0).mean()); boundary_response_rate=float(np.any(y==0,axis=1).mean())
        if scenario=='zeros': y=replace_zeros(y,epsilon)
        p,s=model.predict(x)
        for m in methods:
            hits=membership(y,p,s,x[:,0],m,thresholds[m])
            row=dict(seed=seed,k=k,ncal=ncal,scenario=scenario,shift=shift,epsilon=epsilon,alpha=alpha,method=m,coverage=float(hits.mean()),n_test=ntest,zero_component_rate=zero_component_rate,boundary_response_rate=boundary_response_rate,ncal_g0=int(np.sum(xc[:,0]==0)),ncal_g1=int(np.sum(xc[:,0]==1)))
            for group in (0,1):
                selected=x[:,0]==group
                row[f'coverage_g{group}']=float(hits[selected].mean())
                row[f'n_g{group}']=int(selected.sum())
            # Radius is metric-specific; do not compare radii across geometries.
            q=thresholds[m]
            if m in ('clr_mondrian','clr_weighted'): radius=np.asarray(q)[x[:,0].astype(int)]
            elif m=='clr_scaled': radius=s*q
            else: radius=np.asarray(q)
            row['radius_infinite_fraction']=float(np.mean(np.isinf(radius)))
            row['mean_radius']=float(np.mean(radius)) if np.all(np.isfinite(radius)) else None
            row['radius_status']='infinite' if np.any(np.isinf(radius)) else 'finite'
            row['infinite_threshold']=bool(np.any(np.isinf(q)))
            row['volume_fraction']=None
            rows.append(row)
        if k==3 and nvolume>0:
            # Common uniform simplex candidates; Euclidean area fraction, not clr volume.
            # Separately generated test anchors keep volume sampling out of coverage.
            xv,_=generate(rng,nanchors,k,scenario,beta,shift)
            pv,sv=model.predict(xv)
            candidates=rng.dirichlet(np.ones(k),size=(nanchors,nvolume))
            # Zero replacement defines an interior-response estimand, sets themselves remain on the simplex.
            for row in rows[-len(methods):]:
                m=row['method']; q=thresholds[m]
                g=np.broadcast_to(xv[:,0,None],(nanchors,nvolume))
                hits=membership(candidates,pv[:,None,:],sv[:,None],g,m,q)
                row['volume_fraction']=float(hits.mean())
                row['volume_mc_se_conditional']=float(np.sqrt(np.mean(hits.mean(axis=1)*(1-hits.mean(axis=1)))/(nanchors*nvolume)))
    return rows,time.perf_counter()-started

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); ap.add_argument('--reps',type=int,default=3); ap.add_argument('--start',type=int,default=0); ap.add_argument('--dimensions',type=int,nargs='+',default=[3,10]); ap.add_argument('--calibration',type=int,nargs='+',default=[99,499]); ap.add_argument('--scenarios',nargs='+',default=['homogeneous','heterogeneous']); ap.add_argument('--nvolume',type=int,default=4096); ap.add_argument('--ntest',type=int,default=2000); ap.add_argument('--epsilon',type=float,default=1e-6); ap.add_argument('--alpha',type=float,default=.1); ap.add_argument('--methods',nargs='+',choices=METHODS+('clr_weighted','tv','kl_forward'),default=list(METHODS))
    args=ap.parse_args(); output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    manifest=dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),arguments=vars(args),python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,seed_rule='900000 + replication; independent streams shared across methods, fixed beta seed 1729+K',input='synthetic generator in analysis/benchmark.py',started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2))
    with output.open('w') as f, output.with_suffix('.timings.jsonl').open('w') as timing:
        for rep,k,ncal,scenario in itertools.product(range(args.start,args.start+args.reps),args.dimensions,args.calibration,args.scenarios):
            rows,elapsed=run_rep(900000+rep,k,ncal,scenario,ntest=args.ntest,nvolume=args.nvolume,epsilon=args.epsilon,alpha=args.alpha,methods=tuple(args.methods))
            for row in rows: f.write(json.dumps(row,allow_nan=False)+'\n')
            f.flush(); entry=dict(rep=rep,k=k,ncal=ncal,scenario=scenario,seconds=elapsed); timing.write(json.dumps(entry)+'\n'); timing.flush(); print(json.dumps(entry),flush=True)
    print('HUTIAN_WAKE: benchmark shard complete '+str(output),flush=True)
if __name__=='__main__': main()
