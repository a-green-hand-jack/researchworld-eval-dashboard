"""Interval estimators for a population mean E[Y] from labeled (Y, f) and unlabeled f.

All estimators return (lo, hi). Predictor f is fixed; "calibrated" scores are
s = g(f) where g is learned on the labeled data only, with K-fold cross-fitting.
"""
import numpy as np
from scipy.stats import norm, t as tdist
from sklearn.isotonic import IsotonicRegression
from sklearn.preprocessing import SplineTransformer
from sklearn.linear_model import Ridge

ALPHA = 0.05


def classical(Y, alpha=ALPHA, use_t=False):
    n = len(Y)
    m, se = Y.mean(), Y.std(ddof=1) / np.sqrt(n)
    q = tdist.ppf(1 - alpha / 2, n - 1) if use_t else norm.ppf(1 - alpha / 2)
    return m - q * se, m + q * se


def ppi_scores(Y, s_lab, s_unl, alpha=ALPHA, lam="opt", use_t=False, ddof=1, clip=False, both=False):
    """PPI / PPI++ interval for the mean given scores s (lam=1: PPI; 'opt': PPI++ power tuning).

    Reproduces ppi_py.ppi_mean_ci (checked in tests/check_vs_ppi_py.py).
    """
    n, N = len(Y), len(s_unl)
    if lam == "opt":
        sall = np.concatenate([s_lab, s_unl])
        v = sall.var()
        if v <= 0:
            lam = 0.0
        else:
            c = np.mean((Y - Y.mean()) * (s_lab - s_lab.mean()))
            lam = float(c / ((1 + n / N) * v))
            if clip:
                lam = min(max(lam, 0.0), 1.0)
    r = Y - lam * s_lab
    est = r.mean() + lam * s_unl.mean()
    var = r.var(ddof=ddof) / n + lam ** 2 * s_unl.var(ddof=ddof) / N
    se = np.sqrt(var)
    q = tdist.ppf(1 - alpha / 2, n - 1) if use_t else norm.ppf(1 - alpha / 2)
    if both:   # (z-interval, t-interval) from one fit
        qt = tdist.ppf(1 - alpha / 2, n - 1)
        qz = norm.ppf(1 - alpha / 2)
        return (est - qz * se, est + qz * se), (est - qt * se, est + qt * se)
    return est - q * se, est + q * se


# ---- calibration maps g(f), each: fit(f_train, y_train) -> predict(f_new) --------------

def _fit_iso(f, y):
    m = IsotonicRegression(out_of_bounds="clip", increasing=True).fit(f, y)
    return m.predict


def _fit_bin(f, y, nb=None):
    n = len(f)
    nb = nb or int(max(2, min(10, n // 30)))
    edges = np.unique(np.quantile(f, np.linspace(0, 1, nb + 1)[1:-1]))
    idx = np.searchsorted(edges, f, side="left")
    # merge empty bins (ties in f, e.g. binary predictions): keep only bins occupied in training
    occ = np.unique(idx)
    means = np.full(len(edges) + 1, y.mean())
    for b in occ:
        means[b] = y[idx == b].mean()
    # empty bins (no training points) borrow the nearest occupied bin
    for b in range(len(means)):
        if b not in occ:
            means[b] = means[occ[np.argmin(np.abs(occ - b))]]
    return lambda fn: means[np.searchsorted(edges, fn, side="left")]


def _fit_spl(f, y, nk=5, alpha=1e-3):
    # cubic spline basis with quantile knots on standardized f, light ridge; linear extrapolation
    mu, sd = f.mean(), f.std() + 1e-12
    z = (f - mu) / sd
    st = SplineTransformer(n_knots=nk, degree=3, knots="quantile", extrapolation="linear")
    B = st.fit_transform(z[:, None])
    m = Ridge(alpha=alpha).fit(B, y)
    return lambda fn: m.predict(st.transform(((fn - mu) / sd)[:, None]))


def _fit_lin(f, y):
    A = np.vstack([np.ones_like(f), f]).T
    b = np.linalg.lstsq(A, y, rcond=None)[0]
    return lambda fn: b[0] + b[1] * fn


CAL = {"iso": _fit_iso, "bin": _fit_bin, "spl": _fit_spl, "lin": _fit_lin}


def cross_calibrate(Y, f_lab, f_unl, kind, K=5, rng=None):
    """Out-of-fold g(f) for labeled points; fold-averaged g(f) for unlabeled points."""
    n = len(Y)
    rng = rng if rng is not None else np.random.default_rng(0)
    K = min(K, n)
    folds = rng.permutation(n) % K
    s_lab = np.empty(n)
    s_unl = np.zeros(len(f_unl))
    for k in range(K):
        tr = folds != k
        pred = CAL[kind](f_lab[tr], Y[tr])
        s_lab[~tr] = pred(f_lab[~tr])
        s_unl += pred(f_unl) / K
    return s_lab, s_unl


def cal_ppi(Y, f_lab, f_unl, kind, alpha=ALPHA, K=5, rng=None, lam="opt", use_t=False, both=False):
    s_lab, s_unl = cross_calibrate(Y, f_lab, f_unl, kind, K, rng)
    return ppi_scores(Y, s_lab, s_unl, alpha, lam, use_t, both=both)


def oracle_cal_ppi(Y, f_lab, f_unl, gfun, alpha=ALPHA, lam="opt"):
    """Calibration map fixed in advance (fitted on independent big data): no estimation cost."""
    return ppi_scores(Y, gfun(f_lab), gfun(f_unl), alpha, lam)


def ppi_jackknife(Y, f, fu, alpha=ALPHA, clip=True):
    """PPI++ with a delete-one jackknife SE for the labeled part (lambda re-estimated in each delete-one fit), t(n-1) critical value.

    Small-n correction of the plug-in lambda (candidate for M5). Unlabeled variance term added with the full-sample lambda.
    """
    n, N = len(Y), len(fu)
    m = n - 1
    Sy, Sf, Syf, Sff = Y.sum(), f.sum(), (Y * f).sum(), (f * f).sum()
    Su, Suu = fu.sum(), (fu * fu).sum()

    def lam_of(ybar, fbar, syf, sff_, sf_, m_):
        cov = syf / m_ - ybar * fbar
        pm = (sf_ + Su) / (m_ + N)
        var = (sff_ + Suu) / (m_ + N) - pm ** 2
        lam = np.where(var > 0, cov / ((1 + m_ / N) * np.where(var > 0, var, 1)), 0.0)
        return np.clip(lam, 0, 1) if clip else lam

    yb_i, fb_i = (Sy - Y) / m, (Sf - f) / m
    lam_i = lam_of(yb_i, fb_i, Syf - Y * f, Sff - f * f, Sf - f, m)
    est_i = yb_i - lam_i * fb_i + lam_i * Su / N
    lam = float(lam_of(Sy / n, Sf / n, Syf, Sff, Sf, n))
    est = Y.mean() - lam * f.mean() + lam * Su / N
    var = (n - 1) / n * np.sum((est_i - est_i.mean()) ** 2) + lam ** 2 * fu.var(ddof=1) / N
    q = tdist.ppf(1 - alpha / 2, n - 1)
    se = np.sqrt(var)
    return est - q * se, est + q * se


def conformal(Y, f, fu, alpha=ALPHA):
    """Bonferroni conformal baseline of ppi_py.baselines; (-inf, inf) when the corrected level exceeds 1."""
    from ppi_py.baselines import conformal_mean_ci
    try:
        lo, hi = conformal_mean_ci(Y, f, fu, alpha=alpha)
    except AttributeError:                      # ppi_py 0.2.3 uses np.infty, removed in numpy 2
        return -np.inf, np.inf
    return float(lo), float(hi)
