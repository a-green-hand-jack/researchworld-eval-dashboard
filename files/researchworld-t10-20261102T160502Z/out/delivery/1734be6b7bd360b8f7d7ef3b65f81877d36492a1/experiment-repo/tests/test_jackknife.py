"""ppi_jackknife (vectorised delete-one) == naive loop; cross-fit calibrated estimator unbiased on a known synthetic law."""
import sys, numpy as np
sys.path.insert(0, "src")
import estimators as E, data as D
from scipy.stats import t as tdist

rng = np.random.default_rng(3)
s, th, _ = D.synth_sampler("tanh", 0.5, 1.0)
Y, f = s(rng, 60); _, fu = s(rng, 600)
n, N = len(Y), len(fu)


def est(Yv, fv):
    m = len(Yv); sall = np.concatenate([fv, fu]); v = sall.var()
    lam = np.clip(np.mean((Yv - Yv.mean()) * (fv - fv.mean())) / ((1 + m / N) * v), 0, 1)
    return Yv.mean() - lam * fv.mean() + lam * fu.mean(), lam

e_i = np.array([est(np.delete(Y, i), np.delete(f, i))[0] for i in range(n)])
e, lam = est(Y, f)
var = (n - 1) / n * np.sum((e_i - e_i.mean()) ** 2) + lam ** 2 * fu.var(ddof=1) / N
q = tdist.ppf(0.975, n - 1)
lo, hi = E.ppi_jackknife(Y, f, fu)
assert abs(lo - (e - q * np.sqrt(var))) < 1e-10 and abs(hi - (e + q * np.sqrt(var))) < 1e-10
# unbiasedness of cross-fitted calibrated point estimate (est = midpoint of interval)
mids = []
for _ in range(400):
    Yb, fb = s(rng, 100); _, fub = s(rng, 2000)
    lo, hi = E.cal_ppi(Yb, fb, fub, "iso", rng=rng); mids.append((lo + hi) / 2)
se = np.std(mids) / np.sqrt(400)
assert abs(np.mean(mids) - th) < 4 * se, (np.mean(mids), se)
print("ok")
