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


def _estimate(request):
    n = int(request["n"])
    edges = decode_array(request["edges"])
    x = decode_array(request["covariates"])
    z = decode_array(request["treatment"]).astype(np.float64)
    y = decode_array(request["outcomes"])
    adj = _adjacency(n, edges)
    deg = np.asarray(adj.sum(axis=1)).ravel()

    x_obs = _features(adj, deg, z, x, None)
    beta, *_ = np.linalg.lstsq(x_obs, y, rcond=None)
    resid = y - x_obs @ beta
    # GATE = mean over nodes of prediction(all treated) - prediction(all control).
    contrast = (_features(adj, deg, z, x, 1) - _features(adj, deg, z, x, 0)).mean(axis=0)
    est = float(contrast @ beta)

    # Heteroskedasticity-robust (HC1) sandwich interval for the linear functional.
    bread = np.linalg.pinv(x_obs.T @ x_obs)
    meat = (x_obs * resid[:, None] ** 2).T @ x_obs
    cov = bread @ meat @ bread * n / max(n - x_obs.shape[1], 1)
    se = float(np.sqrt(max(contrast @ cov @ contrast, 0.0)))
    zcrit = 1.959963984540054  # normal quantile for ci_level = 0.95 (the only level requested)
    return {"estimate": est, "ci_low": est - zcrit * se, "ci_high": est + zcrit * se}


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
