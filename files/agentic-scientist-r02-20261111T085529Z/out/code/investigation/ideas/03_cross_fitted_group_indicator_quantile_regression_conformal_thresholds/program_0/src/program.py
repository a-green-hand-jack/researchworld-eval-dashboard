"""Candidate conformal prediction-set procedure for compositional (softmax) outputs.

Entry point: ``handle(request) -> response`` (``python_rpc_v1:handle``).  The wire protocol is
identical to the starter (reset / calibrate / predict; responses ``{"ok": true}`` and
``{"sets": MASK}``); see the starter docstring for the message layout.  No diagnostic fields are
added to any response.

Method (simplex-geometry aware split conformal with Mondrian calibration):

* Score: LAC score ``1 - p[label]`` (an Aitchison-vertex score is available as an alternative
  through ``_SCORE`` but the LAC score gave the smallest sets in design, see notes in memory).
* K <= 10: the evaluator's slices are classes, so we use class-conditional (Mondrian by label)
  thresholds, shrunk toward the pooled threshold for classes with few calibration rows.
* K > 10: Mondrian by predicted-confidence bin (max probability), a taxon that depends on x only
  so the guarantee is exact conditional on the bin.
* Finite-sample quantile level ``ceil((n + 1)(1 - alpha)) / n`` with a small variance-aware
  inflation: the expected under-coverage penalty is far steeper than the size cost of a tiny
  extra margin, and the margin scales with the Beta(n + 1 - l, l) coverage standard deviation.

Gated domain-classifier weighting (this candidate's addition): the unlabeled test probabilities
seen so far are compared with the calibration probabilities through a cross-fitted, ridge-penalised
logistic domain classifier on a few sorted-probability summary features.  The held-out
likelihood-ratio statistic LR gives a positive-part shrinkage beta = max(0, 1 - d / LR); when
beta is (numerically) zero -- always the case under exchangeability, where the held-out LR is
non-positive -- the unweighted Mondrian thresholds above are used verbatim (exact no-op).  Otherwise
per-test-row weighted Mondrian thresholds (Tibshirani et al. 2019, test mass at +inf) are used,
with effective-sample-size margins; any non-finite quantity falls back to the unweighted path.

The remaining helpers (CLR/ILR transforms, Aitchison distance, ILR volume, worst-slab coverage,
weighted conformal quantile, Beta coverage law, paired sign-flip test, Holm correction) implement
the evaluation protocol of the research idea; they are only used internally.
"""
import base64
import math

import numpy as np

try:  # scipy is optional for the serving path
    import scipy.stats
except Exception:  # pragma: no cover
    scipy = None

_state = {}

_SCORE = "lac"          # "lac" or "aitchison"
_EPS = 1e-6             # simplex floor for log-ratio transforms
_Z_GLOBAL = 0.7         # margin multipliers (in coverage standard deviations)
_Z_GROUP = 0.6
_SHRINK_N0 = 20.0       # pseudo-count for shrinking group thresholds toward the pooled one
_MIN_BIN = 80           # minimal calibration rows per confidence bin
_MAX_BINS = 10
_MAX_CLASSCOND_K = 10
_RIDGE = 1.0            # ridge penalty of the domain classifier (standardised features)
_MIN_TEST_DOMAIN = 40   # minimal unlabeled test rows before the domain classifier is fitted
_BETA_ON = 1e-3         # weights are used only if the shrinkage factor exceeds this
_W_CLIP = 8.0           # weights clipped to [1/_W_CLIP, _W_CLIP]
_FEAT_CLIP = 8.0        # standardised features clipped to +-_FEAT_CLIP


# --------------------------------------------------------------------------- wire helpers
def _decode(obj):
    dtype = np.dtype(obj["dtype"]).newbyteorder("<")
    arr = np.frombuffer(base64.b64decode(obj["data"]), dtype=dtype)
    return arr.reshape(obj["shape"])


def _encode_mask(mask):
    packed = np.packbits(mask.astype(np.uint8), axis=1)
    return {"dtype": "uint8", "shape": [int(mask.shape[0]), int(mask.shape[1])],
            "encoding": "packbits_base64", "data": base64.b64encode(packed.tobytes()).decode("ascii")}


# --------------------------------------------------------------------------- compositional geometry
def _close(p, eps=_EPS):
    p = np.clip(np.asarray(p, dtype=np.float64), eps, None)
    return p / p.sum(axis=-1, keepdims=True)


def clr_transform(p, eps=_EPS):
    """Centred log-ratio transform of compositions along the last axis (with simplex floor)."""
    lp = np.log(_close(p, eps))
    return lp - lp.mean(axis=-1, keepdims=True)


def _helmert_basis(D):
    """Orthonormal basis (D x (D-1)) of the CLR hyperplane (Helmert contrast matrix)."""
    V = np.zeros((D, D - 1))
    for j in range(1, D):
        V[:j, j - 1] = 1.0 / j
        V[j, j - 1] = -1.0
        V[:, j - 1] *= math.sqrt(j / (j + 1.0))
    return V


def ilr_transform(p, eps=_EPS):
    """Isometric log-ratio coordinates in R^(D-1) (Egozcue et al. style Helmert basis)."""
    c = clr_transform(p, eps)
    return c @ _helmert_basis(c.shape[-1])


def aitchison_distance(a, b, eps=_EPS):
    """Aitchison distance = Euclidean distance between CLR (equivalently ILR) coordinates."""
    return np.linalg.norm(clr_transform(a, eps) - clr_transform(b, eps), axis=-1)


def ilr_log_volume(radius, D):
    """Log-volume of a (D-1)-dimensional ILR-space ball: (D-1) log r + log V_{D-1}(1)."""
    d = D - 1
    return d * np.log(np.maximum(radius, 1e-300)) + (d / 2.0) * math.log(math.pi) - math.lgamma(d / 2.0 + 1.0)


def _score_matrix(probs):
    """Nonconformity score of every candidate label, shape [n, K]."""
    if _SCORE == "aitchison":
        K = probs.shape[1]
        c = clr_transform(probs)
        lo, hi = math.log(_EPS), math.log(1.0)
        # smoothed vertex e_j has clr = log(v) - mean(log v)
        v = np.full(K, _EPS)
        out = np.empty_like(probs, dtype=np.float64)
        for j in range(K):
            vj = v.copy()
            vj[j] = 1.0
            vj = vj / vj.sum()
            cj = np.log(vj) - np.log(vj).mean()
            out[:, j] = np.linalg.norm(c - cj, axis=1)
        return out
    return 1.0 - probs


# --------------------------------------------------------------------------- conformal quantiles
def finite_sample_level(n, alpha):
    """Conformal quantile level ceil((n + 1)(1 - alpha)) / n (may exceed 1 for tiny n)."""
    alpha = float(alpha) + 1e-12  # guards float round-off in (n + 1) * (1 - alpha)
    return np.ceil((n + 1) * (1 - alpha)) / n


def _kth_smallest(scores, level):
    n = len(scores)
    if n == 0 or level > 1.0:
        return math.inf
    k = int(np.rint(level * n))
    return float(np.sort(scores)[min(max(k, 1), n) - 1])


def _quantile(scores, alpha):
    scores = np.asarray(scores, dtype=np.float64)
    return _kth_smallest(scores, finite_sample_level(len(scores), alpha))


def weighted_conformal_quantile(scores, weights, test_weight, alpha):
    """Likelihood-ratio weighted conformal quantile (Tibshirani et al. 2019).

    Calibration points carry weights w(x_i); the test point's mass w(x) sits at +inf.
    """
    scores = np.asarray(scores, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    order = np.argsort(scores)
    s, w = scores[order], weights[order]
    p = w / (w.sum() + test_weight)
    cum = np.cumsum(p)
    idx = np.searchsorted(cum, 1.0 - alpha - 1e-12, side="left")
    return math.inf if idx >= len(s) else float(s[idx])


def beta_coverage_law(n, alpha):
    """Frozen Beta(n + 1 - l, l) law of split-conformal coverage, l = floor((n + 1) alpha)."""
    l = int(math.floor((n + 1) * alpha + 1e-12))
    l = max(l, 1)
    if scipy is not None:
        return scipy.stats.beta(n + 1 - l, l)
    return None


def mondrian_conformal_quantile(scores, groups, n_groups, alpha, n_total_test=None,
                                z_group=_Z_GROUP, z_global=_Z_GLOBAL, n0=_SHRINK_N0):
    """Per-group conformal thresholds (Mondrian calibration) with pooled-threshold shrinkage.

    ``scores`` are calibration scores, ``groups`` integer taxon ids in [0, n_groups).  Returns an
    array ``q`` of length ``n_groups``.  Each group's level is the finite-sample level
    ceil((n_g + 1)(1 - alpha_g))/n_g with alpha_g reduced by ``z_group`` coverage standard
    deviations; groups too small to support a finite quantile fall back to the pooled threshold.
    """
    scores = np.asarray(scores, dtype=np.float64)
    groups = np.asarray(groups)
    N = len(scores)
    a = float(alpha)
    var = a * (1.0 - a)
    inv_m = 0.0 if not n_total_test else 1.0 / float(n_total_test)
    a_glob = max(a - z_global * math.sqrt(var * (1.0 / max(N, 1) + inv_m)), 1e-6)
    q_glob = _quantile(scores, a_glob)
    if not np.isfinite(q_glob):
        q_glob = _quantile(scores, a)
    q = np.full(n_groups, q_glob)
    for g in range(n_groups):
        sg = scores[groups == g]
        ng = len(sg)
        if ng == 0 or not np.isfinite(_quantile(sg, a)):
            continue
        k_g = float(n_groups) * inv_m if n_total_test else 0.0
        a_g = max(a - z_group * math.sqrt(var * (1.0 / ng + k_g)), 1e-6)
        qg = _kth_smallest(sg, min(1.0, finite_sample_level(ng, a_g)))
        lam = ng / (ng + n0)
        q[g] = lam * qg + (1.0 - lam) * q_glob
    return q


# --------------------------------------------------------------------------- evaluation helpers
def worst_slab_coverage(covered, slab_ids):
    """Minimum empirical coverage over slabs and the worst-slab gap to the best slab-free mean."""
    covered = np.asarray(covered, dtype=np.float64)
    slab_ids = np.asarray(slab_ids)
    covs = [covered[slab_ids == s].mean() for s in np.unique(slab_ids)]
    return float(min(covs)) if covs else float("nan")


def paired_sign_flip_test(diffs, n_perm=2000, seed=0):
    """Two-sided paired sign-flip permutation test on per-draw differences between methods."""
    diffs = np.asarray(diffs, dtype=np.float64)
    rng = np.random.default_rng(seed)
    obs = abs(diffs.mean())
    signs = rng.choice([-1.0, 1.0], size=(n_perm, len(diffs)))
    perm = np.abs((signs * diffs).mean(axis=1))
    return float((1 + np.sum(perm >= obs - 1e-15)) / (n_perm + 1))


def holm_correction(pvals):
    """Holm-Bonferroni step-down adjusted p-values."""
    p = np.asarray(pvals, dtype=np.float64)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


# --------------------------------------------------------------------------- serving path
def _bin_edges(maxp, n_bins):
    if n_bins <= 1:
        return np.zeros(0)
    return np.quantile(maxp, np.arange(1, n_bins) / n_bins)


# --------------------------------------------------------------------------- domain-classifier weights
def _summary_features(probs):
    """Low-dimensional sorted-probability summary of each row, shape [n, 5].

    [logit(max prob), top1-top2 log ratio, normalised entropy, mean top-5 log prob minus top-1
    log prob, log of the normalised Gini impurity]; all from probabilities clipped at 1e-6.
    """
    p = np.clip(np.asarray(probs, dtype=np.float64), _EPS, 1.0)
    K = p.shape[1]
    ps = -np.sort(-p, axis=1)
    ls = np.log(ps)
    k5 = min(K, 5)
    pmax = ps[:, 0]
    f1 = np.log(pmax) - np.log(np.maximum(1.0 - pmax, _EPS))
    f2 = ls[:, 0] - ls[:, 1] if K > 1 else np.zeros(len(p))
    f3 = -(p * np.log(p)).sum(axis=1) / max(math.log(K), 1e-12)
    f4 = ls[:, :k5].mean(axis=1) - ls[:, 0]
    gini = (1.0 - (p * p).sum(axis=1)) / max(1.0 - 1.0 / K, 1e-12)
    f5 = np.log(np.clip(gini, _EPS, None))
    return np.stack([f1, f2, f3, f4, f5], axis=1)


def _fit_domain_logistic(X, y, sw, ridge=_RIDGE, iters=25):
    """Ridge-penalised weighted logistic regression by IRLS (Newton); returns [coef..., intercept]."""
    n, d = X.shape
    A = np.concatenate([X, np.ones((n, 1))], axis=1)
    R = ridge * np.eye(d + 1)
    R[d, d] = 1e-8
    b = np.zeros(d + 1)
    for _ in range(iters):
        eta = np.clip(A @ b, -30.0, 30.0)
        p = 1.0 / (1.0 + np.exp(-eta))
        g = A.T @ (sw * (p - y)) + R @ b
        H = (A * (sw * p * (1.0 - p))[:, None]).T @ A + R
        step = np.linalg.solve(H, g)
        step = np.clip(step, -5.0, 5.0)
        b = b - step
        if np.max(np.abs(step)) < 1e-7:
            break
    return b


def _positive_part_shrink(lr, df):
    """James-Stein style positive-part shrinkage factor beta = max(0, 1 - df / LR)."""
    if not np.isfinite(lr) or lr <= 0.0:
        return 0.0
    return max(0.0, 1.0 - df / lr)


def _domain_logweights(Fc, Ft, fold_c):
    """Cross-fitted domain-classifier log density ratios (test over calibration).

    Returns (beta, z_cal, z_test): ``beta`` the positive-part shrinkage factor computed from the
    held-out likelihood-ratio statistic, ``z`` the centred held-out log-odds (balanced classes).
    A row's value always comes from a model fitted on the other fold (2-fold cross-fitting over
    calibration rows and over test rows).
    """
    nc, d = Fc.shape
    nt = Ft.shape[0]
    fold_t = np.arange(nt) % 2
    zc = np.zeros(nc)
    zt = np.zeros(nt)
    ll_full = 0.0
    ll_null = 0.0
    for f in (0, 1):
        trc, tec = fold_c != f, fold_c == f
        trt, tet = fold_t != f, fold_t == f
        ncr, ntr = int(trc.sum()), int(trt.sum())
        if ncr < 5 or ntr < 5 or tec.sum() < 1 or tet.sum() < 1:
            return 0.0, zc, zt
        X = np.concatenate([Fc[trc], Ft[trt]], axis=0)
        y = np.concatenate([np.zeros(ncr), np.ones(ntr)])
        n = ncr + ntr
        sw = np.where(y > 0.5, n / (2.0 * ntr), n / (2.0 * ncr))
        b = _fit_domain_logistic(X, y, sw)
        ec = Fc[tec] @ b[:-1] + b[-1]
        et = Ft[tet] @ b[:-1] + b[-1]
        prior = math.log(ntr / ncr)
        # held-out log-likelihood of the full model vs the intercept-only (prior) model
        ll_full += float(np.sum(-np.logaddexp(0.0, ec + prior)) + np.sum(-np.logaddexp(0.0, -(et + prior))))
        ll_null += float(np.sum(-np.logaddexp(0.0, prior * np.ones(len(ec))))
                         + np.sum(-np.logaddexp(0.0, -prior * np.ones(len(et)))))
        mu = float(np.mean(ec))
        zc[tec] = ec - mu
        zt[tet] = et - mu
    lr = 2.0 * (ll_full - ll_null)
    return _positive_part_shrink(lr, float(d)), zc, zt


# --------------------------------------------------------------------------- weighted Mondrian thresholds
def _row_threshold(s_sorted, cum, w_test, level_alpha):
    """Per-test-row weighted conformal threshold; the row's own mass ``w_test`` sits at +inf."""
    n = len(s_sorted)
    m = len(w_test)
    if n == 0:
        return np.full(m, math.inf)
    target = (1.0 - level_alpha - 1e-12) * (cum[-1] + w_test)
    idx = np.searchsorted(cum, target, side="left")
    return np.where(idx >= n, math.inf, s_sorted[np.minimum(idx, n - 1)])


def _weighted_group_thresholds(scores, weights, groups, n_groups, w_test, alpha, n_total_test=None,
                               z_group=_Z_GROUP, z_global=_Z_GLOBAL, n0=_SHRINK_N0):
    """Weighted Mondrian thresholds, one per (test row, group): array of shape [n_test, n_groups].

    Calibration rows carry density-ratio weights; each test row carries its own weight at +inf.
    Margins use the effective sample size n_eff = (sum w)^2 / sum w^2 in place of the count (they
    reduce to the unweighted margins for unit weights); groups that cannot support a finite
    quantile fall back to the pooled weighted threshold and the rest are shrunk toward it.
    """
    scores = np.asarray(scores, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    groups = np.asarray(groups)
    w_test = np.asarray(w_test, dtype=np.float64)
    m = len(w_test)
    a = float(alpha)
    var = a * (1.0 - a)
    inv_m = 0.0 if not n_total_test else 1.0 / float(n_total_test)

    order = np.argsort(scores, kind="stable")
    s_all, w_all = scores[order], weights[order]
    cum_all = np.cumsum(w_all)
    n_eff_all = cum_all[-1] ** 2 / np.sum(w_all ** 2)
    a_glob = max(a - z_global * math.sqrt(var * (1.0 / max(n_eff_all, 1.0) + inv_m)), 1e-6)
    q_glob = _row_threshold(s_all, cum_all, w_test, a_glob)
    q_glob = np.where(np.isfinite(q_glob), q_glob, _row_threshold(s_all, cum_all, w_test, a))

    q = np.repeat(q_glob[:, None], n_groups, axis=1)
    for g in range(n_groups):
        sel = groups == g
        if not np.any(sel):
            continue
        og = np.argsort(scores[sel], kind="stable")
        sg, wg = scores[sel][og], weights[sel][og]
        cum = np.cumsum(wg)
        n_eff = cum[-1] ** 2 / np.sum(wg ** 2)
        finite_a = np.isfinite(_row_threshold(sg, cum, w_test, a))
        k_g = float(n_groups) * inv_m
        a_g = max(a - z_group * math.sqrt(var * (1.0 / max(n_eff, 1.0) + k_g)), 1e-6)
        tg = _row_threshold(sg, cum, w_test, a_g)
        tg = np.where(np.isfinite(tg), tg, sg[-1])
        lam = n_eff / (n_eff + n0)
        q[:, g] = np.where(finite_a, lam * tg + (1.0 - lam) * q_glob, q_glob)
    return q


def _finalize(request):
    probs = np.concatenate(_state["probs"], axis=0)
    labels = np.concatenate(_state["labels"], axis=0)
    N, K = probs.shape
    alpha = float(request["alpha"])
    M = int(request.get("n_test", 0)) or None
    scores = _score_matrix(probs)[np.arange(N), labels]
    _state["K"] = K
    _state["alpha"] = alpha
    _state["M"] = M
    _state["cal_scores"] = scores
    if K <= _MAX_CLASSCOND_K:
        _state["mode"] = "class"
        _state["n_groups"] = K
        _state["cal_groups"] = labels
        _state["q"] = mondrian_conformal_quantile(scores, labels, K, alpha, M)
    else:
        n_bins = int(min(_MAX_BINS, max(1, N // _MIN_BIN)))
        maxp = probs.max(axis=1)
        edges = _bin_edges(maxp, n_bins)
        bins = np.searchsorted(edges, maxp, side="right")
        _state["mode"] = "bin"
        _state["edges"] = edges
        _state["n_groups"] = n_bins
        _state["cal_groups"] = bins
        _state["q"] = mondrian_conformal_quantile(scores, bins, n_bins, alpha, M)
    # calibration summary features for the domain classifier (standardised with calibration moments)
    try:
        F = _summary_features(probs)
        mu = F.mean(axis=0)
        sd = F.std(axis=0)
        sd = np.where(sd > 1e-8, sd, 1.0)
        _state["F_mu"], _state["F_sd"] = mu, sd
        _state["F_cal"] = np.clip((F - mu) / sd, -_FEAT_CLIP, _FEAT_CLIP)
        _state["fold_cal"] = _state["rng"].permutation(N) % 2
        _state["F_test"] = []
    except Exception:  # pragma: no cover - keep the unweighted path usable
        _state["F_cal"] = None


def _unweighted_mask(probs, sc):
    q = _state["q"]
    if _state["mode"] == "class":
        return sc <= q[None, :]
    b = np.searchsorted(_state["edges"], probs.max(axis=1), side="right")
    return sc <= q[b][:, None]


def _weighted_mask(probs, sc):
    """Weighted mask for the current chunk, or None if no shift is detected / anything fails."""
    if _state.get("F_cal") is None:
        return None
    Fn = np.clip((_summary_features(probs) - _state["F_mu"]) / _state["F_sd"], -_FEAT_CLIP, _FEAT_CLIP)
    _state["F_test"].append(Fn)
    Ft = np.concatenate(_state["F_test"], axis=0)
    if Ft.shape[0] < _MIN_TEST_DOMAIN or not np.all(np.isfinite(Ft)):
        return None
    beta, zc, zt = _domain_logweights(_state["F_cal"], Ft, _state["fold_cal"])
    if not np.isfinite(beta) or beta <= _BETA_ON:
        return None
    lim = math.log(_W_CLIP)
    w_cal = np.exp(np.clip(beta * zc, -lim, lim))
    w_t = np.exp(np.clip(beta * zt[-len(probs):], -lim, lim))
    if not (np.all(np.isfinite(w_cal)) and np.all(np.isfinite(w_t))):
        return None
    q = _weighted_group_thresholds(_state["cal_scores"], w_cal, _state["cal_groups"], _state["n_groups"],
                                   w_t, _state["alpha"], _state["M"])
    if np.any(np.isnan(q)):
        return None
    if _state["mode"] == "class":
        return sc <= q
    b = np.searchsorted(_state["edges"], probs.max(axis=1), side="right")
    return sc <= q[np.arange(len(probs)), b][:, None]


def handle(request):
    op = request["op"]
    if op == "reset":
        _state.clear()
        _state["rng"] = np.random.default_rng(int(request["seed"]))
        _state["probs"] = []
        _state["labels"] = []
        return {"ok": True}
    if op == "calibrate":
        _state["probs"].append(_decode(request["probs"]).astype(np.float64))
        _state["labels"].append(_decode(request["labels"]).astype(np.int64))
        if request["chunk_index"] == request["num_chunks"] - 1:
            _finalize(request)
        return {"ok": True}
    if op == "predict":
        probs = _decode(request["probs"]).astype(np.float64)
        sc = _score_matrix(probs)
        mask = None
        try:
            mask = _weighted_mask(probs, sc)
        except Exception:
            mask = None
        if mask is None:
            mask = _unweighted_mask(probs, sc)
        return {"sets": _encode_mask(mask)}
    raise ValueError("unknown op")
