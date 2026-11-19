import numpy as np, scipy.sparse as sp, time
rng=np.random.default_rng(0)
def make(N,K):
    p=rng.dirichlet(np.ones(K)*0.7)
    a=rng.choice(K,N,p=p); b=rng.choice(K,N,p=p)
    m=a!=b; a,b=a[m],b[m]
    th=rng.normal(0,0.6,K); y=(rng.random(len(a))<1/(1+np.exp(-(th[a]-th[b])))).astype(float)
    return a,b,y
def fit(a,b,y,w,K,lam=1e-3,th=None,it=30):
    n=len(a); X=sp.csr_matrix((np.r_[np.ones(n),-np.ones(n)],(np.r_[np.arange(n),np.arange(n)],np.r_[a,b])),shape=(n,K))
    th=np.zeros(K) if th is None else th
    for i in range(it):
        z=X@th; p=1/(1+np.exp(-z)); g=X.T@(w*(p-y))+lam*th
        H=(X.T@sp.diags(w*p*(1-p))@X).toarray()+lam*np.eye(K)
        d=np.linalg.solve(H,g); th-=d
        if np.abs(d).max()<1e-9: break
    return th,i+1
for N,K in [(57000,64),(60000,126),(3300,6)]:
    a,b,y=make(N,K); w=np.ones(len(a))
    t=time.time(); th,it=fit(a,b,y,w,K); t1=time.time()-t
    t=time.time(); th2,it2=fit(a,b,y,w,K,th=th,it=30); t2=time.time()-t
    print(N,K,'cold',round(t1,3),it,'warm',round(t2,3),it2)
