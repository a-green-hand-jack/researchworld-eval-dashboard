"""Exact binary signed-component intervals; ordinary PPI composition.
Conditional on the same-budget pilot the binary inference map is fixed.
This does not alter or retrain the supplied base predictor.
"""
import numpy as np
from inference import clopper_pearson,fit_hist,bins,ALPHA


def signed_binomial(y, b, bu, alpha=ALPHA):
    y,b,bu=np.asarray(y),np.asarray(b),np.asarray(bu)
    if any(x.ndim!=1 for x in (y,b,bu)) or not 0<alpha<1:
        raise ValueError('vector inputs and 0<alpha<1 required')
    if len(y)!=len(b) or min(len(y),len(bu))<1:
        raise ValueError('nonempty aligned samples required')
    if not all(np.all((x==0)|(x==1)) for x in [y,b,bu]):
        raise ValueError('binary label and maps required')
    n,N=len(y),len(bu)
    q=int(bu.sum())
    plus=int(np.sum((y==1)&(b==0)))
    minus=int(np.sum((y==0)&(b==1)))
    lq,uq,_=clopper_pearson(q,N,alpha/3)
    lp,up,_=clopper_pearson(plus,n,alpha/3)
    lm,um,_=clopper_pearson(minus,n,alpha/3)
    return max(0.,lq+lp-um),min(1.,uq+up-lm),q/N+(plus-minus)/n


def exact_methods(y,z,u):
    y,z,u=np.asarray(y),np.asarray(z),np.asarray(u)
    if any(x.ndim!=1 for x in (y,z,u)) or len(y)!=len(z) or len(u)<1:
        raise ValueError('aligned vector labels/scores and nonempty unlabeled sample required')
    if not np.all((y==0)|(y==1)):
        raise ValueError('binary labels required')
    if any(not np.all(np.isfinite(x)) or np.any((x<0)|(x>1)) for x in (z,u)):
        raise ValueError('finite scores in [0,1] required')
    n=len(y);p=n//5
    if p<1 or n-p<1:
        raise ValueError('nonempty pilot and evaluation split required')
    yr,zr=y[p:],z[p:]
    learned=fit_hist(y[:p],z[:p],4)>=.5
    result={
        'CPRectRawFull':signed_binomial(y,z>=.5,u>=.5),
        'CPRectRawSplit':signed_binomial(yr,zr>=.5,u>=.5),
        'CPRectHist':signed_binomial(yr,learned[bins(zr,4)],learned[bins(u,4)]),
        'LabelCP':clopper_pearson(int(np.sum(y)),n),
        'LabelCPSplit':clopper_pearson(int(np.sum(yr)),len(yr))
    }
    return result
