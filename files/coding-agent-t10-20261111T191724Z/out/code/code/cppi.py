"""Cross-fitted recalibrated prediction-powered intervals for a population mean (1-D predictor output f).

theta_hat = mean_{lab}(Y - ghat(f)) + mean_{all}(ghat(f)),   ghat ~ E[Y | f] fitted on labeled data with K-fold cross-fitting.
Variance: var_lab(Y - ghat)/n + var_all(ghat)/(n+N).   (Efficient-influence-function plug-in under MCAR labeling.)
"""
import numpy as np
from scipy import stats
from sklearn.isotonic import IsotonicRegression
from sklearn.preprocessing import SplineTransformer

# ---------- 1-D learners: each takes (f_train, y_train) and returns a callable ----------
def _const(f, y):
    m = y.mean(); return lambda x: np.full(len(x), m)

def _lin(f, y):
    fm, ym = f.mean(), y.mean(); v = ((f - fm) ** 2).sum()
    b = ((f - fm) * (y - ym)).sum() / v if v > 0 else 0.0
    return lambda x: ym + b * (x - fm)

def _iso(f, y):
    r = IsotonicRegression(increasing=True, out_of_bounds='clip').fit(f, y)
    return r.predict

def _bin(K):
    def fit(f, y):
        q = np.unique(np.quantile(f, np.linspace(0, 1, K + 1)[1:-1]))
        idx = np.searchsorted(q, f, side='right'); nb = len(q) + 1
        s = np.bincount(idx, weights=y, minlength=nb); c = np.bincount(idx, minlength=nb)
        gm = y.mean(); g = np.where(c > 0, s / np.maximum(c, 1), gm)
        return lambda x: g[np.searchsorted(q, x, side='right')]
    return fit

def _spl(f, y, n_knots=4):
    # cubic regression spline (linear extrapolation), ~ n_knots+2 degrees of freedom
    st = SplineTransformer(n_knots=n_knots, degree=3, knots='quantile', extrapolation='linear')
    B = st.fit_transform(f[:, None]); B1 = np.c_[np.ones(len(f)), B]
    coef = np.linalg.lstsq(B1, y, rcond=None)[0]
    return lambda x: np.c_[np.ones(len(x)), st.transform(x[:, None])] @ coef

BASE = {'const': _const, 'lin': _lin, 'iso': _iso, 'bin10': _bin(10), 'spl': _spl}
AUTO_CANDS = ['lin', 'iso', 'spl']

def _cv_mse(fit, f, y, K, rng):
    n = len(y); folds = rng.permutation(n) % K; err = 0.0
    for k in range(K):
        tr, te = folds != k, folds == k
        err += ((y[te] - fit(f[tr], y[tr])(f[te])) ** 2).sum()
    return err / n

def _auto(f, y, rng=None):
    """Select among linear / isotonic / spline by inner-CV MSE (ties broken toward the simpler model)."""
    rng = np.random.default_rng(0) if rng is None else rng
    if len(y) < 20: return _lin(f, y)
    mses = [_cv_mse(BASE[c], f, y, 4, rng) for c in AUTO_CANDS]
    return BASE[AUTO_CANDS[int(np.argmin(mses))]](f, y)

def get_learner(kind, rng=None):
    if kind == 'auto': return lambda f, y: _auto(f, y, rng)
    return BASE[kind]

# ---------- main estimator ----------
def crossfit_mean(Y, f_lab, f_unl, kind='iso', K=5, rng=None, ghat_fn=None):
    """Returns (theta_hat, se). Y: labeled outcomes; f_lab/f_unl: predictor outputs on labeled / unlabeled sets."""
    rng = np.random.default_rng() if rng is None else rng
    n, N = len(Y), len(f_unl); m = n + N
    fit = get_learner(kind, rng)
    folds = rng.permutation(n) % K
    g_lab = np.empty(n); g_unl = np.zeros(N)
    for k in range(K):
        tr, te = folds != k, folds == k
        fn = fit(f_lab[tr], Y[tr])
        g_lab[te] = fn(f_lab[te])
        if N: g_unl += fn(f_unl) / K
    res = Y - g_lab; gall = np.r_[g_lab, g_unl]
    theta = res.mean() + gall.mean()
    var = res.var(ddof=1) / n + gall.var(ddof=1) / m
    return theta, np.sqrt(var)

def ci_from(theta, se, alpha=0.05, df=None):
    q = stats.norm.ppf(1 - alpha / 2) if df is None else stats.t.ppf(1 - alpha / 2, df)
    return theta - q * se, theta + q * se

# ---------- baselines ----------
def classical_ci(Y, alpha=0.05):
    return ci_from(Y.mean(), Y.std(ddof=1) / np.sqrt(len(Y)), alpha)

def ppi_lam_ci(Y, f_lab, f_unl, lam, alpha=0.05):
    """PPI / PPI++ interval with fixed lam (matches ppi_py.ppi_mean_ci(lam=...))."""
    n, N = len(Y), len(f_unl)
    th = (lam * f_unl).mean() + (Y - lam * f_lab).mean()
    se = np.sqrt((lam * f_unl).std() ** 2 / N + (Y - lam * f_lab).std() ** 2 / n)
    return ci_from(th, se, alpha)

def ppi_pp_unclipped_ci(Y, f_lab, f_unl, alpha=0.05):
    """PPI++ power-tuned interval with the *unclipped* plug-in lambda = cov_lab(Y,f) / ((1+n/N) var_pooled(f)).
    (ppi_py clips lambda to [0,1]; this variant does not.)"""
    n, N = len(Y), len(f_unl)
    c = np.cov(Y, f_lab)[0, 1]; vf = np.concatenate([f_lab, f_unl]).var(ddof=1)
    lam = c / ((1 + n / N) * vf) if vf > 0 else 0.0
    return ppi_lam_ci(Y, f_lab, f_unl, lam, alpha)
