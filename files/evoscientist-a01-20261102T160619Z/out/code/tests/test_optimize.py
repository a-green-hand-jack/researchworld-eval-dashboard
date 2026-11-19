import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import numpy as np
from optimize import solve,scores,subsets,check_borda_witness

def oracle(a,i,rho,rule,strict=False):
    masks=subsets(a.shape[1]);base=scores(a,rule);out=[]
    for z in masks:
        edited=a.copy();edited[i]+=z*rho*(1-a[i]);s=scores(edited,rule);r=np.delete(s,i)
        ok=np.all(s[i]>r+1e-12) if strict and rule!='borda' else np.all(s[i]>=r+(1 if strict else 0)) if rule=='borda' else np.all(s[i]>=r-1e-12)
        if ok:out.append(int(z.sum()))
    return min(out) if out else None

def test_random_oracle():
    rng=np.random.default_rng(101)
    for n in [3,4,5,6]:
      for rep in range(12):
        a=rng.integers(0,9,size=(5,n))/8
        for rule in ['mean','median','borda']:
         for strict in [False,True]:
          for rho in [.25,.5,1.]:
            for i in [0,3]:
              assert solve(a,i,rho,rule,strict)['K']==oracle(a,i,rho,rule,strict)

def test_large_odd_median_and_mean():
    rng=np.random.default_rng(123)
    # The analytic n>10 routes agree with independent subset enumeration.
    for rep in range(8):
      a=rng.integers(0,9,size=(4,11))/8
      for rule in ['mean','median','borda']:
       for strict in [False,True]:
        for rho in [.5,1.]:
          assert solve(a,0,rho,rule,strict)['K']==oracle(a,0,rho,rule,strict)

def test_midrank_and_rival_updates():
    a=np.array([[0.,.5],[.5,.5],[1.,0.]])
    b=scores(a,'borda');assert np.array_equal(b,np.array([3,5,4]))
    z=np.ones(2,dtype=int);assert check_borda_witness(a,0,1.,z,b,False)

def test_saturation_impossibility_and_even_median():
    a=np.array([[0.,0.,0.,0.],[1.,1.,1.,1.]])
    assert solve(a,0,.5,'mean')['K'] is None
    assert solve(a,0,1.,'mean')['K']==4
    assert solve(a,0,1.,'mean',True)['K'] is None
    assert solve(a,0,1.,'median')['K']==3
    assert solve(a,0,1.,'lower_median')['K']==3
    assert solve(a,0,1.,'upper_median')['K']==2

def test_more_headroom_cannot_hurt():
    rng=np.random.default_rng(777)
    for rep in range(20):
      a=rng.random((7,5))
      for rule in ['mean','median','borda']:
        ks=[solve(a,0,r,rule)['K'] for r in [.25,.5,1.]]
        ks=[100 if k is None else k for k in ks];assert ks[0]>=ks[1]>=ks[2]

def test_magnitude_and_attainment_boundaries():
    n=11
    for rule in ['mean','median']:
        a=np.array([[1.]*n,[0.]*n])
        for strict in [False,True]:
            v=solve(a,0,.5,rule,strict);assert v['L1_min']==0 and v['L1_attained'] is True
        a=np.full((2,n),.5)
        v=solve(a,0,.5,rule,False);assert v['K']==0 and v['L1_min']==0 and v['L1_attained'] is True
        v=solve(a,0,.5,rule,True);assert v['K']>0 and v['L1_min']==0 and v['L1_attained'] is False
        a=np.array([[0.]*n,[1.]*n])
        assert solve(a,0,1.,rule,False)['L1_attained'] is True
        for rho in [.5,1.]:
            v=solve(a,0,rho,rule,True);assert v['K'] is None and v['L1_min'] is None and v['L1_attained'] is None
    a=np.array([[0.]*n,[.5]*n])
    v=solve(a,0,.5,'median',False);assert v['K']==6 and abs(v['L1_min']-3/11)<1e-15 and v['L1_attained'] is True
    assert solve(a,0,.5,'median',True)['K'] is None

def test_saved_cardinal_magnitudes_and_headline():
    import pandas as pd
    root=Path(__file__).resolve().parents[1]
    a=pd.read_csv(root/'data/processed/helm.csv',index_col=0).to_numpy()
    d=pd.read_csv(root/'artifacts/results_helm.csv');n=a.shape[1];checked=0
    for row in d[d.rule.isin(['mean','median'])].itertuples():
        if pd.isna(row.K):assert pd.isna(row.L1_min) and pd.isna(row.L1_attained);continue
        x=a[row.i];others=np.delete(a,row.i,axis=0)
        if row.rule=='mean':
            t=others.mean(axis=1).max();expected=max(0.,t-x.mean())
        else:
            t=np.median(others,axis=1).max();c=x+row.rho*(1-x)
            q=np.count_nonzero(x>t) if row.strict else np.count_nonzero(x>=t);need=max(0,(n+1)//2-q)
            eligible=(x<=t)&(c>t) if row.strict else (x<t)&(c>=t)
            expected=sum(sorted((t-x[eligible]).tolist())[:need])/n
        assert abs(row.L1_min-expected)<1e-14
        assert bool(row.L1_attained)==(not row.strict or row.K==0);checked+=1
    assert checked>0
    r=d[(~d.strict)&(d.rho==1)]
    k=r.pivot(index='i',columns='rule',values='K');l=r.pivot(index='i',columns='rule',values='L1_min');rank=r.pivot(index='i',columns='rule',values='rank');ids=rank[(rank[['mean','median']]>1).all(axis=1)].index
    assert len(ids)==77
    assert ((k.loc[ids,'median']>k.loc[ids,'mean'])&(l.loc[ids,'median']<l.loc[ids,'mean'])).sum()==64
    assert (l.loc[ids,'median']<l.loc[ids,'mean']).all()

