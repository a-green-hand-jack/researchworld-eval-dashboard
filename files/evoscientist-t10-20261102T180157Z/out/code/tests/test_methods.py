from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from scipy.stats import norm
from methods import all_intervals, eb_radius, regression, features


def test_reference_package():
    from ppi_py import ppi_mean_ci
    rng=np.random.default_rng(17)
    s=rng.uniform(size=100); u=rng.uniform(size=1000)
    for mean in [s,1-s,.1+.8*s]:
        y=rng.binomial(1,mean)
        out,_=all_intervals(y,s,u)
        ref=ppi_mean_ci(y,s,u,alpha=.05)
        np.testing.assert_allclose(out['ppipp_pkg'][:2],np.clip(np.asarray(ref).reshape(-1),0,1),atol=1e-12)
        ref=ppi_mean_ci(y,s,u,alpha=.05,lam=1)
        ours=out['ppi']
        # Package uses ddof0, ours uses ddof1 intentionally.
        cen=y.mean()+u.mean()-s.mean()
        rad=norm.ppf(.975)*np.sqrt(np.var(y-s)/100+np.var(u)/1000)
        np.testing.assert_allclose(np.clip(np.asarray(ref).reshape(-1),0,1),np.clip([cen-rad,cen+rad],0,1))


def test_variance_square_identity():
    rng=np.random.default_rng(2); s=rng.uniform(size=10000)
    m=.02+.96*(2*s-1)**2; g=.2*s+.7*s*s
    r=.1
    # Distribution with empirical uniform S and Bernoulli labels conditional on S.
    vy=np.mean(m)*(1-np.mean(m))
    cov=np.mean((m-m.mean())*(g-g.mean()))
    v=vy-2*cov+(1+r)*np.var(g)
    v2=vy-np.var(m)/(1+r)+(1+r)*np.var(g-m/(1+r))
    np.testing.assert_allclose(v,v2,atol=1e-14)


def test_constant_scores_and_boundaries():
    y=np.zeros(50); s=np.ones(50)*.3; u=np.ones(500)*.3
    out,idx=all_intervals(y,s,u)
    for lo,hi,raw in out.values():
        assert 0<=lo<=hi<=1
        assert np.isfinite(raw)
    assert out['cp'][0]==0 and out['cp'][1]>0
    assert out['wald'][1]==0
    assert eb_radius(0,50,.05,0)==0
    assert eb_radius(0,50,.05,1)>0
    assert out['eb_select'][0]<=.01<=out['eb_select'][1]


def test_unlabeled_reuse_covariance():
    rng=np.random.default_rng(3); hu=features(rng.uniform(size=1000))
    b=rng.normal(size=(5,4)); weights=np.ones(5)/5
    bbar=weights@b
    np.testing.assert_allclose(np.var(hu@bbar,ddof=1),bbar@np.cov(hu,rowvar=False)@bbar)
    # Averaging fold variances is not the same operation.
    assert abs(np.mean([np.var(hu@t,ddof=1) for t in b])-np.var(hu@bbar,ddof=1))>1e-4


def test_bernoulli_truths():
    from run_experiments import moments, conditional_mean
    s=(np.arange(100000)+.5)/100000
    for name in ['linear','quadratic','step','null','rare']:
        mu,vy,vm,cov=moments(name)
        m=conditional_mean(name,s)
        np.testing.assert_allclose(m.mean(),mu,atol=1e-8)
        np.testing.assert_allclose(np.var(m),vm,atol=1e-8)
        np.testing.assert_allclose(np.mean((m-m.mean())*(s-.5)),cov,atol=1e-8)
        np.testing.assert_allclose(mu*(1-mu),vy,atol=1e-12)
