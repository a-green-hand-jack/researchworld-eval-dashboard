"""Statistical primitives; iid and finite-pool targets kept separate."""
import functools
import numpy as np
from scipy.stats import beta, hypergeom, norm

def wilson(x,n,alpha=.05):
    x=np.asarray(x);z=norm.ppf(1-alpha/2);p=x/n;den=1+z*z/n
    c=(p+z*z/(2*n))/den;h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return np.stack([np.maximum(0,c-h),np.minimum(1,c+h)],axis=-1)

@functools.lru_cache(None)
def cp_table(n,alpha=.05):
    x=np.arange(n+1);lo=np.zeros(n+1);hi=np.ones(n+1)
    lo[1:]=beta.ppf(alpha/2,x[1:],n-x[1:]+1)
    hi[:-1]=beta.ppf(1-alpha/2,x[:-1]+1,n-x[:-1])
    return np.stack([lo,hi],axis=-1)

@functools.lru_cache(None)
def hg_table(M,m,alpha=.05):
    """Equal-tailed inversion over integer successes T in remaining M items.
    Accept T iff P_T(X>=x)>=alpha/2 and P_T(X<=x)>=alpha/2.
    """
    T=np.arange(M+1);out=[]
    for x in range(m+1):
        keep=(hypergeom.sf(x-1,M,T,m)>=alpha/2-1e-14)&(hypergeom.cdf(x,M,T,m)>=alpha/2-1e-14)
        good=T[keep];assert len(good)>0
        out.append([good[0]/M,good[-1]/M])
    return np.array(out)

def multiplier_radius(S,rng,B=999,N=None,independent=False):
    """Gaussian covariance simulation is distribution-identical to row multipliers.
    Uses eigendecomposition, preserving singular columns without variance floors.
    """
    R,n,K=S.shape;rad=np.empty(R);means=S.mean(1)
    for b in range(0,R,32):
        X=S[b:b+32]-means[b:b+32,None,:]
        cov=np.einsum('rni,rnj->rij',X,X)/(n*(n-1))
        if N is not None:cov*=1-n/N
        if independent:cov=cov*np.eye(K)[None,:,:]
        lam,V=np.linalg.eigh(cov);z=rng.normal(size=(len(X),B,K))*np.sqrt(np.maximum(lam,0))[:,None,:]
        draws=np.einsum('rbk,rjk->rbj',z,V)
        rad[b:b+len(X)]=np.quantile(np.max(np.abs(draws),axis=2),.95,axis=1)
    return rad

def evaluate(S,A,target,rng,N=None,total_success=None,B=999,independent=False):
    """S and A are paired 0/1 outcome tensors; A is untouched by selector.
    target: p vector (iid), mu vector (finite pool). Returns per-replay arrays.
    """
    S=np.asarray(S,dtype=float);A=np.asarray(A,dtype=float)
    R,n,K=S.shape;m=A.shape[1];idx=np.arange(R)
    means=S.mean(1);winner=np.argmax(means,axis=1);s=means[idx,winner];truth=np.asarray(target)[winner]
    sy=S[idx,:,winner];ay=A[idx,:,winner];a=ay.mean(1);hits=ay.sum(1).astype(int)
    h=np.sqrt(np.log(2*K/.05)/(2*n));rad=multiplier_radius(S,rng,B,N,independent)
    count=S.sum(1);guard=(n<64)|np.any((count<5)|(count>n-5),axis=1)
    def around(r):return np.stack([np.maximum(0,s-r),np.minimum(1,s+r)],-1)
    intervals={'Naive-Wilson':wilson(s*n,n),'Simult-Hoeffding':around(h),'Multiplier':around(rad),'Guarded-multiplier':around(np.where(guard,h,rad)),'Audit-Wilson':wilson(hits,m)}
    exact=(cp_table(m)[hits] if N is None else hg_table(N-n,m)[hits])
    intervals['Audit-exact']=exact.copy()
    remtruth=truth if N is None else (np.asarray(total_success)[winner]-sy.sum(1))/(N-n)
    raw_exact_coverage=(exact[:,0]<=remtruth+1e-12)&(exact[:,1]>=remtruth-1e-12)
    if N is not None:
        for name in ['Audit-Wilson','Audit-exact']:
            intervals[name]=n/N*s[:,None]+(N-n)/N*intervals[name]
    # Paired audit intervals from two exact discordance intervals and Bonferroni.
    plus=((ay==1)&(A[:,:,0]==0)).sum(1);minus=((ay==0)&(A[:,:,0]==1)).sum(1)
    pairtab=cp_table(m,.025) if N is None else hg_table(N-n,m,.025)
    pl=pairtab[plus];mi=pairtab[minus]
    dlo=pl[:,0]-mi[:,1];dhi=pl[:,1]-mi[:,0]
    ds=s-means[:,0];dtruth=truth-np.asarray(target)[0]
    if N is not None:
        dlo=n/N*ds+(N-n)/N*dlo;dhi=n/N*ds+(N-n)/N*dhi
    dlo[winner==0]=0;dhi[winner==0]=0
    dselect=sy-S[:,:,0];sd=dselect.std(1,ddof=1)/np.sqrt(n)
    naive_promote=ds-norm.ppf(.975)*sd>1e-12
    result={'winner':winner,'optimism':s-truth,'selected_score':s,'audit_score':a,'audit_bias':a-remtruth,'tie':(means==s[:,None]).sum(1)>1,'guard':guard,'zero_var':np.any((count==0)|(count==n),axis=1),'target':truth,'remainder_target':remtruth,'audit_gap':s-a,'remainder_optimism':s-remtruth,'pair_target':dtruth,'pair_cover':(dlo<=dtruth+1e-12)&(dhi>=dtruth-1e-12),'pair_width':dhi-dlo,'pair_promote':dlo>1e-12,'naive_promote':naive_promote,'nonpositive':dtruth<=1e-12,'audit_remainder_cover':raw_exact_coverage,'pair_lower':dlo,'pair_upper':dhi}
    for name,ci in intervals.items():
        result[name+'__cover']=(ci[:,0]<=truth+1e-12)&(ci[:,1]>=truth-1e-12)
        result[name+'__width']=ci[:,1]-ci[:,0]
    return result,intervals
