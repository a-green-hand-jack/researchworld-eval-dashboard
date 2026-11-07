"""Sum-loss ridge Bradley--Terry; deterministic dense Newton and flip audit."""
from dataclasses import dataclass
import numpy as np
from scipy.linalg import solve
from scipy.special import expit
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

@dataclass
class Fit:
 theta: np.ndarray
 hessian: np.ndarray
 grad: float
 iterations: int
 objective: float

class BT:
 def __init__(self, a, b, y, names=None, ridge=1., home=None):
  self.a=np.asarray(a,int); self.b=np.asarray(b,int); self.y=np.asarray(y,float)
  assert len(self.a)==len(self.b)==len(self.y) and np.all(self.a!=self.b)
  assert np.all((self.y>=0)&(self.y<=1))
  self.m=len(names) if names is not None else int(max(self.a.max(),self.b.max())+1)
  self.names=list(names) if names is not None else list(map(str,range(self.m)))
  self.ridge=float(ridge); self.home=None if home is None else np.asarray(home,float)
  # Aggregate identical design rows. Canonicalize pair orientation.
  lo=np.minimum(self.a,self.b); hi=np.maximum(self.a,self.b); sign=np.where(self.a==lo,1.,-1.)
  self.sign=sign; yy=np.where(sign==1,self.y,1-self.y)
  if home is None: design=np.stack([lo,hi],axis=1)
  else: design=np.stack([lo,hi,np.asarray(home)*sign],axis=1)
  uniq,self.edge=np.unique(design,axis=0,return_inverse=True)
  self.u=uniq[:,0].astype(int); self.v=uniq[:,1].astype(int)
  self.d=self.m+(home is not None)
  self.X=np.zeros((len(uniq),self.d)); self.X[np.arange(len(uniq)),self.u]=1; self.X[np.arange(len(uniq)),self.v]=-1
  if home is not None:self.X[:,-1]=uniq[:,2]
  self.n=np.bincount(self.edge,minlength=len(uniq)).astype(float)
  self.w=np.bincount(self.edge,weights=yy,minlength=len(uniq))
  graph=csr_matrix((np.ones(len(self.a)),(self.a,self.b)),shape=(self.m,self.m))
  self.components=connected_components(graph,directed=False)[0]
  self.fit_count=0
  self.max_grad=0.
 def counts(self,ids=None,weights=None):
  if weights is None:
   if ids is None:return self.n.copy(),self.w.copy()
   return (np.bincount(self.edge[ids],minlength=len(self.n)).astype(float),np.bincount(self.edge[ids],weights=np.where(self.sign[ids]==1,self.y[ids],1-self.y[ids]),minlength=len(self.n)))
  return (np.bincount(self.edge,weights=weights,minlength=len(self.n)),np.bincount(self.edge,weights=weights*np.where(self.sign==1,self.y,1-self.y),minlength=len(self.n)))
 def flipped_w(self,ids):
  return self.w+np.bincount(self.edge[ids],weights=(1-2*self.y[ids])*self.sign[ids],minlength=len(self.n))
 def fit(self,n=None,w=None,start=None):
  n=self.n if n is None else np.asarray(n,float);w=self.w if w is None else np.asarray(w,float)
  assert np.all(w>=-1e-8) and np.all(w<=n+1e-8)
  t=np.zeros(self.d) if start is None else np.array(start,copy=True)
  X=self.X; lam=self.ridge
  def obj(t):
   z=X@t
   return np.sum(n*np.logaddexp(0,z)-w*z)+.5*lam*(t@t)
  for it in range(80):
   z=X@t;p=expit(z);g=X.T@(n*p-w)+lam*t
   H=X.T@((n*p*(1-p))[:,None]*X)+lam*np.eye(self.d)
   err=float(np.max(np.abs(g)))
   if err<1e-8:break
   step=solve(H,g,assume_a='pos',check_finite=False)
   f=obj(t); rate=1.
   while rate>1e-8 and obj(t-rate*step)>f-1e-4*rate*(g@step)+1e-11:rate*=.5
   t-=rate*step
  z=X@t;p=expit(z);g=X.T@(n*p-w)+lam*t
  H=X.T@((n*p*(1-p))[:,None]*X)+lam*np.eye(self.d)
  err=float(np.max(np.abs(g)))
  if err>1e-7:raise RuntimeError(f'Newton did not converge: {err}')
  self.fit_count+=1;self.max_grad=max(self.max_grad,err)
  return Fit(t,H,err,it+1,float(obj(t)))
 def benefits(self,fit,leader,challenger):
  c=np.zeros(self.d);c[leader]=1;c[challenger]=-1
  v=solve(fit.hessian,c,assume_a='pos',check_finite=False)
  return -(1-2*self.y)*self.sign*(self.X@v)[self.edge]
 def targets(self,fit):
  order=np.argsort(-fit.theta[:self.m],kind='stable');return int(order[0]),int(order[1])

def disagreement(base,changed):
 m=len(base);u,v=np.triu_indices(m,1)
 return float(np.mean((base[u]-base[v])*(changed[u]-changed[v])<0))

def witness(model,base,leader,challenger,order,cap=None):
 """First power-of-two crossing bracket, then prefix bisection. Not global minimum."""
 order=np.asarray(order,int)
 if cap is not None:order=order[:cap]
 if len(order)==0:return None,{},None
 cache={0:base}; tol=1e-7
 def at(k):
  if k not in cache:cache[k]=model.fit(w=model.flipped_w(order[:k]),start=base.theta)
  return cache[k].theta[leader]-cache[k].theta[challenger]
 hi=1;lo=0
 while True:
  hi=min(hi,len(order))
  if at(hi)<-tol:break
  if hi==len(order):return None,cache,None
  lo=hi;hi*=2
 while hi-lo>1:
  mid=(hi+lo)//2
  if at(mid)<-tol:hi=mid
  else:lo=mid
 at(hi);at(hi-1)
 return hi,cache,order[:hi]
