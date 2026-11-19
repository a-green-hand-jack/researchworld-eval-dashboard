# feasibility timing on SYNTHETIC BT data (not a result; timing only)
import numpy as np, time
rng=np.random.default_rng(0)
def fit(a,b,y,w,K,th=None,it=30):
    th=np.zeros(K) if th is None else th.copy()
    for _ in range(it):
        d=th[a]-th[b]; p=1/(1+np.exp(-d)); g=np.zeros(K)
        r=w*(y-p); np.add.at(g,a,r); np.add.at(g,b,-r)
        v=w*p*(1-p); H=np.zeros((K,K))
        np.add.at(H,(a,a),v); np.add.at(H,(b,b),v); np.add.at(H,(a,b),-v); np.add.at(H,(b,a),-v)
        H+=1e-6*np.eye(K)+np.ones((K,K))*1e-3
        st=np.linalg.solve(H,g-1e-3*th); th=th+st
        if np.abs(st).max()<1e-8: break
    return th
for N,K in [(57000,64),(3300,6),(1230,30),(63000,110)]:
    th0=rng.normal(0,0.5,K); a=rng.integers(0,K,N); b=(a+rng.integers(1,K,N))%K
    y=(rng.random(N)<1/(1+np.exp(-(th0[a]-th0[b])))).astype(float); w=np.ones(N)
    t=time.time(); th=fit(a,b,y,w,K); t1=time.time()-t
    # warm refit with 50 dropped
    w2=w.copy(); w2[rng.choice(N,50,replace=False)]=0
    t=time.time(); fit(a,b,y,w2,K,th); t2=time.time()-t
    # bootstrap 1 replicate
    idx=rng.integers(0,N,N); t=time.time(); fit(a[idx],b[idx],y[idx],w,K,th); t3=time.time()-t
    print(N,K,"cold %.3fs warm-refit %.3fs bootstrap-rep %.3fs"%(t1,t2,t3))
