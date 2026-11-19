"""E1b: re-check of the n=2000 KS deviations with a 2e7-point test pool (shared-pool SE 6.7e-5 instead of 2e-4).
Same calibration seeds as exp1_calibration.py (n=2000, R=5000)."""
import numpy as np, pandas as pd
from scipy import stats
from ccp.geometry import SCORES
from ccp.synth import SynthProblem
from ccp.conformal import beta_params

ALPHA, R, n = 0.1, 5000, 2000
pr = SynthProblem(D=3, family="dirichlet", kappa=100, tau=1.5, seed=1)
rng = np.random.default_rng(12345)
chunks = {k: [] for k in SCORES}
for _ in range(10):                      # 10 x 2e6 = 2e7 test points
    _, mu, y = pr.sample(2_000_000, rng)
    for k, f in SCORES.items():
        chunks[k].append(f(y, mu).astype(np.float32))
St = {k: np.sort(np.concatenate(v)) for k, v in chunks.items()}
M = len(St["euclid"])
a, b = beta_params(n, ALPHA)
k_ = int(np.ceil((n + 1) * (1 - ALPHA)))
V = {k: [] for k in SCORES}
for r in range(R):
    rr = np.random.default_rng([1, n, r])
    _, mu_c, y_c = pr.sample(n, rr)
    for name, f in SCORES.items():
        q = np.sort(f(y_c, mu_c))[k_ - 1]
        V[name].append(np.searchsorted(St[name], np.float32(q), side="right") / M)
rows = []
for name in SCORES:
    v = np.array(V[name]); ks = stats.kstest(v, stats.beta(a, b).cdf)
    rows.append(dict(score=name, pool=M, mean=v.mean(), beta_mean=a / (a + b), sd=v.std(ddof=1), beta_sd=stats.beta(a, b).std(), ks_stat=ks.statistic, ks_p=ks.pvalue))
df = pd.DataFrame(rows); df.to_csv("/work/results/e1b_pool_check.csv", index=False); print(df.round(5))
