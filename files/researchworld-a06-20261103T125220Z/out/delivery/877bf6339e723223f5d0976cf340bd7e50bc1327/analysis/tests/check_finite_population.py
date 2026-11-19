import sys
sys.path.insert(0,'scripts')
import numpy as np
from scipy.stats import hypergeom
from finite_population import hypergeom_interval

minimum=1.
for N in [5,12,30]:
 for m in [1,N//2,N]:
  intervals=np.array([hypergeom_interval(x,m,N) for x in range(m+1)])
  for M in range(N+1):
   accepted=(intervals[:,0]<=M/N+1e-12)&(M/N<=intervals[:,1]+1e-12)
   coverage=float(hypergeom.pmf(np.arange(m+1),N,M,m)[accepted].sum())
   minimum=min(minimum,coverage)
   assert coverage>=.95-1e-12,(N,m,M,coverage)
  if m==N:assert np.allclose(intervals,np.repeat((np.arange(N+1)/N)[:,None],2,axis=1))
print('PASS: exact hypergeometric interval coverage over all population success totals; minimum',minimum)
from finite_population import paired_difference_interval
# Exhaust all possible win/loss samples and population compositions for a small N.
from scipy.stats import multivariate_hypergeom
N=6;m=3;minimum_pair=1.
for W in range(N+1):
 for L in range(N-W+1):
  truth=(W-L)/N;coverage=0.
  for w in range(m+1):
   for l in range(m-w+1):
    lo,hi=paired_difference_interval(w,l,m,N)
    prob=multivariate_hypergeom.pmf([w,l,m-w-l],[W,L,N-W-L],m)
    if lo-1e-12<=truth<=hi+1e-12:coverage+=prob
  minimum_pair=min(minimum_pair,coverage);assert coverage>=.95-1e-12,(W,L,coverage)
print('PASS: paired-difference interval exact finite-population coverage; minimum',minimum_pair)
