"""E-theory: check optimism = sigma^2/sqrt(tau^2+sigma^2) * E[max of B std normals] on an iid-Gaussian-prior synthetic world.
Output: results/theory.csv"""
import sys; sys.path.insert(0,"/work/code")
import numpy as np, pandas as pd
from scipy import stats
from sel import *
rng=np.random.default_rng(2024)
K=1000; a=-0.4; rows=[]
def emax(B, m=200000, rng=np.random.default_rng(5)):
    return float(rng.standard_normal((20000,B)).max(1).mean())
for tau_p in (0.0,0.03,0.06,0.12,0.25):
  mu=tau_p*rng.standard_normal(K)
  acc=stats.norm.cdf(a+mu)
  for rho in (0.0,0.5,0.8):
    N=20000
    z=rng.standard_normal((N,1)); u=rng.standard_normal((N,K))
    Y=((a+mu[None,:]+np.sqrt(rho)*z+np.sqrt(1-rho)*u)>0).astype(np.uint8)
    pbar=Y.mean(0); tau=acc.std()
    # config-specific noise: item-level variance of (y_ci - mean_c' y_c'i)
    resid=Y.astype(float)-Y.mean(1,keepdims=True)
    vsp=float(resid.var(0).mean())*K/(K-1)   # per-item variance of config-specific deviation
    for n in (50,100,200,400,800):
      sig2=vsp/n
      for B in (2,8,32,128,512):
        reps=400; opt=np.empty(reps)
        for r in range(reps):
            S=rng.choice(N,n,replace=False)
            cand=rng.choice(K,B,replace=False)
            m=Y[np.ix_(S,cand)].mean(0)
            j=int(np.argmax(m+1e-9*rng.random(B)))
            opt[r]=m[j]-acc[cand[j]]
        pred=sig2/np.sqrt(tau**2+sig2)*emax(B)
        rows.append(dict(tau_probit=tau_p,tau=tau,rho=rho,n=n,B=B,opt=opt.mean(),opt_se=opt.std()/np.sqrt(reps),pred=pred,sig_spec=np.sqrt(sig2)))
    print(tau_p,rho,flush=True)
pd.DataFrame(rows).to_csv("/work/results/theory.csv",index=False)
