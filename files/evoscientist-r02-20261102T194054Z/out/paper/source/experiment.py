"""Reproducible composition conformal audit; all scientific choices in plan.md."""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, os, platform, resource, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
METHODS = ['TV','L2','Linf','Hellinger','CLR-6','CLR-2','Coord','Bonferroni','ScaledL2','MondrianL2','WeightedL2']
ALPHA = .1

def rng(seed, k, law, stream):
    return np.random.default_rng(np.random.SeedSequence([seed,k,int(law=='zeros'),stream]))

def generate(n, k, law, p, r):
    u = r.uniform(-1,1,(n,2)); g = r.binomial(1,p,n)
    x = np.column_stack([u,g])
    theta=2*np.pi*np.arange(k)/k
    a=(.25*np.sin(theta)+.6*u[:,0,None]*np.cos(theta)+.6*u[:,1,None]*np.sin(theta)
       +.25*(u[:,0]*u[:,1])[:,None]*np.cos(2*theta))
    mu=np.exp(a-a.max(1,keepdims=True)); mu/=mu.sum(1,keepdims=True)
    b=r.binomial(1,.35,n).astype(bool) if law=='zeros' else np.zeros(n,dtype=bool)
    concentration=np.where(g==0,80.,8.)
    y=np.zeros((n,k))
    for flag in [False,True]:
        ind=np.where(b==flag)[0]
        if not len(ind): continue
        m=mu[ind,:k-1] if flag else mu[ind]
        m=m/m.sum(1,keepdims=True)
        z=r.gamma(concentration[ind,None]*m)
        if np.any(z<=0): raise FloatingPointError('Unexpected Dirichlet numerical zero')
        z/=z.sum(1,keepdims=True)
        y[ind,:z.shape[1]]=z
    assert np.allclose(y.sum(1),1,rtol=0,atol=1e-12)
    assert np.array_equal(y[:,-1]==0,b)
    return x,y,b,mu

def features(x):
    a,b,g=x.T
    return np.column_stack([np.ones(len(x)),a,b,a*a,b*b,a*b,g,g*a,g*b])

def project(y):
    v=np.sort(y,axis=-1)[:,::-1]; s=np.cumsum(v,axis=1)-1
    rank=np.arange(1,y.shape[1]+1)
    count=np.sum(v-s/rank>0,axis=1)
    threshold=s[np.arange(len(y)),count-1]/count
    return np.maximum(y-threshold[:,None],0)

def fit(x,y):
    z=features(x); penalty=np.eye(z.shape[1])*1e-3; penalty[0,0]=0
    return np.linalg.solve(z.T@z/len(z)+penalty,z.T@y/len(z))

def predict(beta,x):
    v=project(features(x)@beta)
    return (1-1e-8)*v+1e-8/v.shape[1]

def fit_scale(x,y,r):
    folds=np.array_split(r.permutation(len(x)),5); residual=np.empty(len(x))
    for ix in folds:
        use=np.ones(len(x),bool); use[ix]=False
        f=predict(fit(x[use],y[use]),x[ix]); residual[ix]=np.sum((y[ix]-f)**2,axis=1)
    sigma=np.array([max(1e-3,np.sqrt(residual[x[:,2]==g].mean())) for g in [0,1]])
    return fit(x,y),sigma

def quantile(a,alpha=.1):
    a=np.asarray(a); n=len(a); rank=int(np.ceil((n+1)*(1-alpha)))
    return np.inf if rank>n else np.partition(a,rank-1,axis=0)[rank-1]

def weighted_quantile(scores,weights,test_weight,alpha=.1):
    if len(scores)==0:
        return np.inf  # Only the test atom remains.
    order=np.argsort(scores); c=np.cumsum(np.asarray(weights)[order])
    target=(1-alpha)*(c[-1]+test_weight)
    ix=np.searchsorted(c,target,side='left')
    return np.inf if ix==len(scores) else np.asarray(scores)[order[ix]]

def scores(y,f):
    d=y-f; k=y.shape[-1]
    ans={'TV':.5*np.abs(d).sum(-1),'L2':np.sqrt((d*d).sum(-1)),
         'Linf':np.abs(d).max(-1),'Hellinger':np.sqrt(.5*((np.sqrt(y)-np.sqrt(f))**2).sum(-1))}
    for eps,key in [(1e-6,'CLR-6'),(1e-2,'CLR-2')]:
        z=np.log(y+eps)-np.log(f+eps); z-=z.mean(-1,keepdims=True)
        ans[key]=np.sqrt((z*z).mean(-1))
    return ans

def calibrate(y,f,g,sigma):
    s=scores(y,f); q={key:quantile(val) for key,val in s.items()}
    d=np.abs(y-f); k=y.shape[1]
    q['Coord']=quantile(d); q['Bonferroni']=quantile(d,ALPHA/k)
    q['ScaledL2']=quantile(s['L2']/sigma[g])
    q['MondrianL2']=np.array([quantile(s['L2'][g==i]) for i in [0,1]])
    w=np.where(g==1,4.,.25)
    q['WeightedL2']=np.array([weighted_quantile(s['L2'],w,t) for t in [.25,4.]])
    return q,float(w.sum()**2/(w*w).sum())

def membership(y,f,g,q,sigma):
    s=scores(y,f); out=[]
    for m in METHODS:
        if m in s: out.append(s[m]<=q[m])
        elif m in ['Coord','Bonferroni']: out.append((np.abs(y-f)<=q[m]).all(-1))
        else:
            threshold=(q[m]*sigma[g] if m=='ScaledL2' else q[m][g])
            out.append(s['L2']<=threshold)
    return np.stack(out)

def conditional(ind,mask):
    return float(ind[mask].mean()) if np.any(mask) else float('nan')

def probe_masses(beta,q,sigma,k,seed,law,nx,nfull,nface,pool=0):
    # Balanced covariates, then analytical covariate-mixture weighting.
    r=rng(seed,k,law,20+pool); out=np.zeros((len(METHODS),2,k+1)); blocks=np.zeros((2,len(METHODS),2,k+1))
    for g in [0,1]:
        x=np.column_stack([r.uniform(-1,1,(nx,2)),np.full(nx,g)])
        f=predict(beta,x)[:,None,:]
        for j in range(k+1):
            n=nfull if j==0 else nface
            d=k if j==0 else k-1
            z=r.exponential(size=(nx,n,d)); z/=z.sum(-1,keepdims=True)
            if j>0:
                y=np.zeros((nx,n,k)); y[...,np.arange(k)!=j-1]=z
            else: y=z
            mem=membership(y,f,g,q,sigma)
            out[:,g,j]=mem.mean(axis=(1,2))
            for b,sl in enumerate([slice(0,nx//2),slice(nx//2,nx)]):
                blocks[b,:,g,j]=mem[:,sl].mean(axis=(1,2))
    return out,blocks

def run_cell(seed,k,law,cfg,outdir):
    start=time.perf_counter(); outdir=Path(outdir)
    target=outdir/f'{seed}_{k}_{law}.json'
    if target.exists(): return {'path':str(target),'cached':True}
    x,y,b,_=generate(cfg['n_train'],k,law,.2,rng(seed,k,law,0))
    beta,sigma=fit_scale(x,y,rng(seed,k,law,5))
    xc,yc,bc,_=generate(cfg['n_cal'],k,law,.2,rng(seed,k,law,1))
    fc=predict(beta,xc); q,ess=calibrate(yc,fc,xc[:,2].astype(int),sigma)
    masses,blocks=probe_masses(beta,q,sigma,k,seed,law,cfg['nx'],cfg['nfull'],cfg['nface'])
    rows=[]; controls=[]
    for regime,p,stream in [('source',.2,2),('shift',.8,3)]:
        xt,yt,bt,_=generate(cfg['n_test'],k,law,p,rng(seed,k,law,stream))
        ft=predict(beta,xt); gt=xt[:,2].astype(int)
        mem=membership(yt,ft,gt,q,sigma)
        mix=np.array([1-p,p]); vol=np.einsum('mgj,g->mj',masses,mix)
        bl=np.einsum('bmgj,g->bmj',blocks,mix)
        a=yt[:,-1]>=.5; union=a|bt
        controls.append({'seed':seed,'K':k,'law':law,'regime':regime,'coverage_A':float(a.mean()),'coverage_union':float(union.mean()),'coverage_difference':float((union.astype(int)-a.astype(int)).mean()),'boundary_prevalence':float(bt.mean()),'ambient_mass_difference':0.,'supported_face_mass_difference':1.,'Q_mass_difference':1/(2*k)})
        for mi,m in enumerate(METHODS):
            if m=='WeightedL2' and regime=='source': continue
            mask=mem[mi]; v=vol[mi]; bv=bl[:,mi]
            row={'seed':seed,'K':k,'law':law,'regime':regime,'method':m,
                 'coverage':float(mask.mean()),'covered':int(mask.sum()),'n':len(mask),
                 'coverage_G0':conditional(mask,gt==0),'coverage_G1':conditional(mask,gt==1),
                 'coverage_B0':conditional(mask,~bt),'coverage_B1':conditional(mask,bt),
                 'n_G0':int((gt==0).sum()),'n_G1':int((gt==1).sum()),'n_B0':int((~bt).sum()),'n_B1':int(bt.sum()),
                 'V':float(v[0]),'A_K':float(v[-1]),'A_mean':float(v[1:].mean()),
                 'E_Q':float(.5*v[0]+.5*v[1:].mean()),
                 'E_rho25':float(.25*v[0]+.75*v[1:].mean()),'E_rho75':float(.75*v[0]+.25*v[1:].mean()),
                 'MC_block_delta_Q':float(abs((.5*bv[0,0]+.5*bv[0,1:].mean())-(.5*bv[1,0]+.5*bv[1,1:].mean()))),
                 'MC_block_delta_AK':float(abs(bv[0,-1]-bv[1,-1])),
                 'probe_zero_V':int(v[0]==0),'probe_zero_AK':int(v[-1]==0),
                 'ESS':ess,'n_cal_G1':int((xc[:,2]==1).sum()),'MSE_G0':conditional(np.sum((yt-ft)**2,1),gt==0),
                 'MSE_G1':conditional(np.sum((yt-ft)**2,1),gt==1),
                 'infinite_threshold_rate':float(np.sum(mix*np.isinf(q[m]))) if m in ['MondrianL2','WeightedL2'] else float(np.any(np.isinf(q[m])))}
            for g in [0,1]:
                for flag in [0,1]:
                    sel=(gt==g)&(bt==flag)
                    row[f'coverage_G{g}B{flag}']=conditional(mask,sel)
                    row[f'n_G{g}B{flag}']=int(sel.sum())
            for j in range(k): row[f'A_{j+1}']=float(v[j+1])
            if m in ['Coord','Bonferroni']:
                coord=(np.abs(yt-ft)<=q[m]).mean(0)
                row['coordinate_coverage_mean']=float(coord.mean()); row['coordinate_coverage_min']=float(coord.min())
            rows.append(row)
    elapsed=time.perf_counter()-start
    result={'rows':rows,'controls':controls,'seconds':elapsed,'seed':seed,'K':k,'law':law,
            'max_rss_kb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'sigma':sigma.tolist(),'q':{m:np.asarray(v).tolist() for m,v in q.items()},'ESS':ess}
    outdir.mkdir(parents=True,exist_ok=True)
    tmp=target.with_suffix('.tmp'); tmp.write_text(json.dumps(result,allow_nan=True)); tmp.replace(target)
    np.savez_compressed(outdir/f'{seed}_{k}_{law}_fit.npz',beta=beta,sigma=sigma,**{f'q_{m}':v for m,v in q.items()})
    return {'path':str(target),'seconds':elapsed,'K':k,'law':law,'seed':seed}

def collect(outdir):
    data=[json.loads(p.read_text()) for p in sorted(Path(outdir).glob('*.json'))]
    pd.DataFrame([r for d in data for r in d['rows']]).to_csv(Path(outdir)/'metrics.csv',index=False)
    pd.DataFrame([r for d in data for r in d['controls']]).to_csv(Path(outdir)/'controls.csv',index=False)
    pd.DataFrame([{k:d[k] for k in ['seed','K','law','seconds','max_rss_kb','ESS']} for d in data]).to_csv(Path(outdir)/'runs.csv',index=False)
    return len(data)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['pilot','main','smoke'],default='main'); ap.add_argument('--workers',type=int,default=4); ap.add_argument('--config',default=str(ROOT/'config.json')); args=ap.parse_args()
    cfg=json.loads(Path(args.config).read_text()); mode=args.mode
    seeds=cfg['seeds'] if mode=='main' else ([900001,900002] if mode=='pilot' else [999991])
    if mode=='smoke': cfg={**cfg,'nx':8,'nfull':64,'nface':32}
    outdir=ROOT/'artifacts'/mode; outdir.mkdir(parents=True,exist_ok=True)
    jobs=[(s,k,l) for s in seeds for k in cfg['dimensions'] for l in cfg['laws']]
    started=time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(run_cell,s,k,l,cfg,str(outdir)) for s,k,l in jobs]
        for f in concurrent.futures.as_completed(futures): print(json.dumps(f.result()),flush=True)
    n=collect(outdir)
    print(json.dumps({'completed_cells':n,'wall_seconds':time.time()-started,'config':cfg}),flush=True)

if __name__=='__main__': main()
