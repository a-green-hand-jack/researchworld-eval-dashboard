import time, numpy as np, scipy.sparse as sp
from scipy.io import mmread
t=time.time()
A=mmread('/hutian/work/dl/socfb-Stanford3.mtx').tocsr(); A=((A+A.T)>0).astype(float); A.setdiag(0); A.eliminate_zeros()
n=A.shape[0]; deg=np.asarray(A.sum(1)).ravel()
print(n, A.nnz//2, deg.mean(), deg.max(), 'load',time.time()-t)
rng=np.random.default_rng(0)
Dinv=sp.diags(1/np.maximum(deg,1)); W=Dinv@A
def sim(rep, p=0.5, gam=0.5):
    z=(rng.random(n)<p).astype(float)
    def y(z): return 1+1.0*z+gam*(W@z)+0.5*(W@(W@z))*0 + 0.3*rng.standard_normal(n)*0
    noise=rng.standard_normal(n)
    Y=1+z+gam*(W@z)+noise
    X=np.c_[np.ones(n),z,W@z,A@z]
    b=np.linalg.lstsq(X,Y,rcond=None)[0]
    X1=np.c_[np.ones(n),np.ones(n),W@np.ones(n),A@np.ones(n)]
    X0=np.zeros_like(X1); X0[:,0]=1
    est=(X1@b-X0@b).mean()
    return est, 1+gam
t=time.time()
r=[sim(i) for i in range(200)]
print('200 reps OLS', time.time()-t, np.mean([a for a,_ in r]), np.std([a for a,_ in r]))
