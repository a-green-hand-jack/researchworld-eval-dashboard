import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
from scipy.special import expit
from bt import BT,metrics

def data():
    return pd.DataFrame(dict(a=['a','a','b','a','b','a','b','a'],b=['b','b','c','c','c','b','c','c'],y=[1,0,1,1,0,.5,1,0],home=[1,-1,1,-1,1,-1,1,-1]))

def test_gradient_and_hessian():
    b=BT(data());t=np.array([.2,-.3,.1]);e=1e-5;g,H=b.derivatives(t)
    gn=np.array([(b.objective(t+e*v,b.C,b.S)-b.objective(t-e*v,b.C,b.S))/(2*e) for v in np.eye(3)])
    hn=np.column_stack([(b.derivatives(t+e*v)[0]-b.derivatives(t-e*v)[0])/(2*e) for v in np.eye(3)])
    np.testing.assert_allclose(g,gn,atol=1e-8);np.testing.assert_allclose(H,hn,atol=1e-8)

def test_row_aggregate_and_gauge():
    b=BT(data());f=b.fit();X=b.X[b.group];z=X@f.theta
    row=np.sum(np.logaddexp(0,z)-b.y*z)+.5*b.lam*(f.theta@f.theta)
    assert abs(row-f.objective)<1e-10
    assert abs(f.theta.mean())<1e-12;assert f.gradmax<1e-7

def test_fractional_delete_influence():
    for home in [False,True]:
        b=BT(data(),home=home);f=b.fit();eps=1e-4;inf=b.influence(f,0,1)
        for k in range(b.n):
            w=np.ones(b.n);w[k]-=eps;r=b.fit(weights=w,start=f.theta)
            d=((r.theta[0]-r.theta[1])-(f.theta[0]-f.theta[1]))/eps
            np.testing.assert_allclose(d,inf[k],atol=1e-4)

def test_permutation_and_flip():
    d=data();b=BT(d);f=b.fit();b2=BT(d.sample(frac=1,random_state=7));f2=b2.fit()
    np.testing.assert_allclose(f.theta,f2.theta,atol=1e-9)
    r=b.refit(f,[1],'flip');y=b.y.copy();y[1]=1-y[1]
    np.testing.assert_allclose(r.theta,b.fit(y=y).theta,atol=1e-8)

def test_disconnect_and_ridge():
    d=pd.DataFrame(dict(a=['a','b'],b=['b','c'],y=[1.,1.],home=[0.,0.]))
    b=BT(d);f=b.fit();assert b.components([1])==2
    assert np.isfinite(b.refit(f,[1]).theta).all()

def test_metrics():
    assert metrics(np.array([3.,2.,1.]),np.array([2.,3.,1.]))['kendall_distance']==1/3
