import sys,pathlib
import numpy as np
from scipy.stats import norm
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from statistics_core import cp,cp_table,gaussian_radii,intervals,choose
from infer import parse

def test_cp_boundaries_and_inclusion():
    assert cp(0,10)[0]==0
    assert cp(10,10)[1]==1
    a,b=cp_table(32,12); x,y=cp_table(32)
    assert np.all(a<=x) and np.all(b>=y)
    assert np.all(a<=np.arange(33)/32) and np.all(b>=np.arange(33)/32)

def test_parser():
    assert parse('A',10)==0
    assert parse('(J)',10)==9
    assert parse('J',4)==-1
    assert parse('Answer: A',10)==-1
    assert parse('A or B',10)==-1

def test_ties():
    x=np.zeros((32,12))
    assert choose(x)==0
    assert choose(x,'halving')==0
    bands,j=intervals(x,np.random.default_rng(2),999)
    assert j==0
    assert bands['naive_CP'][1]>0
    assert bands['paired_multiplier'][1]==0 # known nonregular failure, not patched.

def test_duplicate_coordinates():
    z=np.array([0,1]*64)[:,None]
    x=np.repeat(z,12,axis=1)
    r,ri=gaussian_radii(x,np.random.default_rng(3),30000)
    expected=norm.ppf(.975)*.5/np.sqrt(128)
    assert abs(r-expected)<.003
    assert ri>r

def test_covariance_equivalence():
    rng=np.random.default_rng(7); x=rng.binomial(1,.6,(64,4)); xc=x-x.mean(0)
    g=rng.normal(size=(50000,64))@xc/64
    q=np.quantile(abs(g).max(1),.95)
    r,_=gaussian_radii(x,np.random.default_rng(8),50000)
    assert abs(q-r)<.005

def test_cp_exact_coverage_enumeration():
    from scipy.stats import binom
    for n in [10,32,128]:
        for p in [.01,.3,.6,.99]:
            a,b=cp_table(n)
            mass=binom.pmf(np.arange(n+1),n,p)
            assert mass[(a<=p)&(p<=b)].sum()>=.95-1e-12
