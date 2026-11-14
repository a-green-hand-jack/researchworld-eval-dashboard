"""Interval estimators for the population mean E[Y] given
  - labeled sample (Y_i, f_i), i=1..n   (f = fixed predictor output)
  - unlabeled sample f_j, j=1..N
All estimators return (theta_hat, se); the 95% Wald interval is theta +- z*se.

Estimators of the control-variate form  theta(lam) = mean(Y) - lam' (mean_L(H) - mean_U(H)),
where H = H(f) is a (vector) function of the prediction.  PPI++ is H = f (scalar lam).
"""
import numpy as np
from scipy.stats import norm, t as student_t
from sklearn.isotonic import IsotonicRegression

Z95 = norm.ppf(0.975)


# ---------------------------------------------------------------- core machinery
def cv_estimate(Y, HL, HU, lam=None, tcorr=False):
    """Optimal (plug-in) control-variate estimator; returns theta, se, lam.
    lam* = (S_L + (n/N) S_U)^{-1} Cov_L(H, Y)  minimises
    Var(Y - lam'H)/n + lam' S_U lam / N."""
    n, N = len(Y), len(HU)
    HL = HL.reshape(n, -1)
    HU = HU.reshape(N, -1)
    muL, muU = HL.mean(0), HU.mean(0)
    if lam is None:
        SL = np.atleast_2d(np.cov(HL, rowvar=False))
        SU = np.atleast_2d(np.cov(HU, rowvar=False))
        c = ((HL - muL) * (Y - Y.mean())[:, None]).sum(0) / (n - 1)
        lam = np.linalg.pinv(SL + (n / N) * SU, rcond=1e-10) @ c
    theta = Y.mean() - lam @ (muL - muU)
    se2_lab = np.var(Y - HL @ lam, ddof=1) / n
    se2_unl = np.var(HU @ lam, ddof=1) / N
    se = np.sqrt(se2_lab + se2_unl)
    if tcorr:  # df correction for the p estimated control coefficients + Student-t critical value
        p = len(np.atleast_1d(lam))
        df = n - p - 1
        if df < 2:
            return np.nan, np.nan, lam
        se = np.sqrt(se2_lab * (n - 1) / df + se2_unl) * student_t.ppf(0.975, df) / Z95
    return theta, se, lam


# ---------------------------------------------------------------- baselines
def classical(Y, FL, FU):
    return Y.mean(), Y.std(ddof=1) / np.sqrt(len(Y))


def classical_t(Y, FL, FU):
    n = len(Y)
    return Y.mean(), Y.std(ddof=1) / np.sqrt(n) * student_t.ppf(0.975, n - 1) / Z95


def ppipp_own_t(Y, FL, FU):
    th, se, _ = cv_estimate(Y, FL, FU, tcorr=True)
    return th, se


def ppi_lam1(Y, FL, FU):
    """Original PPI (Angelopoulos et al. 2023), lam = 1."""
    th, se, _ = cv_estimate(Y, FL, FU, lam=np.array([1.0]))
    return th, se


def ppipp_own(Y, FL, FU):
    """PPI++ with unclipped plug-in optimal scalar lam (own implementation)."""
    th, se, _ = cv_estimate(Y, FL, FU)
    return th, se


def ppipp_pkg(Y, FL, FU):
    """PPI++ via the reference package ppi_py (lam tuned & clipped to [0,1])."""
    from ppi_py import ppi_mean_ci
    lo, hi = ppi_mean_ci(Y, FL, FU, alpha=0.05)
    return float(np.squeeze(0.5 * (lo + hi))), float(np.squeeze(0.5 * (hi - lo) / Z95))


def ppi_pkg_lam1(Y, FL, FU):
    from ppi_py import ppi_mean_ci
    lo, hi = ppi_mean_ci(Y, FL, FU, alpha=0.05, lam=1.0)
    return float(np.squeeze(0.5 * (lo + hi))), float(np.squeeze(0.5 * (hi - lo) / Z95))


def _bins(pooled, K):
    u = np.unique(pooled)
    if len(u) <= K:
        edges = (u[1:] + u[:-1]) / 2
    else:
        edges = np.unique(np.quantile(pooled, np.linspace(0, 1, K + 1)[1:-1]))
    return edges


def strat_ppi(Y, FL, FU, K=5):
    """Post-stratified PPI (lam=1 within strata of the prediction); an adaptation of the
    stratified-PPI idea to simple random labeling (strata = pooled quantile bins).
    theta = sum_k w_k [mean_L,k(Y-f) + mean_U,k(f)],  w_k = unlabeled share of stratum k.
    SE: conditional on labeled data, theta = mean_U(a_j) with a_j = f_j + rbar_{k(j)}  (variance of the
    unlabeled average incl. random stratum shares) plus sum_k w_k^2 var_L,k(Y-f)/n_k."""
    edges = _bins(np.concatenate([FL, FU]), K)
    sL, sU = np.searchsorted(edges, FL, side="right"), np.searchsorted(edges, FU, side="right")
    nk_all = len(edges) + 1
    rbar = np.zeros(nk_all)
    v_lab = 0.0
    N = len(FU)
    for k in range(nk_all):
        mL, mU = sL == k, sU == k
        nk, Nk = mL.sum(), mU.sum()
        if nk < 2 or Nk < 1:
            return np.nan, np.nan
        r = Y[mL] - FL[mL]
        rbar[k] = r.mean()
        v_lab += (Nk / N) ** 2 * r.var(ddof=1) / nk
    a = FU + rbar[sU]
    return a.mean(), np.sqrt(v_lab + a.var(ddof=1) / N)


# ---------------------------------------------------------------- proposed: nonlinear controls
def _ncs_basis(x, knots):
    """Harrell restricted (natural) cubic spline basis: columns [x, d_1..d_{k-2}]."""
    k = len(knots)
    pos = lambda u: np.maximum(u, 0.0) ** 3
    tk, tk1 = knots[-1], knots[-2]
    cols = [x]
    for j in range(k - 2):
        tj = knots[j]
        d = (pos(x - tj) - pos(x - tk1) * (tk - tj) / (tk - tk1) + pos(x - tk) * (tk1 - tj) / (tk - tk1)) / (tk - knots[0]) ** 2
        cols.append(d)
    return np.column_stack(cols)


_KNOT_Q = {3: [0.10, 0.50, 0.90], 4: [0.05, 0.35, 0.65, 0.95], 5: [0.05, 0.275, 0.5, 0.725, 0.95],
           6: [0.05, 0.23, 0.41, 0.59, 0.77, 0.95], 7: [0.025, 0.1833, 0.3417, 0.5, 0.6583, 0.8167, 0.975]}


def spline_basis(FL, FU, k=4):
    pooled = np.concatenate([FL, FU])
    u = np.unique(pooled)
    if len(u) <= k + 2:  # (nearly) discrete prediction: dummy-code the support
        cols = [(pooled == v).astype(float) for v in u[1:]]
        H = np.column_stack(cols) if cols else pooled[:, None]
    else:
        mu, sd = pooled.mean(), pooled.std()
        x = (pooled - mu) / sd
        knots = np.quantile(x, _KNOT_Q[k])
        if len(np.unique(knots)) < k:  # heavy ties: fall back to the linear control
            H = x[:, None]
        else:
            H = _ncs_basis(x, knots)
    return H[: len(FL)], H[len(FL):]


def spline_ppi(Y, FL, FU, k=4):
    """PPI++ with a natural-cubic-spline control variate H(f) (vector lam, k-1 columns).
    The span contains f, so it is asymptotically never worse than PPI++."""
    HL, HU = spline_basis(FL, FU, k)
    th, se, _ = cv_estimate(Y, HL, HU)
    return th, se


def spline_ppi_t(Y, FL, FU, k=4):
    HL, HU = spline_basis(FL, FU, k)
    th, se, _ = cv_estimate(Y, HL, HU, tcorr=True)
    return th, se


def cf_isotonic_ppi(Y, FL, FU, rng=None, folds=5, increasing="auto"):
    """Cross-fitted isotonic recalibration g_hat(f) ~ E[Y|f] as control variate, scalar lam."""
    n = len(Y)
    rng = np.random.default_rng() if rng is None else rng
    perm = rng.permutation(n)
    fold = np.empty(n, int)
    fold[perm] = np.arange(n) % folds
    HL = np.empty(n)
    HU = np.zeros(len(FU))
    for k in range(folds):
        tr, te = fold != k, fold == k
        iso = IsotonicRegression(increasing=increasing, out_of_bounds="clip").fit(FL[tr], Y[tr])
        HL[te] = iso.predict(FL[te])
        HU += iso.predict(FU) / folds
    th, se, _ = cv_estimate(Y, HL, HU)
    return th, se


def cf_gbm_ppi(Y, FL, FU, XL, XU, rng=None, folds=5):
    """Extension (uses covariates X in addition to f): cross-fitted gradient-boosting
    g_hat(f, X) as control variate, scalar lam."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    n = len(Y)
    rng = np.random.default_rng() if rng is None else rng
    perm = rng.permutation(n)
    fold = np.empty(n, int)
    fold[perm] = np.arange(n) % folds
    AL, AU = np.column_stack([FL, XL]), np.column_stack([FU, XU])
    HL = np.empty(n)
    HU = np.zeros(len(FU))
    for k in range(folds):
        tr, te = fold != k, fold == k
        m = HistGradientBoostingRegressor(max_depth=3, max_iter=100, learning_rate=0.1,
                                          min_samples_leaf=20, random_state=0).fit(AL[tr], Y[tr])
        HL[te] = m.predict(AL[te])
        HU += m.predict(AU) / folds
    th, se, _ = cv_estimate(Y, HL, HU)
    return th, se


METHODS = {
    "classical": classical,
    "classical_t": classical_t,
    "ppi": ppi_lam1,
    "ppi++": ppipp_pkg,
    "ppi++_own": ppipp_own,
    "ppi++_own_t": ppipp_own_t,
    "strat_ppi5": strat_ppi,
    "spline3": lambda Y, FL, FU: spline_ppi(Y, FL, FU, 3),
    "spline4": lambda Y, FL, FU: spline_ppi(Y, FL, FU, 4),
    "spline4_t": lambda Y, FL, FU: spline_ppi_t(Y, FL, FU, 4),
    "spline6": lambda Y, FL, FU: spline_ppi(Y, FL, FU, 6),
}
RNG_METHODS = {"cf_iso": cf_isotonic_ppi}


def run_all(Y, FL, FU, rng, names=None):
    """Returns dict name -> (theta, se)."""
    out = {}
    for nm, fn in METHODS.items():
        if names is None or nm in names:
            out[nm] = fn(Y, FL, FU)
    for nm, fn in RNG_METHODS.items():
        if names is None or nm in names:
            out[nm] = fn(Y, FL, FU, rng=rng)
    return out
