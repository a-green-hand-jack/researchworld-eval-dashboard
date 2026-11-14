"""Exact simultaneous binomial interval for a fixed two-stratum partition."""
import numpy as np
from scipy.stats import beta
from functools import lru_cache

@lru_cache(maxsize=100000)
def cp(k,n,alpha):
    if n==0:
        return 0.,1.
    return (0. if k==0 else float(beta.ppf(alpha/2,k,n-k+1)),
            1. if k==n else float(beta.ppf(1-alpha/2,k+1,n-k)))

def stratified_interval(y,sl,su,alpha=.05):
    y=np.asarray(y); il=np.asarray(sl)>.5; iu=np.asarray(su)>.5
    if not np.all((y==0)|(y==1)):
        raise ValueError('Binary outcomes required')
    q0=cp(int(y[~il].sum()),int((~il).sum()),alpha/3)
    q1=cp(int(y[il].sum()),int(il.sum()),alpha/3)
    p=cp(int(il.sum()+iu.sum()),len(sl)+len(su),alpha/3)
    lo=min((1-t)*q0[0]+t*q1[0] for t in p)
    hi=max((1-t)*q0[1]+t*q1[1] for t in p)
    return float(lo),float(hi),float(hi-lo)
