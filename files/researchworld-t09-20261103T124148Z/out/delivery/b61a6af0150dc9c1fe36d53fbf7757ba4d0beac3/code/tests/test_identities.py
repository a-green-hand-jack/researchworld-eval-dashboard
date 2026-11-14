"""Scientific checks: estimand, exact variance, and full-exposure weighting."""
import unittest
import numpy as np
from gatebench.core import (Graph, exposure, features, assignment, outcome_mean, true_gate, noise_operator,
                            contrast_weights, exposure_probabilities, full_exposure_estimates, regression)
from gatebench.graphs import synthetic
from gatebench.ht_risk import exact_ht_risk

class Identities(unittest.TestCase):
    def test_rational_exposure_boundaries_include_threshold_and_exclude_tail(self):
        from scipy import sparse
        for degree, treated, boundary in [(80,60,.75),(20,17,.85)]:
            adjacency=sparse.lil_matrix((degree+2,degree+2))
            adjacency[0,1:degree+1]=1;adjacency[1:degree+1,0]=1
            g=Graph('boundary',adjacency.tocsr(),np.zeros(degree+2),np.arange(degree+2))
            z=np.zeros(g.n);z[1:treated+1]=1;z[-1]=1
            s,_=exposure(g,z)
            self.assertEqual(s[0],boundary)
            self.assertEqual(s[-1],1.)  # isolate convention
            if boundary==.75:
                self.assertEqual(features(g,z,'threshold_oracle')[0,-1],1.)
                self.assertEqual(outcome_mean(g,z,'threshold')[0],1.)
            else:
                self.assertFalse(s[0]>.85)
                self.assertEqual(outcome_mean(g,z,'hidden_tail')[0],outcome_mean(g,z,'linear')[0])

    def test_linear_identity(self):
        g = synthetic("regular", 120, 6, seed=8)
        rng = np.random.default_rng(30)
        z = assignment(g, rng)
        x,c,inv,a,*_ = contrast_weights(g,z,"linear")
        m = outcome_mean(g,z,"linear")
        self.assertAlmostEqual(a@m,true_gate(g,"linear"),places=10)
        self.assertTrue(np.allclose(a@x,c))
        b = noise_operator(g,.8)
        analytic = np.sum((b.T@a)**2)
        # Direct dense covariance provides an independent algebraic check.
        self.assertAlmostEqual(analytic, a@(b@b.T)@a, places=12)

    def test_endpoint_targets(self):
        g = synthetic("er", 100, 4, seed=5)
        for mechanism in ("linear","quadratic","cubic","sigmoid","threshold","twohop"):
            self.assertAlmostEqual(true_gate(g,mechanism),2.)
        self.assertAlmostEqual(true_gate(g,"hidden_tail"),3.)

    def test_ht_by_enumeration(self):
        g = synthetic("regular", 8, 2, seed=2, cluster_size=3)
        for design in ("bernoulli","cluster"):
            k = g.n if design=="bernoulli" else g.clusters.max()+1
            probs = exposure_probabilities(g,design)
            values=[]
            for code in range(2**k):
                bits = ((code>>np.arange(k))&1).astype(float)
                z = bits if design=="bernoulli" else bits[g.clusters]
                y = outcome_mean(g,z,"quadratic")
                values.append(full_exposure_estimates(g,z,y,probs)["ht"])
            self.assertAlmostEqual(np.mean(values),true_gate(g,"quadratic"),places=10)

    def test_complement_symmetry_and_rank_failure(self):
        g=synthetic("regular",200,12,seed=9)
        z=assignment(g,np.random.default_rng(20))
        estimates=[]
        for zz in (z,1-z):
            a=contrast_weights(g,zz,"linear")[3]
            estimates.append(a@outcome_mean(g,zz,"quadratic"))
        self.assertAlmostEqual(np.mean(estimates),true_gate(g,"quadratic"),places=10)
        failed=contrast_weights(g,np.zeros(g.n),"linear")
        self.assertGreater(failed[6],.1)
        m=outcome_mean(g,z,"no_interference")
        a=contrast_weights(g,z,"linear")[3]
        self.assertAlmostEqual(a@m,1.,places=10)

    def test_naive_mean_difference_and_empty_arm(self):
        g=synthetic("regular",120,6,seed=8)
        z=assignment(g,np.random.default_rng(30))
        y=outcome_mean(g,z,"linear")
        b=noise_operator(g)
        answer=regression(g,z,y,y,true_gate(g,"linear"),b,"naive")
        self.assertAlmostEqual(answer["estimate"],y[z==1].mean()-y[z==0].mean(),places=10)
        empty=regression(g,np.zeros(g.n),y,y,2.,b,"naive")
        self.assertFalse(empty['valid'])
        self.assertTrue(np.isnan(empty['estimate']))

    def test_hidden_tail_coupling(self):
        g=synthetic("regular",200,80,seed=9)
        z=assignment(g,np.random.default_rng(22))
        self.assertLessEqual(np.max(g.transition@z),.85)
        m1=outcome_mean(g,z,"linear")
        m2=outcome_mean(g,z,"hidden_tail")
        self.assertTrue(np.array_equal(m1,m2))
        self.assertAlmostEqual(true_gate(g,"hidden_tail")-true_gate(g,"linear"),1.)
        for model in ['linear','quadratic','cubic','spline']:
            a=contrast_weights(g,z,model)[3]
            self.assertEqual(a@m1,a@m2)

    def test_ht_risk_by_enumeration(self):
        g=synthetic("regular",8,2,seed=2,cluster_size=3)
        b=noise_operator(g,.8)
        for design in ("bernoulli","cluster"):
            k=g.n if design=="bernoulli" else g.clusters.max()+1
            probs=exposure_probabilities(g,design,.3)
            total=0.
            for code in range(2**k):
                bits=((code>>np.arange(k))&1).astype(float)
                z=bits if design=="bernoulli" else bits[g.clusters]
                s=g.adjacency
                t=(z==1)&(s@(1-z)==0)
                c=(z==0)&(s@z==0)
                weights=(t/probs[0]-c/probs[1])/g.n
                mean=outcome_mean(g,z,"quadratic")
                conditional_mse=(weights@mean-true_gate(g,"quadratic"))**2+np.sum((b.T@weights)**2)
                total+=.3**bits.sum()*.7**(k-bits.sum())*conditional_mse
            exact=exact_ht_risk(g,design,.3,b,"quadratic")["ht_exact_variance"]
            self.assertAlmostEqual(total,exact,places=9)

    def test_polynomial_misspecification_is_detected(self):
        g = synthetic("regular", 200, 12, seed=9)
        z = assignment(g,np.random.default_rng(20))
        m = outcome_mean(g,z,"quadratic")
        a_linear=contrast_weights(g,z,"linear")[3]
        a_quad=contrast_weights(g,z,"quadratic")[3]
        self.assertGreater(abs(a_linear@m-2),1e-5)
        self.assertAlmostEqual(a_quad@m,2,places=10)

if __name__ == "__main__":
    unittest.main()
