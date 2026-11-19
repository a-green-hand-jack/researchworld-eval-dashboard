"""Numerical validity checks, independent optimizer and infinitesimal perturbation."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from bt import fit,aggregate,hessian,influence
rng=np.random.default_rng(731);m=5;n=200
a=rng.integers(0,m,n);b=(a+rng.integers(1,m,n))%m
y=rng.binomial(1,expit(np.linspace(-1,1,m)[a]-np.linspace(-1,1,m)[b])).astype(float)
y[::11]=.5
for ridge in [.1,1,10]:
 t,diag=fit(a,b,y,m,ridge)
 def loss(t):return np.sum(np.logaddexp(0,t[a]-t[b])-y*(t[a]-t[b]))+ridge*(t@t)/2
 opt=minimize(loss,np.zeros(m),method='BFGS',tol=1e-9)
 assert np.max(abs(t-opt.x))<2e-5,(t,opt)
 t2,_=fit(b,a,1-y,m,ridge);assert np.max(abs(t-t2))<1e-9
 u=np.arange(m);c=np.zeros(m);c[0]=1;c[1]=-1
 i,j,counts,_=aggregate(a,b,y,m);H=hessian(t,i,j,counts,ridge)
 delta=np.zeros(n);delta[0]=1e-4
 actual=fit(a,b,y+delta,m,ridge,init=t)[0]-t
 theory=np.linalg.solve(H,np.bincount(a,weights=delta,minlength=m)-np.bincount(b,weights=delta,minlength=m))
 assert np.max(abs(actual-theory))<1e-9
 t3,_=fit(np.tile(a,2),np.tile(b,2),np.tile(y,2),m,2*ridge);assert max(abs(t-t3))<1e-9
 print('PASS ridge',ridge,'independent optimizer / orientation / influence / duplication')
