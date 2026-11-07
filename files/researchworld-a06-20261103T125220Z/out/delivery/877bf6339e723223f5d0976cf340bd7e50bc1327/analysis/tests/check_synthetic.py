"""Distributional checks against analytic moments, endpoints and exact CP coverage."""
import sys
sys.path.insert(0,'scripts')
import numpy as np
from scipy.stats import binom
from run_synthetic import joint_counts, cp_table, run_cell

rng=np.random.default_rng(41819);n=20;reps=200000;p=np.array([.2,.4,.7]);rho=.6
x=joint_counts(rng,reps,n,p,rho)
means=x.mean(axis=0);expected=n*p
mean_se=np.sqrt(n*p*(1-p)/reps)
assert np.all(abs(means-expected)<6*mean_se),(means,expected)
cov=np.cov(x,rowvar=False)
target=n*rho*(np.minimum.outer(p,p)-np.outer(p,p))
np.fill_diagonal(target,n*p*(1-p))
assert np.max(abs(cov-target))<.07,(cov,target)
for r in [0.,1.]:
 z=joint_counts(rng,10000,8,np.full(4,.4),r)
 if r==1:assert np.all(z==z[:,[0]])
 else:assert abs(np.corrcoef(z.T)[0,1])<.04
lo,hi=cp_table(16,.05)
for true_p in [.01,.1,.4,.9,.99]:
 exact=binom.pmf(np.arange(17),16,true_p)[(lo<=true_p)&(true_p<=hi)].sum()
 assert exact>=.95-1e-12,exact
rows=run_cell(1000,32,1,.5,0.,492)
d={x['metric']:x for x in rows}
assert d['regret']['mean']==0
assert d['selection_is_default']['mean']==1
assert d['coverage_naive']['mean']==d['coverage_simultaneous']['mean']
assert d['false_superiority_naive']['mean']==0
print('PASS: count generator matches known means/covariances, dependence endpoints, exact CP coverage and K=1 invariants.')
print('empirical means',means.tolist(),'target',expected.tolist())
print('maximum covariance error',float(abs(cov-target).max()))
