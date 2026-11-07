import numpy as np
from sklearn.ensemble import RandomForestRegressor


def conf_quantile(s, alpha):
    """Split-conformal threshold: ceil((n+1)(1-alpha))-th smallest score; inf if rank > n."""
    n = len(s)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    return np.inf if k > n else np.sort(s)[k - 1]


class SigmaModel:
    """Local-scale estimator sigma(x): RF on log-scores from a held-out split (multi-output across scores)."""

    def __init__(self, seed=0):
        self.m = RandomForestRegressor(n_estimators=60, min_samples_leaf=15, n_jobs=1, random_state=seed)

    def fit(self, F, S):  # S (n, k) positive scores
        self.m.fit(F, np.log(S + 1e-6))
        return self

    def predict(self, F):
        return np.exp(self.m.predict(F))


def conformal_sets_coverage(s_cal, s_test, alphas):
    return {a: (s_test <= conf_quantile(s_cal, a)) for a in alphas}
