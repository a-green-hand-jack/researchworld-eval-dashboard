"""Starter candidate: PPI++ (power-tuned prediction-powered) confidence interval for a mean.

Interface: ``handle(request) -> response`` over finite JSON-compatible values
(``python_rpc_v1:handle``). The candidate runs in an isolated process with no
filesystem or network access shared with the evaluator; all data arrive inline.

Task. A fixed predictor, a small labeled sample and a larger unlabeled sample are given.
Return a confidence interval [lo, hi] for the population mean E[Y] at level 1 - alpha.
Nominal coverage must hold in repeated sampling; the score rewards narrower intervals than
the PPI++ interval (``ppi_py.ppi_mean_ci`` default power tuning) at maintained coverage.
No extra labels, no predictor change, no extra unlabeled data exist.

Operations (every request is a dict with an ``"op"`` key):

``{"op": "reset", "seed": int}``
    Sent exactly once at the start of every episode (and the process may be restarted
    first). Must clear ALL cross-episode state and seed only the candidate's own
    randomness. Any non-negative integer seed is valid; the seed never selects a dataset,
    plane or workload. Response: exactly ``{"ok": True}``.

``{"op": "estimate", "n": int, "N": int, "alpha": float,
   "Y_labeled": ARR, "Yhat_labeled": ARR, "Yhat_unlabeled": ARR}``
    One independent labeled/unlabeled draw per episode (one estimate call per episode).
    ``ARR`` is ``{"dtype": "float64", "shape": [length], "encoding": "base64-le",
    "data": <base64 of little-endian float64 bytes>}``. ``len(Y_labeled) ==
    len(Yhat_labeled) == n`` and ``len(Yhat_unlabeled) == N``. All values are finite.
    The labeled and unlabeled records are i.i.d. draws from one population; the labeled
    Yhat are the predictor outputs on the labeled records. alpha is 0.05 in every plane.
    Response: exactly ``{"lo": float, "hi": float}`` (finite, lo <= hi); no other keys
    are allowed. A malformed, non-finite, reversed or late response counts as a miss
    with a worst-case width (10x the classical interval).
    Per-call wall deadline: 3 seconds (enforced). Keep BLAS threads at 1.
    The dataset or family name, population truth, baseline outputs and scores are never
    sent. Requests of up to N = 20000 unlabeled and n = 500 labeled records occur
    (about 225 KB base64 per request).

Any other op, or an estimate before reset, is an error.
"""

import base64
import math
import os
import time
from statistics import NormalDist

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np  # noqa: E402

_STATE = {"ready": False, "seed": None, "rng": None}


def _decode(arr, name):
    if (type(arr) is not dict or arr.get("dtype") != "float64"
            or arr.get("encoding") != "base64-le" or type(arr.get("data")) is not str):
        raise ValueError(f"bad array {name}")
    raw = base64.b64decode(arr["data"].encode("ascii"), validate=True)
    out = np.frombuffer(raw, dtype="<f8").astype(np.float64)
    if list(arr.get("shape", [])) != [out.size] or not np.all(np.isfinite(out)):
        raise ValueError(f"bad array {name}")
    return out


def classical_ci(y, alpha):
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    half = z * y.std() / math.sqrt(y.size)
    return y.mean() - half, y.mean() + half


def ppi_pp_ci(y, yhat, yhat_unl, alpha):
    """PPI++ mean interval with the closed-form power-tuning parameter, clipped to [0, 1]."""
    n, big_n = y.size, yhat_unl.size
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    pooled_var = np.concatenate([yhat, yhat_unl]).var(ddof=1)
    if pooled_var > 1e-24:
        cov = float(np.mean((y - y.mean()) * (yhat - yhat.mean())))
        lam = min(1.0, max(0.0, cov / ((1.0 + n / big_n) * pooled_var)))
    else:
        lam = 0.0
    center = (lam * yhat_unl).mean() + (y - lam * yhat).mean()
    se = math.hypot((lam * yhat_unl).std() / math.sqrt(big_n),
                    (y - lam * yhat).std() / math.sqrt(n))
    return center - z * se, center + z * se


def ppi_plus_plus_mean_ci(y, yhat, yhat_unl, alpha):
    """Named alias of the PPI++ baseline interval (scalar power tuning on raw Yhat)."""
    return ppi_pp_ci(y, yhat, yhat_unl, alpha)


def ppi_mean_ci(y, yhat, yhat_unl, alpha):
    """Vanilla PPI (lambda = 1) interval."""
    n, big_n = y.size, yhat_unl.size
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    center = yhat_unl.mean() + (y - yhat).mean()
    se = math.hypot(yhat_unl.std() / math.sqrt(big_n), (y - yhat).std() / math.sqrt(n))
    return center - z * se, center + z * se


def _t_crit(alpha, df):
    """Student-t two-sided critical value (Cornish-Fisher expansion; normal if df is huge)."""
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    df = max(float(df), 3.0)
    return (z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)
            + (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / (384 * df ** 3))


# ----------------------------------------------------------------------------------------
# Recalibration maps g(Yhat) ~ E[Y | Yhat], fit on labeled training folds only.
# ----------------------------------------------------------------------------------------
try:  # sklearn is preferred, a numpy fallback keeps the candidate self-contained
    from sklearn.isotonic import IsotonicRegression
    from sklearn.model_selection import KFold
except Exception:  # pragma: no cover
    IsotonicRegression = None
    KFold = None


def _pav(x, y):
    """Numpy isotonic (increasing) regression; returns (knots, values) for interpolation."""
    order = np.argsort(x, kind="mergesort")
    xs, ys = x[order], y[order]
    ux, inv = np.unique(xs, return_inverse=True)
    w = np.bincount(inv).astype(float)
    m = np.bincount(inv, weights=ys) / w
    vals, wts, cnt = [], [], []
    for mi, wi in zip(m, w):
        vals.append(mi)
        wts.append(wi)
        cnt.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            tw = wts[-2] + wts[-1]
            vals[-2] = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / tw
            wts[-2] = tw
            cnt[-2] += cnt[-1]
            vals.pop(), wts.pop(), cnt.pop()
    fitted = np.repeat(vals, cnt)
    return ux, fitted


def _fit_isotonic(x, y):
    """Return a predictor for a monotone map fit on (x, y); direction chosen by sign of corr."""
    if np.ptp(x) <= 0:
        mu = float(y.mean())
        return lambda t: np.full(t.shape, mu)
    sign = 1.0 if np.mean((x - x.mean()) * (y - y.mean())) >= 0 else -1.0
    if IsotonicRegression is not None:
        iso = IsotonicRegression(increasing=bool(sign > 0), out_of_bounds="clip")
        iso.fit(x, y)
        return iso.predict
    ux, fitted = _pav(sign * x, y)
    return lambda t: np.interp(sign * t, ux, fitted)


def _fit_binned(x, y, n_bins):
    """Quantile-binned conditional means (piecewise constant); empty bins use the grand mean."""
    edges = np.unique(np.quantile(x, np.linspace(0, 1, n_bins + 1)[1:-1]))
    idx = np.searchsorted(edges, x, side="right")
    k = edges.size + 1
    cnt = np.bincount(idx, minlength=k)
    sums = np.bincount(idx, weights=y, minlength=k)
    means = np.where(cnt > 0, sums / np.maximum(cnt, 1), y.mean())
    return lambda t: means[np.searchsorted(edges, t, side="right")]


def _folds(n, k, seed):
    k = max(2, min(k, n))
    if KFold is not None:
        return list(KFold(n_splits=k, shuffle=True, random_state=int(seed) % (2 ** 31)).split(np.arange(n)))
    perm = np.random.default_rng(seed).permutation(n)
    parts = np.array_split(perm, k)
    return [(np.concatenate([parts[j] for j in range(k) if j != i]), parts[i]) for i in range(k)]


def _cross_fit(y, yhat, yhat_unl, fitter, k, seed):
    """K-fold cross-fitted g: out-of-fold g on labeled points, fold-averaged g on unlabeled."""
    g_lab = np.empty(y.size)
    g_unl = np.zeros(yhat_unl.size)
    splits = _folds(y.size, k, seed)
    for tr, te in splits:
        g = fitter(yhat[tr], y[tr])
        g_lab[te] = g(yhat[te])
        g_unl += g(yhat_unl)
    return g_lab, g_unl / len(splits)


def _control_variate_ci(y, f_lab, f_unl, alpha, extra_df=0):
    """Interval for E[Y] from theta = mean_unl(lam.f) + mean_lab(Y - lam.f), lam minimising the
    estimated variance (multivariate power tuning). f_* are (n, p) / (N, p) feature matrices."""
    n, big_n = y.shape[0], f_unl.shape[0]
    pooled = np.vstack([f_lab, f_unl])
    mu, sd = pooled.mean(axis=0), pooled.std(axis=0)
    keep = sd > 1e-12 * max(1.0, float(np.abs(mu).max()))
    if not keep.any():
        return None
    fl = (f_lab[:, keep] - mu[keep]) / sd[keep]
    fu = (f_unl[:, keep] - mu[keep]) / sd[keep]
    p = fl.shape[1]
    sig_l = fl.T @ fl / n
    sig_u = fu.T @ fu / big_n
    c = fl.T @ (y - y.mean()) / n
    a = sig_l + (n / big_n) * sig_u
    a = a + 1e-6 * np.trace(a) / p * np.eye(p)
    lam = np.linalg.solve(a, c)
    r = y - fl @ lam
    u = fu @ lam
    center = u.mean() + r.mean()
    se = math.hypot(u.std() / math.sqrt(big_n), r.std(ddof=1) / math.sqrt(n))
    df = n - 1 - p - extra_df
    half = _t_crit(alpha, df) * se
    return center, half


def crppi_mean_ci(y, yhat, yhat_unl, alpha, method="isotonic", k=5, seed=0):
    """Cross-fitted recalibrated PPI interval. g is fit on labeled folds (isotonic or
    quantile-binned); Yhat and g(Yhat) enter as two control variates with variance-minimising
    weights, so the PPI++ linear-in-Yhat adjustment is nested. Returns (lo, hi) or None."""
    n = y.size
    if n < 20 or np.ptp(yhat) <= 0:
        return None
    if method == "isotonic":
        fitter = _fit_isotonic
    else:
        n_bins = int(min(10, max(2, (n * (k - 1) // k) // 25)))
        fitter = lambda x, t: _fit_binned(x, t, n_bins)  # noqa: E731
    g_lab, g_unl = _cross_fit(y, yhat, yhat_unl, fitter, k, seed)
    out = _control_variate_ci(y, np.column_stack([yhat, g_lab]),
                              np.column_stack([yhat_unl, g_unl]), alpha)
    if out is None:
        return None
    center, half = out
    return center - half, center + half


def stratified_ppi_mean_ci(y, yhat, yhat_unl, alpha, n_bins=5):
    """Stratified PPI baseline: quantile strata of Yhat, lambda = 1 inside each stratum,
    strata weighted by their unlabeled share. Falls back to classical if a stratum has < 2 labels."""
    n_bins = int(max(1, min(n_bins, y.size // 20)))
    pooled = np.concatenate([yhat, yhat_unl])
    edges = np.unique(np.quantile(pooled, np.linspace(0, 1, n_bins + 1)[1:-1]))
    sl = np.searchsorted(edges, yhat, side="right")
    su = np.searchsorted(edges, yhat_unl, side="right")
    center, var = 0.0, 0.0
    for b in range(edges.size + 1):
        ml, mu_ = sl == b, su == b
        nb, nu = int(ml.sum()), int(mu_.sum())
        if nu == 0:
            continue
        if nb < 2:
            return classical_ci(y, alpha)
        w = nu / yhat_unl.size
        rb = y[ml] - yhat[ml]
        center += w * (yhat_unl[mu_].mean() + rb.mean())
        var += w * w * (rb.var(ddof=1) / nb + (yhat_unl[mu_].var(ddof=1) / nu if nu > 1 else 0.0))
    half = NormalDist().inv_cdf(1.0 - alpha / 2.0) * math.sqrt(var)
    return center - half, center + half


# ----------------------------------------------------------------------------------------
# Stacked calibration library + repeated cross-fitting (cycle 3).
# ----------------------------------------------------------------------------------------
try:
    from scipy.optimize import nnls
except Exception:  # pragma: no cover
    nnls = None

_BIN_COUNTS = (3, 5, 8)
_LIBRARY = ("isotonic", "bin3", "bin5", "bin8", "kernel_mono", "kernel_ll", "linear")
_TIME_BUDGET = 1.3  # seconds after which no further repeated split is started (3 s deadline)


def _make_ctx(yhat, yhat_unl):
    """Label-free quantities (pooled labeled+unlabeled Yhat): bin edges, kernel grid, spread."""
    pooled = np.concatenate([yhat, yhat_unl])
    ctx = {}
    for b in _BIN_COUNTS:
        ctx[("edges", b)] = np.unique(np.quantile(pooled, np.linspace(0, 1, b + 1)[1:-1]))
    ctx["grid"] = np.unique(np.quantile(pooled, np.linspace(0.005, 0.995, 41)))
    q25, q75 = np.quantile(pooled, [0.25, 0.75])
    sd = float(pooled.std())
    ctx["spread"] = float(min(sd, (q75 - q25) / 1.34)) if q75 > q25 else sd
    return ctx


def _fit_binned_edges(x, y, edges):
    idx = np.searchsorted(edges, x, side="right")
    k = edges.size + 1
    cnt = np.bincount(idx, minlength=k)
    sums = np.bincount(idx, weights=y, minlength=k)
    means = np.where(cnt > 0, sums / np.maximum(cnt, 1), y.mean())
    return lambda t: means[np.searchsorted(edges, t, side="right")]


def _fit_linear(x, y):
    xbar, ybar = x.mean(), y.mean()
    vx = float(np.mean((x - xbar) ** 2))
    if vx <= 1e-24:
        return lambda t: np.full(t.shape, ybar)
    slope = float(np.mean((x - xbar) * (y - ybar))) / vx
    return lambda t: ybar + slope * (t - xbar)


def _fit_kernel(x, y, ctx, monotone):
    """Gaussian local-linear smoother evaluated on a label-free grid (linear interpolation in
    between), optionally projected on the monotone cone by PAV."""
    grid = ctx["grid"]
    if grid.size < 3 or ctx["spread"] <= 1e-12:
        return None
    h = 0.9 * ctx["spread"] * x.size ** -0.2
    d = x[None, :] - grid[:, None]
    w = np.exp(-0.5 * (d / h) ** 2)
    s0 = w.sum(1)
    s1 = (w * d).sum(1)
    s2 = (w * d * d).sum(1)
    t0_ = w @ y
    t1 = (w * d) @ y
    den = s0 * s2 - s1 * s1
    ok_ll = den > 1e-8 * np.maximum(s0 * s2, 1e-300)
    ok_nw = s0 > 1e-8
    vals = np.full(grid.size, float(y.mean()))
    nw = np.where(ok_nw, t0_ / np.maximum(s0, 1e-300), vals)
    ll = np.where(ok_ll, (s2 * t0_ - s1 * t1) / np.where(ok_ll, den, 1.0), nw)
    vals = np.clip(ll, y.min(), y.max())
    if not monotone:
        return lambda t: np.interp(t, grid, vals)
    sign = 1.0 if np.mean((x - x.mean()) * (y - y.mean())) >= 0 else -1.0
    ux, fitted = _pav(sign * grid, vals)
    return lambda t: np.interp(sign * t, ux, fitted)


def _fit_library(name, x, y, ctx):
    """Fit one library calibrator on (x, y); None if it is not usable for this sample size."""
    if np.ptp(x) <= 0:
        return None if name != "linear" else _fit_linear(x, y)
    if name == "isotonic":
        return _fit_isotonic(x, y)
    if name.startswith("bin"):
        b = int(name[3:])
        if x.size < 10 * b or ctx[("edges", b)].size == 0:
            return None
        return _fit_binned_edges(x, y, ctx[("edges", b)])
    if name == "kernel_mono":
        return _fit_kernel(x, y, ctx, True)
    if name == "kernel_ll":
        return _fit_kernel(x, y, ctx, False)
    if name == "linear":
        return _fit_linear(x, y)
    raise ValueError(name)


def stacked_calibrator_weights(x, y, ctx, library=_LIBRARY, k_inner=4, seed=0):
    """Non-negative stacking weights (sum to one) of the library calibrators: inner K-fold
    out-of-fold predictions on the TRAINING sample (x, y) only, then NNLS of y on them."""
    m = len(library)
    w_out = np.zeros(m)
    lin = library.index("linear") if "linear" in library else None
    if m == 1 or nnls is None or x.size < 12:
        w_out[lin if lin is not None else 0] = 1.0
        return w_out
    folds = _folds(x.size, k_inner, seed)
    p_mat = np.empty((x.size, m))
    valid = np.ones(m, dtype=bool)
    for j, name in enumerate(library):
        for tr, te in folds:
            g = _fit_library(name, x[tr], y[tr], ctx)
            if g is None:
                valid[j] = False
                break
            p_mat[te, j] = g(x[te])
    if not valid.any():
        w_out[lin if lin is not None else 0] = 1.0
        return w_out
    w, _ = nnls(p_mat[:, valid], y)
    w[w < 0.01 * max(w.sum(), 1e-300)] = 0.0
    if w.sum() <= 1e-12:
        idx = lin if (lin is not None and valid[lin]) else int(np.flatnonzero(valid)[0])
        w_out[idx] = 1.0
        return w_out
    w_out[valid] = w / w.sum()
    return w_out


def _fit_stack(x, y, ctx, library, weights):
    parts = []
    for name, wt in zip(library, weights):
        if wt > 0:
            g = _fit_library(name, x, y, ctx)
            if g is not None:
                parts.append((wt, g))
    if not parts:
        return _fit_linear(x, y)
    tot = sum(wt for wt, _ in parts)
    return lambda t: sum(wt * g(t) for wt, g in parts) / tot


def _stack_cross_fit(y, yhat, yhat_unl, ctx, library, k, seed):
    """One K-fold cross-fit of the stacked calibrator; weights use training-fold labels only."""
    g_lab = np.empty(y.size)
    g_unl = np.zeros(yhat_unl.size)
    splits = _folds(y.size, k, seed)
    for i, (tr, te) in enumerate(splits):
        w = stacked_calibrator_weights(yhat[tr], y[tr], ctx, library, seed=seed + 13 * i + 1)
        g = _fit_stack(yhat[tr], y[tr], ctx, library, w)
        g_lab[te] = g(yhat[te])
        g_unl += g(yhat_unl)
    return g_lab, g_unl / len(splits)


def split_variability_variance(y, f_lab_list, f_unl_list, variance_mode="avg_resid",
                               use_dispersion=True):
    """Aggregate R repeated cross-fits of the two-control-variate estimator [Yhat, g_r].

    The variance-minimising lambda is solved once on the split-averaged design. Point estimate
    = mean over splits of theta_r = mean_unl(lam.f_r) + mean_lab(Y - lam.f_r). Variance:
    ``avg_resid``  -> sandwich variance of the averaged residuals (covariance-aware),
    ``mean_split`` -> mean of the per-split sandwich variances; plus, if ``use_dispersion``,
    the across-split variance of the theta_r. Returns (center, variance, p) or None."""
    n, big_n = y.shape[0], f_unl_list[0].shape[0]
    fl_bar = np.mean(f_lab_list, axis=0)
    fu_bar = np.mean(f_unl_list, axis=0)
    pooled = np.vstack([fl_bar, fu_bar])
    mu, sd = pooled.mean(axis=0), pooled.std(axis=0)
    keep = sd > 1e-12 * max(1.0, float(np.abs(mu).max()))
    if not keep.any():
        return None
    fl = (fl_bar[:, keep] - mu[keep]) / sd[keep]
    fu = (fu_bar[:, keep] - mu[keep]) / sd[keep]
    p = fl.shape[1]
    sig_l = fl.T @ fl / n
    sig_u = fu.T @ fu / big_n
    c = fl.T @ (y - y.mean()) / n
    a = sig_l + (n / big_n) * sig_u
    a = a + 1e-6 * np.trace(a) / p * np.eye(p)
    lam = np.linalg.solve(a, c)
    centers, var_split = [], []
    for fl_r, fu_r in zip(f_lab_list, f_unl_list):
        u = ((fu_r[:, keep] - mu[keep]) / sd[keep]) @ lam
        r = y - ((fl_r[:, keep] - mu[keep]) / sd[keep]) @ lam
        centers.append(u.mean() + r.mean())
        var_split.append(r.var(ddof=1) / n + u.var() / big_n)
    center = float(np.mean(centers))
    if variance_mode == "mean_split":
        var = float(np.mean(var_split))
    else:
        r_bar = y - fl @ lam
        var = float(r_bar.var(ddof=1) / n + (fu @ lam).var() / big_n)
    if use_dispersion and len(centers) > 1:
        var += float(np.var(centers, ddof=1))
    return center, var, p


def repeated_crossfit_stack_ci(y, yhat, yhat_unl, alpha, R=5, k=5, seed=0, library=_LIBRARY,
                               variance_mode="avg_resid", use_dispersion=True, deadline=None):
    """Repeated (R splits) K-fold cross-fitted stacked-calibration interval with control
    variates [Yhat, g]. Student-t critical value with n - 1 - p (= n - 3) degrees of freedom.
    ``deadline`` (perf_counter time) stops starting new splits after the first. Returns
    (lo, hi) or None."""
    n = y.size
    if n < 20 or np.ptp(yhat) <= 0:
        return None
    ctx = _make_ctx(yhat, yhat_unl)
    f_lab_list, f_unl_list = [], []
    for r in range(R):
        if r >= 1 and deadline is not None and time.perf_counter() > deadline:
            break
        g_lab, g_unl = _stack_cross_fit(y, yhat, yhat_unl, ctx, library, k, seed + 7919 * r)
        f_lab_list.append(np.column_stack([yhat, g_lab]))
        f_unl_list.append(np.column_stack([yhat_unl, g_unl]))
    out = split_variability_variance(y, f_lab_list, f_unl_list, variance_mode, use_dispersion)
    if out is None:
        return None
    center, var, p = out
    half = _t_crit(alpha, n - 1 - p) * math.sqrt(var)
    return center - half, center + half


def incumbent_interval(y, yhat, yhat_unl, alpha, seed):
    """PPI++ baseline versus cross-fitted recalibrated candidates; a candidate replaces the
    baseline only if its half-width is at least 1% smaller (guards against selection noise)."""
    base = ppi_plus_plus_mean_ci(y, yhat, yhat_unl, alpha)
    best, best_half = base, 0.5 * (base[1] - base[0])
    if not (math.isfinite(base[0]) and math.isfinite(base[1])):
        best, best_half = classical_ci(y, alpha), math.inf
    threshold = 0.99 * best_half
    for method in ("isotonic", "binned"):
        try:
            cand = crppi_mean_ci(y, yhat, yhat_unl, alpha, method=method, seed=seed)
        except Exception:
            cand = None
        if cand is None or not (math.isfinite(cand[0]) and math.isfinite(cand[1])):
            continue
        half = 0.5 * (cand[1] - cand[0])
        if half < threshold:
            best, threshold = cand, half
    return best


def _best_interval(y, yhat, yhat_unl, alpha, seed, t0=None):
    """PPI++ baseline versus the repeated cross-fitted stacked-calibration interval; the
    candidate replaces the baseline only if its half-width is at least 1% smaller (guards
    against selection noise). If the stacked route fails, the single-split incumbent is used."""
    base = ppi_plus_plus_mean_ci(y, yhat, yhat_unl, alpha)
    if not (math.isfinite(base[0]) and math.isfinite(base[1])):
        return classical_ci(y, alpha)
    base_half = 0.5 * (base[1] - base[0])
    deadline = None if t0 is None else t0 + _TIME_BUDGET
    try:
        cand = repeated_crossfit_stack_ci(y, yhat, yhat_unl, alpha, seed=seed, deadline=deadline)
    except Exception:
        cand = None
    if cand is None or not (math.isfinite(cand[0]) and math.isfinite(cand[1])):
        try:
            return incumbent_interval(y, yhat, yhat_unl, alpha, seed)
        except Exception:
            return base
    if 0.5 * (cand[1] - cand[0]) < 0.99 * base_half:
        return cand
    return base


def _estimate(request):
    t0 = time.perf_counter()
    n, big_n, alpha = request["n"], request["N"], request["alpha"]
    y = _decode(request["Y_labeled"], "Y_labeled")
    yhat = _decode(request["Yhat_labeled"], "Yhat_labeled")
    yhat_unl = _decode(request["Yhat_unlabeled"], "Yhat_unlabeled")
    if y.size != n or yhat.size != n or yhat_unl.size != big_n or not 0.0 < alpha < 1.0:
        raise ValueError("inconsistent estimate request")
    seed = int(_STATE["rng"].integers(0, 2 ** 31 - 1))
    lo, hi = _best_interval(y, yhat, yhat_unl, alpha, seed, t0=t0)
    if not (math.isfinite(lo) and math.isfinite(hi)):
        lo, hi = classical_ci(y, alpha)
    return {"lo": float(lo), "hi": float(hi)}


def handle(request):
    op = request.get("op") if isinstance(request, dict) else None
    if op == "reset":
        seed = request["seed"]
        if type(seed) is not int or seed < 0:
            raise ValueError("bad seed")
        _STATE.update(ready=True, seed=seed, rng=np.random.default_rng(seed))
        return {"ok": True}
    if op == "estimate":
        if not _STATE["ready"]:
            raise RuntimeError("estimate before reset")
        return _estimate(request)
    raise ValueError("unknown op")
