"""Calibration test: mocks WITH a boson of mass mu0 whose BH has been spun down to a_crit(211) (worst case);
fraction of mocks in which the method wrongly excludes mu0 at 95% should be <= 5%."""
import numpy as np, sr
rng = np.random.default_rng(3)
Nmock, ns = 1000, 1500
t = 3e6
res = []
for k in range(Nmock):
    Mt = rng.uniform(10, 20); al0 = rng.uniform(0.05, 0.45); mu0 = al0 / (sr.ALPHA_PER * Mt)
    at = 0.99                      # initial spin, then sequential spin-down through all active levels
    for _ in range(6):
        for (n, l, m) in sr.LEVELS:
            if sr.excluded(np.array([Mt]), np.array([at]), mu0, t_yr=t, levels=[(n, l, m)])[0]:
                at = min(at, sr.a_crit(al0, n, m))
    Mo = Mt + rng.normal(0, 1.5); ao = at + rng.normal(0, 0.05)   # observed point estimates
    M = rng.normal(Mo, 1.5, ns); a = rng.normal(ao, 0.05, ns)
    keep = (a < 1) & (a > 0) & (M > 1); M, a = M[keep], a[keep]
    L0 = 1 - sr.excluded(M, a, mu0, t_yr=t).mean()
    # control: boson 3 dex... a 'wrong' mass inside the same BH data (mu0*3) for power estimate
    L1 = 1 - sr.excluded(M, a, mu0 * 0.5, t_yr=t).mean()
    res.append((al0, L0, L1))
res = np.array(res); np.save('../outputs/mock_calibration.npy', res)
print('false exclusion rate at 95%:', (res[:, 1] < 0.05).mean(), ' at 68%:', (res[:, 1] < 0.32).mean())
print('exclusion of 0.5*mu0 (different boson):', (res[:, 2] < 0.05).mean())
