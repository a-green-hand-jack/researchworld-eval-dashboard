"""Small exact-enumeration and decoding checks for the research implementation."""
import itertools, unittest
import numpy as np
from scipy.stats import binom
from analyze import cp_table,paired_p
from infer import make_prompt,configurations

class CoreTests(unittest.TestCase):
    def test_exact_interval_coverage(self):
        n=32;lo,hi=cp_table(n);s=np.arange(n+1)
        for p in np.linspace(0,1,201):
            coverage=np.sum(binom.pmf(s,n,p)*((lo<=p)&(p<=hi)))
            self.assertGreaterEqual(coverage,.95-1e-12)
        self.assertAlmostEqual(hi[0],1-.025**(1/n))

    def test_selected_simultaneous_exact_enumeration(self):
        n=6;mu=[.3,.4];lo,hi=cp_table(n,.05/2);coverage=0
        for a,b in itertools.product(range(n+1),repeat=2):
            prob=binom.pmf(a,n,mu[0])*binom.pmf(b,n,mu[1])
            js=[0] if a>b else ([1] if b>a else [0,1])
            coverage+=prob*np.mean([lo[[a,b][j]]<=mu[j]<=hi[[a,b][j]] for j in js])
        self.assertGreaterEqual(coverage,.95)

    def test_paired_exact_p(self):
        self.assertEqual(paired_p(0,0),1)
        self.assertAlmostEqual(paired_p(5,0),1/32)

    def test_rotation_and_gold_exclusion(self):
        q=dict(question='What is two plus two?',options=['3','4','5','6'],answer_index=1,cot_content='SECRET_GOLD')
        for c in configurations():
            prompt,order=make_prompt(q,c)
            self.assertEqual(q['options'][order[order.index(1)]],'4')
            self.assertNotIn('SECRET_GOLD',prompt)
            self.assertEqual(sorted(order),list(range(4)))
        for m in range(3,11):
            q['options']=[str(x) for x in range(m)]
            for c in configurations():
                _,order=make_prompt(q,c)
                self.assertEqual(sorted(order),list(range(m)))

if __name__=='__main__':unittest.main()
