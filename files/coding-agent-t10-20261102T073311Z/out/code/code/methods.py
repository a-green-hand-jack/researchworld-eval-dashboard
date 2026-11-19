"""Mean intervals from immutable scalar scores. No access to unlabeled outcomes.
Wald procedures are asymptotic, EB procedures have finite-sample guarantees.
"""
import numpy as np
from scipy.stats import norm, beta
from numpy.polynomial.legendre import legvander

ALPHA = .05
Z = float(norm.ppf(1-ALPHA/2))

def phi(s, degree=3):
    return legvander(2*np.asarray(s)-1, degree)[:, 1:]

def moments(a):
    a = np.asarray(a)
    c = a-a.mean(axis=0)
    return c.T @ c/(len(a)-1)

def wald(y, sl, su, b=None, pl=None, pu=None):
    n,N=len(y),len(su)
    if b is None:
        b=np.empty(0);pl=np.empty((n,0));pu=np.empty((N,0))
    gl,gu=pl@b,pu@b
    point=float(np.mean(y-gl)+np.mean(gu))
    var=float(np.var(y-gl,ddof=1)/n+np.var(gu,ddof=1)/N)
    half=Z*np.sqrt(max(var,0))
    return point-half,point+half

def coefficient(y,pl,pu):
    n,N=len(y),len(pu)
    cov=(pl-pl.mean(0)).T@(y-y.mean())/(n-1)
    # PPI++ denominator uses pooled score covariance; no independent extra data.
    covp=moments(np.concatenate([pl,pu],axis=0))
    return (N/(N+n))*np.linalg.pinv(covp,rcond=1e-10,hermitian=True)@cov

def dictionary(y,sl,su,degree=3):
    pl,pu=phi(sl,degree),phi(su,degree)
    return wald(y,sl,su,coefficient(y,pl,pu),pl,pu)

def crossfit(y,sl,su,degree=3,folds=5):
    n,N=len(y),len(su);rho=N/(N+n)
    pl,pu=phi(sl,degree),phi(su,degree)
    bs=[];point=float(y.mean()); vl=0.; used=np.zeros(n,dtype=bool)
    for ix in np.array_split(np.arange(n),folds):
        tr=np.ones(n,dtype=bool);tr[ix]=False
        x=pl[tr];yc=y[tr]-y[tr].mean()
        c=(x-x.mean(0)).T@yc/(tr.sum()-1)
        b=rho*np.linalg.pinv(moments(x),rcond=1e-10,hermitian=True)@c
        wt=len(ix)/n;bs.append((wt,b))
        point+=wt*float((pu.mean(0)-pl[ix].mean(0))@b)
        vl+=len(ix)/n**2*np.var(y[ix]-pl[ix]@b,ddof=1)
        used[ix]=True
    assert used.all()
    bb=sum(w*b for w,b in bs)
    var=vl+np.var(pu@bb,ddof=1)/N
    h=Z*np.sqrt(max(var,0))
    return point-h,point+h

def eb_radius(values,delta,span):
    """Two-sided Maurer--Pontil (2009), Thm 4, union over both tails."""
    n=len(values)
    return np.sqrt(2*np.var(values,ddof=1)*np.log(4/delta)/n)+7*span*np.log(4/delta)/(3*(n-1))

def clip_ci(point,half):
    # Intersect with the known parameter space. If disjoint, return nearest point;
    # replacing an empty set by a point cannot lower coverage.
    return float(np.clip(point-half,0,1)),float(np.clip(point+half,0,1))

def eb_label(y,alpha=ALPHA):
    return clip_ci(np.mean(y),eb_radius(y,alpha,1))

def eb_helper(y,gl,gu,alpha=ALPHA):
    r=y-gl
    point=float(r.mean()+gu.mean())
    return clip_ci(point,eb_radius(r,alpha/2,2)+eb_radius(gu,alpha/2,1))

def menu_functions(s):
    s=np.asarray(s);t=2*s-1
    return [s,t*t,(s>.5).astype(float),(np.abs(t)>.5).astype(float)]

def eb_menu(y,sl,su,alpha=ALPHA):
    # Five candidates fixed before any labels are observed; selection is protected.
    candidates=[eb_label(y,alpha/5)]
    candidates += [eb_helper(y,gl,gu,alpha/5) for gl,gu in zip(menu_functions(sl),menu_functions(su))]
    j=min(range(5),key=lambda k:candidates[k][1]-candidates[k][0])
    return candidates[j]

def all_intervals(y,sl,su,binary=False):
    sl=np.asarray(sl);su=np.asarray(su);y=np.asarray(y)
    assert y.ndim==sl.ndim==su.ndim==1
    assert len(sl)==len(y)
    assert np.all((y>=0)&(y<=1)) and np.all((sl>=0)&(sl<=1)) and np.all((su>=0)&(su<=1))
    pl,pu=phi(sl,3),phi(su,3)
    b=coefficient(y,pl[:,:1],pu[:,:1])
    # phi_1=2S-1, so raw score lambda corresponds to b=lambda/2.
    clipped_b=np.clip(2*b,0,1)/2
    out={
      'Classical':wald(y,sl,su),
      'PPI':wald(y,sl,su,np.array([.5]),pl[:,:1],pu[:,:1]),
      'PPI++':wald(y,sl,su,b,pl[:,:1],pu[:,:1]),
      'PPI++clip':wald(y,sl,su,clipped_b,pl[:,:1],pu[:,:1]),
      'CV3':wald(y,sl,su,coefficient(y,pl,pu),pl,pu),
      'CF1':crossfit(y,sl,su,degree=1),
      'CF3':crossfit(y,sl,su),
      'Hoeffding':hoeffding(y),
      'EB-label':eb_label(y),
      'EB-raw':eb_helper(y,sl,su),
      'EB-split1':eb_split(y,sl,su,degree=1),
      'EB-split3':eb_split(y,sl,su,degree=3)}
    if binary:out['Exact-binomial']=exact_binomial(y)
    return out

def eb_split(y,sl,su,degree=3,alpha=ALPHA):
    """20% pilot fits a nuisance control on scores; f itself is never refit.
    Conditional on the pilot, inference observations and U remain iid, so the
    empirical-Bernstein guarantee holds at every n with n_eval>=2.
    """
    t=len(y)//5
    l=len(y)-t;N=len(su);rho=N/(N+l)
    train=np.column_stack([np.ones(t),phi(sl[:t],degree)])
    beta=np.linalg.lstsq(train,y[:t],rcond=1e-10)[0]
    def g(s):
        v=np.column_stack([np.ones(len(s)),phi(s,degree)])@beta
        return rho*np.clip(v,0,1)
    gl,gu=g(sl[t:]),g(su);res=y[t:]-gl
    h=eb_radius(res,alpha/2,1+rho)+eb_radius(gu,alpha/2,rho)
    return clip_ci(res.mean()+gu.mean(),h)


def hoeffding(y,alpha=ALPHA):
    return clip_ci(y.mean(),np.sqrt(np.log(2/alpha)/(2*len(y))))

def exact_binomial(y,alpha=ALPHA):
    assert np.all((y==0)|(y==1))
    k=int(y.sum());n=len(y)
    return (0. if k==0 else float(beta.ppf(alpha/2,k,n-k+1)),
            1. if k==n else float(beta.ppf(1-alpha/2,k+1,n-k)))
