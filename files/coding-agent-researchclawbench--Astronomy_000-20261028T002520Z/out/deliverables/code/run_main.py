import numpy as np, json, sr
rng = np.random.default_rng(1)
sys_ = {
 'M33_X-7': dict(file='../data/M33_X-7_samples.dat', t=3e6, mu=np.logspace(-14.0, -11.0, 400)),
 'IRAS_09149-6206': dict(file='../data/IRAS_09149-6206_samples.dat', t=4.5e7, mu=np.logspace(-21.7, -18.0, 400)),
}
res = {}
for name, s in sys_.items():
    d = np.loadtxt(s['file']); M, a = d[:, 0], d[:, 1]
    mu = s['mu']
    out = {'mu': mu}
    out['L_base'] = sr.likelihood(M, a, mu, t_yr=s['t'])
    out['L_marg'] = sr.likelihood(M, a, mu, t_yr=s['t'], sigma_dex=0.5, nquad=7)
    for lab, fac in [('t/10', 0.1), ('t*10', 10)]:
        out['L_' + lab] = sr.likelihood(M, a, mu, t_yr=s['t'] * fac)
    out['L_211only'] = sr.likelihood(M, a, mu, t_yr=s['t'], levels=[(2, 1, 1)])
    out['L_amax0.5'] = sr.likelihood(M, a, mu, t_yr=s['t'], alpha_max=0.5)
    out['L_t_hubble'] = sr.likelihood(M, a, mu, t_yr=1.0e9)
    np.savez(f'../outputs/L1d_{name}.npz', **out)
    for k in out:
        if k != 'mu':
            print(name, k, [(f'{lo:.3g}', f'{hi:.3g}') for lo, hi in sr.limits(mu, out[k], 0.05)])
