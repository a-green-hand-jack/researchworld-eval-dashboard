"""Estimators for the mean of Y with a fixed predictor f.

All estimators return (theta_hat, sigma_hat) so any z/t interval can be built later.

Family: "PPI++ with vector control variates".
    theta = mean_L(Y) - beta' (mean_L(Z) - mean_U(Z)),   Z = phi(f) (n x p / N x p)
    beta  = Sigma^{-1} Cov_L(Z, Y) / (1 + n/N)           (PPI++ power tuning, vector form)
    var   = Var_L(Y - beta'Z)/n + beta' Sigma_U beta / N
p = 1, Z = f  -> PPI++ of Angelopoulos-Duchi-Zrnic (scalar lambda).
Z = basis(f)  -> recalibrated / post-stratified / polynomial PPI++ (no data-fitted g).
Z = g_cf(f)   -> cross-fitted calibrator (isotonic, GBM, ...), p = 1.
"""
import numpy as np
from scipy import stats
from sklearn.isotonic import IsotonicRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import SplineTransformer


# ---------------------------------------------------------------- core
def control_variate_mean(Y, ZL, ZU, ridge=1e-8):
    """Vector-control-variate PPI++ estimate of E[Y]. ZL: (n,p), ZU: (N,p)."""
    n, N = len(Y), len(ZU)
    ZL = ZL.reshape(n, -1)
    ZU = ZU.reshape(N, -1)
    p = ZL.shape[1]
    Zall = np.vstack([ZL, ZU])
    mu_all = Zall.mean(0)
    Sig = np.atleast_2d(np.cov(Zall, rowvar=False))
    Sig = Sig + ridge * np.trace(Sig) / p * np.eye(p) + 1e-300 * np.eye(p)
    Yc = Y - Y.mean()
    ZLc = ZL - ZL.mean(0)
    c = ZLc.T @ Yc / (n - 1)
    beta = np.linalg.solve(Sig, c) / (1.0 + n / N)
    theta = Y.mean() - beta @ (ZL.mean(0) - ZU.mean(0))
    r = Y - ZL @ beta
    SigU = np.atleast_2d(np.cov(ZU, rowvar=False))
    var = r.var(ddof=1) / n + beta @ SigU @ beta / N
    return theta, float(np.sqrt(max(var, 0.0))), beta


def classical(Y):
    return Y.mean(), Y.std(ddof=1) / np.sqrt(len(Y))


def ppi_vanilla(Y, fL, fU):
    n, N = len(Y), len(fU)
    th = Y.mean() - fL.mean() + fU.mean()
    sd = np.sqrt((Y - fL).var(ddof=1) / n + fU.var(ddof=1) / N)
    return th, sd


# ---------------------------------------------------------------- bases (use only f, never Y)
def basis_poly(fL, fU, k):
    allf = np.concatenate([fL, fU])
    m, s = allf.mean(), allf.std() + 1e-12
    mk = lambda f: np.column_stack([((f - m) / s) ** j for j in range(1, k + 1)])
    return mk(fL), mk(fU)


def basis_strata(fL, fU, B):
    allf = np.concatenate([fL, fU])
    qs = np.unique(np.quantile(allf, np.linspace(0, 1, B + 1)[1:-1]))
    def mk(f):
        idx = np.searchsorted(qs, f, side="right")
        oh = np.zeros((len(f), len(qs) + 1))
        oh[np.arange(len(f)), idx] = 1.0
        return oh[:, 1:]  # drop reference stratum (intercept absorbs it)
    return mk(fL), mk(fU)


def basis_spline(fL, fU, n_knots=4, degree=3):
    allf = np.concatenate([fL, fU]).reshape(-1, 1)
    st = SplineTransformer(n_knots=n_knots, degree=degree, knots="quantile",
                           extrapolation="constant", include_bias=False).fit(allf)
    return st.transform(fL.reshape(-1, 1)), st.transform(fU.reshape(-1, 1))


# ---------------------------------------------------------------- cross-fitted calibrators
def _fit_pred(kind, Ftr, ytr, Fte_list):
    """Fit calibrator on (Ftr, ytr); return predictions for each array in Fte_list.
    Ftr is (m, d); column 0 is the predictor f."""
    if kind == "iso":
        ir = IsotonicRegression(out_of_bounds="clip", increasing="auto").fit(Ftr[:, 0], ytr)
        return [ir.predict(F[:, 0]) for F in Fte_list]
    if kind in ("hgb", "hgbX"):
        mdl = HistGradientBoostingRegressor(max_iter=60, learning_rate=0.1, max_leaf_nodes=8,
                                            min_samples_leaf=max(5, len(ytr) // 40),
                                            l2_regularization=1.0, early_stopping=False)
        cols = [0] if kind == "hgb" else list(range(Ftr.shape[1]))
        mdl.fit(Ftr[:, cols], ytr)
        return [mdl.predict(F[:, cols]) for F in Fte_list]
    raise ValueError(kind)


def crossfit_calibrated(kind, Y, FL, FU, K=5, rng=None):
    """Return (gL, gU): out-of-fold calibrated predictions for labeled, fold-averaged for unlabeled."""
    n = len(Y)
    perm = rng.permutation(n)
    folds = np.array_split(perm, K)
    gL = np.empty(n)
    gU = np.zeros(len(FU))
    for idx in folds:
        tr = np.setdiff1d(np.arange(n), idx, assume_unique=True)
        pl, pu = _fit_pred(kind, FL[tr], Y[tr], [FL[idx], FU])
        gL[idx] = pl
        gU += pu / K
    return gL, gU


# ---------------------------------------------------------------- interval helpers
def interval(theta, sd, alpha=0.05, df=None):
    q = stats.norm.ppf(1 - alpha / 2) if df is None else stats.t.ppf(1 - alpha / 2, df)
    return theta - q * sd, theta + q * sd


def ppi_pp_reference(Y, fL, fU):
    """Reference implementation: ppi-python 0.2.3 ppi_mean_ci (lambda clipped to [0,1])."""
    from ppi_py import ppi_mean_ci
    lo, hi = ppi_mean_ci(Y, fL, fU, alpha=0.05)
    lo, hi = float(np.squeeze(lo)), float(np.squeeze(hi))
    return 0.5 * (lo + hi), (hi - lo) / (2 * stats.norm.ppf(0.975))


def fp_regression_mean(Y, ZL, ZU):
    """Finite-population (design-based) regression/GREG estimator of the mean over the M = n+N units.
    The n labeled units are a simple random sample of the M units; population mean of Z is known exactly.
        theta = mean_L(Y) - b'(mean_L(Z) - mean_M(Z)),  b = OLS slope of Y on Z (labeled)
        var   = (1 - n/M) * s_e^2 / n,   s_e^2 = residual variance (n-1-p dof)
    """
    n, N = len(Y), len(ZU)
    M = n + N
    ZL = ZL.reshape(n, -1)
    ZU = ZU.reshape(N, -1)
    p = ZL.shape[1]
    zbarM = (ZL.sum(0) + ZU.sum(0)) / M
    A = np.column_stack([np.ones(n), ZL])
    coef = np.linalg.lstsq(A, Y, rcond=1e-10)[0]
    b = coef[1:]
    theta = Y.mean() - b @ (ZL.mean(0) - zbarM)
    e = Y - A @ coef
    s2 = (e @ e) / max(n - 1 - p, 1)
    return theta, float(np.sqrt((1 - n / M) * s2 / n)), p


def fp_classical(Y, N):
    n = len(Y); M = n + N
    return Y.mean(), float(np.sqrt((1 - n / M) * Y.var(ddof=1) / n))


SUPER = ["classical", "ppi", "ppi++py", "ppi++", "poly2", "poly3", "strat5", "strat10",
         "spline", "iso_cf", "hgb_cf", "hgbX_cf"]
FP = ["FP-classical", "FP-f", "FP-poly2", "FP-strat5", "FP-spline", "FP-iso_cf", "FP-hgb_cf", "FP-hgbX_cf"]
ALL_METHODS = SUPER + FP


def run_all(Y, FL, FU, rng, methods=ALL_METHODS, K=5):
    """FL, FU: (n,d)/(N,d) arrays whose column 0 is the fixed predictor f; extra columns are optional features.
    Returns dict method -> (theta, sd, p)."""
    fL, fU = FL[:, 0], FU[:, 0]
    out = {}
    cache = {}

    def bas(name):
        if name not in cache:
            if name == "f": cache[name] = (fL[:, None], fU[:, None])
            elif name == "poly2": cache[name] = basis_poly(fL, fU, 2)
            elif name == "poly3": cache[name] = basis_poly(fL, fU, 3)
            elif name == "strat5": cache[name] = basis_strata(fL, fU, 5)
            elif name == "strat10": cache[name] = basis_strata(fL, fU, 10)
            elif name == "spline": cache[name] = basis_spline(fL, fU)
            elif name.endswith("_cf"):
                if name == "hgbX_cf" and FL.shape[1] < 2:
                    cache[name] = None
                else:
                    gL, gU = crossfit_calibrated(name[:-3], Y, FL, FU, K=K, rng=rng)
                    cache[name] = (gL[:, None], gU[:, None])
        return cache[name]

    for m in methods:
        if m == "classical":
            out[m] = (*classical(Y), 0)
        elif m == "ppi":
            out[m] = (*ppi_vanilla(Y, fL, fU), 0)
        elif m == "ppi++py":
            out[m] = (*ppi_pp_reference(Y, fL, fU), 1)
        elif m == "FP-classical":
            out[m] = (*fp_classical(Y, len(fU)), 0)
        elif m.startswith("FP-"):
            b = bas({"FP-f": "f"}.get(m, m[3:]))
            if b is not None:
                out[m] = fp_regression_mean(Y, *b)
        else:
            b = bas({"ppi++": "f"}.get(m, m))
            if b is not None:
                t, s, beta = control_variate_mean(Y, *b)
                out[m] = (t, s, len(beta))
    return out
