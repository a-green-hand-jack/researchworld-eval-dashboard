"""Core estimators and data loaders for the fixed-budget prediction-powered CI study.

Setting: labeled sample (X_i, Y_i), i=1..n; unlabeled sample X~_j, j=1..N; fixed predictor f.
Target: mu = E[Y].  All CIs are Wald intervals  est +/- z_{1-alpha/2} * sqrt(var).

Notation used in the code:
  a = n / (n + N)            labeled fraction of the pooled sample
  Z                          information available to the estimator: f(X) alone, or (f(X), X)
  m-hat                      a (possibly cross-fitted) calibrator of Y on Z
"""
import numpy as np
from scipy.stats import norm
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

ALPHA = 0.05
Z_CRIT = norm.ppf(1 - ALPHA / 2)


def wald(est, var, z=Z_CRIT):
    h = z * np.sqrt(var)
    return est, est - h, est + h, 2 * h


# ----------------------------------------------------------------------------
# Baselines (as in the cited literature)
# ----------------------------------------------------------------------------

def classical(Y_L, **_):
    """Labeled-only sample mean (ignores predictor and unlabeled data)."""
    n = len(Y_L)
    return Y_L.mean(), Y_L.var(ddof=1) / n


def ppi(Y_L, f_L, f_U, **_):
    """PPI with lambda = 1 (Angelopoulos et al., 2023)."""
    n, N = len(Y_L), len(f_U)
    r = Y_L - f_L
    est = f_U.mean() + r.mean()
    var = f_U.var(ddof=1) / N + r.var(ddof=1) / n
    return est, var


def ppi_pp(Y_L, f_L, f_U, **_):
    """PPI++ with plug-in optimal lambda (Angelopoulos, Duchi, Zrnic, 2023).

    lambda* = Cov(Y,f) / (Var(f) (1 + n/N)); estimator mean_L(Y - lam f) + lam mean_U(f).
    Equivalent to the linear-calibrator form of Section 'Pooled linear calibration' in the paper.
    """
    n, N = len(Y_L), len(f_U)
    cov = np.cov(Y_L, f_L, ddof=1)[0, 1]
    lam = cov / (f_L.var(ddof=1) * (1 + n / N))
    r = Y_L - lam * f_L
    est = lam * f_U.mean() + r.mean()
    var = r.var(ddof=1) / n + lam**2 * f_U.var(ddof=1) / N
    return est, var


def ppi_linear(Y_L, Z_L, Z_U, **_):
    """PPI++ with a linear calibrator on a multi-column Z (e.g. Z = (f, X)); in-sample OLS.

    This is the multiple-control-variate version of PPI++.  With Z = f it coincides with ppi_pp.
    """
    n, N = len(Y_L), len(Z_U)
    a = n / (n + N)
    Zl = Z_L.reshape(n, -1)
    Zu = Z_U.reshape(N, -1)
    lr = LinearRegression().fit(Zl, Y_L)
    beta = lr.coef_
    # estimator: mean_L(Y - (1-a) Z beta) + (1-a) mean_U(Z beta)   (intercept cancels)
    rL = Y_L - (1 - a) * (Zl @ beta)
    est = rL.mean() + (1 - a) * (Zu @ beta).mean()
    var = rL.var(ddof=1) / n + (1 - a) ** 2 * np.var(Zu @ beta, ddof=1) / N
    return est, var


def sppi(Y_L, f_L, f_U, K=5, **_):
    """Stratified PPI (lambda=1 within strata) with quantile strata of the prediction.

    Strata are quantile bins of the pooled predictions.  Within stratum k, the PPI estimate
    is mean_{U,k}(f) + mean_{L,k}(Y - f); the stratum weights are the unlabeled proportions.
    Summing over strata gives mean_U(f + rbar_{b(f)}), i.e. a PPI estimator with the
    piecewise-constant calibrator f + rbar_b.  Its linearisation (which accounts for the
    randomness of the estimated stratum weights) gives
        var = Var_U(f + rbar_b) / N + Var_L(Y - f - rbar_b) / n.
    Strata with fewer than 2 labeled points use the pooled residual mean.
    """
    n, N = len(Y_L), len(f_U)
    pooled = np.concatenate([f_L, f_U])
    edges = np.quantile(pooled, np.linspace(0, 1, K + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    bL = np.clip(np.searchsorted(edges, f_L, side="right") - 1, 0, K - 1)
    bU = np.clip(np.searchsorted(edges, f_U, side="right") - 1, 0, K - 1)
    r = Y_L - f_L
    rbar = np.full(K, r.mean())
    for k in range(K):
        sel = bL == k
        if sel.sum() >= 2:
            rbar[k] = r[sel].mean()
    cal_U = f_U + rbar[bU]
    cal_L = r - rbar[bL]
    est = cal_U.mean()
    var = cal_U.var(ddof=1) / N + cal_L.var(ddof=1) / n
    return est, var


# ----------------------------------------------------------------------------
# Proposed: cross-fitted pooled calibration with a flexible learner
# ----------------------------------------------------------------------------

def make_learner(kind, seed=0):
    if kind == "linear":
        return LinearRegression()
    if kind == "hgb":
        return HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=200,
                                             min_samples_leaf=10, random_state=seed)
    if kind == "hgb_shallow":
        return HistGradientBoostingRegressor(max_depth=2, learning_rate=0.05, max_iter=150,
                                             min_samples_leaf=10, random_state=seed)
    if kind == "spline":
        return make_pipeline(StandardScaler(), SplineTransformer(degree=3, n_knots=5),
                             Ridge(alpha=1.0))
    raise ValueError(kind)


def cf_ppi(Y_L, Z_L, Z_U, learner="hgb", K=5, seed=0, **_):
    """Cross-fitted pooled calibration (proposed).

    m-hat is fitted on K-1 folds of the labeled data and evaluated on the held-out fold
    (out-of-fold values m_L).  Unlabeled values use the average of the K fold models (m_U).

        est = mean_L(Y) + (1-a) * (mean_U(m_U) - mean_L(m_L))
        var = Var_L(Y - (1-a) m_L) / n + (1-a)^2 Var_U(m_U) / N

    Unbiased for every fixed learner under cross-fitting (E m_L = E m_U); the variance formula is
    the PPI++ formula with the linear calibrator replaced by the learned one.
    """
    n, N = len(Y_L), len(Z_U)
    a = n / (n + N)
    Zl = Z_L.reshape(n, -1)
    Zu = Z_U.reshape(N, -1)
    rng = np.random.default_rng(seed)
    folds = rng.permutation(n) % K
    mL = np.empty(n)
    mU = np.zeros(N)
    for k in range(K):
        tr, te = folds != k, folds == k
        g = make_learner(learner, seed=seed + k)
        g.fit(Zl[tr], Y_L[tr])
        mL[te] = g.predict(Zl[te])
        mU += g.predict(Zu) / K
    est = Y_L.mean() + (1 - a) * (mU.mean() - mL.mean())
    var = np.var(Y_L - (1 - a) * mL, ddof=1) / n + (1 - a) ** 2 * np.var(mU, ddof=1) / N
    return est, var


METHODS_F_ONLY = ["classical", "ppi", "ppi_pp", "sppi", "cf_hgb", "cf_linear", "cf_spline"]
METHODS_WITH_X = ["ppi_linear_X", "cf_hgb_X", "cf_linear_X", "cf_spline_X"]


def run_all(Y_L, f_L, f_U, X_L=None, X_U=None, methods=None, seed=0):
    """Return dict method -> (est, lo, hi, width). X_* are optional covariate matrices."""
    out = {}
    fo = {
        "classical": lambda: classical(Y_L),
        "ppi": lambda: ppi(Y_L, f_L, f_U),
        "ppi_pp": lambda: ppi_pp(Y_L, f_L, f_U),
        "sppi": lambda: sppi(Y_L, f_L, f_U),
        "cf_hgb": lambda: cf_ppi(Y_L, f_L, f_U, learner="hgb", seed=seed),
        "cf_linear": lambda: cf_ppi(Y_L, f_L, f_U, learner="linear", seed=seed),
        "cf_spline": lambda: cf_ppi(Y_L, f_L, f_U, learner="spline", seed=seed),
    }
    if X_L is not None:
        ZL = np.column_stack([f_L, X_L])
        ZU = np.column_stack([f_U, X_U])
        fo.update({
            "ppi_linear_X": lambda: ppi_linear(Y_L, ZL, ZU),
            "cf_hgb_X": lambda: cf_ppi(Y_L, ZL, ZU, learner="hgb", seed=seed),
            "cf_linear_X": lambda: cf_ppi(Y_L, ZL, ZU, learner="linear", seed=seed),
            "cf_spline_X": lambda: cf_ppi(Y_L, ZL, ZU, learner="spline", seed=seed),
        })
    for name, fn in fo.items():
        if methods is not None and name not in methods:
            continue
        est, var = fn()
        out[name] = wald(est, var)
    return out


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------

PPI_DIR = "/work/data/"


def load_real(name, feature_mode="f"):
    """Return (Y, f, X) for a pool with full labels.  feature_mode 'f' -> X None; 'fX' -> covariates.

    Only pools where every unit has a label and a prediction are used (see README).
    Constant covariate columns are dropped.
    """
    from ppi_py.datasets import load_dataset

    d = load_dataset(PPI_DIR, name)
    Y = d["Y"].astype(float)
    f = d["Yhat"].astype(float)
    X = None
    if feature_mode == "fX":
        if "X" in d.files:
            X = d["X"].astype(float)
        elif name == "alphafold":
            X = np.column_stack([d["phosphorylated"], d["ubiquitinated"], d["acetylated"]]).astype(float)
        else:
            raise ValueError(f"no covariates for {name}")
        keep = X.std(axis=0) > 0
        X = X[:, keep]
    return Y, f, X
