"""Confidence intervals for a mean from (labeled Y, predictions f, optional features X).

All methods consume the same arrays: labeled (y_l, f_l, x_l) and unlabeled (f_u, x_u).
Interval = (estimate, half-width).  Every method is asymptotically valid under
labeled/unlabeled exchangeability; they differ in how the prediction information is used.
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
from scipy.stats import norm, t as tdist
from sklearn.isotonic import IsotonicRegression
from sklearn.ensemble import HistGradientBoostingRegressor

Z = norm.ppf(0.975)


def _wrap(theta, se, n, use_t=False):
    q = tdist.ppf(0.975, n - 1) if use_t else Z
    return theta, q * se


# ---------- baselines -------------------------------------------------------
def classical(y_l, **_):
    n = len(y_l)
    return y_l.mean(), np.sqrt(y_l.var(ddof=1) / n)


def ppi_family(y_l, f_l, f_u, lam=None):
    """lam=1: PPI (Angelopoulos et al. 2023); lam=None: power-tuned PPI++ (closed form for the mean)."""
    n, N = len(y_l), len(f_u)
    if lam is None:
        f_all = np.concatenate([f_l, f_u])
        v = f_all.var()
        lam = 0.0 if v == 0 else np.cov(y_l, f_l, ddof=0)[0, 1] / ((1 + n / N) * v)
    th = lam * f_u.mean() + (y_l - lam * f_l).mean()
    var = (y_l - lam * f_l).var(ddof=1) / n + lam**2 * f_u.var(ddof=1) / N
    return th, np.sqrt(var), lam


# ---------- cross-fitted adjusters -----------------------------------------
class Iso:
    def fit(self, Zl, y):
        self.m = IsotonicRegression(out_of_bounds="clip", increasing=True).fit(Zl[:, 0], y)
        return self

    def predict(self, Zm):
        return self.m.predict(Zm[:, 0])


class Lin:
    def __init__(self, cols=None, ridge=0.0):
        self.cols, self.ridge = cols, ridge

    def _d(self, Zm):
        Zc = Zm if self.cols is None else Zm[:, self.cols]
        return np.column_stack([np.ones(len(Zc)), Zc])

    def fit(self, Zl, y):
        D = self._d(Zl)
        P = self.ridge * np.eye(D.shape[1]); P[0, 0] = 0
        self.b = np.linalg.lstsq(D.T @ D + P, D.T @ y, rcond=None)[0]  # min-norm if singular (e.g. constant f in a fold)
        return self

    def predict(self, Zm):
        return self._d(Zm) @ self.b


class Poly:
    """Polynomial of degree `deg` in the first column (the prediction), standardised, ridge-stabilised."""
    def __init__(self, deg=3, ridge=1e-3):
        self.deg, self.ridge = deg, ridge

    def _d(self, Zm):
        z = (Zm[:, 0] - self.mu) / self.sd
        return np.column_stack([z**k for k in range(1, self.deg + 1)] + [np.ones(len(z))])

    def fit(self, Zl, y):
        self.mu, self.sd = Zl[:, 0].mean(), Zl[:, 0].std() + 1e-12
        D = self._d(Zl); P = self.ridge * len(y) * np.eye(D.shape[1]); P[-1, -1] = 0
        self.b = np.linalg.lstsq(D.T @ D + P, D.T @ y, rcond=None)[0]  # min-norm if singular (e.g. constant f in a fold)
        return self

    def predict(self, Zm):
        return self._d(Zm) @ self.b


class GBM:
    def __init__(self, **kw):
        self.kw = dict(max_depth=3, max_iter=60, learning_rate=0.1, min_samples_leaf=20,
                       l2_regularization=1.0, early_stopping=False)
        self.kw.update(kw)

    def fit(self, Zl, y):
        self.m = HistGradientBoostingRegressor(**self.kw).fit(Zl, y)
        return self

    def predict(self, Zm):
        return self.m.predict(Zm)


LEARNERS = {
    "lin_f": lambda: Lin(cols=[0]),            # affine recalibration of f (PPI++-type)
    "iso_f": lambda: Iso(),                    # monotone recalibration of f
    "lin_fX": lambda: Lin(ridge=1e-6),         # linear in (f, X)
    "poly_f": lambda: Poly(),                  # cubic polynomial in f (few parameters, nonlinear)
    "gbm_f": lambda: GBM(),                    # nonlinear in f only (use cols below)
    "gbm_fX": lambda: GBM(),                   # nonlinear in (f, X)
}
COLS = {"lin_f": [0], "iso_f": [0], "poly_f": [0], "lin_fX": None, "gbm_f": [0], "gbm_fX": None}


def crossfit_adjust(y_l, Z_l, Z_u, learner, K=5, rng=None, tune=True, use_t=False):
    """Cross-fitted regression-adjusted ("AIPW / DML"-type) interval.

    m is learned ONLY from labeled data; labeled point i is scored by the model fit without its fold,
    unlabeled points by the fold-average.  theta = Ybar + lam*(mean_u m_bar - mean_l m_(-k)).
    """
    n, N = len(y_l), len(Z_u)
    cols = COLS[learner]
    Zl = Z_l if cols is None else Z_l[:, cols]
    Zu = Z_u if cols is None else Z_u[:, cols]
    rng = rng or np.random.default_rng(0)
    folds = np.array_split(rng.permutation(n), K)
    m_l = np.empty(n)
    m_u = np.zeros(N)
    for idx in folds:
        tr = np.setdiff1d(np.arange(n), idx, assume_unique=True)
        mdl = LEARNERS[learner]().fit(Zl[tr], y_l[tr])
        m_l[idx] = mdl.predict(Zl[idx])
        m_u += mdl.predict(Zu) / K
    if tune:
        allm = np.concatenate([m_l, m_u])
        v = allm.var()
        lam = 0.0 if v == 0 else np.cov(y_l, m_l, ddof=0)[0, 1] / ((1 + n / N) * v)
    else:
        lam = 1.0
    th = y_l.mean() + lam * (m_u.mean() - m_l.mean())
    var = (y_l - lam * m_l).var(ddof=1) / n + lam**2 * m_u.var(ddof=1) / N
    return th, np.sqrt(var), lam, m_l, m_u


def boot_t(y_l, m_l, m_u, B=999, rng=None, lam_fixed=None):
    """Studentised (bootstrap-t) interval for the control-variate estimator, conditional on (m_l, m_u).

    Labeled pairs (y, m) are resampled exactly; the unlabeled part enters through its mean and variance
    only (mean perturbed by its normal approximation, variance held at the sample value), since N >> n.
    lambda is re-tuned in each resample.  Returns (midpoint, halfwidth) of [lo, hi].
    """
    rng = rng or np.random.default_rng(0)
    n, N = len(y_l), len(m_u)
    vpool = np.concatenate([m_l, m_u]).var()
    mu_u, su2 = m_u.mean(), m_u.var(ddof=1)

    def est(y, m, mub):
        if lam_fixed is None:
            yc, mc = y - y.mean(1, keepdims=True), m - m.mean(1, keepdims=True)
            lam = np.zeros(len(y)) if vpool == 0 else (yc * mc).mean(1) / ((1 + n / N) * vpool)
        else:
            lam = np.full(len(y), lam_fixed)
        r = y - lam[:, None] * m
        th = r.mean(1) + lam * mub
        se = np.sqrt(r.var(1, ddof=1) / n + lam**2 * su2 / N)
        return th, se

    th0, se0 = est(y_l[None], m_l[None], np.array([mu_u]))
    ib = rng.integers(0, n, (B, n))
    mub = mu_u + np.sqrt(su2 / N) * rng.standard_normal(B)
    thb, seb = est(y_l[ib], m_l[ib], mub)
    with np.errstate(divide="ignore", invalid="ignore"):
        T = (thb - th0[0]) / seb
    T = T[np.isfinite(T)]
    if len(T) < 50: return th0[0], Z * se0[0]
    lo_q, hi_q = np.quantile(T, [0.025, 0.975])
    lo, hi = th0[0] - hi_q * se0[0], th0[0] - lo_q * se0[0]
    return (lo + hi) / 2, (hi - lo) / 2


def all_intervals(y_l, f_l, x_l, f_u, x_u, learners, K=5, rng=None, boot=False):
    """Return {name: (theta, halfwidth)} for the common set of methods."""
    out = {}
    n = len(y_l)
    th, hw = classical(y_l); out["classical"] = _wrap(th, hw, n)[0], Z * hw
    th, se, _ = ppi_family(y_l, f_l, f_u, lam=1.0); out["ppi"] = th, Z * se
    th, se, lam = ppi_family(y_l, f_l, f_u); out["ppi++"] = th, Z * se
    out["_lam_ppi++"] = lam, 0
    out["ppi++_t"] = th, tdist.ppf(0.975, n - 1) * se
    if boot:
        out["ppi++_boot"] = boot_t(y_l, f_l, f_u, rng=rng)
        out["classical_boot"] = boot_t(y_l, np.zeros(n), np.zeros(len(f_u)), rng=rng)
        out["classical_t"] = out["classical"][0], tdist.ppf(0.975, n - 1) * out["classical"][1] / Z
    if learners:
        if x_l is not None:
            Z_l, Z_u = np.column_stack([f_l, x_l]), np.column_stack([f_u, x_u])
        else:
            Z_l, Z_u = f_l[:, None], f_u[:, None]
        for L in learners:
            th, se, lam, m_l, m_u = crossfit_adjust(y_l, Z_l, Z_u, L, K=K, rng=rng)
            if boot: out[f"cf_{L}_boot"] = boot_t(y_l, m_l, m_u, rng=rng)
            out[f"cf_{L}"] = th, Z * se
            out[f"cf_{L}_t"] = th, tdist.ppf(0.975, n - 1) * se
            out[f"_lam_cf_{L}"] = lam, 0
    return out
