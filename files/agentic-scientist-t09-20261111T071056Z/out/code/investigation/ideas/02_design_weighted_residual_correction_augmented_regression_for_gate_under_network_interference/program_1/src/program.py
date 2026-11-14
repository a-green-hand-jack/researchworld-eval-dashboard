"""Regression-based GATE estimator under network interference (starter candidate).

Interface: ``python_rpc_v1:handle``.  ``handle(request) -> response`` takes and returns
finite JSON-compatible values only.  The candidate owns all of its state in memory; it
shares no filesystem with the evaluator and must not read or write evaluator paths.

Operations
----------
``{"op": "reset", "seed": <int >= 0>}``
    Clears ALL candidate state and seeds the candidate RNG.  The seed only initializes
    randomness; it never identifies a plane, case or workload.  Any non-negative integer
    is valid.  Response: exactly ``{"ok": true}`` (no other keys).

``{"op": "estimate", ...}``
    One full dataset from one randomized experiment on a network.  The evaluator sends
    exactly one ``reset`` per episode and then four ``estimate`` requests in an
    evaluator-private order.  All four have the identical format and size and the same
    budget; the candidate must treat every request as an ordinary dataset and must not
    try to detect which one is which.  Each ``estimate`` is independent: return the best
    estimate for the request in hand.

    Request fields (all present, no others):
      op         "estimate"
      n          int, number of nodes (nodes are 0..n-1)
      edges      array object, undirected unique edges (u < v), dtype int32, shape [E, 2]
      covariates array object, node covariates, dtype float64, shape [n, 2]
      treatment  array object, realized treatment assignment, dtype uint8 (0/1), shape [n]
      outcomes   array object, observed outcomes, dtype float64, shape [n]
      design     {"kind": "bernoulli" | "cluster",
                  "probability": float,   # marginal treatment probability of the design
                  "cluster_labels": array object (int32, shape [n]) or null}
                 "bernoulli": each node treated independently with ``probability``.
                 "cluster":   whole clusters (``cluster_labels``) are treated together;
                              exactly round(K*probability) of the K clusters are treated,
                              chosen uniformly at random.
      workload   {"max_op_seconds": float,  # soft per-request time budget (hard cap is a
                                            # little larger; exceeding it fails the episode)
                  "ci_level": float}        # nominal level of the requested interval

    Array objects are ``{"dtype": "<name>", "shape": [...], "encoding": "base64-le",
    "data": "<base64 of the C-order little-endian buffer>"}``; see ``decode_array``.

    Target: the global average treatment effect (GATE), i.e. the mean over nodes of
    Y_i(all nodes treated) - Y_i(all nodes control) for the (hidden) potential outcomes.
    The interference mechanism, its parameters and the true GATE are never revealed.

    Response (JSON object): required keys ``estimate``, ``ci_low``, ``ci_high``
    (finite numbers with ci_low <= estimate <= ci_high); optional key ``diagnostics``
    (a JSON object, at most 4096 bytes serialized; ignored for scoring).  Any other key,
    a non-finite number, a malformed type or an interval that does not contain the
    estimate makes that request invalid (the episode keeps its worst-case contribution).

Limits (enforced by the evaluator; a violation is a failed request, never retried):
  * ``reset`` must answer within 4 s (it includes process/import start-up);
  * each ``estimate`` must answer within 3 s wall clock (``workload.max_op_seconds`` = 2.5 s
    is the soft budget to aim for); at most 4 threads of CPU are available;
  * a complete request is below 0.5 MiB and a complete response must stay far below the
    64 MiB wire limit (a valid response is < 5 KiB);
  * no filesystem or network is shared with the evaluator; do not read or write evaluator paths.
Determinism: all candidate randomness must derive from the ``reset`` seed, because the evaluator
replays one episode after a fresh ``reset`` and requires the primary estimate to agree to 1e-6
(relative to max(1, |estimate|)).

Scoring (evaluator-owned): per episode relative error min(|estimate - GATE| / |GATE|, 2),
a failed/invalid request counts as 2 (and as "not covered" with worst-case width);
RMSE over seeds per case, mean over the 8 cases, ``combined_score`` = -that mean.
The evaluator additionally runs matched negative controls (permuted outcomes, node-relabelled
graph, constant outcome) through the same operation; a constant-outcome request must
return an estimate within 1e-4 of 0, and the run must be deterministic given the reset seed.
"""

import base64

import numpy as np
import scipy.sparse as sp

_STATE = {"rng": None, "seed": None}

_DTYPES = {"int32": "<i4", "float64": "<f8", "uint8": "u1"}


def decode_array(obj):
    """Decode an array object (see module docstring) into a numpy array."""
    if obj is None:
        return None
    if obj["encoding"] != "base64-le" or obj["dtype"] not in _DTYPES:
        raise ValueError("unsupported array encoding")
    buf = base64.b64decode(obj["data"])
    return np.frombuffer(buf, dtype=np.dtype(_DTYPES[obj["dtype"]])).reshape(obj["shape"]).copy()


def _adjacency(n, edges):
    if len(edges) == 0:
        return sp.csr_matrix((n, n))
    u, v = edges[:, 0], edges[:, 1]
    rows = np.concatenate([u, v])
    cols = np.concatenate([v, u])
    return sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))


def _features(adj, deg, z, x, treated_all):
    """Design matrix [1, own treatment, neighbour-treated fraction, covariates]."""
    if treated_all is None:
        frac = (adj @ z) / np.maximum(deg, 1.0)
        own = z
    else:
        frac = np.where(deg > 0, float(treated_all), 0.0)
        own = np.full(len(z), float(treated_all))
    return np.column_stack([np.ones(len(z)), own, frac, x])


_ZCRIT = 1.959963984540054  # normal quantile for ci_level = 0.95 (the only level requested)
_FLOORS = (0.1, 0.05, 0.02)  # candidate probability floors for the exposure weights
_N_BUCKETS = 4


def difference_in_means(y, z):
    """Naive treated-minus-control mean difference (used only as a safety fallback)."""
    t = z > 0.5
    if t.all() or (~t).all():
        return 0.0
    return float(y[t].mean() - y[~t].mean())


def _cluster_index(n, labels):
    if labels is None:
        return None, 0
    _, idx = np.unique(np.asarray(labels).ravel(), return_inverse=True)
    return idx.astype(np.int64), int(idx.max()) + 1 if len(idx) else 0


def exposure_probabilities(deg, design, labels, adj):
    """Exact probabilities pi1/pi0 that a unit's closed neighbourhood is all treated / all control.

    Bernoulli: p^(1+deg), (1-p)^(1+deg) (computed in logs).
    Cluster (exactly m = round(K p) of K clusters treated, uniformly): with c_i distinct
    clusters touching the closed neighbourhood,
    pi1 = prod_{j<c} (m-j)/(K-j),  pi0 = prod_{j<c} (K-m-j)/(K-j).
    """
    n = len(deg)
    p = float(np.clip(design.get("probability", 0.5), 1e-12, 1.0 - 1e-12))
    idx, k = _cluster_index(n, labels)
    if design.get("kind") != "cluster" or idx is None or k < 2:
        e = 1.0 + deg
        return np.exp(e * np.log(p)), np.exp(e * np.log1p(-p))
    onehot = sp.csr_matrix((np.ones(n), (np.arange(n), idx)), shape=(n, k))
    touched = (adj + sp.identity(n, format="csr")) @ onehot
    touched = sp.csr_matrix(touched)
    touched.eliminate_zeros()
    c = np.diff(touched.indptr).astype(np.int64)
    cmax = int(c.max()) if len(c) else 0
    m = int(round(k * float(design.get("probability", 0.5))))
    j = np.arange(cmax, dtype=np.float64)
    den = np.maximum(k - j, 1.0)
    cum1 = np.concatenate([[1.0], np.cumprod(np.clip(m - j, 0.0, None) / den)])
    cum0 = np.concatenate([[1.0], np.cumprod(np.clip(k - m - j, 0.0, None) / den)])
    return cum1[c], cum0[c]


def design_weights_capped(pi1, pi0, floor):
    """Inverse-probability weights; a unit is dropped (both weights 0) if either pi is below floor.

    Requiring both corners keeps the corrected contrast r(1) - r(0) coherent for retained units.
    """
    ok = (pi1 >= floor) & (pi0 >= floor)
    w1 = np.where(ok, 1.0 / np.maximum(pi1, 1e-300), 0.0)
    w0 = np.where(ok, 1.0 / np.maximum(pi0, 1e-300), 0.0)
    return w1, w0


def shrink_factor(t_stat):
    """max(0, 1 - 1/t^2): zero for |t| <= 1 (pure-noise correction dropped)."""
    if not np.isfinite(t_stat) or abs(t_stat) <= 1.0:
        return 0.0
    return float(max(0.0, 1.0 - 1.0 / (t_stat * t_stat)))


def correction_variance(term, groups, n_groups, n):
    """Variance proxy of sum(term)/n: squared (cluster-aggregated) term sums over n^2."""
    if groups is None:
        return float(np.sum(term * term)) / (n * n)
    s = np.bincount(groups, weights=term, minlength=n_groups)
    return float(np.sum(s * s)) / (n * n)


def augmented_gate_estimate(y, e1, e0, resid, pi1, pi0, deg, groups, n_groups, base_est):
    """Linear-regression GATE plus shrunk, degree-stratified HT residual correction.

    Returns (estimate, correction, correction_variance, info).
    """
    n = len(y)
    lg = np.log1p(deg)
    qs = np.unique(np.quantile(lg, np.linspace(0, 1, _N_BUCKETS + 1)[1:-1]))
    degree_bucket = np.searchsorted(qs, lg, side="right")
    best = (0.0, 0.0, 0.0, None, 0)  # (criterion, corner_residual_correction, var, floor, buckets)
    for floor in _FLOORS:
        w1, w0 = design_weights_capped(pi1, pi0, floor)
        term = (e1 * w1 - e0 * w0) * resid
        corr = 0.0
        var = 0.0
        used = 0
        for b in range(len(qs) + 1):
            tb = np.where(degree_bucket == b, term, 0.0)
            if not np.any(tb):
                continue
            est_b = float(tb.sum()) / n
            var_b = correction_variance(tb, groups, n_groups, n)
            t_stat = est_b / np.sqrt(var_b) if var_b > 0 else 0.0
            s = shrink_factor(t_stat)
            if s > 0:
                used += 1
            corr += s * est_b
            var += s * s * var_b
        # Estimated MSE change vs no correction: variance added minus estimated bias^2 removed
        # (c^2 - v); choose the floor with the most negative 2v - c^2.
        crit = 2.0 * var - corr * corr
        if crit < best[0] and np.isfinite(crit):
            best = (crit, corr, var, floor, used)
    _, corner_residual_correction, cvar, floor, used = best
    return base_est + corner_residual_correction, corner_residual_correction, cvar, {
        "floor": floor, "buckets_used": int(used)}


def _estimate(request):
    n = int(request["n"])
    edges = decode_array(request["edges"])
    x = decode_array(request["covariates"])
    z = decode_array(request["treatment"]).astype(np.float64)
    y = decode_array(request["outcomes"])
    design = request.get("design") or {}
    labels = decode_array(design.get("cluster_labels")) if design.get("cluster_labels") is not None else None

    # Constant outcomes: no effect of any kind, return exactly 0.
    if float(np.max(y) - np.min(y)) <= 1e-12 * (1.0 + float(np.max(np.abs(y)))):
        return {"estimate": 0.0, "ci_low": 0.0, "ci_high": 0.0,
                "diagnostics": {"constant_outcome": True}}

    adj = _adjacency(n, edges)
    deg = np.asarray(adj.sum(axis=1)).ravel()

    x_obs = _features(adj, deg, z, x, None)
    beta, *_ = np.linalg.lstsq(x_obs, y, rcond=None)
    resid = y - x_obs @ beta
    # GATE = mean over nodes of prediction(all treated) - prediction(all control).
    contrast = (_features(adj, deg, z, x, 1) - _features(adj, deg, z, x, 0)).mean(axis=0)
    base_est = float(contrast @ beta)

    # Heteroskedasticity-robust (HC1) sandwich interval for the linear functional.
    bread = np.linalg.pinv(x_obs.T @ x_obs)
    meat = (x_obs * resid[:, None] ** 2).T @ x_obs
    cov = bread @ meat @ bread * n / max(n - x_obs.shape[1], 1)
    se = float(np.sqrt(max(contrast @ cov @ contrast, 0.0)))

    est, corr, cvar, info = base_est, 0.0, 0.0, {"floor": None, "buckets_used": 0}
    try:
        # Closed neighbourhood fully treated / fully control (isolated nodes: self only).
        s = adj @ z + z
        e1 = (s >= deg + 1.0 - 0.5).astype(np.float64)
        e0 = (s <= 0.5).astype(np.float64)
        pi1, pi0 = exposure_probabilities(deg, design, labels, adj)
        groups, n_groups = _cluster_index(n, labels) if design.get("kind") == "cluster" else (None, 0)
        est_a, corr_a, cvar_a, info_a = augmented_gate_estimate(
            y, e1, e0, resid, pi1, pi0, deg, groups, n_groups, base_est)
        if np.isfinite(est_a) and np.isfinite(cvar_a):
            est, corr, cvar, info = est_a, corr_a, cvar_a, info_a
    except Exception:  # strict no-regret fallback to the linear estimator
        pass

    if not np.isfinite(est):
        est, se, cvar = difference_in_means(y, z), 0.0, 0.0
    half = _ZCRIT * float(np.sqrt(max(se * se + cvar, 0.0)))
    if not np.isfinite(half):
        half = 0.0
    return {"estimate": float(est), "ci_low": float(est - half), "ci_high": float(est + half),
            "diagnostics": {"base_estimate": base_est, "corner_residual_correction": float(corr),
                            "floor": info["floor"], "buckets_used": info["buckets_used"]}}


def handle(request):
    op = request.get("op")
    if op == "reset":
        seed = int(request["seed"])
        _STATE["seed"] = seed
        _STATE["rng"] = np.random.default_rng(seed)
        return {"ok": True}
    if op == "estimate":
        return _estimate(request)
    raise ValueError("unknown op")
