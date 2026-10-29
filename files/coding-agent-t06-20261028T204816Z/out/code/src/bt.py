"""CPU Newton solver and influence-prefix audits for row-level BT comparisons.

All optimizations use summed loss and symmetric ridge, with sum(scores)=0.
Only reported witness sets, never non-successes, certify a property.
"""
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from scipy.special import expit

@dataclass
class Fit:
 theta: np.ndarray
 hessian: np.ndarray
 grad_norm: float
 iterations: int

class BT:
 def __init__(self, data, ridge=1e-6, home=False):
  self.a=np.array(data['a']);self.b=np.array(data['b']);self.y=np.array(data['y'])
  self.names=np.array(data['names']);self.cluster=np.array(data['cluster'])
  self.n=len(self.y);self.m=len(self.names);self.ridge=ridge;self.home=home
  self.z=np.array(data['home']) if home else np.zeros(self.n)
  # Distinct (pair, home indicator) cells. A row remains an indivisible edit unit.
  keys=self.a*self.m+self.b
  if home: keys=keys*3+(self.z+1).astype(int)
  uniq,self.cell=np.unique(keys,return_inverse=True);self.e=len(uniq)
  first=np.unique(self.cell,return_index=True)[1]
  self.u=self.a[first];self.v=self.b[first];self.ez=self.z[first]
  self.dim=self.m+int(home)
  self.gauge=np.zeros((self.dim,self.dim));self.gauge[:self.m,:self.m]=1/self.m
  self.ii=np.arange(self.m)
 def aggregate(self, weights=None, y=None):
  weights=np.ones(self.n) if weights is None else np.asarray(weights)
  y=self.y if y is None else y
  return (np.bincount(self.cell,weights=weights,minlength=self.e),np.bincount(self.cell,weights=weights*y,minlength=self.e))
 def design_diff(self,t):
  return t[self.u]-t[self.v]+(self.ez*t[-1] if self.home else 0)
 def calc(self,t,w,s):
  eta=self.design_diff(t);p=expit(eta);r=w*p-s
  g=np.zeros(self.dim);g[:self.m]=np.bincount(self.u,weights=r,minlength=self.m)-np.bincount(self.v,weights=r,minlength=self.m)
  if self.home:g[-1]=self.ez@r
  g+=self.ridge*t
  h=np.zeros((self.dim,self.dim));q=w*p*(1-p)
  np.add.at(h,(self.u,self.v),-q);np.add.at(h,(self.v,self.u),-q)
  h[self.ii,self.ii]=np.bincount(self.u,weights=q,minlength=self.m)+np.bincount(self.v,weights=q,minlength=self.m)
  if self.home:
   cross=np.bincount(self.u,weights=q*self.ez,minlength=self.m)-np.bincount(self.v,weights=q*self.ez,minlength=self.m)
   h[:self.m,-1]=cross;h[-1,:self.m]=cross;h[-1,-1]=q@(self.ez**2)
  h.flat[::self.dim+1]+=self.ridge
  obj=np.sum(w*np.logaddexp(0,eta)-s*eta)+.5*self.ridge*(t@t)
  return obj,g,h
 def fit(self,weights=None,y=None,init=None,counts=None):
  w,s=self.aggregate(weights,y) if counts is None else counts
  t=np.zeros(self.dim) if init is None else np.array(init,copy=True)
  tolerance=2e-7+1e-11*w.sum()
  for iteration in range(70):
   obj,g,h=self.calc(t,w,s);norm=np.abs(g).max()
   if norm<tolerance: break
   step=np.linalg.solve(h+self.gauge,g);rate=1.
   for _ in range(30):
    new=t-rate*step;new[:self.m]-=new[:self.m].mean()
    newobj=self.calc(new,w,s)[0]
    if newobj<=obj-1e-4*rate*(g@step)+1e-10:break
    rate*=.5
   t=new
  obj,g,h=self.calc(t,w,s);norm=float(np.abs(g).max())
  if norm>2e-5: raise RuntimeError(f'Newton failed: grad={norm} n={self.n}')
  return Fit(t,h,norm,iteration+1)
 def influence(self,fit,a,b,kind):
  c=np.zeros(self.dim);c[a]=1;c[b]=-1
  v=np.linalg.solve(fit.hessian+self.gauge,c)
  projection=v[self.a]-v[self.b]+(self.z*v[-1] if self.home else 0)
  if kind=='delete':harm=(self.y-expit(fit.theta[self.a]-fit.theta[self.b]+(self.z*fit.theta[-1] if self.home else 0)))*projection
  elif kind=='flip':harm=(2*self.y-1)*projection
  else:raise ValueError(kind)
  return harm
 def edited_fit(self,indices,kind,base):
  w,s=self.aggregate()
  dc=np.bincount(self.cell[indices],minlength=self.e)
  if kind=='delete':
   w=w-dc;s=s-np.bincount(self.cell[indices],weights=self.y[indices],minlength=self.e)
  else:s=s+np.bincount(self.cell[indices],weights=1-2*self.y[indices],minlength=self.e)
  return self.fit(init=base.theta,counts=(w,s))
 def attack(self,base,a,b,kind='delete',scope='all',cap=.05):
  gap=float(base.theta[a]-base.theta[b]);harm=self.influence(base,a,b,kind)
  eligible=harm>1e-14
  if scope=='direct':eligible&=((self.a==min(a,b))&(self.b==max(a,b)))
  if scope=='incident':eligible&=((self.a==a)|(self.a==b)|(self.b==a)|(self.b==b))
  order=np.flatnonzero(eligible);order=order[np.argsort(-harm[order],kind='stable')]
  maxk=min(int(np.floor(cap*self.n)),len(order));order=order[:maxk]
  cum=np.cumsum(harm[order]);kpred=int(np.searchsorted(cum,gap)+1) if len(cum) else 1
  pred=float(kpred) if kpred<=maxk else np.nan
  # Geometric prefix scan and local bisection. Monotonicity is not assumed as a
  # theorem: this returns a found successful prefix, not a global minimum.
  tested={};cache={}
  def evaluate(k):
   if k not in tested:
    f=self.edited_fit(order[:k],kind,base);tested[k]=float(f.theta[a]-f.theta[b]);cache[k]=f
   return tested[k]
  k=min(maxk,max(1,kpred))
  low=0;high=None
  while maxk>0:
   if evaluate(k)<-1e-8:high=k;break
   low=k
   if k==maxk:break
   k=min(maxk,max(k+1,int(np.ceil(k*1.6))))
  if high is not None:
   while high-low>1:
    mid=(low+high)//2
    if evaluate(mid)<-1e-8:high=mid
    else:low=mid
   witness=order[:high];f=cache[high]
   exposure=int(((self.a==a)|(self.b==a)|(self.a==b)|(self.b==b)).sum())
   incident=((self.a[witness]==a)|(self.b[witness]==a)|(self.a[witness]==b)|(self.b[witness]==b))
   return dict(k=high,kpred=pred,gap=gap,post_gap=tested[high],alpha=high/self.n,local=high/exposure,exposure=exposure,incident_share=float(incident.mean()),grad_norm=f.grad_norm,tested=len(tested),predicted_post=gap-float(cum[high-1])),witness,tested
  return dict(k=np.nan,kpred=pred,gap=gap,post_gap=np.nan,alpha=np.nan,local=np.nan,exposure=int(((self.a==a)|(self.b==a)|(self.a==b)|(self.b==b)).sum()),incident_share=np.nan,grad_norm=np.nan,tested=len(tested),predicted_post=np.nan),np.array([],dtype=int),tested

def load(name,ridge=1e-6,home=False):
 root=Path(__file__).resolve().parents[1]
 with np.load(root/f'data/processed/{name}.npz') as data:return BT(data,ridge,home)
