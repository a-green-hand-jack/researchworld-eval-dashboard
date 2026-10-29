"""Numerical checks for the scientific core, using explicit synthetic comparisons."""
import itertools
import numpy as np
from bt import BT

def model(a,b,y,m):
 return BT(dict(a=np.array(a),b=np.array(b),y=np.array(y,dtype=float),names=np.array([str(i) for i in range(m)]),cluster=np.arange(len(y)),home=np.zeros(len(y))))
def main():
 bt=model([0]*12,[1]*12,[1]*8+[0]*4,2);f=bt.fit();assert abs(f.theta.sum())<1e-10
 assert abs((f.theta[0]-f.theta[1])-np.log(2))<1e-6
 for kind,expected in [('delete',5),('flip',3)]:
  result,ix,_=bt.attack(f,0,1,kind,cap=.9);assert result['k']==expected,(kind,result)
  for k in range(expected):
   assert all(bt.edited_fit(np.array(ix0,dtype=int),kind,f).theta[0]>=-1e-8 for ix0 in itertools.combinations(range(bt.n),k))
 bt=model([0,0,1,0,0,1,0,0,1],[1,2,2]*3,[1,0,1,0,1,0,1,1,0],3);f=bt.fit()
 for a,b in [(0,1),(1,2)]:
  for kind in ['delete','flip']:
   harm=bt.influence(f,a,b,kind);eps=1e-4
   for i in range(bt.n):
    if kind=='delete':
     weights=np.ones(bt.n);weights[i]-=eps;f1=bt.fit(weights=weights,init=f.theta)
    else:
     y=bt.y.copy();y[i]+=eps*(1-2*y[i]);f1=bt.fit(y=y,init=f.theta)
    actual=((f.theta[a]-f.theta[b])-(f1.theta[a]-f1.theta[b]))/eps
    assert abs(actual-harm[i])<5e-4,(actual,harm[i])
 w,s=bt.aggregate();obj,g,h=bt.calc(f.theta,w,s)
 assert np.abs(g).max()<1e-5
 assert np.linalg.eigvalsh(h+bt.gauge).min()>0
 print('PASS: gauge, known two-player MLE, exhaustive two-player edit counts, finite-difference deletion/flip influence, KKT, Hessian.')
if __name__=='__main__':main()
