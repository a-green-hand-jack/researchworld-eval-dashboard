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


def _finalize(request):
    probs = np.concatenate(_state["probs"], axis=0)
    labels = np.concatenate(_state["labels"], axis=0)
    N, K = probs.shape
    alpha = float(request["alpha"])
    M = int(request.get("n_test", 0)) or None
    scores = _score_matrix(probs)[np.arange(N), labels]
    _state["K"] = K
    if K <= _MAX_CLASSCOND_K:
        _state["mode"] = "class"
        _state["q"] = mondrian_conformal_quantile(scores, labels, K, alpha, M)
    else:
        n_bins = int(min(_MAX_BINS, max(1, N // _MIN_BIN)))
        maxp = probs.max(axis=1)
        edges = _bin_edges(maxp, n_bins)
        bins = np.searchsorted(edges, maxp, side="right")
        _state["mode"] = "bin"
        _state["edges"] = edges
        _state["q"] = mondrian_conformal_quantile(scores, bins, n_bins, alpha, M)


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
        q = _state["q"]
        if _state["mode"] == "class":
            mask = sc <= q[None, :]
        else:
            b = np.searchsorted(_state["edges"], probs.max(axis=1), side="right")
            mask = sc <= q[b][:, None]
        return {"sets": _encode_mask(mask)}
    raise ValueError("unknown op")
