"""Estimators of the global average treatment effect (GATE).

All regression-based estimators follow the same recipe (Chin 2019): fit an outcome
model m(Z, exposures, x); predict every unit under the all-treated exposure
(z=1, f1=1, f2=1) and under the all-control exposure (z=0, f1=0, f2=0); return the
difference of the two averages. For linear models this is g'beta with
g = mean(x_all1) - mean(x_all0), so the variance is g' V g with V a sandwich
covariance estimate.

Estimators
  dim   : difference in means (no interference model; targets the direct effect)
  r1    : OLS on (1, z, x); the coefficient on z is the direct effect
  r2    : OLS on (1, z, f1, x)                 -- 1-hop exposure model
  r3    : OLS on (1, z, f1, f2, x)             -- 1-hop + 2-step exposure model
  r4    : OLS on (1, z, f1, f1^2, x)           -- quadratic 1-hop exposure model
  r5    : gradient-boosted trees on (z, f1, f2, x), predictions at the two extremes

SEs: HC1 (heteroskedasticity-robust, ignores dependence) and CR1 (cluster-robust,
clusters = Louvain communities, which are the randomisation clusters under GCR).
"""
import numpy as np
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor


def _design(z, f1, f2, x, spec):
    one = np.ones_like(z)
    if spec == "r1":
        return np.column_stack([one, z, x])
    if spec == "r2":
        return np.column_stack([one, z, f1, x])
    if spec == "r3":
        return np.column_stack([one, z, f1, f2, x])
    if spec == "r4":
        return np.column_stack([one, z, f1, f1**2, x])
    raise ValueError(spec)


def _sandwich(X, resid, labels=None, K=None):
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    if labels is None:
        meat = (X * resid[:, None] ** 2).T @ X * n / (n - k)
        df = n - k
    else:
        S = np.column_stack([np.bincount(labels, weights=X[:, j] * resid, minlength=K)
                             for j in range(k)])
        meat = S.T @ S * (K / (K - 1)) * (n - 1) / (n - k)
        df = K - 1
    return XtX_inv @ meat @ XtX_inv, df


def _linear(z, f1, f2, x, y, spec, labels, K):
    X = _design(z, f1, f2, x, spec)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ beta
    one, zero = np.ones_like(z), np.zeros_like(z)
    X1 = _design(one, one, one, x, spec)
    X0 = _design(zero, zero, zero, x, spec)
    g = X1.mean(0) - X0.mean(0)
    est = float(g @ beta)
    V_hc, df_hc = _sandwich(X, resid)
    V_cr, df_cr = _sandwich(X, resid, labels, K)
    return {
        "est": est,
        "se_hc1": float(np.sqrt(g @ V_hc @ g)), "df_hc1": df_hc,
        "se_cr1": float(np.sqrt(g @ V_cr @ g)), "df_cr1": df_cr,
    }


def dim(z, y):
    y1, y0 = y[z == 1], y[z == 0]
    n1, n0 = len(y1), len(y0)
    est = y1.mean() - y0.mean()
    se = np.sqrt(y1.var(ddof=1) / n1 + y0.var(ddof=1) / n0)
    return {"est": float(est), "se_hc1": float(se), "df_hc1": n1 + n0 - 2,
            "se_cr1": np.nan, "df_cr1": np.nan}


def gbm(z, f1, f2, x, y, seed):
    X = np.column_stack([z, f1, f2, x])
    model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05,
                                          max_leaf_nodes=31, random_state=seed)
    model.fit(X, y)
    one, zero = np.ones_like(z), np.zeros_like(z)
    p1 = model.predict(np.column_stack([one, one, one, x]))
    p0 = model.predict(np.column_stack([zero, zero, zero, x]))
    return {"est": float(p1.mean() - p0.mean()), "se_hc1": np.nan, "df_hc1": np.nan,
            "se_cr1": np.nan, "df_cr1": np.nan}


def all_estimators(z, f1, f2, x, y, labels, K, seed):
    out = {"dim": dim(z, y)}
    for spec in ["r1", "r2", "r3", "r4"]:
        out[spec] = _linear(z, f1, f2, x, y, spec, labels, K)
    out["r5"] = gbm(z, f1, f2, x, y, seed)
    return out


def ci(est, se, df):
    """Two-sided 95% interval using a t critical value with df degrees of freedom."""
    if not np.isfinite(se):
        return np.nan, np.nan
    t = stats.t.ppf(0.975, df)
    return est - t * se, est + t * se
