"""Frozen generators; gold labels in unlabeled pool are NEVER drawn or used."""
from pathlib import Path
import numpy as np


def conditional_mean(name, z):
    if name == 'linear':
        return .1+.8*z
    if name == 'nonlinear':
        return .05+.9*((z<.25)|(z>=.75))
    if name == 'anticorrelated':
        return .9-.8*z
    if name == 'uninformative':
        return np.full_like(z,.5)
    if name == 'rare':
        return .002+.04*(z>=.9)
    raise ValueError(name)


def truth(name):
    return .006 if name=='rare' else .5


def draw(name,n,N,rng,root):
    if name in ['galaxies','forest']:
        d = np.load(Path(root)/'data'/f'{name}.npz')
        y,z=d['Y'],d['Yhat']
        il=rng.integers(0,len(y),n)
        iu=rng.integers(0,len(y),N)
        return y[il],z[il],z[iu],float(y.mean()),None
    base = 'nonlinear' if name=='shift' else name
    z = rng.uniform(size=n)
    u = rng.beta(2,5,size=N) if name=='shift' else rng.uniform(size=N)
    p=conditional_mean(base,z)
    y=rng.binomial(1,p).astype(float)
    oracle=lambda x:conditional_mean(base,x)
    # shift stress tests original labeled-population mean; this violates iid matching.
    return y,z,u,truth(base),oracle


def oracle_variances(name,n,N):
    """Analytic, not empirical. Returned values are diagnostic reference curves."""
    a=N/(N+n)
    th=truth(name)
    vy=th*(1-th)
    if name in ['linear','anticorrelated']:
        vm=.8**2/12
        linear=vm
    elif name=='nonlinear':
        vm=.9**2*.25
        linear=0.
    elif name=='uninformative':
        vm=linear=0.
    elif name=='rare':
        vm=.04**2*.1*.9
        cov=.04*.045
        linear=cov**2/(1/12)
    else: raise ValueError(name)
    return {'theta':th,'v_label':vy/n,'v_affine':(vy-a*linear)/n,
            'v_oracle':(vy-a*vm)/n,'nonlinear_gap':a*(vm-linear)/n}
