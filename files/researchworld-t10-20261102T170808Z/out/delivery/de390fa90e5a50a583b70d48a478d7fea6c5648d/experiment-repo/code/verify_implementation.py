#!/usr/bin/env python3
"""Independent reference and algebra checks (not Monte Carlo coverage proof)."""
import json
from pathlib import Path
import numpy as np
from ppi_py import ppi_mean_ci
from run_experiments import intervals,draw,eb_radius
rng=np.random.default_rng(19042); errors=[]
for scenario in ['linear','quadratic','null','bernoulli_quadratic']:
 for n in [50,300]:
  y,s,u,_,bounded=draw(rng,scenario,n,10*n,{})
  mine=intervals(y,s,u,bounded)
  for method,lam in [('label',0),('ppi',1),('ppi++',None)]:
   ref=np.array(ppi_mean_ci(y,s,u,alpha=.05,lam=lam),dtype=float).reshape(-1)
   err=float(np.max(np.abs(ref-np.array(mine[method]))))
   assert err<1e-10,(scenario,n,method,ref,mine[method])
   errors.append(err)
# Empirical variance identity for h and m under a very large known DGP.
s=rng.uniform(size=500000); eps=rng.normal(0,.15,len(s)); m=(2*s-1)**2; y=m+eps; h=.3*s+.6*s*s; r=.1
# Identity includes covariance of noise with h in finite MC; tolerance checks algebra in expectation.
lhs=np.var(y-h)+r*np.var(h)
rhs=np.var(y)-np.var(m)/(1+r)+(1+r)*np.var(h-m/(1+r))
assert abs(lhs-rhs)<.001
# Range and shift/scale equivariance of empirical Bernstein radius.
a=rng.uniform(size=100)
assert np.allclose(eb_radius(3+2*a,2,.05),2*eb_radius(a,1,.05))
record={'reference':'ppi-python==0.2.3','reference_comparisons':len(errors),'maximum_endpoint_absolute_error':max(errors),'variance_identity_monte_carlo_absolute_error':abs(lhs-rhs),'status':'pass'}
Path('results/verification.json').write_text(json.dumps(record,indent=2)); print(json.dumps(record,indent=2))
