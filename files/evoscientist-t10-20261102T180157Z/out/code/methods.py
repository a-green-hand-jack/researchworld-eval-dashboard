"""Mean intervals using only current labeled Y and frozen scores.
All learned calibrations are inference nuisances, never replacements for f.
"""
from __future__ import annotations
import numpy as np
from scipy.stats import beta, norm

ALPHA = 0.05
Z = norm.ppf(1-ALPHA/2)
METHODS = ['wald','ppi','ppipp','ppipp_pkg','cf_linear','cf_poly2','cf_rich',
           'insample_rich','cp','eb_labeled','eb_ppi','eb_select']

def features(s):
    s = np.asarray(s, dtype=float)
    t = 2*s-1
    return np.column_stack((s, t*t, t*t*t, (s>0.5).astype(float)))

def interval(center, radius):
    # Intersection with known parameter space; if disjoint, collapse to nearest
    # endpoint. This changes only failure events and never removes a covered mu.
    lo, hi = center-radius, center+radius
    return float(np.clip(lo,0,1)), float(np.clip(hi,0,1)), float(2*radius)

def wald(center, variance):
    return interval(center, Z*np.sqrt(max(variance,0)))

def eb_radius(var, size, delta, range_length):
    if range_length == 0:
        return 0.
    if size < 2:
        raise ValueError('At least two observations required')
    log = np.log(4/delta)
    return np.sqrt(2*max(float(var),0)*log/size) + 7*range_length*log/(3*(size-1))

def regression(x, y, gram=None, cross=None):
    """Intercept via centering; deterministic vanishing ridge, not tuning."""
    if gram is None:
        xc=x-x.mean(0)
        gram=xc.T@xc/len(y)
        cross=xc.T@(y-y.mean())/len(y)
    ridge=1e-4/len(y)
    return np.linalg.solve(gram+ridge*np.eye(gram.shape[0]), cross)

def crossfit(y, hl, hu_mean, hu_cov, p, n_u, folds=5):
    n=len(y); r=n/n_u
    # Row order is iid. Assign folds by index BEFORE looking at any values.
    ids=np.arange(n)%folds
    preds=np.empty(n); mean_delta=0.; bavg=np.zeros(p)
    for k in range(folds):
        test=ids==k; train=~test; w=test.mean()
        b=regression(hl[train,:p],y[train])/(1+r)
        preds[test]=hl[test,:p]@b
        mean_delta += w*((hu_mean[:p]-hl[test,:p].mean(0))@b)
        bavg+=w*b
    est=y.mean()+mean_delta
    var=np.var(y-preds,ddof=1)/n + (bavg@hu_cov[:p,:p]@bavg)/n_u
    return wald(est,var)

def all_intervals(y, sl, su, oracle_l=None, oracle_u=None):
    """No access to unobserved labels or data-generating truth."""
    y=np.asarray(y); sl=np.asarray(sl); su=np.asarray(su)
    n=len(y); N=len(su); r=n/N
    ym=y.mean(); vm=np.var(y,ddof=1)
    out={'wald':wald(ym,vm/n)}
    def scalar(lam, pooled=False):
        est=ym+lam*(su.mean()-sl.mean())
        vu=np.var(np.concatenate((sl,su)),ddof=1) if pooled else np.var(su,ddof=1)
        return wald(est,np.var(y-lam*sl,ddof=1)/n+lam*lam*vu/N)
    out['ppi']=scalar(1.)
    vs=np.var(np.concatenate((sl,su)),ddof=1)
    cov=np.cov(y,sl,ddof=1)[0,1]
    lam=cov/((1+r)*vs) if vs>1e-15 else 0.
    out['ppipp']=scalar(lam,True)
    # Exact ppi-python 0.2.3 default for binary means: covariance uses ddof0,
    # clips lambda to [0,1], variance uses ddof0 and unlabeled-only score var.
    pkg_lam=float(np.clip(lam*(n-1)/n,0,1))
    pkg_est=ym+pkg_lam*(su.mean()-sl.mean())
    pkg_var=np.var(y-pkg_lam*sl,ddof=0)/n+pkg_lam**2*np.var(su,ddof=0)/N
    out['ppipp_pkg']=wald(pkg_est,pkg_var)
    hl=features(sl); hu=features(su)
    um=hu.mean(0); uc=np.cov(hu,rowvar=False,ddof=1)
    for name,p in [('cf_linear',1),('cf_poly2',2),('cf_rich',4)]:
        out[name]=crossfit(y,hl,um,uc,p,N)
    b=regression(hl,y)/(1+r)
    est=ym+(um-hl.mean(0))@b
    out['insample_rich']=wald(est,np.var(y-hl@b,ddof=1)/n+(b@uc@b)/N)
    successes=int(np.sum(y))
    if not np.all((y==0)|(y==1)):
        raise ValueError('CP baseline requires binary outcomes')
    lo=0. if successes==0 else beta.ppf(ALPHA/2,successes,n-successes+1)
    hi=1. if successes==n else beta.ppf(1-ALPHA/2,successes+1,n-successes)
    out['cp']=(float(lo),float(hi),float(hi-lo))
    out['eb_labeled']=interval(ym,eb_radius(vm,n,ALPHA,1.))
    rl=y-sl
    rad=eb_radius(np.var(rl,ddof=1),n,ALPHA/2,2.)+eb_radius(np.var(su,ddof=1),N,ALPHA/2,1.)
    out['eb_ppi']=interval(ym+su.mean()-sl.mean(),rad)
    a=1/(1+r); K=5
    candidates=[interval(ym,eb_radius(vm,n,ALPHA/K,1.))]
    for gl,gu in [(a*sl,a*su),(a*(1-sl),a*(1-su)),
                  (a*(2*sl-1)**2,a*(2*su-1)**2),
                  (a*(sl>.5),a*(su>.5))]:
        res=y-gl
        rad=eb_radius(np.var(res,ddof=1),n,ALPHA/(2*K),1+a)+eb_radius(np.var(gu,ddof=1),N,ALPHA/(2*K),a)
        candidates.append(interval(res.mean()+gu.mean(),rad))
    # Actual reported (truncated) width, fixed tie break by order.
    idx=int(np.argmin([t[1]-t[0] for t in candidates]))
    out['eb_select']=candidates[idx]
    if oracle_l is not None:
        gl=oracle_l/(1+r); gu=oracle_u/(1+r)
        out['oracle']=wald(ym+gu.mean()-gl.mean(),np.var(y-gl,ddof=1)/n+np.var(gu,ddof=1)/N)
    return out, idx
