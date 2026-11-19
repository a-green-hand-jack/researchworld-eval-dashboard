import sys, numpy as np, json, warnings
from scipy.stats import norm, t as tdist
from sklearn.isotonic import IsotonicRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from multiprocessing import Pool
warnings.filterwarnings('ignore')
D='/work/data/'; ALPHA=0.05; Z=norm.ppf(1-ALPHA/2)
DS=['galaxies','forest','alphafold','gene_expression','census_income','census_healthcare']
def load(name):
    d=np.load(D+name+'.npz'); Y=d['Y'].astype(float); F=d['Yhat'].astype(float)
    X=d['X'].astype(float) if 'X' in d else None
    return Y,F,X
def ci(est,se,crit=Z): return est-crit*se, est+crit*se
def ppi_family(Y,F,Fu,lam=None):
    n,N=len(Y),len(Fu)
    if lam is None:  # PPI++ power tuning (one-dim mean): lam = cov(Y,F)/((1+n/N)var F)
        c=np.cov(Y,F)[0,1]; lam=c/((1+n/N)*np.var(np.r_[F,Fu]))
    est=np.mean(Y-lam*F)+lam*np.mean(Fu)
    se=np.sqrt(np.var(Y-lam*F,ddof=1)/n+lam**2*np.var(Fu,ddof=1)/N)
    return est,se
def crossfit(Y,Z_,Zu,kind,K=5,rng=None):
    n=len(Y); fold=rng.permutation(n)%K
    f_lab=np.zeros(n); f_unl=np.zeros(len(Zu))
    for k in range(K):
        tr=fold!=k
        if kind=='iso':
            m=IsotonicRegression(out_of_bounds='clip',increasing='auto').fit(Z_[tr,0],Y[tr])
            p=lambda A:m.predict(A[:,0])
        else:
            m=HistGradientBoostingRegressor(max_iter=60,learning_rate=0.1,max_leaf_nodes=6,min_samples_leaf=20).fit(Z_[tr],Y[tr])
            p=m.predict
        f_lab[~tr]=p(Z_[~tr]); f_unl+=p(Zu)/K
    return f_lab,f_unl
def one(args):
    name,n,N,seed=args
    Y_,F_,X_=load(name); rng=np.random.default_rng(seed); truth=Y_.mean()
    i=rng.integers(0,len(Y_),n); j=rng.integers(0,len(Y_),N)
    Y,F,Fu=Y_[i],F_[i],F_[j]; out={}
    out['classical']=ci(Y.mean(),Y.std(ddof=1)/np.sqrt(n))
    out['PPI']=ci(*ppi_family(Y,F,Fu,1.0))
    e,s=ppi_family(Y,F,Fu); out['PPI++']=ci(e,s)
    tc=tdist.ppf(1-ALPHA/2,n-1)
    out['PPI++_t']=ci(e,s,tc)
    Zl=F[:,None]; Zu=Fu[:,None]
    kinds=[('iso',Zl,Zu)]
    if X_ is not None:
        kinds.append(('gbm',np.c_[F,X_[i]],np.c_[Fu,X_[j]]))
    else: kinds.append(('gbm',Zl,Zu))
    for kind,A,B in kinds:
        fl,fu=crossfit(Y,A,B,kind,rng=rng)
        e,s=ppi_family(Y,fl,fu)
        out['recal-'+kind]=ci(e,s); out['recal-'+kind+'_t']=ci(e,s,tc)
    return name,n,{k:(v[0]<=truth<=v[1],v[1]-v[0]) for k,v in out.items()}
if __name__=='__main__':
    R=int(sys.argv[1]); N=5000
    jobs=[(d,n,N,hash((d,n,r))%2**31 if False else 1000*r+7*n+DS.index(d)) for d in DS for n in (50,200,1000) for r in range(R)]
    res={}
    with Pool(36) as p:
        for name,n,o in p.imap_unordered(one,jobs,chunksize=8):
            for k,(c,w) in o.items(): res.setdefault(f"{name}|{n}|{k}",[]).append((float(c),float(w)))
    json.dump({k:v for k,v in res.items()},open('/work/code/results.json','w'))
