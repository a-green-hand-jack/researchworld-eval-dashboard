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


def _best_interval(y, yhat, yhat_unl, alpha, seed):
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


def _estimate(request):
    n, big_n, alpha = request["n"], request["N"], request["alpha"]
    y = _decode(request["Y_labeled"], "Y_labeled")
    yhat = _decode(request["Yhat_labeled"], "Yhat_labeled")
    yhat_unl = _decode(request["Yhat_unlabeled"], "Yhat_unlabeled")
    if y.size != n or yhat.size != n or yhat_unl.size != big_n or not 0.0 < alpha < 1.0:
        raise ValueError("inconsistent estimate request")
    seed = int(_STATE["rng"].integers(0, 2 ** 31 - 1))
    lo, hi = _best_interval(y, yhat, yhat_unl, alpha, seed)
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
