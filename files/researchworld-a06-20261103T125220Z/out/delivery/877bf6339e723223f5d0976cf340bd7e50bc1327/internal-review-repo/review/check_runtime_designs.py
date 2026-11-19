"""Independent artificial diagnostics for the B/C runtime-selection argument.

Run: python3 review/check_runtime_designs.py
No main responses are read; tail inversion is independent of study code.
"""
from collections import Counter
from functools import lru_cache
from itertools import permutations, product
from math import comb
from pathlib import Path
import json
import numpy as np
from scipy.stats import hypergeom

# Fixed disjoint positions of one permutation, after marginalizing omitted ones.
counts=Counter()
for p in permutations(range(8)):
    search=tuple(sorted((p[0],p[2])))
    audit=tuple(sorted((p[4],p[6])))
    counts[search,audit]+=1
assert len(counts)==comb(8,2)*comb(6,2)
assert set(counts.values())=={96}  # 2! search * 2! audit * 4! other positions.

@lru_cache(None)
def interval(x,m,N,alpha):
    M=np.arange(x,N-m+x+1)
    accepted=(hypergeom.sf(x-1,N,M,m)>=alpha/2)&(hypergeom.cdf(x,N,M,m)>=alpha/2)
    return int(M[accepted][0]),int(M[accepted][-1])

# Enumerate group success counts with their exact combinatorial multiplicities.
# Groups: retained search, omitted search, retained audit, omitted audit, remainder.
# This is exhaustive for arbitrary fixed binary populations of each total M.
N=14;sizes=(2,2,3,3,4);alpha=.025
checks=[]
for M in range(N+1):
    total=comb(N,M)
    failures={kind:Counter() for kind in ['audit','search']}
    c_failure_mass=0
    for v in product(*(range(n+1) for n in sizes)):
        if sum(v)!=M:continue
        mass=1
        for n,x in zip(sizes,v):mass*=comb(n,x)
        xC,xO,yC,yO,_=v
        design_failures={kind:[] for kind in failures}
        for s,m,x,y in [(4,6,xC+xO,yC+yO),(2,3,xC,yC)]:
            remaining=M-x;R=N-s
            lo,hi=interval(y,m,R,alpha)
            design_failures['audit'].append(not lo<=remaining<=hi)
            lo,hi=interval(x,s,N,alpha)
            design_failures['search'].append(not lo-x<=remaining<=hi-x)
        for kind,(b,c) in design_failures.items():
            if b:failures[kind]['B']+=mass
            if c:failures[kind]['C']+=mass
            if b or c:failures[kind]['adversarial_choice']+=mass
        if design_failures['audit'][1]:c_failure_mass+=mass
    row={'population_successes':M}
    for kind,events in failures.items():
        rates={key:events[key]/total for key in ['B','C','adversarial_choice']}
        assert rates['B']<=alpha+1e-12 and rates['C']<=alpha+1e-12
        assert rates['adversarial_choice']<=.05+1e-12
        row[kind+'_failure_rates']=rates
    # A trigger choosing C only when its audit interval fails has zero conditional
    # C coverage whenever the trigger has positive probability. Unconditional
    # coverage remains protected. This artificial trigger is deliberately more
    # adversarial than an actual runtime rule; it is not a model of that rule.
    row['adversarial_C_trigger_probability']=c_failure_mass/total
    checks.append(row)
assert any(r['adversarial_C_trigger_probability']>0 for r in checks)
out={'scope':'Artificial exhaustive diagnostic only; no LLM performance or release approval',
     'uniformity':{'permutations':40320,'search_audit_set_pairs':len(counts),'multiplicity_each':96},
     'two_design_diagnostics':{'population_size':N,'group_sizes':sizes,'per_design_alpha':alpha,'checks':checks},
     'conditional_warning':'A trigger choosing C precisely on its failure event yields conditional coverage zero on a positive-probability trigger; no conditional-on-trigger guarantee follows.',
     'passed':['Fixed retained audit is uniform conditional only on retained search identities',
               'Audit and transformed-search fixed-design failures are at most .025',
               'An arbitrary B/C choice cannot fail more often than the union, at most .05']}
Path('review/runtime-design-check.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'uniformity':out['uniformity'],'max_failure_rates':{
 kind:{key:max(r[kind+'_failure_rates'][key] for r in checks) for key in ['B','C','adversarial_choice']}
 for kind in ['audit','search']},'passed':out['passed']},indent=2))
