#!/usr/bin/env python3
"""Exact finite-endpoint support optimization; numerical MILP for larger Borda.
Cardinal equality tolerance is 1e-12 on aggregate mean or median scores.
Borda uses exact float ordering and integer doubled midrank points.
"""
import itertools
import numpy as np
from scipy.stats import rankdata
from scipy.optimize import milp, Bounds, LinearConstraint
TOL=1e-12

def scores(a,rule):
    if rule=='mean':return a.mean(axis=1)
    if rule=='median':return np.median(a,axis=1)
    if rule=='lower_median':return np.sort(a,axis=1)[:,(a.shape[1]-1)//2]
    if rule=='upper_median':return np.sort(a,axis=1)[:,a.shape[1]//2]
    if rule=='borda':return np.sum(2*rankdata(a,axis=0,method='average')-2,axis=1).astype(int)
    raise ValueError(rule)

def subsets(n):
    return np.array(list(itertools.product([0,1],repeat=n)),dtype=int)

def wins(value,threshold,strict=False):
    return value>threshold+TOL if strict else value>=threshold-TOL

def borda_problem(a,i,rho,base=None):
    """Return rival indices, integer margin gains G, required margin rhs."""
    m,n=a.shape;x=a[i];c=x+rho*(1-x);base=scores(a,'borda') if base is None else base
    rivals=np.arange(m)!=i
    other=a[rivals]
    old=2*(other<x)+(other==x)
    new=2*(other<c)+(other==c)
    gain=np.sum(new-old,axis=0).astype(int)
    # Rival's pairwise points against the target decrease by the same amount.
    loss=(new-old).astype(int)
    indices=np.where(rivals)[0]
    # Each rival can lose at most 2*n points. Nobody below max-2*n can bind.
    keep=base[indices]>=base[indices].max()-2*n
    ids=indices[keep]
    G=gain[None,:]+loss[keep]
    rhs=base[ids]-base[i]
    return ids,G.astype(float),rhs.astype(float),gain

def check_borda_witness(a,i,rho,z,base,strict):
    x=a[i];c=x+rho*(1-x);y=np.where(z,c,x)
    rivals=np.arange(len(a))!=i;other=a[rivals]
    diff=(2*(other<y)+(other==y))-(2*(other<x)+(other==x))
    own=base[i]+diff.sum();others=base[rivals]-diff.sum(axis=1)
    return bool(np.all(own-others >= int(strict)))

def solve(a,i,rho,rule,strict=False,base=None,allsets=None):
    m,n=a.shape;x=a[i];d=rho*(1-x);base=scores(a,rule) if base is None else base
    threshold=np.max(np.delete(base,i));zero=np.zeros(n,dtype=int)
    out={'K':None,'mask':zero,'status':'infeasible','gap':None,'dual':None,'L1_min':None,'L1_attained':None}
    if rule=='borda':
        ids,G,rhs,_=borda_problem(a,i,rho,base);rhs=rhs+int(strict)
        if np.all(rhs<=0):out.update(K=0,status='optimal',L1_min=0.,L1_attained=True);return out
        if np.any(G.sum(axis=1)<rhs):return out
        if n<=10:
            allsets=subsets(n) if allsets is None else allsets
            ok=np.all(G@allsets.T>=rhs[:,None],axis=0)
            choices=np.flatnonzero(ok);ks=allsets[choices].sum(axis=1);k=ks.min()
            choices=choices[ks==k];j=choices[np.argmin(allsets[choices]@d)];z=allsets[j]
            out.update(K=int(k),mask=z,status='optimal',gap=0.,dual=float(k))
        else:
            result=milp(np.ones(n),integrality=np.ones(n),bounds=Bounds(np.zeros(n),np.ones(n)),constraints=LinearConstraint(G,rhs,np.inf),options={'time_limit':20.,'mip_rel_gap':0.})
            if result.x is None:
                out['status']='unresolved';out['dual']=getattr(result,'mip_dual_bound',None);return out
            z=np.rint(result.x).astype(int)
            assert np.all(G@z>=rhs), (i,rho,rule)
            out.update(K=int(z.sum()),mask=z,status='optimal' if result.status==0 else 'bounded',gap=float(result.mip_gap),dual=float(result.mip_dual_bound))
        assert check_borda_witness(a,i,rho,out['mask'],base,strict)
        return out
    if wins(base[i],threshold,strict):out.update(K=0,status='optimal',L1_min=0.,L1_attained=True);return out
    if n<=10:
        allsets=subsets(n) if allsets is None else allsets
        vals=scores(x[None,:]+allsets*d,rule)
        ok=vals>threshold+TOL if strict else vals>=threshold-TOL
        choices=np.flatnonzero(ok)
        if not len(choices):return out
        ks=allsets[choices].sum(axis=1);k=ks.min();choices=choices[ks==k]
        j=choices[np.argmin(allsets[choices]@d)];z=allsets[j]
        out.update(K=int(k),mask=z,status='optimal',gap=0.,dual=float(k))
    elif rule=='mean':
        order=np.argsort(-d,kind='stable');vals=(x.sum()+np.cumsum(d[order]))/n
        good=np.flatnonzero(vals>threshold+TOL if strict else vals>=threshold-TOL)
        if not len(good):return out
        k=int(good[0]+1);z=zero.copy();z[order[:k]]=1
        out.update(K=k,mask=z,status='optimal',gap=0.,dual=float(k))
    elif rule=='median' and n%2:
        above=x>threshold+TOL if strict else x>=threshold-TOL
        reachable=x+d>threshold+TOL if strict else x+d>=threshold-TOL
        need=(n+1)//2-int(above.sum());candidates=np.flatnonzero(reachable&~above)
        if len(candidates)<need:return out
        order=candidates[np.argsort(d[candidates],kind='stable')];z=zero.copy();z[order[:need]]=1
        out.update(K=int(need),mask=z,status='optimal',gap=0.,dual=float(need))
        # Magnitude optimum (infimum for strict first): cheapest threshold crossings.
        costs=np.maximum(threshold-x[candidates],0);out['L1_min']=float(np.sort(costs)[:need].sum()/n);out['L1_attained']=not strict
    else:raise NotImplementedError((rule,n))
    if rule=='mean':
        out['L1_min']=float(max(0.,threshold-x.mean()));out['L1_attained']=not strict
    assert wins(scores((x+out['mask']*d)[None,:],rule)[0],threshold,strict)
    return out

def heuristic(G,rhs,order):
    if np.all(rhs<=0):return 0
    margin=np.zeros(len(rhs))
    for k,j in enumerate(order,1):
        margin+=G[:,j]
        if np.all(margin>=rhs):return k
    return None
