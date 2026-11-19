"""Meaningful numerical checks, independent analytic expectations where possible."""
import numpy as np
from benchmark import quantile,clr,fit_thresholds,membership,METHODS,run_rep,weighted_quantile,score
import json
rng=np.random.default_rng(622)
# Finite rank result: continuous iid scores, n=99, alpha=.1 => E coverage=.9.
a=rng.uniform(size=(20000,100)); q=np.sort(a[:,:99],axis=1)[:,89]
cov=np.mean(a[:,99]<=q)
assert abs(cov-.9)<.01,cov
assert np.isinf(quantile(np.array([1.,2.]),.1))
# Aitchison distance is invariant to coordinate permutation and perturbation.
y=rng.dirichlet(np.ones(4),30); p=rng.dirichlet(np.ones(4),30); perturb=np.array([1.,2.,3.,4.])
y2=y*perturb; y2/=y2.sum(axis=1,keepdims=True)
p2=p*perturb; p2/=p2.sum(axis=1,keepdims=True)
assert np.allclose(np.linalg.norm(clr(y)-clr(p),axis=1),np.linalg.norm(clr(y2)-clr(p2),axis=1))
# Coordinate controls are nested, Bonferroni always weakly larger than naive.
s=np.ones(30); g=np.tile([0,1],15); qs=fit_thresholds(y,p,s,g,.1)
assert np.all(qs['coord_bonferroni']>=qs['coord_naive'])
for m in METHODS:
    hit=membership(y,p,s,g,m,qs[m]); assert hit.shape==(30,)
# For an equilateral 3-simplex the total Euclidean area is sqrt(3)/2;
# inscribed raw L2 ball with r=.1 has fraction 2*pi*r^2/sqrt(3).
y=rng.dirichlet(np.ones(3),200000); center=np.full((1,3),1/3); r=.1
observed=np.mean(np.linalg.norm(y-center,axis=1)<=r)
expected=2*np.pi*r*r/np.sqrt(3)
assert abs(observed-expected)<.0015,(observed,expected)
print({'rank_coverage':cov,'volume_observed':observed,'volume_analytic':expected,'checks':'passed'})

# Exercise the real record/serialization path with calibration groups too small
# to support finite thresholds, not just a standalone infinity value.
rows,_=run_rep(771,3,2,'homogeneous',ntest=100,nvolume=128,nanchors=2)
assert any(r['infinite_threshold'] for r in rows)
assert all(r['mean_radius'] is None for r in rows if r['radius_status']=='infinite')
for row in rows: json.dumps(row,allow_nan=False)
assert all(r['coverage']==1 for r in rows if r['method']=='clr_mondrian')
print({'tiny_calibration_serialization':'passed','infinite_records':sum(r['infinite_threshold'] for r in rows)})

# Independent summarizer fixture: include both finite and whole-simplex runs.
from summarize import summarize
from tempfile import TemporaryDirectory
from pathlib import Path
import pandas as pd
with TemporaryDirectory() as tmp:
    tmp=Path(tmp); fixture=[]
    for seed in (1,2):
        for method in METHODS:
            fixture.append(dict(k=3,ncal=2,scenario='fixture',shift=False,epsilon=1e-6,alpha=.1,method=method,seed=seed,coverage=.9 if seed==1 else 1.,coverage_g0=.9 if seed==1 else 1.,coverage_g1=.9 if seed==1 else 1.,volume_fraction=.1 if seed==1 else 1.,mean_radius=.2 if seed==1 else None,radius_infinite_fraction=0. if seed==1 else 1.,infinite_threshold=seed==2))
    source=tmp/'input.jsonl'; source.write_text(''.join(json.dumps(r)+'\n' for r in fixture))
    summarize([source],tmp/'summary')
    output=pd.read_csv(tmp/'summary/summary.csv')
    radius=output[output.metric=='mean_radius']
    assert radius['mean'].isna().all() and (radius.n_rep_total==2).all() and (radius.n_rep==1).all()
    volume=output[output.metric=='volume_fraction']
    assert np.allclose(volume['mean'],.55) and (volume.n_rep==2).all()
    diagnostic=pd.read_csv(tmp/'summary/diagnostics.csv')
    assert (diagnostic.infinite_threshold_replications==1).all()
print({'mixed_finite_infinite_summary':'passed'})

# A unit weight at infinity yields the exact ordinary split quantile.
for n in (2,9,19,99):
    scores=np.arange(n,dtype=float)
    for alpha in (.1,.05,.2):
        assert weighted_quantile(scores,np.ones(n),1.,alpha)==quantile(scores,alpha)
assert np.isinf(weighted_quantile(np.array([.1,.2]),np.ones(2),100.,.1))
assert weighted_quantile(np.array([.1,.2]),np.array([9.,1.]),.01,.1)==.2
print({'weighted_test_atom_checks':'passed'})

# Orthonormal ilr basis spans clr subspace; distances must coincide.
k=5; projection=np.eye(k)-np.ones((k,k))/k
basis=np.linalg.qr(projection[:,:-1])[0]
y=rng.dirichlet(np.ones(k),50); p=rng.dirichlet(np.ones(k),50)
delta=clr(y)-clr(p)
assert np.allclose(np.linalg.norm(delta,axis=1),np.linalg.norm(delta@basis,axis=1))
# Empty group must still receive a valid (infinite) conformal threshold.
q=fit_thresholds(y,p,np.ones(len(y)),np.zeros(len(y)),.1)
assert np.isinf(q['clr_mondrian'][1])
assert membership(y,p,np.ones(len(y)),np.ones(len(y)),'clr_mondrian',q['clr_mondrian']).all()
# Conservative ties: all identical calibration/test scores are always covered.
assert quantile(np.ones(19),.1)==1.
print({'ilr_empty_group_tie_checks':'passed'})

# Source-driven TV and forward-KL controls: geometry, boundary and asymmetry.
y=rng.dirichlet(np.ones(3),100);p=rng.dirichlet(np.ones(3),100)
assert np.allclose(.5*np.sum(abs(y-p),axis=1),np.max(abs(y-p),axis=1),atol=1e-14)
assert np.array_equal(score(y,p,None,'tv'),score(y,p,None,'raw_linf'))
y10=rng.dirichlet(np.ones(10),100);p10=rng.dirichlet(np.ones(10),100)
assert np.allclose(score(y10,p10,None,'tv'),.5*np.sum(abs(y10-p10),axis=1))
assert not np.allclose(score(y10,p10,None,'tv'),score(y10,p10,None,'raw_linf'))
assert np.all(score(y10,p10,None,'kl_forward')>=0)
assert np.all(score(p10,p10,None,'kl_forward')==0)
assert np.isclose(score(np.array([[0.,1.]]),np.array([[.5,.5]]),None,'kl_forward')[0],np.log(2.))
a=np.array([[.8,.2]]);b=np.array([[.5,.5]])
assert not np.isclose(score(a,b,None,'kl_forward')[0],score(b,a,None,'kl_forward')[0])
print({'tv_kl_geometry_numerics':'passed'})
