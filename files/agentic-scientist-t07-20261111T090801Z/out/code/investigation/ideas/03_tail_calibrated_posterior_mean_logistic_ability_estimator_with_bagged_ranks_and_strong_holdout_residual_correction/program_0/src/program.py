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


def _decode(b64, rows, cols):
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).reshape(rows, -1)
    return np.unpackbits(raw, axis=1)[:, :cols]


def _reset(seed):
    _STATE.clear()
    _STATE["rng"] = np.random.default_rng(int(seed))
    _STATE["rng_f"] = np.random.default_rng(int(seed) * 7 + 13)
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
                                                   "lin": key, "log": None}, pred))
        for key, B in logc.items():
            for alpha in ALPHA_GRID[1:]:
                pred = np.clip(alpha * B + (1 - alpha) * A, 0.0, 1.0)
                scored.append((_mse(pred, truth), {"design": di, "w": (1.0 - alpha, 0.0, float(alpha)),
                                                   "lin": None, "log": key}, pred))
        if lin and logc:
            top_lin = sorted(lin.items(), key=lambda kv: _mse(np.clip(kv[1], 0.0, 1.0), truth))[:3]
            top_log = sorted(logc.items(), key=lambda kv: _mse(np.clip(kv[1], 0.0, 1.0), truth))[:3]
            for lk, Bl in top_lin:
                for gk, Bg in top_log:
                    w = stack_weights(A, np.clip(Bl, 0.0, 1.0), np.clip(Bg, 0.0, 1.0), truth)
                    pred = np.clip(w[0] * A + w[1] * np.clip(Bl, 0.0, 1.0) + w[2] * np.clip(Bg, 0.0, 1.0), 0.0, 1.0)
                    scored.append((_mse(pred, truth), {"design": di, "w": w, "lin": lk, "log": gk}, pred))
    scored.sort(key=lambda t: t[0])
    top = scored[:15]
    best_rmse = math.sqrt(max(top[0][0], 1e-18))
    best, best_obj = None, np.inf
    for mse, spec, pred in top:
        obj = math.sqrt(mse) / best_rmse + (1.0 - _rank_scores(pred, truth, sizes))
        if obj < best_obj:
            best_obj, best = obj, (mse, spec)
    mse, spec = best
    cfg = dict(spec)
    cfg["val_rmse"] = math.sqrt(mse)
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
