import itertools
import numpy as np
from scipy.special import expit
from bt import BT, witness

def test_symmetric():
 m=BT([0,0],[1,1],[1,0]);r=m.fit();assert np.max(np.abs(r.theta))<1e-9

def test_two_player_stationary_equation():
 m=BT(np.zeros(20,int),np.ones(20,int),[1]*15+[0]*5,ridge=.1);r=m.fit();d=r.theta[0]-r.theta[1]
 assert abs(20*expit(d)-15+.1*d/2)<1e-8

def test_finite_difference_flip_derivative():
 m=BT([0,0,0,1,1,2]*3,[1,1,2,2,2,0]*3,[1,0,1,1,0,0]*3);r=m.fit();h=m.benefits(r,0,1)
 i=2;delta=(1-2*m.y[i])*m.sign[i];w=m.w.copy();eps=1e-5;w[m.edge[i]]+=eps*delta
 new=m.fit(w=w,start=r.theta)
 assert abs(-((new.theta[0]-new.theta[1])-(r.theta[0]-r.theta[1]))/eps-h[i])<1e-5

def test_aggregation_and_duplication():
 a=np.array([0,1,0,2,1,2]);b=np.array([1,0,2,0,2,1]);y=np.array([1,0,1,.5,0,1])
 m=BT(a,b,y);r=m.fit();other=BT(np.tile(a,3),np.tile(b,3),np.tile(y,3),ridge=3)
 assert np.allclose(r.theta,other.fit().theta,atol=1e-8)
 # Orientation inversion leaves the objective unchanged.
 assert np.allclose(r.theta,BT(b,a,1-y).fit().theta,atol=1e-8)

def test_refits_and_tiny_exhaustive():
 a=np.array([0]*10);b=np.array([1]*10);y=np.array([1]*7+[0]*3);m=BT(a,b,y);r=m.fit()
 order=np.argsort(-m.benefits(r,0,1));order=order[m.benefits(r,0,1)[order]>0]
 k,cache,ids=witness(m,r,0,1,order)
 assert k==3
 y2=y.copy();y2[ids]=1-y2[ids];direct=BT(a,b,y2).fit()
 assert np.allclose(cache[k].theta,direct.theta,atol=1e-9)
 assert cache[k-1].theta[0]>=cache[k-1].theta[1]-1e-7
 for n in [1,2]:
  for subset in itertools.combinations(range(10),n):
   new=m.fit(w=m.flipped_w(np.array(subset)),start=r.theta)
   assert new.theta[0]>=new.theta[1]-1e-7

def test_home_derivative():
 m=BT([0,1,0,2,1,2]*3,[1,0,2,0,2,1]*3,[1,0,1,0,1,0]*3,home=[1,-1,-1,1,1,-1]*3)
 r=m.fit();assert np.isfinite(r.theta).all() and r.grad<1e-7

def test_tie_is_not_strict_dethroning():
 m=BT([1]*10,[0]*10,[1]*7+[0]*3);base=m.fit()
 changed=m.fit(w=m.flipped_w(np.array([0,1])),start=base.theta)
 assert not (np.max(changed.theta)-changed.theta[1]>1e-7)
 assert abs(changed.theta[0]-changed.theta[1])<1e-7

