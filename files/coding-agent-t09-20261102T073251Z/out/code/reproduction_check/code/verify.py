"""Numerical and exhaustive checks of scientific identities, not outcome claims."""
import itertools,json
import numpy as np
import networkx as nx
from scipy import sparse
from study import weights,features,conditional_variance,ht_weights,peano_bound

def main():
    rng=np.random.default_rng(455)
    n=120;x=rng.normal(size=n);z=rng.binomial(1,.5,n).astype(float)
    g=nx.random_regular_graph(6,n,seed=9)
    A=sparse.csr_matrix(nx.to_scipy_sparse_array(g,nodelist=range(n),dtype=float))
    P=A/6;s=P@z;t=P@s
    evidence={}
    for model in ['OLS-L','OLS-Q','OLS-C','OLS-2H','Ridge-C']:
        X,c=features(z,s,t,x,model)
        X1,_=features(np.ones(n),np.ones(n),np.ones(n),x,model)
        X0,_=features(np.zeros(n),np.zeros(n),np.zeros(n),x,model)
        assert np.allclose((X1-X0).mean(axis=0),c)
        w,X,c,rank=weights(z,s,t,x,model)
        if model!='Ridge-C':
            assert np.allclose(X.T@w,c,atol=1e-9)
            beta=np.arange(X.shape[1])*.2
            assert abs(w@(X@beta)-c@beta)<1e-8
        evidence[model+'_norm2']=float(w@w)
    # Exact conditional bias/noise identity, including correlated Gaussian noise.
    w,X,c,_=weights(z,s,t,x,'OLS-L');groups=np.arange(n)//10
    sigma=.5;rho=.5;mu=1+.3*x+z+2*s**3
    var=conditional_variance(w,groups,sigma,rho)
    samples=[]
    for _ in range(30000):
        e=sigma*(np.sqrt(1-rho)*rng.normal(size=n)+np.sqrt(rho)*rng.normal(size=12)[groups])
        samples.append(w@e)
    empirical=float(np.var(samples,ddof=1));ratio=empirical/var
    assert abs(ratio-1)<.04
    evidence['noise_variance_empirical_over_exact']=ratio
    # Curvature sensitivity: h(s)=2s^3 has M=12. Secant residuals have zero endpoints.
    residual=2*s**3-2*s
    B=6*np.sum(abs(w)*s*(1-s))
    assert abs(w@residual)<=B+1e-10
    evidence['curvature_bias']=float(w@residual);evidence['curvature_bound']=float(B)
    integral,knots,K=peano_bound(w,s)
    grid=np.linspace(0,1,30001)
    Kgrid=np.sum(w[:,None]*np.maximum(s[:,None]-grid[None,:],0),axis=0)-(1-grid)
    assert abs(integral-np.trapezoid(abs(Kgrid),grid))<1e-6
    assert abs(w@residual)<=12*integral+1e-10
    assert 12*integral<=B+1e-10
    # Peano identity for cubic h: second derivative 12t.
    assert abs(w@residual-np.trapezoid(Kgrid*12*grid,grid))<1e-6
    evidence['sharp_curvature_bound']=12*integral
    # Enumerate all assignments on cycle(6): HT unbiased, in one-hop model.
    small=nx.cycle_graph(6)
    P=sparse.csr_matrix(nx.to_scipy_sparse_array(small,dtype=float))/2
    estimates=[]
    for zz in itertools.product([0.,1.],repeat=6):
        zz=np.array(zz);ss=P@zz;yy=1+zz+2*ss**3
        ww=ht_weights(zz,ss,P,np.arange(6),'bernoulli')
        estimates.append(float(ww@yy))
    assert abs(np.mean(estimates)-3)<1e-12
    evidence['enumerated_HT_mean']=float(np.mean(estimates))
    # A constant exposure column does not identify the endpoint contrast.
    assert weights(z,np.full(n,.5),np.full(n,.5),x,'OLS-L') is None
    print(json.dumps(evidence,indent=2))

if __name__=='__main__':main()
