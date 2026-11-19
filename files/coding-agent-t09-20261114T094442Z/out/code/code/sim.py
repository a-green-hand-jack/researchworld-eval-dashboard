import numpy as np, scipy.sparse as sp, sys, json, time, warnings
from multiprocessing import Pool
sys.path.insert(0,'/work/code')
from lib import *
from sklearn.ensemble import HistGradientBoostingRegressor as HGB
warnings.filterwarnings('ignore')
_gc={}
def graph(spec,gseed):
    key=json.dumps(spec,sort_keys=True)+str(gseed)
    if key not in _gc:
        A,lab=make_graph(spec,gseed); deg=np.asarray(A.sum(1)).ravel(); keep=np.where(deg>0)[0]
        A=A[keep][:,keep].tocsr(); lab=np.unique(lab[keep],return_inverse=True)[1]
        _gc.clear(); _gc[key]=(A,lab)
    return _gc[key]

def run(cfg):
    """cfg: graph(spec), model, design('bern'|'cluster'), p, gam, tau, sigma, R, nhgb"""
    spec=cfg['graph']; A,lab=graph(spec,cfg.get('gseed',1)); n=A.shape[0]
    deg=np.asarray(A.sum(1)).ravel(); dbar=deg.mean(); ld=np.log(deg); ld=(ld-ld.mean())/(ld.std()+1e-12)
    p,tau,gam,sig_=cfg['p'],cfg.get('tau',1.),cfg['gam'],cfg.get('sigma',1.)
    cl = lab if cfg['design']=='cluster' else np.arange(n)
    K=cl.max()+1
    M=sp.csr_matrix((np.ones(n),(np.arange(n),cl)),shape=(n,K))
    S=((A+sp.eye(n))@M); S.data[:]=1; kcl=np.asarray(S.sum(1)).ravel()   # clusters in closed nbhd
    P1=p**kcl; P0=(1-p)**kcl
    one=np.ones(n); zero=np.zeros(n)
    truth=np.mean(outcome_terms(cfg['model'],one,one,deg/dbar,tau,gam)-outcome_terms(cfg['model'],zero,zero,zero,tau,gam))
    ests=['dm']+OLS+['hgb','hajek']
    err={e:[] for e in ests}; cov={e:[] for e in ['ols_frac','ols_count','ols_rich','poly']}
    rng=np.random.default_rng(cfg['seed']); R=cfg['R']
    F1={m:phi(m,one,one,deg/dbar,ld) for m in OLS}; F0={m:phi(m,zero,zero,zero,ld) for m in OLS}
    xcache=None
    for r in range(R):
        zc=(rng.random(K)<p).astype(float); z=zc[cl]
        x=A@z/deg; c=A@z/dbar
        Y=0.5*ld+outcome_terms(cfg['model'],z,x,c,tau,gam)+sig_*rng.standard_normal(n)
        err['dm'].append(Y[z==1].mean()-Y[z==0].mean()-truth)
        for m in OLS:
            X=phi(m,z,x,c,ld); XtXi=np.linalg.pinv(X.T@X); b=XtXi@X.T@Y
            cvec=(F1[m]-F0[m]).mean(0); est=cvec@b; err[m].append(est-truth)
            if m in cov:
                e=Y-X@b; V=XtXi@((X*(e**2)[:,None]).T@X)@XtXi*n/(n-X.shape[1]); se=np.sqrt(cvec@V@cvec)
                cov[m].append(abs(est-truth)<=1.96*se)
        if r<cfg.get('nhgb',0):
            Xf=np.c_[z,x,c,ld]; h=HGB(max_iter=150,learning_rate=0.1,random_state=r).fit(Xf,Y)
            err['hgb'].append(np.mean(h.predict(np.c_[one,one,deg/dbar,ld])-h.predict(np.c_[zero,zero,zero,ld]))-truth)
        e1=(S@(1-zc)==0); e0=(S@zc==0)   # whole closed nbhd in treated / control clusters
        if e1.any() and e0.any():
            w1=e1/P1; w0=e0/P0
            err['hajek'].append((w1@Y)/w1.sum()-(w0@Y)/w0.sum()-truth)
        else: err['hajek'].append(np.nan)
    rows=[]; rb=np.random.default_rng(0)
    for e in ests:
        a=np.array(err[e]); nn=int(np.isnan(a).sum()); a=a[~np.isnan(a)]
        if len(a)<3: continue
        bs=[np.sqrt(np.mean(a[rb.integers(0,len(a),len(a))]**2)) for _ in range(200)]
        rows.append(dict(est=e,bias=a.mean(),bias_se=a.std(ddof=1)/np.sqrt(len(a)),sd=a.std(ddof=1),rmse=np.sqrt(np.mean(a**2)),
            rmse_lo=np.percentile(bs,2.5),rmse_hi=np.percentile(bs,97.5),nreps=len(a),nan_frac=nn/R,
            cover=float(np.mean(cov[e])) if e in cov else None))
    base={k:(json.dumps(v) if isinstance(v,dict) else v) for k,v in cfg.items()}
    base.update(truth=truth,n=n,dbar=dbar,nclust=int(K),
        mean_x_sd=None)
    return [dict(base,**r) for r in rows]

def main(cfgs,out,procs=36):
    t=time.time()
    with Pool(procs) as P: res=P.map(run,cfgs,chunksize=1)
    rows=[r for rs in res for r in rs]
    json.dump(rows,open(out,'w')); print(out,len(rows),'rows',round(time.time()-t),'s')
