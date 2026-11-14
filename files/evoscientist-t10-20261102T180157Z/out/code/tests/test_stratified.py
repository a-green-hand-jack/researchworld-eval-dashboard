from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from scipy.stats import multinomial,binom
from exact_stratified import cp,stratified_interval


def test_cp_empty_and_all_outcomes():
    assert cp(0,0,.05)==(0.,1.)
    assert cp(0,10,.05)[0]==0
    assert cp(10,10,.05)[1]==1
    y=np.array([0,1,0,0]); sl=np.zeros(4); su=np.zeros(20)
    lo,hi,w=stratified_interval(y,sl,su)
    assert 0<=lo<=hi<=1


def test_small_exact_enumeration():
    # Numerical audit by summing every possible count outcome (not a proof).
    n=6; N=8; p=.3; q0=.1; q1=.9
    mu=(1-p)*q0+p*q1
    probs=[(1-p)*(1-q0),(1-p)*q0,p*(1-q1),p*q1]
    coverage=0.; total=0.
    for a in range(n+1):
        for b in range(n-a+1):
            for c in range(n-a-b+1):
                d=n-a-b-c; mass=multinomial.pmf([a,b,c,d],n,probs)
                y=np.array([0]*a+[1]*b+[0]*c+[1]*d)
                sl=np.array([0]*(a+b)+[1]*(c+d))
                for k in range(N+1):
                    su=np.array([1]*k+[0]*(N-k))
                    lo,hi,_=stratified_interval(y,sl,su)
                    pr=mass*binom.pmf(k,N,p)
                    total+=pr; coverage+=pr*int(lo<=mu<=hi)
    np.testing.assert_allclose(total,1,atol=1e-12)
    assert coverage>=.95-1e-12
