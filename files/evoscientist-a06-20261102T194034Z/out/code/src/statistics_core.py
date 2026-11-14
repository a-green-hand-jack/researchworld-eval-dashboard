"""Frozen statistical estimators; iid rows and a fixed finite candidate family."""
import functools
import numpy as np
from scipy.stats import beta, norm
ALPHA=.05

@functools.lru_cache(None)
def cp_table(n, k=1, alpha=ALPHA):
    """Coordinate CP confidence level 1-alpha/k; union bound yields family band."""
    counts=np.arange(n+1)
    lo=np.zeros(n+1); hi=np.ones(n+1)
    lo[1:]=beta.ppf(alpha/(2*k),counts[1:],n-counts[1:]+1)
    hi[:-1]=beta.ppf(1-alpha/(2*k),counts[:-1]+1,n-counts[:-1])
    return lo,hi

def cp(count,n,k=1):
    lo,hi=cp_table(n,k); return float(lo[int(count)]),float(hi[int(count)])

def gaussian_radii(x,rng,b=499,alpha=ALPHA):
    """Conditional Gaussian-multiplier max, using exact covariance factorization.
    Each row gets one common multiplier across candidates. Generating from the
    estimated covariance is distributionally identical, not a different bootstrap.
    Includes one-sided improvement decision only via conservative two-sided bands.
    """
    x=np.asarray(x,dtype=float); n,k=x.shape; xc=x-x.mean(axis=0)
    cov=xc.T@xc/n
    ev,vec=np.linalg.eigh(cov); ev=np.maximum(ev,0)
    z=rng.standard_normal((b,k))
    g=z@(vec*np.sqrt(ev)).T
    q=np.quantile(np.max(np.abs(g),axis=1),1-alpha,method='higher')/np.sqrt(n)
    gi=z*np.sqrt(np.maximum(np.diag(cov),0))
    qi=np.quantile(np.max(np.abs(gi),axis=1),1-alpha,method='higher')/np.sqrt(n)
    return float(q),float(qi)

def choose(x,rule='exhaustive'):
    if rule=='exhaustive': return int(np.argmax(x.mean(axis=0)))
    if rule!='halving': raise ValueError(rule)
    # Predeclared adaptive allocation/reveal within the frozen family.
    n,k=x.shape; active=np.arange(k); used=max(2,n//8)
    while len(active)>1:
        means=x[:min(used,n),active].mean(axis=0)
        active=active[np.argsort(-means,kind='stable')[:(len(active)+1)//2]]
        used=min(2*used,n)
    return int(active[0])

def intervals(x,rng,b=499,rule='exhaustive'):
    x=np.asarray(x,dtype=float); n,k=x.shape
    means=x.mean(axis=0); j=choose(x,rule); m=means[j]; c=int(x[:,j].sum())
    r,ri=gaussian_radii(x,rng,b)
    z=norm.ppf(.975); se=np.sqrt(m*(1-m)/n)
    h=np.sqrt(np.log(2*k/ALPHA)/(2*n))
    out={'naive_CP':(*cp(c,n),j),'bonferroni_CP':(*cp(c,n,k),j),
         'hoeffding':(max(0,m-h),min(1,m+h),j),
         'paired_multiplier':(max(0,m-r),min(1,m+r),j),
         'independent_multiplier':(max(0,m-ri),min(1,m+ri),j),
         'naive_Wald':(max(0,m-z*se),min(1,m+z*se),j)}
    n1=n//2; js=choose(x[:n1],rule); xs=x[n1:,js]; a,b1=cp(int(xs.sum()),len(xs))
    out['split_CP']=(a,b1,js)
    return out,j

def paired_decision(x,rng,b=499):
    """Compare the accuracy-selected winner with predeclared candidate 0."""
    n,k=x.shape; j=choose(x); d=x-x[:,[0]]; delta=d.mean(axis=0)
    se=d.std(axis=0,ddof=1)/np.sqrt(n)
    r,ri=gaussian_radii(d,rng,b)
    # range=2 for paired differences in [-1,1]
    h=np.sqrt(2*np.log(2*k/ALPHA)/n)
    return j,{'naive_paired':float(delta[j]-norm.ppf(.975)*se[j]),
              'paired_multiplier':float(delta[j]-r),
              'independent_multiplier':float(delta[j]-ri),
              'hoeffding':float(delta[j]-h)}
