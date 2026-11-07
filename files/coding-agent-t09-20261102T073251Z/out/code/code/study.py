"""Endpoint extrapolation study. CPU only; all output numbers are computed here.

Run from repository root with OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1.
"""
from __future__ import annotations
import argparse, gzip, hashlib, json, os, platform, time
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
from scipy import sparse, stats

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261102
DGMS = ['linear', 'quadratic', 'cubic', 'threshold', 'twohop']
MODELS = ['DM', 'OLS-L', 'OLS-Q', 'OLS-C', 'OLS-2H', 'Ridge-C', 'HT']

def load_graphs(scaling=False):
    specs = [(1600, k) for k in (8, 32, 128)]
    if scaling:
        specs = [(n,k) for n in (800,3200) for k in (8,32,128)]
    graphs = {}
    for n,k in specs:
        graphs[f'reg{n}k{k}'] = nx.random_regular_graph(k, n, seed=SEED+n+k)
    if not scaling:
        sizes = [40]*40
        probs = np.full((40,40), 4/1560)
        np.fill_diagonal(probs, 0.6)
        graphs['SBM'] = nx.stochastic_block_model(sizes, probs, seed=SEED+11)
        graphs['BA'] = nx.barabasi_albert_graph(1600, 16, seed=SEED+12)
        with gzip.open(ROOT/'data/raw/facebook_combined.txt.gz', 'rt') as f:
            g = nx.read_edgelist(f, nodetype=int)
        graphs['Facebook'] = nx.convert_node_labels_to_integers(g, ordering='sorted')
    return graphs

def setup_graph(g, name, index):
    n=len(g)
    a=sparse.csr_matrix(nx.to_scipy_sparse_array(g, nodelist=range(n), dtype=float))
    deg=np.asarray(a.sum(axis=1)).ravel()
    assert deg.min()>0
    p=sparse.diags(1/deg)@a
    if name=='SBM':
        groups=np.arange(n)//40
    else:
        # Deterministic partition; no outcomes or assignments used.
        comms=nx.community.louvain_communities(g, resolution=2, seed=SEED)
        groups=np.empty(n, dtype=int)
        for j,c in enumerate(sorted(comms, key=lambda c:min(c))):
            groups[list(c)]=j
    rng=np.random.default_rng(SEED+700+index)
    x=np.log1p(deg)+rng.normal(size=n)
    x=(x-x.mean())/x.std()
    inside=float(np.mean(groups[np.repeat(np.arange(n),np.diff(a.indptr))]==groups[a.indices]))
    meta=dict(graph=name,n=n,edges=g.number_of_edges(),mean_degree=float(deg.mean()),
              min_degree=int(deg.min()),max_degree=int(deg.max()),clusters=int(groups.max()+1),
              within_edge_fraction=inside,clustering=float(nx.average_clustering(g)))
    return p,deg,groups,x,meta

def features(z,s,t,x,model):
    cols=[np.ones(len(z)),x,z,(s>=.8).astype(float) if model=='OLS-T' else s]
    c=[0.,0.,1.,1.]
    if model in ('OLS-Q','OLS-C','Ridge-C'):
        # Centered polynomial basis improves numeric conditioning. At endpoints,
        # (s-.5)^2 has zero contrast, (s-.5)^3 has contrast .25.
        cols.append((s-.5)**2);c.append(0.)
    if model in ('OLS-C','Ridge-C'):
        cols.append((s-.5)**3);c.append(.25)
    if model=='OLS-2H':
        cols.append(t);c.append(1.)
    return np.column_stack(cols),np.array(c)

def weights(z,s,t,x,model):
    n=len(z)
    if model=='DM':
        if z.sum() in (0,n): return None
        return z/z.sum()-(1-z)/(n-z.sum()),None,None,None
    X,c=features(z,s,t,x,model)
    if model=='Ridge-C':
        # Unit-variance scaling; fixed penalty lambda=10, not chosen on outcomes.
        center=X.mean(axis=0); center[0]=0
        scale=X.std(axis=0);scale[0]=1;scale[scale<1e-14]=1
        X=(X-center)/scale;c=c/scale
        pen=np.diag([0]+[10.]*(X.shape[1]-1))
        w=X@np.linalg.solve(X.T@X+pen,c)
        return w,X,c,int(np.linalg.matrix_rank(X))
    U,d,Vh=np.linalg.svd(X,full_matrices=False)
    keep=d>1e-12*d[0]
    # Record the rank; endpoint estimability, not rank alone, controls validity.
    proj=Vh[keep].T@Vh[keep]@c
    if np.linalg.norm(proj-c)>1e-7:
        return None
    w=U[:,keep]@((Vh[keep]@c)/d[keep])
    return w,X,c,int(keep.sum())

def conditional_variance(w,groups,sigma,rho):
    return sigma**2*((1-rho)*np.dot(w,w)+rho*np.dot(
        np.bincount(groups,weights=w),np.bincount(groups,weights=w)))

def peano_bound(w,s):
    """Exact integral |K(t)| dt for a signed endpoint-reproducing functional.

    Piecewise linear kernel: sum_i w_i(s_i-t)_+ - (1-t).
    Returns the unit-curvature sharp bound (multiplied by M by the caller).
    """
    order=np.argsort(s);ss=s[order];ww=w[order]
    knots=np.unique(np.r_[0.,ss,1.])
    sw=np.r_[np.cumsum(ww[::-1])[::-1],0.]
    sws=np.r_[np.cumsum((ww*ss)[::-1])[::-1],0.]
    j=np.searchsorted(ss,knots,side='right')
    K=sws[j]-knots*sw[j]-(1-knots)
    left=K[:-1];right=K[1:];length=np.diff(knots)
    area=length*(np.abs(left)+np.abs(right))/2
    cross=left*right<0
    area[cross]=length[cross]*(left[cross]**2+right[cross]**2)/(2*(np.abs(left[cross])+np.abs(right[cross])))
    return float(area.sum()),knots,K

def ht_weights(z,s,p,groups,design):
    # Closed-neighborhood exposure is sufficient for all one-hop DGMs here,
    # but not for the two-hop DGM, which is explicitly marked invalid for HT.
    n=len(z)
    exposed1=(z==1)&(s>=1-1e-12)
    exposed0=(z==0)&(s<=1e-12)
    if design=='bernoulli':
        count=np.diff(p.indptr)+1
    else:
        count=np.array([len(set(groups[p.indices[p.indptr[i]:p.indptr[i+1]]])|{groups[i]}) for i in range(n)])
    prob=np.exp2(-count.astype(float))
    return (exposed1.astype(float)-exposed0.astype(float))/prob/n

def run_suite(reps, scaling=False, rho=0., suffix='main'):
    start=time.time();rows=[];metas=[]
    sigma=.5
    for gi,(name,g) in enumerate(load_graphs(scaling).items()):
        p,deg,groups,x,meta=setup_graph(g,name,gi)
        metas.append(meta);n=len(g)
        designs=['bernoulli'] if scaling else ['bernoulli','cluster']
        for di,design in enumerate(designs):
            rng=np.random.default_rng(np.random.SeedSequence([SEED,gi,di,int(rho*1000),int(scaling)]))
            for r in range(reps):
                z=(rng.binomial(1,.5,size=n) if design=='bernoulli' else
                   rng.binomial(1,.5,size=groups.max()+1)[groups]).astype(float)
                s=p@z;t=p@s
                means=np.column_stack([1+.5*x+z+2*s,1+.5*x+z+2*s*s,
                    1+.5*x+z+2*s**3,1+.5*x+z+2*(s>=.8),1+.5*x+z+s+t])
                eps=sigma*(np.sqrt(1-rho)*rng.normal(size=n)+
                           np.sqrt(rho)*rng.normal(size=groups.max()+1)[groups])
                ys=means+eps[:,None]
                mlist=MODELS if not scaling else ['OLS-L','OLS-C']
                for model in mlist:
                    if model=='HT':
                        w=ht_weights(z,s,p,groups,design);X=None;rank=-1
                    else:
                        ans=weights(z,s,t,x,model)
                        if ans is None:
                            for dgm in DGMS:
                                rows.append(dict(graph=name,design=design,rep=r,dgm=dgm,model=model,valid=False))
                            continue
                        w,X,c,rank=ans
                    est=w@ys;bias=w@means-3
                    var=conditional_variance(w,groups,sigma,rho)
                    iidvar=sigma**2*np.dot(w,w)
                    # Predictive error on conditional mean, free of outcome noise.
                    # Main CV experiment below uses held-out noisy outcomes.
                    if X is None: pmse=np.full(len(DGMS),np.nan)
                    else:
                        bh=np.linalg.lstsq(X,ys,rcond=1e-12)[0]
                        if model=='Ridge-C':
                            bh=np.linalg.solve(X.T@X+np.diag([0]+[10.]*(X.shape[1]-1)),X.T@ys)
                        pmse=np.mean((X@bh-means)**2,axis=0)
                    for j,dgm in enumerate(DGMS):
                        se=np.sqrt(var);ise=np.sqrt(iidvar)
                        rows.append(dict(graph=name,design=design,rep=r,dgm=dgm,model=model,
                            valid=True,estimate=float(est[j]),error=float(est[j]-3),
                            conditional_bias=float(bias[j]),noise_var=float(var),iid_var=float(iidvar),
                            cover_oracle=abs(est[j]-3)<=1.96*se,
                            cover_iid=abs(est[j]-3)<=1.96*ise,
                            norm2=float(np.dot(w,w)),l1=float(np.abs(w).sum()),
                            curve_factor=float(.5*np.dot(np.abs(w),s*(1-s))),
                            prediction_mse=float(pmse[j]),rank=rank,
                            exposure_sd=float(s.std()),tail_fraction=float(np.mean(s>=.8)),
                            fully_exposed=int(np.sum((z==1)&(s>=1-1e-12))+
                                              np.sum((z==0)&(s<=1e-12)))))
            print(suffix,name,design,'elapsed',round(time.time()-start,1),flush=True)
    out=ROOT/'results';out.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(out/f'{suffix}_raw.csv.gz',index=False)
    pd.DataFrame(metas).to_csv(out/f'{suffix}_graphs.csv',index=False)
    (out/f'{suffix}_run.json').write_text(json.dumps(dict(seed=SEED,reps=reps,rho=rho,
        seconds=time.time()-start,python=platform.python_version(),sigma=sigma,
        dgms=DGMS,models=MODELS,scaling=scaling),indent=2))

def validation(reps):
    """Node-held-out prediction selection vs actual endpoint loss; no test oracle selection."""
    from sklearn.ensemble import RandomForestRegressor
    out=[];start=time.time()
    for gi,k in enumerate((8,32,128)):
        name=f'reg1600k{k}';g=nx.random_regular_graph(k,1600,seed=SEED+1600+k)
        p,deg,groups,x,meta=setup_graph(g,name,gi)
        rng=np.random.default_rng(SEED+8000+k)
        for r in range(reps):
            z=rng.binomial(1,.5,1600).astype(float);s=p@z;t=p@s
            mu=1+.5*x+z+2*s**3;y=mu+.5*rng.normal(size=1600)
            perm=rng.permutation(1600);train=perm[:1120];test=perm[1120:]
            scores={};estimates={}
            for model in ['OLS-L','OLS-Q','OLS-C']:
                X,c=features(z,s,t,x,model)
                beta=np.linalg.lstsq(X[train],y[train],rcond=1e-12)[0]
                score=np.mean((X[test]@beta-y[test])**2)
                w,_,_,_=weights(z,s,t,x,model);est=float(w@y)
                scores[model]=score;estimates[model]=est
                out.append(dict(k=k,rep=r,model=model,mse=score,estimate=est,error=est-3))
            # RF is deliberately interpolation-focused; report its extrapolation limitation.
            X=np.column_stack([x,z,s]);xt=np.column_stack([x,np.ones(1600),np.ones(1600)])
            xc=np.column_stack([x,np.zeros(1600),np.zeros(1600)])
            rf=RandomForestRegressor(n_estimators=60,min_samples_leaf=10,max_features=1.,
                                     n_jobs=1,random_state=SEED+r)
            rf.fit(X[train],y[train]);score=float(np.mean((rf.predict(X[test])-y[test])**2))
            rf.fit(X,y);est=float(np.mean(rf.predict(xt)-rf.predict(xc)))
            out.append(dict(k=k,rep=r,model='RF',mse=score,estimate=est,error=est-3))
            chosen=min(scores,key=scores.get)
            out.append(dict(k=k,rep=r,model='CV-select',selected=chosen,mse=scores[chosen],
                            estimate=estimates[chosen],error=estimates[chosen]-3))
        print('validation',k,'elapsed',round(time.time()-start,1),flush=True)
    pd.DataFrame(out).to_csv(ROOT/'results/validation_raw.csv.gz',index=False)
    (ROOT/'results/validation_run.json').write_text(json.dumps(dict(reps=reps,seconds=time.time()-start,seed=SEED+8000),indent=2))

def saturation(reps):
    """Sensitivity to treatment probability breaks the quadratic symmetry example."""
    rows=[];k=32;n=1600
    g=nx.random_regular_graph(k,n,seed=SEED+n+k)
    p,deg,groups,x,_=setup_graph(g,'reg1600k32',1)
    for pi,pr in enumerate((.2,.5,.8)):
        rng=np.random.default_rng(SEED+9000+pi)
        for r in range(reps):
            z=rng.binomial(1,pr,n).astype(float);s=p@z;t=p@s
            y=1+.5*x+z+2*s*s+.5*rng.normal(size=n)
            for model in ['OLS-L','OLS-Q']:
                w,_,_,_=weights(z,s,t,x,model)
                rows.append(dict(p=pr,rep=r,model=model,error=float(w@y-3)))
    pd.DataFrame(rows).to_csv(ROOT/'results/saturation_raw.csv.gz',index=False)

def sensitivity(reps):
    start=time.time();out=[];kernels=[];oracle=[]
    for gi,(name,g) in enumerate(load_graphs().items()):
        p,deg,groups,x,meta=setup_graph(g,name,gi);n=len(g)
        for di,design in enumerate(['bernoulli','cluster']):
            # Same assignments and noises as the main experiment, independently regenerated.
            rng=np.random.default_rng(np.random.SeedSequence([SEED,gi,di,0,0]))
            for r in range(reps):
                z=(rng.binomial(1,.5,n) if di==0 else rng.binomial(1,.5,groups.max()+1)[groups]).astype(float)
                s=p@z;t=p@s
                eps=.5*rng.normal(size=n)
                rng.normal(size=groups.max()+1) # keep main stream exactly aligned
                oa=weights(z,s,t,x,'OLS-T')
                if oa is None:
                    oracle.append(dict(graph=name,design=design,rep=r,valid=False))
                else:
                    ow,_,_,_=oa;oe=float(ow@(1+.5*x+z+2*(s>=.8)+eps)-3)
                    oracle.append(dict(graph=name,design=design,rep=r,valid=True,error=oe,
                                       noise_var=.25*float(ow@ow)))
                ans=weights(z,s,t,x,'OLS-L')
                if ans is None:continue
                w,_,_,_=ans
                bound,knots,K=peano_bound(w,s)
                loose=.5*np.sum(abs(w)*s*(1-s));se=.5*np.linalg.norm(w)
                for dgm,M,h in [('linear',0,2*s),('quadratic',4,2*s*s),('cubic',12,2*s**3)]:
                    mu=1+.5*x+z+h
                    error=float(w@(mu+eps)-3);bias=float(w@mu-3)
                    out.append(dict(graph=name,design=design,rep=r,dgm=dgm,error=error,
                        conditional_bias=bias,M=M,sharp=M*bound,loose=M*loose,unit_sharp=bound,
                        unit_loose=loose,noise_se=se,cover_sensitivity=abs(error)<=1.96*se+M*bound,
                        cover_gaussian=abs(error)<=1.96*se))
                if r==0 and di==0 and name.startswith('reg'):
                    kernels.extend(dict(graph=name,t=float(a),K=float(b)) for a,b in zip(knots,K))
            print('sensitivity',name,design,'elapsed',round(time.time()-start,1),flush=True)
    pd.DataFrame(out).to_csv(ROOT/'results/sensitivity_raw.csv.gz',index=False)
    pd.DataFrame(kernels).to_csv(ROOT/'results/kernels.csv',index=False)
    pd.DataFrame(oracle).to_csv(ROOT/'results/threshold_oracle_raw.csv.gz',index=False)
    (ROOT/'results/sensitivity_run.json').write_text(json.dumps(dict(reps=reps,seconds=time.time()-start),indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['main','scaling','noise','validation','saturation','sensitivity'],default='main')
    ap.add_argument('--reps',type=int,default=400);args=ap.parse_args()
    if args.mode=='validation':validation(args.reps)
    elif args.mode=='saturation':saturation(args.reps)
    elif args.mode=='sensitivity':sensitivity(args.reps)
    else:run_suite(args.reps,scaling=args.mode=='scaling',rho=.5 if args.mode=='noise' else 0.,suffix=args.mode)
