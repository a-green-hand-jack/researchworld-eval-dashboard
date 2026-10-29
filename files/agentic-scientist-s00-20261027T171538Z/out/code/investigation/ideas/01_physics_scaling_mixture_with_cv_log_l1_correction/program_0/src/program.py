"""Starter candidate: log-linear ridge regression of cover time on six graph statistics.

Interface (``python_rpc_v1:handle``): ``handle(request) -> response`` over finite,
JSON-compatible values only (no NaN/Infinity, no files, no paths). The evaluator and
this candidate share no filesystem; all inputs arrive inline in the request.

Episode transcript (identical in smoke, search and final; exactly one episode per reset):

1. ``{"op": "reset", "seed": int}`` -> ``{"ok": True}`` (exactly this one key).
   Clears all state. ``seed`` is any non-negative integer and only seeds candidate-internal
   randomness; it never identifies the plane, data or workload.
   Timeout: 5 s (includes process start and imports).

2. ``{"op": "fit", "feature_names": [str]*6, "X": [[float]*6]*N_train, "y": [float]*N_train,
   "y_se": [float]*N_train, "n_walks": int}`` -> ``{"ok": True}`` with optional
   ``"method": str`` (<= 256 chars). No other keys are allowed.
   ``feature_names`` is ``["n", "m", "mean_degree", "max_degree", "min_degree", "diameter"]``
   (mean_degree = 2m/n, diameter by BFS). Each row of ``X`` describes one connected graph
   with 5 <= n <= 30 from the training pool. ``y`` is the evaluator's Monte Carlo estimate of
   the uniform-start expected cover time (steps until a simple random walk, started at a
   uniformly random vertex, has visited every vertex), ``y_se`` its standard error, and
   ``n_walks`` the number of walks per label. N_train is conveyed only by the row count
   (roughly 20-130). Timeout: 45 s.

3. ``{"op": "predict", "X": [[float]*6]*N}`` -> ``{"pred": [float]*N}`` (exactly this one key):
   one strictly positive finite predicted expected cover time per row, in request order.
   Each episode issues exactly three predict calls after fit, on held-out graphs (rows may
   be reordered or re-paired between calls); predictions should be a pure function of the
   six statistics of each row. Timeout: 10 s per call.

Any other response shape (wrong keys, wrong length, non-numeric or non-finite values, an
exception) fails the whole episode. Non-positive predictions are scored as worst case.
Scoring (evaluator-side): per-graph error min(|ln pred - ln C|, ln 1000), averaged per graph
family with equal family weights; lower error is better. Requests never contain graph
identifiers, family labels, adjacency, held-out labels or scores.
"""

import math

import numpy as np

_STATE = {}


def _design(X):
    X = np.asarray(X, dtype=float)
    n, m, mean_deg, max_deg, min_deg, diam = (X[:, i] for i in range(6))
    cols = [np.ones(len(X)), np.log(n), np.log(m), np.log(mean_deg), np.log(max_deg),
            np.log(min_deg), np.log(diam), np.log(n) * np.log(diam)]
    return np.column_stack(cols)


def _reset(request):
    seed = request.get("seed")
    if type(seed) is not int or seed < 0:
        raise ValueError("invalid seed")
    _STATE.clear()
    _STATE["seed"] = seed
    return {"ok": True}


def _fit(request):
    A = _design(request["X"])
    y = np.log(np.asarray(request["y"], dtype=float))
    mu = A[:, 1:].mean(axis=0)
    sd = A[:, 1:].std(axis=0)
    sd[sd < 1e-12] = 1.0
    Z = np.column_stack([A[:, 0], (A[:, 1:] - mu) / sd])
    ridge = 1e-3 * np.eye(Z.shape[1])
    ridge[0, 0] = 0.0
    beta = np.linalg.solve(Z.T @ Z + ridge, Z.T @ y)
    _STATE.update(mu=mu, sd=sd, beta=beta, fallback=float(y.mean()))
    return {"ok": True, "method": "ridge_log_linear_v0"}


def _predict(request):
    if "beta" not in _STATE:
        raise RuntimeError("predict before fit")
    A = _design(request["X"])
    Z = np.column_stack([A[:, 0], (A[:, 1:] - _STATE["mu"]) / _STATE["sd"]])
    log_pred = np.clip(Z @ _STATE["beta"], -50.0, 50.0)
    log_pred = np.where(np.isfinite(log_pred), log_pred, _STATE["fallback"])
    return {"pred": [float(math.exp(v)) for v in log_pred]}


def handle(request):
    op = request.get("op") if isinstance(request, dict) else None
    if op == "reset":
        return _reset(request)
    if op == "fit":
        return _fit(request)
    if op == "predict":
        return _predict(request)
    raise ValueError("unknown op")
