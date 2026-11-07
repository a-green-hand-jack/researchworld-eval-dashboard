"""Penalized BT, exact Newton refits and leading-pair label-reversal influence."""
import numpy as np
from scipy.special import expit
from scipy.sparse.csgraph import connected_components
from scipy.stats import kendalltau

def aggregate(a,b,y,m,weights=None):
 w=np.ones(len(y)) if weights is None else np.asarray(weights)
 idx=a*m+b
 count=np.bincount(idx,weights=w,minlength=m*m).reshape(m,m)
 wins=np.bincount(idx,weights=w*y,minlength=m*m).reshape(m,m)
 i,j=np.nonzero(count)
 return i,j,count[i,j],wins[i,j]
def hessian(theta,i,j,n,ridge):
 p=expit(theta[i]-theta[j]);v=n*p*(1-p)
 h=np.diag(np.bincount(i,weights=v,minlength=len(theta))+np.bincount(j,weights=v,minlength=len(theta))+ridge)
 np.add.at(h,(i,j),-v);np.add.at(h,(j,i),-v)
 return h
def fit(a,b,y,m,ridge=1.,weights=None,init=None):
 i,j,n,w=aggregate(a,b,y,m,weights);t=np.zeros(m) if init is None else np.array(init,copy=True)
 t-=t.mean()
 def obj(t):return np.sum(n*np.logaddexp(0,t[i]-t[j])-w*(t[i]-t[j]))+.5*ridge*(t@t)
 converged=False
 for iteration in range(60):
  r=n*expit(t[i]-t[j])-w
  g=np.bincount(i,weights=r,minlength=m)-np.bincount(j,weights=r,minlength=m)+ridge*t
  if np.max(np.abs(g))<1e-8:converged=True;break
  step=np.linalg.solve(hessian(t,i,j,n,ridge),g);base=obj(t);scale=1.
  while obj(t-scale*step)>base-1e-4*scale*(g@step)+1e-10:
   scale*=.5
   if scale<1e-10:break
  t-=scale*step;t-=t.mean()
  if np.max(np.abs(step*scale))<1e-10:
   if np.max(np.abs(g))<1e-5:converged=True;break
 if not converged:raise RuntimeError(f'BT convergence failed: gradient {max(abs(g))}')
 return t,dict(iterations=iteration,gradient_max=float(max(abs(g))),objective=float(obj(t)))
def order(t):return np.argsort(-t,kind='stable')
def influence(a,b,y,t,ridge=1.,pair=None):
 m=len(t);pair=tuple(order(t)[:2]) if pair is None else pair
 c=np.zeros(m);c[pair[0]]=1;c[pair[1]]=-1
 i,j,n,_=aggregate(a,b,y,m);v=np.linalg.solve(hessian(t,i,j,n,ridge),c)
 # c^T delta theta = (1-2y) * x^T H^-1 c. Positive benefit reduces c^T theta.
 gain=-(1-2*y)*(v[a]-v[b]);eligible=np.flatnonzero((y!=.5)&(gain>1e-14))
 ranking=eligible[np.argsort(-gain[eligible],kind='stable')]
 return ranking,gain,pair

def metrics(t,base,pair):
 o=order(t);ranks=np.empty(len(t),int);ranks[o]=np.arange(len(t))
 return dict(margin=float(t[pair[0]]-t[pair[1]]),pair_reversed=int(t[pair[1]]>t[pair[0]]+1e-10),winner_changed=int(o[0]!=order(base)[0]),top_rank=int(ranks[order(base)[0]]+1),kendall_distance=float((1-kendalltau(t,base).statistic)/2),top5_overlap=float(len(set(o[:5])&set(order(base)[:5]))/min(5,len(t))))
def graph(a,b,m):
 c=np.zeros((m,m));np.add.at(c,(a,b),1);c+=c.T
 ev=np.linalg.eigvalsh(np.diag(c.sum(1))-c)
 return dict(components=int(connected_components(c,directed=False)[0]),observed_edges=int(np.count_nonzero(np.triu(c,1))),possible_edges=m*(m-1)//2,min_support=int(c.sum(1).min()),max_support=int(c.sum(1).max()),laplacian_gap=float(ev[1]))
