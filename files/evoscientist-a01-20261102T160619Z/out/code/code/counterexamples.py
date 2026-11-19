#!/usr/bin/env python3
"""Find small exact (dyadic rational) counterexamples; label as synthetic theory."""
from pathlib import Path
from fractions import Fraction
import json,itertools,sys
import numpy as np
from optimize import solve,subsets
ROOT=Path(__file__).resolve().parents[1]
RULES=['mean','median','borda']
def exact_score(a,rule):
    if rule=='mean':return [sum(row)/len(row) for row in a]
    if rule=='median':return [sorted(row)[len(row)//2] for row in a]
    return [sum(sum(Fraction(1) if row[j]>r[j] else Fraction(1,2) if row[j]==r[j] else Fraction(0) for k,r in enumerate(a) if k!=i) for j in range(len(row))) for i,row in enumerate(a)]
def exact_K(a,rule):
    for k in range(len(a[0])+1):
      for ss in itertools.combinations(range(len(a[0])),k):
        b=[row[:] for row in a]
        for j in ss:b[0][j]=Fraction(1)
        v=exact_score(b,rule)
        if v[0]>=max(v[1:]):return k
    return None

def main():
    rng=np.random.default_rng(916);found={};num=0
    pairs=[(r,s) for r in RULES for s in RULES if r!=s]
    while len(found)<6 and num<10000:
        num+=1;a=rng.integers(0,9,size=(4,5))/8
        ks={r:solve(a,0,1.,r)['K'] for r in RULES}
        if any(v==0 or v is None for v in ks.values()):continue
        for r,s in pairs:
            if (r,s) not in found and ks[r]<ks[s]:
                rational=[[Fraction(float(x)) for x in row] for row in a]
                exact={rr:exact_K(rational,rr) for rr in RULES};assert exact==ks
                found[r,s]={'less':r,'more':s,'matrix':[[str(x) for x in row] for row in rational],'K':exact,'rho':1,'target':0,'kind':'synthetic exact counterexample, NOT empirical leaderboard data'}
    assert len(found)==6
    (ROOT/'artifacts/counterexamples.json').write_text(json.dumps({'seed':916,'candidates_examined':num,'examples':list(found.values())},indent=2));print('Exact counterexamples',len(found),'candidates',num)
if __name__=='__main__':main()
