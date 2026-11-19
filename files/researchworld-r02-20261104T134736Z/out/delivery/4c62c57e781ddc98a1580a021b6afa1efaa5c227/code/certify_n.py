"""Prop. 1(c): smallest calibration size n such that P(|V - (1-alpha)| <= eps) >= 1-delta, V ~ Beta(n+1-l, l),
l = floor((n+1)alpha); next to the normal approximation n ~ alpha(1-alpha) z_{1-delta/2}^2 / eps^2.
Also a simulation sanity check of one setting (split-conformal with continuous scores, i.i.d. uniform scores).
Output: results/tables/certify_n.csv"""
import numpy as np, pandas as pd
from scipy.stats import beta, norm


def prob_within(n, alpha, eps):
    l = int(np.floor((n + 1) * alpha))
    if l < 1:
        return 0.0
    a, b = n + 1 - l, l
    return beta.cdf(1 - alpha + eps, a, b) - beta.cdf(1 - alpha - eps, a, b)


def smallest_n(alpha, eps, delta, nmax=2_000_000):
    # prob_within is not monotone in n (floor effects): report the smallest n after which the condition holds for all n' up to 2*n
    n = max(int(np.ceil(1 / alpha)) - 1, 1)
    while n < nmax:
        if prob_within(n, alpha, eps) >= 1 - delta and all(prob_within(k, alpha, eps) >= 1 - delta for k in range(n, int(1.2 * n) + 5, max(1, n // 50))):
            return n
        n += 1 if n < 5000 else max(1, n // 200)
    return np.nan


rows = []
for alpha in (0.05, 0.1, 0.2):
    for eps in (0.01, 0.02, 0.05):
        delta = 0.05
        n = smallest_n(alpha, eps, delta)
        rows.append(dict(alpha=alpha, eps=eps, delta=delta, n_exact=n,
                         n_normal=alpha * (1 - alpha) * norm.ppf(1 - delta / 2) ** 2 / eps ** 2,
                         prob_at_n=prob_within(int(n), alpha, eps)))
out = pd.DataFrame(rows)
# simulation sanity check: alpha=0.1, n=n_exact(eps=0.02)
rng = np.random.default_rng(0)
n = int(out[(out.alpha == 0.1) & (out.eps == 0.02)].n_exact.iloc[0])
reps = 20000
S = rng.uniform(size=(reps, n))      # calibration scores, continuous exchangeable
k = int(np.ceil((n + 1) * 0.9))
q = np.sort(S, 1)[:, k - 1]
V = q                                 # P(score_test <= q | cal) = q for U(0,1) scores
emp = np.mean(np.abs(V - 0.9) <= 0.02)
out["sim_check"] = np.nan
out.loc[(out.alpha == 0.1) & (out.eps == 0.02), "sim_check"] = emp
out.to_csv("results/tables/certify_n.csv", index=False)
print(out.round(4).to_string()); print("sim check n=%d: %.4f (exact %.4f), reps=%d" % (n, emp, prob_within(n, 0.1, 0.02), reps))
