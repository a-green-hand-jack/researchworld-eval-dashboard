"""Interval estimators for a population mean from (labeled, unlabeled, fixed predictor).

All estimators take
    Y   (n,)      gold labels
    F   (n,)      predictor output on the labeled points
    X   (n,p)     extra covariates on the labeled points (p may be 0)
    Fu  (N,)      predictor output on unlabeled points
    Xu  (N,p)     extra covariates on unlabeled points
and return dict method -> (estimate, standard_error, df).
Intervals are built by `interval`.
"""
import numpy as np
from scipy import stats
from sklearn.isotonic import IsotonicRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from ppi_py import ppi_mean_ci, classical_mean_ci

ALPHA = 0.05


# --------------------------------------------------------------------------- baselines
def baselines(Y, Fl, Fu, alpha=ALPHA):
    out = {}
    z = stats.norm.ppf(1 - alpha / 2)

    def pack(ci):
        lo, hi = float(np.ravel(ci[0])[0]), float(np.ravel(ci[1])[0])
        return 0.5 * (lo + hi), 0.5 * (hi - lo) / z

    out["classical"] = pack(classical_mean_ci(Y, alpha=alpha))
    out["ppi"] = pack(ppi_mean_ci(Y, Fl, Fu, alpha=alpha, lam=1))
    out["ppi++"] = pack(ppi_mean_ci(Y, Fl, Fu, alpha=alpha))
    return out


# --------------------------------------------------------------------------- nuisance learners
class _Lin:
    """OLS of y on [1, columns]; cols=None -> only predictor column."""
    def __init__(self, use_x):
        self.use_x = use_x

    def fit(self, Z, y):
        A = np.c_[np.ones(len(Z)), Z if self.use_x else Z[:, :1]]
        self.beta = np.linalg.lstsq(A, y, rcond=None)[0] if len(y) > A.shape[1] else np.r_[y.mean(), np.zeros(A.shape[1] - 1)]
        return self

    def predict(self, Z):
        A = np.c_[np.ones(len(Z)), Z if self.use_x else Z[:, :1]]
        return A @ self.beta


class _Iso:
    def fit(self, Z, y):
        self.m = IsotonicRegression(out_of_bounds="clip").fit(Z[:, 0], y)
        return self

    def predict(self, Z):
        return self.m.predict(Z[:, 0])


class _Gbm:
    def fit(self, Z, y):
        self.m = HistGradientBoostingRegressor(max_iter=60, learning_rate=0.1, max_depth=3,
                                               min_samples_leaf=10, early_stopping=False).fit(Z, y)
        return self

    def predict(self, Z):
        return self.m.predict(Z)


def make_learner(name):
    return {"lin": lambda: _Lin(False), "linX": lambda: _Lin(True),
            "iso": _Iso, "gbm": _Gbm}[name]()


# --------------------------------------------------------------------------- cross-fitted AIPW
def crossfit(Y, ZL, ZU, learner, K, rng):
    """Out-of-fold predictions on labeled points; fold-ensemble predictions on unlabeled points."""
    n = len(Y)
    folds = rng.permutation(n) % K
    gL = np.empty(n)
    gU = np.zeros(len(ZU))
    for k in range(K):
        tr, te = folds != k, folds == k
        m = make_learner(learner).fit(ZL[tr], Y[tr])
        gL[te] = m.predict(ZL[te])
        if len(ZU):
            gU += m.predict(ZU) / K
    return gL, gU


def aipw_from_g(Y, gL, gU):
    """theta = mean over all n+N of g  +  mean over labeled of (Y-g); two-sample variance estimate.
    Labeled points use out-of-fold g in both terms."""
    n, N = len(Y), len(gU)
    a = (Y - gL) / n + gL / (n + N)
    theta = a.sum() + gU.sum() / (n + N)
    var = n * a.var(ddof=1) + (N * gU.var(ddof=1) / (n + N) ** 2 if N > 1 else 0.0)
    return theta, np.sqrt(var)


def aipw_unlab_only(Y, gL, gU):
    """PPI-style (labeled points not used in the 'imputed' term): mean_U g + mean_L (Y-g)."""
    n, N = len(Y), len(gU)
    theta = gU.mean() + (Y - gL).mean()
    var = (Y - gL).var(ddof=1) / n + gU.var(ddof=1) / N
    return theta, np.sqrt(var)


def aipw_methods(Y, Fl, Xl, Fu, Xu, learners, K=5, rng=None):
    """Returns dict name -> (est, se, df) for each learner, plus 'auto' (min out-of-fold MSE)."""
    n = len(Y)
    ZL = np.c_[Fl, Xl] if Xl.shape[1] else Fl[:, None]
    ZU = np.c_[Fu, Xu] if Xu.shape[1] else Fu[:, None]
    out, mse, cache = {}, {}, {}
    Kn = min(K, n)
    # same folds for every learner (shared seed state) so that 'auto' compares like with like
    seed = int(rng.integers(2**31))
    for l in learners:
        gL, gU = crossfit(Y, ZL, ZU, l, Kn, np.random.default_rng(seed))
        cache[l] = (gL, gU)
        mse[l] = np.mean((Y - gL) ** 2)
        th, se = aipw_from_g(Y, gL, gU)
        out["aipw-" + l] = (th, se, n - 1)
    best = min(mse, key=mse.get)
    out["aipw-auto"] = out["aipw-" + best]
    out["_auto_choice"] = best
    th, se = aipw_unlab_only(Y, *cache[best])
    out["aipw-auto-Uonly"] = (th, se, n - 1)
    return out


def interval(est, se, df=None, alpha=ALPHA):
    q = stats.norm.ppf(1 - alpha / 2) if df is None else stats.t.ppf(1 - alpha / 2, df)
    return est - q * se, est + q * se
