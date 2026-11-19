"""Numerical checks for fitting, influence sign and the finite-edit certificate.

All toy records here are SYNTHETIC verification fixtures, not study evidence.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import itertools,unittest,json,time
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from bt import Panel,BT
from data import ROOT


class NumericalChecks(unittest.TestCase):
    def fixture(self):
        return Panel('synthetic',['a','b','c'],np.array([0]*9+[0,1,1,1,1]),
            np.array([1]*9+[2,2,2,2,2]),np.array([1]*8+[0,1,1,1,0,0]),np.arange(14))

    def test_independent_optimizer(self):
        p=self.fixture();b=BT(p);t=b.fit()
        X=p.X[p.group]
        def fun(v):
            z=X@v
            return np.logaddexp(0,z).sum()-p.y@z+.5*(v@v)
        def jac(v):return X.T@(expit(X@v)-p.y)+v
        res=minimize(fun,np.zeros(p.m),jac=jac,method='BFGS',options={'gtol':1e-9})
        np.testing.assert_allclose(t,res.x,atol=1e-7)

    def test_influence_finite_difference(self):
        p=self.fixture();b=BT(p);t=b.fit();c=b.contrast(0,1);row=0
        eps=1e-4
        w=p.wins.copy();w[p.group[row]]+=eps*(1-2*p.y[row])
        changed=b.fit(wins=w,start=t)
        derivative=float(c@(changed-t))/eps
        self.assertAlmostEqual(derivative,-b.gains(t,c)[row],places=5)

    def test_exhaustive_certificate(self):
        p=Panel('synthetic',['a','b'],np.zeros(10,int),np.ones(10,int),
                np.array([1]*9+[0]),np.arange(10))
        b=BT(p);t=b.fit();c=b.contrast(0,1)
        safe=b.certificate(t,c)['safe_k'];self.assertGreater(safe,0)
        for size in range(safe+1):
            for ids in itertools.combinations(range(p.n),size):
                ids=np.array(ids,int);w=p.wins.copy()
                w+=np.bincount(p.group[ids],weights=1-2*p.y[ids],minlength=len(p.X))
                changed=b.fit(wins=w,start=t)
                self.assertGreater(float(c@changed),0)

    def test_orientation_and_replication(self):
        p=self.fixture();b=BT(p);t=b.fit()
        rev=Panel('reverse',p.models,p.b,p.a,1-p.y,p.cluster)
        np.testing.assert_allclose(BT(rev).fit(),t,atol=1e-9)
        ids=np.tile(np.arange(p.n),3);rep=p.subset(ids)
        np.testing.assert_allclose(BT(rep,ridge=3).fit(),t,atol=1e-9)

    def test_direct_transfer_relaxation_exhaustive(self):
        p=self.fixture();b=BT(p);t=b.fit();c=b.contrast(0,1)
        bound=b.direct_bound(t,c)
        for size in range(4):
            virtual=b.fit(linear=size*c,start=t)
            for ids in itertools.combinations(range(p.n),size):
                ids=np.array(ids,int);w=p.wins.copy()
                w+=np.bincount(p.group[ids],weights=1-2*p.y[ids],minlength=len(p.X))
                changed=b.fit(wins=w,start=t)
                self.assertGreaterEqual(float(c@(changed-virtual)),-1e-8)
                if size<bound['lower_k']:self.assertGreater(float(c@changed),-1e-8)
        a=b.attack(t,c)
        if bound['exact_by_capacity']:self.assertEqual(a['k'],bound['lower_k'])


if __name__=='__main__':
    start=time.time()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(NumericalChecks)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    (ROOT/'results/verification.json').write_text(json.dumps(dict(
        tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        seconds=time.time()-start),indent=2)+'\n')
    if not result.wasSuccessful():raise SystemExit(1)
