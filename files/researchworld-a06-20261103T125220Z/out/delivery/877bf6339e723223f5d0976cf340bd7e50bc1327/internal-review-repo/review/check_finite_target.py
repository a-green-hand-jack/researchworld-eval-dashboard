"""Exhaustive diagnostic of selected finite-remaining-target interval logic.

Run from review repository: python3 review/check_finite_target.py /hutian/experiment
Uses artificial binary fixtures solely for software/theory checking, never LLM
measurements. Brute-force inversion is independent of the production binary search.
"""
from functools import lru_cache
from itertools import combinations
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import hypergeom

root=Path(sys.argv[1])
sys.path.insert(0,str(root/'scripts'))
from finite_population import hypergeom_interval

@lru_cache(None)
def direct_interval(x,m,N,alpha):
    totals=np.arange(x,N-m+x+1)
    accepted=(hypergeom.sf(x-1,N,totals,m)>=alpha/2)&(hypergeom.cdf(x,N,totals,m)>=alpha/2)
    inside=totals[accepted]
    return inside[0]/N,inside[-1]/N

comparisons=0
for N in [6,11,18]:
    for m in [1,N//2,N]:
        for alpha in [.05,.05/8,.2]:
            for x in range(m+1):
                assert np.allclose(hypergeom_interval(x,m,N,alpha),direct_interval(x,m,N,alpha),rtol=0,atol=1e-14)
                comparisons+=1

# Exhaust every uniform search subset; weight all empirical-max ties uniformly.
N=14;s=6;C=3;m=4
rows=np.array([[int(i%2==0),int(i<8),int(i in [1,2,3,6,8,10,13])] for i in range(N)])
M=rows.sum(axis=0)
subsets=np.array(list(combinations(range(N),s)))
counts=rows[subsets].sum(axis=1)
weights=(counts==counts.max(axis=1,keepdims=True)).astype(float)
weights/=weights.sum(axis=1,keepdims=True)
selected_checks=[]
for alpha in [.05,.2]:
    intervals=np.array([hypergeom_interval(x,s,N,alpha/C) for x in range(s+1)])
    # Transform total-success interval to accuracy on the actual complement of S.
    transformed=np.clip((N*intervals[counts]-counts[:,:,None])/(N-s),0,1)
    truth=(M-counts)/(N-s)
    contained=(transformed[:,:,0]<=truth+1e-14)&(truth<=transformed[:,:,1]+1e-14)
    coverage=float((weights*contained).sum(axis=1).mean())
    assert coverage>=1-alpha-1e-12
    # Conditional audit distribution on the complement, after freezing selected j.
    audit_intervals=np.array([hypergeom_interval(x,m,N-s,alpha) for x in range(m+1)])
    audit_cover=[]
    for success in range(N-s+1):
        inside=(audit_intervals[:,0]<=success/(N-s)+1e-14)&(success/(N-s)<=audit_intervals[:,1]+1e-14)
        audit_cover.append(float(hypergeom.pmf(np.arange(m+1),N-s,success,m)[inside].sum()))
    audit_cover=np.array(audit_cover)
    conditional=audit_cover[M-counts]
    assert conditional.min()>=1-alpha-1e-12
    selected_checks.append({'alpha':alpha,'search_subsets':len(subsets),'selected_remaining_coverage':coverage,'minimum_conditional_audit_coverage':float(conditional.min())})

out={'scope':'Artificial exhaustive diagnostic only; not actual LLM results or release approval',
     'source_sha256':hashlib.sha256((root/'scripts/finite_population.py').read_bytes()).hexdigest(),
     'direct_inversion_comparisons':comparisons,'selected_target_checks':selected_checks,
     'passed':['Production binary search agrees with exhaustive tail acceptance set','Simultaneous full-benchmark interval transforms correctly for selected remaining target','Fresh finite-complement audit covers after search-only selection']}
Path('review/finite-target-check.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
