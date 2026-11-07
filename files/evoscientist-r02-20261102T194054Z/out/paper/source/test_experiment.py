import unittest
import numpy as np
import experiment as e

class Correctness(unittest.TestCase):
    def test_quantile_rank(self):
        a=np.arange(499.)
        self.assertEqual(e.quantile(a),449.)
        self.assertTrue(np.isinf(e.quantile(np.arange(8.))))
        self.assertTrue(np.isinf(e.quantile(np.empty(0))))
        self.assertEqual(e.quantile(a,.1/10),494.)
    def test_weighted_atom(self):
        a=np.arange(499.); w=np.ones(499)
        self.assertEqual(e.weighted_quantile(a,w,1),e.quantile(a))
        self.assertTrue(np.isinf(e.weighted_quantile(a,w,10000)))
        # Equality: test atom == alpha is finite (not infinite).
        self.assertEqual(e.weighted_quantile(np.arange(9.),np.ones(9),1),8.)
    def test_weighted_empty(self):
        self.assertTrue(np.isinf(e.weighted_quantile([],[],1.0)))
    def test_generator(self):
        for law in ['interior','zeros']:
            for k in [3,5,10]:
                x,y,b,mu=e.generate(2000,k,law,.2,e.rng(999990,k,law,0))
                self.assertTrue(np.all(y>=0)); np.testing.assert_allclose(y.sum(1),1,atol=1e-12)
                np.testing.assert_array_equal(y[:,-1]==0,b)
                if law=='zeros': self.assertLess(abs(b.mean()-.35),.05)
                else: self.assertTrue(np.all(y>0))
    def test_geometry(self):
        r=np.random.default_rng(7); y=r.dirichlet(np.ones(5),1000); f=r.dirichlet(np.ones(5),1000)
        s=e.scores(y,f)
        np.testing.assert_allclose(2*s['TV'],np.abs(y-f).sum(1),atol=1e-15)
        q=e.quantile(s['TV']); q_l1=e.quantile(np.abs(y-f).sum(1))
        np.testing.assert_array_equal(s['TV']<=q,np.abs(y-f).sum(1)<=q_l1)
        self.assertTrue(np.all(s['Hellinger']<=1+1e-14))
        yy=np.eye(5); ff=np.full((5,5),.2)
        self.assertTrue(all(np.isfinite(v).all() for v in e.scores(yy,ff).values()))
    def test_predictor_and_membership(self):
        r=np.random.default_rng(22); x,y,b,_=e.generate(150,5,'zeros',.2,r)
        beta,sigma=e.fit_scale(x,y,r); f=e.predict(beta,x)
        self.assertTrue((f>0).all()); np.testing.assert_allclose(f.sum(1),1)
        q,_=e.calibrate(y,f,x[:,2].astype(int),sigma)
        mem=e.membership(y,f,x[:,2].astype(int),q,sigma)
        for key in q: q[key]=np.full_like(np.asarray(q[key]),np.inf,dtype=float)
        self.assertTrue(e.membership(y,f,x[:,2].astype(int),q,sigma).all())
        for key in q: q[key]=np.full_like(np.asarray(q[key]),-1.,dtype=float)
        self.assertFalse(e.membership(y,f,x[:,2].astype(int),q,sigma).any())
    def test_closed_geometry_control(self):
        r=np.random.default_rng(9)
        for k in [3,5,10]:
            y=r.dirichlet(np.ones(k),10000); a=y[:,-1]>=.5; union=a|(y[:,-1]==0)
            np.testing.assert_array_equal(a,union)
            z=np.column_stack([r.dirichlet(np.ones(k-1),10000),np.zeros(10000)])
            self.assertFalse((z[:,-1]>=.5).any()); self.assertTrue((z[:,-1]==0).all())

if __name__=='__main__': unittest.main(verbosity=2)
