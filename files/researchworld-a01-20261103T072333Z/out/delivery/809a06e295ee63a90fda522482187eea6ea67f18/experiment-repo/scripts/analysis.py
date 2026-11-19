"""Exact task-count counterfactuals. All intervention scores, not training effects."""
import argparse,itertools,json,time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.stats import rankdata
ROOT=Path(__file__).resolve().parents[1]
TOL=1e-10
RULES=['mean','median','geometric','minimum','borda']

def aggregate(x,rule):
    if rule=='mean':return np.mean(x,axis=-1)
    if rule=='median':return np.median(x,axis=-1)
    if rule=='minimum':return np.min(x,axis=-1)
    if rule=='geometric':return np.prod(x,axis=-1)**(1/x.shape[-1])
    raise ValueError(rule)

def point(x,y):return (x>y).astype(float)+.5*(x==y)

def patterns(n):
    p=np.array(list(itertools.product([0.,1.],repeat=n)))
    return p[np.argsort(p.sum(axis=1),kind='stable')]

def context(X,rule):
    if rule=='borda':return (rankdata(X,axis=0,method='average')-1).sum(axis=1)
    return aggregate(X,rule)

def winning_patterns(X,t,u,rule,base,P,strict=False):
    """Evaluate subsets; recompute opponents' Borda changes exactly."""
    x=X[t]; Y=x+P*(u-x)
    others=np.arange(len(X))!=t
    eps=TOL if strict else -TOL
    if rule!='borda':return aggregate(Y,rule)>=np.max(base[others])+eps
    d=point(u[None,:],X)-point(x[None,:],X);d[t]=0
    g=d.sum(axis=0)
    # An opponent loses at most n points. Others cannot become strongest after intervention.
    contenders=others & (base>=np.max(base[others])-X.shape[1]-TOL)
    target=base[t]+P@g
    rivals=base[contenders,None]-d[contenders]@P.T
    return target>=rivals.max(axis=0)+eps

def solve(X,t,u,rule,base,strict=False):
    n=X.shape[1];x=X[t];others=np.arange(len(X))!=t
    eps=TOL if strict else -TOL
    threshold=np.max(base[others])+eps
    if n<=10:
        P=patterns(n);success=winning_patterns(X,t,u,rule,base,P,strict)
        if not success.any():return None,'infeasible',None
        z=P[np.flatnonzero(success)[0]]
        return z,'enumerated',None
    if base[t]>=threshold:return np.zeros(n),'exact',None
    if rule in ('mean','geometric'):
        forced=np.zeros(n,dtype=bool)
        if rule=='mean':
            gain=u-x;needed=n*threshold-x.sum()
        else:
            # A positive geometric threshold forces every original zero to be upgraded.
            if threshold<=0:return np.zeros(n),'exact',None
            forced=x==0
            if np.any(u[forced]<=0):return None,'infeasible',None
            start=x.copy();start[forced]=u[forced]
            gain=np.log(u)-np.log(start);needed=n*np.log(threshold)-np.log(start).sum()
        gain[forced]=0
        order=np.argsort(-gain,kind='stable');z=forced.astype(float)
        if needed<=TOL:return z,'exact',None
        for j in order:
            if gain[j]<=0:continue
            z[j]=1;needed-=gain[j]
            if needed<=TOL:return z,'exact',None
        return None,'infeasible',None
    if rule=='minimum':
        z=(x<threshold).astype(float)
        return (z,'exact',None) if np.all(np.where(z,u,x)>=threshold) else (None,'infeasible',None)
    if rule=='median':
        assert n%2==1
        q=int((x>=threshold).sum());need=(n+1)//2-q
        candidates=np.flatnonzero((x<threshold)&(u>=threshold))
        if len(candidates)<need:return None,'infeasible',None
        z=np.zeros(n);z[candidates[:need]]=1
        return z,'exact',None
    d=point(u[None,:],X)-point(x[None,:],X);d[t]=0;g=d.sum(axis=0)
    contenders=others & (base>=np.max(base[others])-n-TOL)
    A=g[None,:]+d[contenders]
    b=base[contenders]-base[t]+(.5 if strict else -TOL)
    result=milp(np.ones(n),integrality=np.ones(n),bounds=Bounds(0,1),constraints=LinearConstraint(A,b,np.inf),options={'time_limit':30,'mip_rel_gap':0})
    if result.status==2:return None,'infeasible',None
    if result.x is None:return None,'solver_failure',dict(status=int(result.status),message=result.message)
    z=np.rint(result.x)
    if result.status!=0:return z,'bounded',dict(lower_bound=float(result.mip_dual_bound),gap=float(result.mip_gap))
    return z,'optimal',dict(lower_bound=float(result.mip_dual_bound),gap=float(result.mip_gap))

def random_baseline(X,t,u,rule,base,k,rng,reps):
    n=X.shape[1]
    if n<=10:
        P=patterns(n);success=winning_patterns(X,t,u,rule,base,P)
        counts=P.sum(axis=1).astype(int)
        probs=np.array([success[counts==j].mean() for j in range(n+1)])
        return float(probs[k]),float(np.sum(1-probs)),0
    P=np.zeros((reps*(n+1),n))
    for r in range(reps):
        order=rng.permutation(n)
        P[r*(n+1)+np.arange(1,n+1)[:,None],order[None,:]]=np.tri(n)
    success=winning_patterns(X,t,u,rule,base,P).reshape(reps,n+1)
    # n+1 if never successful: explicitly censored, not an actual cost.
    first=np.where(success.any(axis=1),success.argmax(axis=1),n+1)
    return float(success[:,k].mean()),float(first.mean()),reps

def run(dataset,settings,strict=False,limit=None,random_reps=0):
    df=pd.read_csv(ROOT/f'data/processed/{dataset}.csv',index_col=0)
    X=df.to_numpy();m,n=X.shape;rows=[];rng=np.random.default_rng(20261103)
    for ceiling,alpha in settings:
        U=np.ones(n) if ceiling=='unit' else X.max(axis=0)
        for rule in RULES:
            base=context(X,rule);ranks=rankdata(-base,method='min')
            for t in range(m if limit is None else min(limit,m)):
                u=X[t]+alpha*(U-X[t]);start=time.perf_counter()
                z,status,detail=solve(X,t,u,rule,base,strict)
                k=None if z is None else int(z.sum())
                if z is not None:
                    assert winning_patterns(X,t,u,rule,base,z[None,:],strict)[0],(dataset,t,rule,status)
                p=er=None;reps=0
                random_requested=bool(random_reps and not strict)
                random_method='not_requested'
                if random_requested and z is not None:
                    p,er,reps=random_baseline(X,t,u,rule,base,k,rng,random_reps)
                    random_method='mc_permutations' if reps else 'exact_subsets'
                elif random_requested and status=='infeasible':
                    er=float(n+1)
                    random_method='exact_infeasible' 
                rows.append(dict(dataset=dataset,model=df.index[t],n_models=m,n_tasks=n,rule=rule,ceiling=ceiling,alpha=alpha,strict=strict,baseline_rank=int(ranks[t]),baseline_score=float(base[t]),k=k,k_fraction=None if k is None else k/n,status=status,selected_tasks=None if z is None else json.dumps(df.columns[z.astype(bool)].tolist()),solver_detail=json.dumps(detail),random_success_at_k=p,random_expected_censored_k=er,random_reps=reps,random_requested=random_requested,random_baseline_method=random_method,seconds=time.perf_counter()-start))
            print(f'{dataset} {ceiling} {alpha} {rule}: {len(rows)} rows',flush=True)
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',required=True);ap.add_argument('--output',required=True);ap.add_argument('--pilot',type=int);ap.add_argument('--strict',action='store_true');ap.add_argument('--random-reps',type=int,default=0);ap.add_argument('--primary-only',action='store_true');a=ap.parse_args()
    settings=[('unit',1.)] if a.primary_only else [('unit',v) for v in [1.,.5,.25,.1]]+[('observed',1.)]
    start=time.perf_counter();df=run(a.dataset,settings,a.strict,a.pilot,a.random_reps)
    df.to_csv(ROOT/a.output,index=False,float_format='%.12g');print(f'HUTIAN_WAKE: completed {a.output} {len(df)} rows in {time.perf_counter()-start:.2f}s',flush=True)
if __name__=='__main__':main()
