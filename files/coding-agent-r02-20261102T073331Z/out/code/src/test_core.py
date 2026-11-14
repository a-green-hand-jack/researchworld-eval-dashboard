"""Checks for substantive rank, boundary, density, and weighting correctness."""
import unittest
import numpy as np
from scipy.stats import binom, dirichlet
from core import quantile, scores, Calibrator, generate, oracle_score, SCENARIOS

class Checks(unittest.TestCase):
    def test_rank_and_small_sample(self):
        self.assertEqual(quantile(np.arange(499),.1),449)
        self.assertTrue(np.isinf(quantile(np.arange(4),.1)))
        np.testing.assert_equal(quantile(np.arange(12).reshape(4,3),.5),[6,7,8])

    def test_raw_boundary_extension(self):
        m=np.array([[.2,.3,.5],[.2,.3,.5]])
        y=np.array([[0.,.4,.6],[.2,.3,.5]])
        s=scores(m,y)
        self.assertTrue(np.isinf(s['CLR'][0]))
        self.assertEqual(s['CLR'][1],0)
        for name in ['Max','L2','H','CLR-e3']:
            self.assertTrue(np.isfinite(s[name]).all())
        self.assertTrue((s['CLR'] <= np.inf).all())

    def test_atom_coverage_exact_enumeration(self):
        n=6; alpha=.3; k=int(np.ceil((n+1)*(1-alpha)))
        for p in [.02,.2,.7]:
            avg=0.
            for m in range(n+2):
                a=np.r_[np.arange(n+1-m),np.full(m,np.inf)]
                hit=[]
                for test in range(n+1):
                    q=quantile(np.delete(a,test),alpha)
                    hit.append(a[test]<=q)
                avg+=binom.pmf(m,n+1,p)*np.mean(hit)
            expected=k/(n+1)+(1-k/(n+1))*binom.sf(n+1-k,n+1,p)
            self.assertAlmostEqual(avg,expected,places=13)

    def test_oracle_density(self):
        m=np.array([[.2,.3,.5],[.2,.3,.5]])
        y=np.array([[.1,.4,.5],[0.,.4,.6]])
        g=np.zeros(2,dtype=int)
        s=oracle_score(m,y,g,'zeros')
        f0=2*.85*dirichlet.pdf(y[0],40*m[0])/2
        f1=2*.15*dirichlet.pdf(y[1,1:],40*m[1,1:])
        np.testing.assert_allclose(s,-np.log([f0,f1]),rtol=1e-13)

    def test_weighted_equals_pooled_without_shift(self):
        rng=np.random.default_rng(1)
        p=generate(rng,1000,3,'mixed'); c=generate(rng,499,3,'mixed')
        fitted=Calibrator.fit(p,c,scenario='mixed')
        np.testing.assert_allclose(fitted.thresholds['H-weight'],fitted.thresholds['H'])

    def test_structural_zeros_only(self):
        for sc in SCENARIOS:
            for k in [3,8,20]:
                d=generate(np.random.default_rng(44),500,k,sc)
                np.testing.assert_allclose(d['y'].sum(axis=1),1)
                self.assertTrue(np.array_equal((d['y']==0).any(axis=1),d['zero']))

    def test_candidate_stratum_membership(self):
        rng=np.random.default_rng(22)
        p=generate(rng,1000,3,'mixed'); c=generate(rng,499,3,'mixed')
        fitted=Calibrator.fit(p,c,scenario='mixed')
        fitted.thresholds['H-Z']=np.array([0.,np.inf])
        y=np.array([[0.,.4,.6],[.1,.4,.5]])
        m=np.repeat([[.2,.3,.5]],2,axis=0);g=np.zeros(2,dtype=int)
        hit=fitted.contains(m,y,g)['H-Z']
        np.testing.assert_array_equal(hit,[True,False])

if __name__=='__main__': unittest.main()
