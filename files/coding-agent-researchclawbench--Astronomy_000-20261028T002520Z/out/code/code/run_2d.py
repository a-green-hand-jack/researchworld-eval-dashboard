import numpy as np, sr
rng = np.random.default_rng(2)
cfg = {'M33_X-7': dict(t=3e6, mu=np.logspace(-13.3, -11.0, 100), nsub=None),
       'IRAS_09149-6206': dict(t=4.5e7, mu=np.logspace(-20.4, -18.2, 100), nsub=3000)}
logf = np.linspace(14, 28, 85)   # log10(f/eV)  (f/GeV = 1e5..1e19)
for name, c in cfg.items():
    d = np.loadtxt(f'../data/{name}_samples.dat')
    if c['nsub']: d = d[rng.choice(len(d), c['nsub'], replace=False)]
    M, a = d.T
    res = {}
    for key, kw in [('base', {}), ('cbn0.1', dict(cbn=0.1)), ('cbn10', dict(cbn=10.0))]:
        L = np.zeros((len(logf), len(c['mu'])))
        for i, lf in enumerate(logf):
            L[i] = sr.likelihood(M, a, c['mu'], f=10**lf, t_yr=c['t'], **kw)
        res['L_' + key] = L
    np.savez(f'../outputs/L2d_{name}.npz', mu=c['mu'], logf=logf, **res)
    print(name, 'done', {k: (v < 0.05).sum() for k, v in res.items()})
