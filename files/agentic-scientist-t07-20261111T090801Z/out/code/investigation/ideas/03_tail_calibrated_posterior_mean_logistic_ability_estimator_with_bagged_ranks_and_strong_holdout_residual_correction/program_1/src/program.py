"""Model-assisted difference estimator with D-optimal latent-space item selection (python_rpc_v1:handle).

Task.  An episode gives you the binary correct/incorrect matrix of SOURCE models on a benchmark
whose items are opaque column indices.  You choose at most ``k`` item columns; the evaluator then
reveals each TARGET model's responses on those columns only and you predict every target's accuracy
on the FULL benchmark.  Targets are either "random_targets" (look like the sources) or
"strong_targets" (stronger than every source, so predictions must extrapolate).

Protocol (unchanged from the starter): reset -> load_source (1-2 chunks) -> select -> predict, each with
the exact documented response dicts ({"ok": True}, {"indices": [...]}, {"predictions": [...]}).

Method (survey-estimation view)
-------------------------------
1. Latent model.  Centre the source matrix, take a low-rank SVD (np.linalg.svd on the small model x model
   Gram matrix) -> item means mu_i, item loadings W[:, i], prior variance of each ability coordinate and a
   per-item residual variance v_i.  A target's ability z solves a ridge/MAP weighted normal equation
   (np.linalg.solve) on its k answers; P(correct) on every item is clip(mu + z W, 0, 1).
2. Selection.  Several candidate designs of exactly k items are built: difficulty-stratified (the starter),
   greedy Bayesian D-optimal over item loadings (max log-det gain, Sherman-Morrison style updates, final
   np.linalg.slogdet check), hybrids with a stratified or latent-space k-means medoid half.
3. Estimator.  Model-assisted difference estimator
       (sum observed + sum_{unselected} P_hat [+ (n-k) * mean residual on the subset]) / n
   blended with the starter's source-calibrated subset mean:  alpha * B + (1 - alpha) * A.
4. All hyper-parameters (design, rank, prior strength, bias correction on/off, blend weight alpha) are chosen
   ONLY from source models, by pseudo-target validation inside the source set: random folds for
   "random_targets", hold-out of the strongest 20% / 10% source models for "strong_targets" (the
   ``split`` field supplied with load_source).  alpha = 0 (pure starter estimator on the stratified design)
   is always in the search space, so the method falls back to the starter where the latent model hurts.

Additions in this candidate (c02, on top of the above, which stays reachable as a subset)
-----------------------------------------------------------------------------------------
5. Logistic latent model ``fit_logistic_latent``: logit P = b_i + a_i . theta_m, alternating L2-regularised
   Newton/IRLS sweeps; target abilities by MAP-Newton on the k revealed answers
   (``predict_full_score_logistic``); estimate = mean sigmoid probability (+ optional residual correction).
6. Fisher D-optimal designs ``select_items_fisher_dopt``: greedy log-det of sum_i p_i (1 - p_i) a_i a_i^T at
   reference abilities from the upper tail of the source abilities (+ margin beyond it); pure and hybrid
   (stratified / linear D-opt half) designs are added to the design list.
7. ``stack_weights``: scipy.optimize.nnls weights (sum ~ 1) over starter / linear / logistic estimates fit
   on the same source-only pseudo-target folds (strongest-holdout folds for strong_targets).  Selection of
   design / rank / tau / weights uses the incumbent's RMSE + rank objective; logistic fits are time-boxed
   (LOGI_BUDGET) and any failure falls back to the incumbent configuration.

Additions in this candidate (c03, on top of everything above, which stays reachable)
-----------------------------------------------------------------------------------
8. ``fit_logistic_latent_bagged``: logistic fits for ranks (2, 3, 4) on all source models and on bootstrap
   resamples of them.  ``posterior_mean_probs``: Laplace posterior of the target ability (MAP + inverse of
   Fisher information + prior precision) and probit-style posterior-mean item probabilities; predictions are
   averaged over the bag.  ``select_prior_precision`` picks the prior scale on the pseudo-target folds
   (strongest-holdout for strong_targets).
9. ``fit_tail_correction`` / ``apply_tail_correction``: ridge-shrunk (to identity) monotone residual
   correction fitted on strongest-holdout pseudo-target predictions, applied only above the source median
   accuracy.  The corrected posterior-mean predictor is a 4th column of an NNLS stack
   (``stack_weights_multi``) with the incumbent winner's components; it is used only if it beats the
   incumbent on the pseudo-target folds (MSE factor TAIL_ACCEPT, no rank loss), and any exception / time-out
   falls back to the incumbent prediction.  Not implemented: Fisher matrix averaging over bags for item
   selection (latent coordinates are not aligned across bags); the incumbent designs are unchanged.
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "8")

import base64
import math
import time

import numpy as np

try:  # optional, used for the rank-aware part of validation / k-means medoid design
    import scipy.stats
except Exception:  # pragma: no cover
    scipy = None
try:  # optional, used for the non-negative stacking weights
    import scipy.optimize
except Exception:  # pragma: no cover
    pass
try:
    from sklearn.cluster import KMeans
except Exception:  # pragma: no cover
    KMeans = None

_STATE = {}

RMAX = 12
R_GRID = (1, 2, 3, 5, 8, 12)
TAU_GRID = (1.0, 4.0, 16.0)
ALPHA_GRID = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
# (name, base design for the non-D-opt part, fraction of the budget chosen by D-optimality)
DESIGNS = (
    ("strat", "strat", 0.0),
    ("strat_dopt", "strat", 0.5),
    ("dopt", "strat", 1.0),
    ("kmeans_dopt", "kmeans", 0.5),
)
# Fisher-information D-optimal designs under the logistic latent model: (name, base for the other half, fraction by Fisher)
FISHER_DESIGNS = (
    ("fisher", "strat", 1.0),
    ("strat_fisher", "strat", 0.5),
    ("lin_fisher", "lin", 0.5),
)
LOG_R_GRID = (2, 3, 1, 5)  # order matters: cheapest / most useful first when the time budget runs out
LOG_TAU_GRID = (1.0, 4.0, 16.0)
LOG_R_DESIGN = 3
REF_MARGINS = (0.0, 0.5, 1.0)  # reference abilities: top-10% mean + margin * std along the ability direction
LOGI_BUDGET = 45.0  # seconds of select() that may be spent on logistic fits
# tail-calibrated posterior-mean stage (c03): bagged ranks x bootstrap resamples of the source models
TAIL_RANKS = (2, 3, 4)
TAIL_BOOT = 1  # bootstrap resamples per rank (in addition to the full-source fit)
TAIL_TAU_GRID = (1.0, 4.0, 16.0, 64.0)  # prior covariance scale (larger = weaker prior)
TAIL_RIDGE = 0.5  # ridge pull of the residual-correction coefficients towards identity (zero correction)
TAIL_ACCEPT = 0.97  # the tail stack must beat the incumbent pseudo-target MSE by this factor
BAG_BUDGET = 100.0  # seconds of select() that may be spent on the tail stage


def _decode(b64, rows, cols):
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).reshape(rows, -1)
    return np.unpackbits(raw, axis=1)[:, :cols]


def _reset(seed):
    _STATE.clear()
    _STATE["rng"] = np.random.default_rng(int(seed))
    _STATE["rng_f"] = np.random.default_rng(int(seed) * 7 + 13)
    _STATE["rng_b"] = np.random.default_rng(int(seed) * 31 + 5)
    _STATE["chunks"] = {}
    return {"ok": True}


def _load_source(req):
    chunks = _STATE["chunks"]
    chunks[int(req["chunk_index"])] = _decode(req["data_b64"], int(req["row_count"]), int(req["n_items"]))
    _STATE["n_chunks"] = int(req["n_chunks"])
    _STATE["k"] = int(req["k"])
    _STATE["split"] = str(req.get("split", "random_targets"))
    if len(chunks) == _STATE["n_chunks"]:
        _STATE["src"] = np.concatenate([chunks[i] for i in sorted(chunks)], axis=0)
    return {"ok": True}


# ----------------------------------------------------------------------------------------------
# latent model
# ----------------------------------------------------------------------------------------------
def _fit_latent(S, rmax=RMAX):
    """Low-rank fit of the centred source matrix S (m x n, float64)."""
    m, n = S.shape
    mu = S.mean(axis=0)
    Sc = S - mu
    gram = Sc @ Sc.T  # m x m, symmetric PSD
    U, s2, _ = np.linalg.svd(gram)
    s_all = np.sqrt(np.maximum(s2, 0.0))
    r = int(min(rmax, max(m - 1, 1)))
    s = s_all[:r]
    keep = s > 1e-6 * max(float(s_all[0]), 1e-12)
    r = int(keep.sum())
    if r == 0:
        v = np.full(n, 0.05)
        return {"mu": mu, "W": np.zeros((1, n)), "pv": np.array([1e-6]), "v": v, "m": m}
    s = s[:r]
    U = U[:, :r]
    W = (U.T @ Sc) / s[:, None]  # r x n, orthonormal rows
    Z = U * s
    resid = Sc - Z @ W
    v = (resid ** 2).mean(axis=0)
    floor = max(0.02, float(np.percentile(v, 5)))
    v = np.maximum(v, floor)
    return {"mu": mu, "W": W, "pv": s ** 2 / m, "v": v, "m": m}


def predict_full_score(fit, idx, Y, r, tau):
    """Model-assisted estimates for targets with answers Y (t x k) on items idx.

    Returns (plain, bias_corrected): plain = (observed sum + sum of predicted P(correct) on unselected
    items)/n ; bias_corrected adds the mean residual (observed - predicted) of the subset on the remaining
    n - k items (generalised-regression correction)."""
    mu, W, pv, v = fit["mu"], fit["W"], fit["pv"], fit["v"]
    n = mu.shape[0]
    idx = np.asarray(idx, dtype=int)
    k = idx.size
    r = int(min(r, W.shape[0]))
    Ws = W[:r][:, idx]
    wts = 1.0 / v[idx]
    A = (Ws * wts) @ Ws.T + np.diag(1.0 / (tau * pv[:r]))
    b = (Ws * wts) @ (Y - mu[idx]).T
    z = np.linalg.solve(A, b)  # r x t
    P = np.clip(mu[None, :] + z.T @ W[:r], 0.0, 1.0)
    Psel = P[:, idx]
    unsel = P.sum(axis=1) - Psel.sum(axis=1)
    obs = Y.sum(axis=1)
    resid_mean = (Y - Psel).mean(axis=1)
    plain = (obs + unsel) / n
    corrected = (obs + unsel + (n - k) * resid_mean) / n
    return np.clip(plain, 0.0, 1.0), np.clip(corrected, 0.0, 1.0)


def _calibrated_mean(S, idx, Y):
    """Starter estimator: linear map fitted on sources, subset mean -> full accuracy."""
    tmean = Y.mean(axis=1)
    sub = S[:, idx].mean(axis=1)
    full = S.mean(axis=1)
    if sub.size >= 3 and np.ptp(sub) > 1e-9:
        slope, intercept = np.polyfit(sub, full, 1)
        return np.clip(slope * tmean + intercept, 0.0, 1.0)
    return np.clip(tmean, 0.0, 1.0)


# ----------------------------------------------------------------------------------------------
# logistic (multidimensional 2PL / IRT-style) latent model
# ----------------------------------------------------------------------------------------------
def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -12.0, 12.0)))


def fit_logistic_latent(S, r, sweeps=8, lam_a=0.5, lam_b=0.05, lam_t=1.0, deadline=None):
    """Rank-r logistic latent model  logit P_mi = b_i + a_i . theta_m  fit on the source matrix S (m x n).

    Alternating L2-regularised Newton/IRLS sweeps: item parameters (b_i, a_i) given theta (batched
    (r+1)x(r+1) Newton systems), then model abilities theta_m given the items.  theta is initialised from
    the SVD of the centred matrix.  Returns a dict with a (n x r), b (n), theta (m x r) and the empirical
    mean / covariance of the source abilities (used as the Gaussian prior for target abilities)."""
    m, n = S.shape
    r = int(max(1, min(r, m - 1, n)))
    d = r + 1
    mu = S.mean(axis=0)
    b = np.log(np.clip(mu, 0.02, 0.98) / (1.0 - np.clip(mu, 0.02, 0.98)))
    Sc = S - mu
    U, _, _ = np.linalg.svd(Sc @ Sc.T)
    theta = U[:, :r] * math.sqrt(m)
    a = np.zeros((n, r))
    reg_item = np.array([lam_b] + [lam_a] * r)
    eye_r = np.eye(r)
    for _ in range(int(sweeps)):
        # --- items given abilities
        X = np.hstack([np.ones((m, 1)), theta])
        XX = (X[:, :, None] * X[:, None, :]).reshape(m, d * d)
        Bp = np.hstack([b[:, None], a])
        P = _sigmoid(X @ Bp.T)
        w = P * (1.0 - P)
        G = X.T @ (S - P) - (Bp * reg_item).T
        H = (w.T @ XX).reshape(n, d, d) + np.diag(reg_item)[None]
        step = np.linalg.solve(H, G.T[:, :, None])[:, :, 0]
        Bp = Bp + np.clip(step, -2.0, 2.0)
        b, a = Bp[:, 0].copy(), Bp[:, 1:].copy()
        # --- abilities given items
        AA = (a[:, :, None] * a[:, None, :]).reshape(n, r * r)
        P = _sigmoid(b[None, :] + theta @ a.T)
        w = P * (1.0 - P)
        G = (S - P) @ a - lam_t * theta
        H = (w @ AA).reshape(m, r, r) + lam_t * eye_r[None]
        step = np.linalg.solve(H, G[:, :, None])[:, :, 0]
        theta = theta + np.clip(step, -2.0, 2.0)
        if deadline is not None and time.time() > deadline:
            break
    tmean = theta.mean(axis=0)
    tc = theta - tmean
    cov = (tc.T @ tc) / m + 1e-4 * eye_r
    return {"a": a, "b": b, "theta": theta, "mean": tmean, "cov": cov, "r": r, "m": m}


def predict_full_score_logistic(fit, idx, Y, r, tau):
    """Logistic-model estimates for targets with answers Y (t x k) on items idx.

    Target abilities are MAP estimates (Newton on the k answers, Gaussian prior = tau * source ability
    covariance).  Returns (plain, bias_corrected) exactly like ``predict_full_score``: plain =
    (observed sum + sum of sigmoid probabilities on unselected items)/n, corrected adds (n-k) * mean subset
    residual.  ``r`` is the rank the fit was built with (kept for interface symmetry)."""
    a, b = fit["a"], fit["b"]
    n, rr = a.shape
    idx = np.asarray(idx, dtype=int)
    k = idx.size
    t = Y.shape[0]
    a_s, b_s = a[idx], b[idx]
    prec = np.linalg.inv(tau * fit["cov"])
    prec = 0.5 * (prec + prec.T)
    AA = (a_s[:, :, None] * a_s[:, None, :]).reshape(k, rr * rr)
    mean = fit["mean"]
    th = np.tile(mean, (t, 1))
    for _ in range(15):
        P = _sigmoid(b_s[None, :] + th @ a_s.T)
        w = P * (1.0 - P)
        G = (Y - P) @ a_s - (th - mean) @ prec
        H = (w @ AA).reshape(t, rr, rr) + prec[None]
        step = np.clip(np.linalg.solve(H, G[:, :, None])[:, :, 0], -3.0, 3.0)
        th = th + step
        if float(np.abs(step).max()) < 1e-6:
            break
    P = _sigmoid(b[None, :] + th @ a.T)
    Psel = P[:, idx]
    unsel = P.sum(axis=1) - Psel.sum(axis=1)
    obs = Y.sum(axis=1)
    resid_mean = (Y - Psel).mean(axis=1)
    plain = (obs + unsel) / n
    corrected = (obs + unsel + (n - k) * resid_mean) / n
    return np.clip(plain, 0.0, 1.0), np.clip(corrected, 0.0, 1.0)


def _reference_abilities(lfit, S):
    """Reference abilities in the upper tail of (and slightly beyond) the source ability distribution."""
    th = lfit["theta"]
    m, rr = th.shape
    acc = S.mean(axis=1)
    dvec = th.T @ (acc - acc.mean())
    nrm = float(np.linalg.norm(dvec))
    if nrm < 1e-12:
        dvec = np.zeros(rr)
        dvec[0] = 1.0
    else:
        dvec = dvec / nrm
    proj = th @ dvec
    sd = float(proj.std())
    top = np.argsort(proj, kind="stable")[-max(1, m // 10):]
    base = th[top].mean(axis=0)
    return np.array([base + mg * sd * dvec for mg in REF_MARGINS])


def stack_weights(A, B_lin, B_log, truth):
    """Non-negative stacking weights (sum ~ 1) over starter / linear / logistic estimates.

    Solved with scipy.optimize.nnls on source pseudo-target predictions, with an augmented heavily
    weighted sum-to-one row.  Falls back to the starter alone on any numerical failure."""
    try:
        cols = np.column_stack([A, B_lin, B_log])
        lam = 5.0 * math.sqrt(len(truth))
        aug = np.vstack([cols, lam * np.ones((1, cols.shape[1]))])
        rhs = np.concatenate([truth, [lam]])
        w, _ = scipy.optimize.nnls(aug, rhs)
        s = float(w.sum())
        if not np.all(np.isfinite(w)) or s <= 1e-9:
            return (1.0, 0.0, 0.0)
        w = w / s
        return (float(w[0]), float(w[1]), float(w[2]))
    except Exception:
        return (1.0, 0.0, 0.0)


# ----------------------------------------------------------------------------------------------
# tail-calibrated posterior-mean estimator (bagged logistic fits + Laplace posterior mean +
# strongest-holdout residual correction); always an *extra* stack candidate on top of the incumbent
# ----------------------------------------------------------------------------------------------
def fit_logistic_latent_bagged(S, ranks, n_boot, rng, deadline=None, sweeps=6):
    """Bag of logistic latent fits: for every rank in ``ranks`` one fit on all source models plus
    ``n_boot`` fits on bootstrap resamples of the source models (rows drawn with rng.choice).
    Raises TimeoutError when ``deadline`` passes so the caller can fall back to the incumbent."""
    m = S.shape[0]
    bags = []
    for r in ranks:
        for bi in range(int(n_boot) + 1):
            if deadline is not None and time.time() > deadline:
                raise TimeoutError("bag budget exhausted")
            rows = np.arange(m) if bi == 0 else rng.choice(m, size=m, replace=True)
            bags.append(fit_logistic_latent(S[rows], r, sweeps=sweeps))
    return bags


def posterior_mean_probs(fit, idx, Y, tau):
    """Posterior-mean P(correct) on every item for targets with answers Y (t x k) on items idx.

    Laplace approximation of the target ability posterior: mean = MAP (Newton, prior = tau * source
    ability covariance), covariance = inverse(Fisher information + prior precision).  The item
    probability is the probit-style approximation sigmoid(m_i / sqrt(1 + pi v_i / 8)) with m_i = b_i +
    a_i . theta_MAP and v_i = a_i^T Sigma a_i."""
    a, b = fit["a"], fit["b"]
    n, rr = a.shape
    idx = np.asarray(idx, dtype=int)
    k = idx.size
    t = Y.shape[0]
    a_s, b_s = a[idx], b[idx]
    prec = np.linalg.inv(tau * fit["cov"])
    prec = 0.5 * (prec + prec.T)
    AA = (a_s[:, :, None] * a_s[:, None, :]).reshape(k, rr * rr)
    mean = fit["mean"]
    th = np.tile(mean, (t, 1))
    for _ in range(15):
        P = _sigmoid(b_s[None, :] + th @ a_s.T)
        w = P * (1.0 - P)
        G = (Y - P) @ a_s - (th - mean) @ prec
        H = (w @ AA).reshape(t, rr, rr) + prec[None]
        step = np.clip(np.linalg.solve(H, G[:, :, None])[:, :, 0], -3.0, 3.0)
        th = th + step
        if float(np.abs(step).max()) < 1e-6:
            break
    P = _sigmoid(b_s[None, :] + th @ a_s.T)
    w = P * (1.0 - P)
    H = (w @ AA).reshape(t, rr, rr) + prec[None]
    Sigma = np.linalg.inv(H)
    m_all = b[None, :] + th @ a.T
    v = np.empty_like(m_all)
    for j in range(t):
        v[j] = np.einsum("nr,nr->n", a @ Sigma[j], a)
    v = np.maximum(v, 0.0)
    return _sigmoid(m_all / np.sqrt(1.0 + np.pi * v / 8.0))


def predict_full_score_bagged(bags, idx, Y, tau):
    """Bag-averaged posterior-mean estimates (plain, bias_corrected), same definitions as
    ``predict_full_score_logistic``.  Non-finite bags are skipped; raises if none is usable."""
    idx = np.asarray(idx, dtype=int)
    k = idx.size
    obs = Y.sum(axis=1)
    plains, corrs = [], []
    for fit in bags:
        try:
            P = posterior_mean_probs(fit, idx, Y, tau)
        except Exception:
            continue
        n = P.shape[1]
        Psel = P[:, idx]
        unsel = P.sum(axis=1) - Psel.sum(axis=1)
        resid_mean = (Y - Psel).mean(axis=1)
        plain = (obs + unsel) / n
        corr = (obs + unsel + (n - k) * resid_mean) / n
        if np.all(np.isfinite(plain)) and np.all(np.isfinite(corr)):
            plains.append(np.clip(plain, 0.0, 1.0))
            corrs.append(np.clip(corr, 0.0, 1.0))
    if not plains:
        raise ValueError("no usable bag")
    return np.mean(plains, axis=0), np.mean(corrs, axis=0)


def select_prior_precision(bag_folds, folds, S, idx, grid=TAIL_TAU_GRID):
    """Choose the prior scale tau (and plain / bias-corrected variant) of the bagged posterior-mean
    predictor by pseudo-target MSE on source hold-out folds (the strongest-holdout folds when the episode
    split is strong_targets).  Returns (tau, use_corrected, pooled pseudo-target predictions)."""
    full = S.mean(axis=1)
    truth = np.concatenate([full[te] for _, te in folds])
    best = None
    for tau in grid:
        parts = ([], [])
        for bags, (_, te) in zip(bag_folds, folds):
            Y = S[te][:, idx].astype(np.float64)
            plain, corr = predict_full_score_bagged(bags, idx, Y, tau)
            parts[0].append(plain)
            parts[1].append(corr)
        for ci in (0, 1):
            pred = np.concatenate(parts[ci])
            mse = _mse(pred, truth)
            if np.isfinite(mse) and (best is None or mse < best[0]):
                best = (mse, float(tau), ci, pred)
    if best is None:
        raise ValueError("prior precision selection failed")
    return best[1], best[2], best[3]


def _tail_feats(p, corr):
    return np.clip((p - corr["thr"]) / corr["ramp"], 0.0, 1.0), np.maximum(p - corr["thr"], 0.0) / corr["sd"]


def apply_tail_correction(pred, corr):
    """Apply the residual correction only where pred exceeds the source median accuracy (corr["thr"]);
    corr=None is the identity."""
    pred = np.asarray(pred, dtype=np.float64)
    if corr is None:
        return pred
    f1, f2 = _tail_feats(pred, corr)
    return np.clip(pred + corr["a"] * f1 + corr["c"] * f2, 0.0, 1.0)


def fit_tail_correction(pred, truth, thr, ramp, lam=TAIL_RIDGE):
    """Ridge-shrunk (towards identity) monotone correction y ~ p + a * ramp(p) + c * hinge(p), fitted on
    pseudo-target predictions above ``thr`` only.  Returns None (identity) if the fit is degenerate,
    non-finite or non-monotone."""
    try:
        pred = np.asarray(pred, dtype=np.float64)
        truth = np.asarray(truth, dtype=np.float64)
        sel = pred > thr
        if int(sel.sum()) < 4:
            return None
        p = pred[sel]
        e = truth[sel] - p
        sd = float((p - thr).std())
        if not sd > 1e-6:
            return None
        corr = {"thr": float(thr), "ramp": float(max(ramp, 1e-3)), "sd": sd, "a": 0.0, "c": 0.0}
        f1, f2 = _tail_feats(p, corr)
        X = np.column_stack([f1, f2])
        npts = X.shape[0]
        beta = np.linalg.solve(X.T @ X / npts + lam * np.eye(2), X.T @ e / npts)
        if not np.all(np.isfinite(beta)):
            return None
        corr["a"], corr["c"] = float(beta[0]), float(beta[1])
        g = np.linspace(thr, 1.0, 200)
        h1, h2 = _tail_feats(g, corr)
        raw = g + corr["a"] * h1 + corr["c"] * h2
        if np.any(np.diff(raw) < -1e-9):
            return None
        return corr
    except Exception:
        return None


def stack_weights_multi(cols, truth):
    """Non-negative stacking weights (sum ~ 1) over any number of candidate columns via
    scipy.optimize.nnls with a heavily weighted sum-to-one row; falls back to the first column."""
    first = np.zeros(len(cols))
    first[0] = 1.0
    try:
        C = np.column_stack(cols)
        lam = 5.0 * math.sqrt(len(truth))
        aug = np.vstack([C, lam * np.ones((1, C.shape[1]))])
        rhs = np.concatenate([truth, [lam]])
        w, _ = scipy.optimize.nnls(aug, rhs)
        s = float(w.sum())
        if not np.all(np.isfinite(w)) or s <= 1e-9:
            return first
        return w / s
    except Exception:
        return first


def _tail_stage(S, split, idx, cfg, deadline, rng_b):
    """Extra stack candidate: bagged posterior-mean logistic predictor + tail correction.

    Uses the pseudo-target folds / component predictions of the incumbent winner ``cfg`` (same folds, same
    truth).  Returns a dict with the final bags, tau, correction and 4-column stack weights, or None when the
    candidate does not beat the incumbent on the source pseudo-targets (-> incumbent behaviour)."""
    folds, truth, sizes = cfg["_folds"], cfg["_truth"], cfg["_sizes"]
    A, Bl, Bg = cfg["_comp"]
    inc = cfg["_pred"]
    bag_folds = [fit_logistic_latent_bagged(S[tr], TAIL_RANKS, TAIL_BOOT, rng_b, deadline) for tr, _ in folds]
    tau, use_corr, raw = select_prior_precision(bag_folds, folds, S, idx)
    full = S.mean(axis=1)
    corr = None
    if split == "strong_targets":
        thr = float(np.median(full))
        corr = fit_tail_correction(raw, truth, thr, 0.5 * float(np.std(full)) + 1e-3)
    Tc = np.clip(apply_tail_correction(raw, corr), 0.0, 1.0)
    cols = [A, A if Bl is None else Bl, A if Bg is None else Bg, Tc]
    w4 = stack_weights_multi(cols, truth)
    new = np.clip(sum(float(w) * c for w, c in zip(w4, cols)), 0.0, 1.0)
    mse_new, mse_inc = _mse(new, truth), _mse(inc, truth)
    if not (np.isfinite(mse_new) and mse_new < TAIL_ACCEPT * mse_inc):
        return None
    if _rank_scores(new, truth, sizes) < _rank_scores(inc, truth, sizes) - 0.01:
        return None
    if w4[3] <= 1e-6:
        return None
    bags = fit_logistic_latent_bagged(S, TAIL_RANKS, TAIL_BOOT, rng_b, deadline)
    if cfg.get("log") is not None:
        rl = cfg["log"][0]
        if rl not in _STATE["logfits"]:
            _STATE["logfits"][rl] = fit_logistic_latent(S, rl)
    return {"bags": bags, "tau": tau, "c": int(use_corr), "corr": corr, "w4": [float(w) for w in w4]}


# ----------------------------------------------------------------------------------------------
# item selection
# ----------------------------------------------------------------------------------------------
def _stratified(difficulty, n_pick, rng, exclude=()):
    if n_pick <= 0:
        return []
    n = difficulty.shape[0]
    order = np.argsort(difficulty + 1e-9 * rng.random(n), kind="stable")
    strata = np.array_split(order, min(n_pick, n))
    return [int(rng.choice(g)) for g in strata if len(g)]


def _kmeans_medoids(X, n_pick, rng):
    n = X.shape[0]
    if n_pick <= 0:
        return []
    if KMeans is None or n_pick >= n:
        return [int(i) for i in rng.choice(n, size=min(n_pick, n), replace=False)]
    km = KMeans(n_clusters=n_pick, n_init=1, max_iter=50, random_state=int(rng.integers(0, 2 ** 31 - 1)))
    labels = km.fit_predict(X)
    d = ((X - km.cluster_centers_[labels]) ** 2).sum(axis=1)
    picks = []
    for c in range(n_pick):
        members = np.flatnonzero(labels == c)
        if members.size:
            picks.append(int(members[np.argmin(d[members])]))
    return picks


def _item_features(fit, r):
    r = int(min(r, fit["W"].shape[0]))
    return (fit["W"][:r] / np.sqrt(fit["v"])).T  # n x r, noise-weighted loadings


def select_items_dopt(fit, r, n_pick, chosen):
    """Greedy Bayesian D-optimal design over item loadings.

    Maximises log det(M), M = prior precision + sum_i f_i f_i^T; the greedy gain of item i is
    log(1 + f_i^T M^{-1} f_i).  ``chosen`` items are already in the design.  Returns (new items, logdet)."""
    F = _item_features(fit, r)
    n, rr = F.shape
    M = np.diag(1.0 / fit["pv"][:rr])
    chosen = [int(i) for i in chosen]
    avail = np.ones(n, dtype=bool)
    for i in chosen:
        M += np.outer(F[i], F[i])
        avail[i] = False
    new = []
    for _ in range(int(min(n_pick, avail.sum()))):
        AF = np.linalg.solve(M, F.T).T
        gain = np.einsum("ij,ij->i", AF, F)
        gain[~avail] = -np.inf
        j = int(np.argmax(gain))
        M += np.outer(F[j], F[j])
        avail[j] = False
        new.append(j)
    sign, logdet = np.linalg.slogdet(M)
    return new, (float(logdet) if sign > 0 else -np.inf)


def select_items_fisher_dopt(lfit, r, n_pick, chosen, theta_ref, tau=4.0):
    """Greedy D-optimal design on Fisher information of the logistic model at reference abilities.

    Item i contributes I_i = p_i (1 - p_i) a_i a_i^T, with p_i averaged over the reference abilities
    ``theta_ref`` (R x r, e.g. upper tail of the source abilities plus a margin), on top of the prior
    precision (tau * source ability covariance)^-1.  Greedy gain log(1 + f_i^T M^-1 f_i) with f_i =
    sqrt(w_i) a_i (rank-one updates).  Returns (new items, logdet of the final information matrix)."""
    a, b = lfit["a"], lfit["b"]
    n, rr = a.shape
    refs = np.atleast_2d(theta_ref)
    p = _sigmoid(b[None, :] + refs @ a.T)
    wI = (p * (1.0 - p)).mean(axis=0)
    F = a * np.sqrt(wI)[:, None]
    M = np.linalg.inv(tau * lfit["cov"])
    M = 0.5 * (M + M.T)
    avail = np.ones(n, dtype=bool)
    for i in chosen:
        M = M + np.outer(F[int(i)], F[int(i)])
        avail[int(i)] = False
    new = []
    for _ in range(int(min(n_pick, avail.sum()))):
        AF = np.linalg.solve(M, F.T).T
        gain = np.einsum("ij,ij->i", AF, F)
        gain[~avail] = -np.inf
        j = int(np.argmax(gain))
        M = M + np.outer(F[j], F[j])
        avail[j] = False
        new.append(j)
    sign, logdet = np.linalg.slogdet(M)
    return new, (float(logdet) if sign > 0 else -np.inf)


def _build_fisher_design(base, frac, lfit, theta_ref, fit, k, r_sel, difficulty, rng):
    n = difficulty.shape[0]
    n_f = int(round(frac * k))
    n_b = k - n_f
    if n_b <= 0:
        picks = []
    elif base == "lin":
        picks, _ = select_items_dopt(fit, r_sel, n_b, [])
    else:
        picks = _stratified(difficulty, n_b, rng)
    picks = list(dict.fromkeys(int(i) for i in picks))
    new, logdet = select_items_fisher_dopt(lfit, lfit["r"], k - len(picks), picks, theta_ref)
    picks += new
    picks = list(dict.fromkeys(picks))
    if len(picks) < k:
        rest = np.setdiff1d(np.arange(n), np.array(picks, dtype=int))
        picks += [int(i) for i in rng.choice(rest, size=min(k - len(picks), rest.size), replace=False)]
    return np.array(picks[:k], dtype=int), logdet


def _build_design(base, frac, fit, k, r_sel, difficulty, kmX, rng):
    n = difficulty.shape[0]
    n_d = int(round(frac * k))
    n_b = k - n_d
    if base == "kmeans":
        picks = _kmeans_medoids(kmX, n_b, rng)
    else:
        picks = _stratified(difficulty, n_b, rng)
    picks = list(dict.fromkeys(picks))
    logdet = 0.0
    if n_d > 0 or len(picks) < k:
        new, logdet = select_items_dopt(fit, r_sel, k - len(picks), picks)
        picks += new
    picks = list(dict.fromkeys(picks))
    if len(picks) < k:  # safety: top up with random unused items
        rest = np.setdiff1d(np.arange(n), np.array(picks, dtype=int))
        picks += [int(i) for i in rng.choice(rest, size=min(k - len(picks), rest.size), replace=False)]
    return np.array(picks[:k], dtype=int), logdet


# ----------------------------------------------------------------------------------------------
# validation inside the source set (no target information is used)
# ----------------------------------------------------------------------------------------------
def _make_folds(S, split, rng):
    m = S.shape[0]
    if m < 10:
        return []
    full = S.mean(axis=1)
    if split == "strong_targets":
        order = np.argsort(full, kind="stable")
        folds = []
        for frac in (0.2, 0.1):
            h = max(2, int(round(frac * m)))
            folds.append((order[:-h], order[-h:]))
        return folds
    perm = rng.permutation(m)
    parts = np.array_split(perm, 5)
    return [(np.concatenate([parts[j] for j in range(5) if j != i]), parts[i]) for i in range(5)]


def _rank_scores(pred, truth, fold_sizes):
    if scipy is None:
        return 1.0
    out, start = [], 0
    for sz in fold_sizes:
        p, t = pred[start:start + sz], truth[start:start + sz]
        start += sz
        if sz >= 3 and np.ptp(p) > 0 and np.ptp(t) > 0:
            rho = scipy.stats.spearmanr(p, t)[0]
            ken = scipy.stats.kendalltau(p, t)[0]
            out.append(0.5 * (rho + ken))
    return float(np.mean(out)) if out else 1.0


def _mse(pred, truth):
    return float(np.mean((pred - truth) ** 2))


def _validate(S, split, designs, rng, deadline):
    """Pick (design, linear cfg, logistic cfg, blend/stack weights) minimising pseudo-target error.

    Candidate families per design (all scored on the same source-only pseudo-target folds):
      * incumbent: alpha * linear + (1 - alpha) * starter (alpha = 0 is the pure starter),
      * logistic:  alpha * logistic + (1 - alpha) * starter,
      * stacked:   non-negative weights over (starter, linear, logistic) from ``stack_weights``."""
    folds = _make_folds(S, split, rng)
    if not folds:
        return None
    full = S.mean(axis=1)
    fits = [_fit_latent(S[tr]) for tr, _ in folds]
    truth = np.concatenate([full[te] for _, te in folds])
    sizes = [len(te) for _, te in folds]
    # logistic fits, once per (fold, rank); stop when the time budget is exhausted
    log_fold = {}
    for r in LOG_R_GRID:
        if time.time() > deadline:
            break
        try:
            lfs = []
            for tr, _ in folds:
                if r >= len(tr) or time.time() > deadline + 15.0:
                    raise ValueError("skip rank")
                lfs.append(fit_logistic_latent(S[tr], r))
            log_fold[r] = lfs
        except Exception:
            continue
    scored = []  # (mse, spec, prediction)
    for di, (name, idx) in enumerate(designs):
        A_parts = []
        lin_parts = {}
        log_parts = {}
        log_ok = True
        for fi, ((tr, te), fit) in enumerate(zip(folds, fits)):
            Y = S[te][:, idx].astype(np.float64)
            A_parts.append(_calibrated_mean(S[tr], idx, Y))
            for r in R_GRID:
                if r > fit["W"].shape[0] and r != R_GRID[0]:
                    continue
                for tau in TAU_GRID:
                    plain, corr = predict_full_score(fit, idx, Y, r, tau)
                    lin_parts.setdefault((r, tau, 0), []).append(plain)
                    lin_parts.setdefault((r, tau, 1), []).append(corr)
            if log_ok:
                try:
                    for r, lfs in log_fold.items():
                        for tau in LOG_TAU_GRID:
                            plain, corr = predict_full_score_logistic(lfs[fi], idx, Y, r, tau)
                            log_parts.setdefault((r, tau, 0), []).append(plain)
                            log_parts.setdefault((r, tau, 1), []).append(corr)
                except Exception:
                    log_ok = False
        A = np.concatenate(A_parts)
        lin = {k_: np.concatenate(p) for k_, p in lin_parts.items() if len(p) == len(folds)}
        logc = {k_: np.concatenate(p) for k_, p in log_parts.items() if len(p) == len(folds)} if log_ok else {}
        for key, B in lin.items():
            for alpha in ALPHA_GRID:
                pred = np.clip(alpha * B + (1 - alpha) * A, 0.0, 1.0)
                scored.append((_mse(pred, truth), {"design": di, "w": (1.0 - alpha, float(alpha), 0.0),
                                                   "lin": key, "log": None,
                                                   "_comp": (A, np.clip(B, 0.0, 1.0), None)}, pred))
        for key, B in logc.items():
            for alpha in ALPHA_GRID[1:]:
                pred = np.clip(alpha * B + (1 - alpha) * A, 0.0, 1.0)
                scored.append((_mse(pred, truth), {"design": di, "w": (1.0 - alpha, 0.0, float(alpha)),
                                                   "lin": None, "log": key,
                                                   "_comp": (A, None, np.clip(B, 0.0, 1.0))}, pred))
        if lin and logc:
            top_lin = sorted(lin.items(), key=lambda kv: _mse(np.clip(kv[1], 0.0, 1.0), truth))[:3]
            top_log = sorted(logc.items(), key=lambda kv: _mse(np.clip(kv[1], 0.0, 1.0), truth))[:3]
            for lk, Bl in top_lin:
                for gk, Bg in top_log:
                    w = stack_weights(A, np.clip(Bl, 0.0, 1.0), np.clip(Bg, 0.0, 1.0), truth)
                    pred = np.clip(w[0] * A + w[1] * np.clip(Bl, 0.0, 1.0) + w[2] * np.clip(Bg, 0.0, 1.0), 0.0, 1.0)
                    scored.append((_mse(pred, truth), {"design": di, "w": w, "lin": lk, "log": gk,
                                                       "_comp": (A, np.clip(Bl, 0.0, 1.0), np.clip(Bg, 0.0, 1.0))},
                                   pred))
    scored.sort(key=lambda t: t[0])
    top = scored[:15]
    best_rmse = math.sqrt(max(top[0][0], 1e-18))
    best, best_obj = None, np.inf
    for mse, spec, pred in top:
        obj = math.sqrt(mse) / best_rmse + (1.0 - _rank_scores(pred, truth, sizes))
        if obj < best_obj:
            best_obj, best = obj, (mse, spec, pred)
    mse, spec, pred = best
    cfg = dict(spec)
    cfg["val_rmse"] = math.sqrt(mse)
    # internal hand-over to the tail stage (same pseudo-target folds / truth / winner predictions)
    cfg["_folds"], cfg["_truth"], cfg["_sizes"], cfg["_pred"] = folds, truth, sizes, pred
    return cfg


# ----------------------------------------------------------------------------------------------
# protocol ops
# ----------------------------------------------------------------------------------------------
def _select(req):
    t0 = time.time()
    deadline = t0 + LOGI_BUDGET
    src = _STATE["src"]
    rng = _STATE["rng"]
    n = src.shape[1]
    k = max(1, min(int(req["k"]), n))
    S = src.astype(np.float64)
    difficulty = S.mean(axis=0)
    default = {"design": 0, "w": (1.0, 0.0, 0.0), "lin": (3, 4.0, 1), "log": None}
    _STATE["logfits"] = {}
    try:
        fit = _fit_latent(S)
        _STATE["fit"] = fit
        r_sel = int(min(8, max(2, k // 10), fit["W"].shape[0]))
        F = _item_features(fit, r_sel)
        kmX = np.column_stack([difficulty, F])
        kmX = (kmX - kmX.mean(axis=0)) / (kmX.std(axis=0) + 1e-12)
        designs, kept = [], []
        for name, base, frac in DESIGNS:
            if base == "kmeans" and KMeans is None:
                continue
            idx, logdet = _build_design(base, frac, fit, k, r_sel, difficulty, kmX, rng)
            if frac > 0 and not np.isfinite(logdet):
                continue
            designs.append((name, idx))
            kept.append(name)
        # Fisher-information D-optimal designs under the logistic latent model (extra candidates)
        try:
            rF = int(min(LOG_R_DESIGN, max(1, S.shape[0] - 2)))
            lfit = fit_logistic_latent(S, rF)
            _STATE["logfits"][rF] = lfit
            refs = _reference_abilities(lfit, S)
            rng_f = _STATE["rng_f"]
            for name, base, frac in FISHER_DESIGNS:
                try:
                    idx, logdet = _build_fisher_design(base, frac, lfit, refs, fit, k, r_sel, difficulty, rng_f)
                except Exception:
                    continue
                if not np.isfinite(logdet) or len(set(int(i) for i in idx)) != k:
                    continue
                designs.append((name, idx))
                kept.append(name)
        except Exception:
            pass
        cfg = None
        try:
            cfg = _validate(S, _STATE.get("split", "random_targets"), designs, rng, deadline)
        except Exception:
            cfg = None
        if cfg is None:  # too few source models to validate: conservative blend on the hybrid design
            di = kept.index("strat_dopt") if "strat_dopt" in kept else 0
            cfg = dict(default, design=di, w=(0.7, 0.3, 0.0))
        if cfg["w"][2] > 0.0 and cfg["log"] is not None:
            try:
                rl = cfg["log"][0]
                if rl not in _STATE["logfits"]:
                    _STATE["logfits"][rl] = fit_logistic_latent(S, rl)
            except Exception:
                cfg = dict(default, design=cfg["design"])
        idx = designs[cfg["design"]][1]
        _STATE["cfg"] = cfg
        # tail-calibrated posterior-mean candidate; any failure / no pseudo-target gain -> incumbent
        _STATE["tail"] = None
        if cfg.get("_comp") is not None and cfg.get("_folds"):
            try:
                _STATE["tail"] = _tail_stage(S, _STATE.get("split", "random_targets"), np.asarray(idx, dtype=int),
                                             cfg, time.time() + BAG_BUDGET, _STATE["rng_b"])
            except Exception:
                _STATE["tail"] = None
    except Exception:
        _STATE.pop("fit", None)
        idx = np.array(_stratified(difficulty, k, rng), dtype=int)
        _STATE["cfg"] = dict(default)
    picks = [int(i) for i in idx]
    _STATE["indices"] = picks
    return {"indices": picks}


def _predict(req):
    src = _STATE["src"]
    idx = [int(i) for i in req["indices"]]
    tgt = _decode(req["data_b64"], int(req["n_targets"]), len(idx)).astype(np.float64)
    S = src.astype(np.float64)
    A = _calibrated_mean(S, idx, tgt)
    pred = A
    cfg = _STATE.get("cfg", {})
    w = cfg.get("w", (1.0, 0.0, 0.0))
    fit = _STATE.get("fit")
    comps = [A, A, A]
    if fit is not None and w[1] > 0.0 and cfg.get("lin") is not None:
        try:
            r, tau, c = cfg["lin"]
            plain, corr = predict_full_score(fit, idx, tgt, r, tau)
            B = corr if c else plain
            if np.all(np.isfinite(B)):
                comps[1] = B
        except Exception:
            pass
    lfit = _STATE.get("logfits", {}).get(cfg["log"][0]) if cfg.get("log") is not None else None
    if lfit is not None and w[2] > 0.0:
        try:
            r, tau, c = cfg["log"]
            plain, corr = predict_full_score_logistic(lfit, idx, tgt, r, tau)
            B = corr if c else plain
            if np.all(np.isfinite(B)):
                comps[2] = B
        except Exception:
            pass
    pred = w[0] * comps[0] + w[1] * np.clip(comps[1], 0.0, 1.0) + w[2] * np.clip(comps[2], 0.0, 1.0)
    pred = np.clip(pred, 0.0, 1.0)
    tail = _STATE.get("tail")
    if tail is not None:
        try:
            cols = [A, A, A]
            if cfg.get("lin") is not None:
                r, tau, c = cfg["lin"]
                plain, corr = predict_full_score(fit, idx, tgt, r, tau)
                cols[1] = np.clip(corr if c else plain, 0.0, 1.0)
            if cfg.get("log") is not None:
                r, tau, c = cfg["log"]
                plain, corr = predict_full_score_logistic(_STATE["logfits"][r], idx, tgt, r, tau)
                cols[2] = np.clip(corr if c else plain, 0.0, 1.0)
            plain, corr = predict_full_score_bagged(tail["bags"], idx, tgt, tail["tau"])
            T = np.clip(apply_tail_correction(corr if tail["c"] else plain, tail["corr"]), 0.0, 1.0)
            cols.append(T)
            alt = np.clip(sum(float(wi) * ci for wi, ci in zip(tail["w4"], cols)), 0.0, 1.0)
            if np.all(np.isfinite(alt)):
                pred = alt
        except Exception:
            pass
    return {"predictions": [float(p) if math.isfinite(float(p)) else 0.5 for p in pred]}


def handle(request):
    op = request.get("op")
    if op == "reset":
        return _reset(request["seed"])
    if op == "load_source":
        return _load_source(request)
    if op == "select":
        return _select(request)
    if op == "predict":
        return _predict(request)
    raise ValueError("unknown op")
