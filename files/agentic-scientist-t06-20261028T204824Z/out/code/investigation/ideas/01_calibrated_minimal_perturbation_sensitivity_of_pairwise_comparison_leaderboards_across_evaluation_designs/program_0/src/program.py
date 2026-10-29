"""Starter candidate: first-order influence edit search for Bradley-Terry leaderboards.

Interface (``python_rpc_v1:handle``): ``handle(request) -> response`` over finite
JSON-compatible values.  Only the operations below exist; unknown ops are an error.

Operations
----------
{"op": "reset", "seed": <int >= 0>}
    Starts exactly one episode.  Clears ALL candidate-owned state (nothing may
    persist across resets) and seeds candidate randomness.  Any non-negative
    integer seed must be accepted; the seed never selects data or workload.
    Response: exactly {"ok": true}.

{"op": "propose", "mode": "drop" | "flip", "budget": <int k >= 1>, "n_models": <int K>,
 "n_comparisons": <int n>, "target": <str>,
 "model_a": ARR, "model_b": ARR, "outcome": ARR}
    ARR = {"dtype": "int16" | "int8", "shape": [n], "encoding": "base64-le", "data": <str>}
    model_a / model_b are int16 competitor indices in [0, K) (anonymized, relabelled
    per episode), outcome is int8: +1 a wins, -1 b wins, 0 tie.  Rows are in the
    order of the original data stream.  The same arrays are re-sent in every call of
    an episode; every call is independent (no feedback about earlier proposals is ever
    given).  Five propose calls are made per episode, with budgets k growing from about
    0.1% to 2% of n (k = max(1, ceil(f*n)), f in {0.1%, 0.25%, 0.5%, 1%, 2%}).
    Goal ("target"): choose at most k rows so that the competitor ranked first by the
    evaluator's Bradley-Terry fit on the *edited* data is no longer ranked first.
      * mode "drop": the chosen rows are removed from the data (any row may be chosen).
      * mode "flip": the chosen rows' outcomes are reversed (a win becomes a loss);
        only decisive rows (outcome != 0) may be chosen.
    Evaluator Bradley-Terry specification (public): P(a beats b) = sigmoid(t_a - t_b);
    a tie counts as half a win for each side; maximum penalised likelihood with ridge
    penalty 0.5*1e-3*sum(t**2) on the scores, solved to gradient tolerance 1e-10; the
    rank-1 competitor is the argmax of t; the gap is t_top - max_{j != top} t_j.
    Response: exactly {"indices": [<int>, ...]} -- at most k distinct integer row indices
    in [0, n).  Extra keys, floats, booleans, duplicates, out-of-range indices, more
    than k indices, or tie rows in flip mode make that call invalid and score 0 for that
    budget level.  The score of a level is 1 if rank 1 is displaced, else
    clip(1 - gap_after / gap_before, 0, 1), computed by the evaluator's own refit.
    Anything the candidate reports about its own gaps/ranks is ignored.

Resources: CPU only (2 threads); numpy and scipy are available; no network, no files.
Each call has a hard wall-clock limit of 30 seconds.
"""
import base64
import math

import numpy as np

RIDGE = 1e-3  # matches the public evaluator specification
_STATE = {"seed": None, "rng": None}


def _decode(arr):
    if (type(arr) is not dict or arr.get("encoding") != "base64-le"
            or arr.get("dtype") not in ("int16", "int8")):
        raise ValueError("bad array")
    out = np.frombuffer(base64.b64decode(arr["data"]), dtype="<i2" if arr["dtype"] == "int16" else "i1")
    if list(arr["shape"]) != [out.size]:
        raise ValueError("bad shape")
    return out.astype(np.int64)


def _fit(a, b, y, n_models):
    """Newton solve of the ridge-penalised Bradley-Terry MLE from pair-win counts."""
    k = n_models
    w = np.zeros((k, k))
    win_a, win_b, tie = y == 1, y == -1, y == 0
    np.add.at(w, (a[win_a], b[win_a]), 1.0)
    np.add.at(w, (b[win_b], a[win_b]), 1.0)
    np.add.at(w, (a[tie], b[tie]), 0.5)
    np.add.at(w, (b[tie], a[tie]), 0.5)
    n = w + w.T
    theta = np.zeros(k)
    for _ in range(100):
        p = 1.0 / (1.0 + np.exp(-(theta[:, None] - theta[None, :])))
        g = (w - n * p).sum(1) - RIDGE * theta
        if np.max(np.abs(g)) < 1e-10:
            break
        h = n * p * (1.0 - p)
        a_mat = np.diag(h.sum(1) + RIDGE) - h
        step = np.linalg.solve(a_mat, g)
        theta = theta + step
    p = 1.0 / (1.0 + np.exp(-(theta[:, None] - theta[None, :])))
    h = n * p * (1.0 - p)
    return theta, np.diag(h.sum(1) + RIDGE) - h


def _propose(req):
    mode, k = req["mode"], int(req["budget"])
    a, b, y = _decode(req["model_a"]), _decode(req["model_b"]), _decode(req["outcome"])
    n_models = int(req["n_models"])
    theta, a_mat = _fit(a, b, y, n_models)
    order = np.argsort(-theta)
    top, rival = int(order[0]), int(order[1])
    e = np.zeros(n_models)
    e[top], e[rival] = 1.0, -1.0
    v = np.linalg.solve(a_mat, e)  # sensitivity direction of the top-vs-rival gap
    p = 1.0 / (1.0 + np.exp(-(theta[a] - theta[b])))
    yv = (y + 1) / 2.0
    s = v[a] - v[b]
    if mode == "drop":
        effect = -s * (yv - p)  # first-order change of the gap when the row is removed
        eligible = np.ones(a.size, dtype=bool)
    else:
        effect = s * ((1.0 - yv) - yv)  # first-order change when the outcome is reversed
        eligible = y != 0
    effect = np.where(eligible, effect, np.inf)
    # most gap-reducing rows first; ties broken by row index for determinism
    idx = np.lexsort((np.arange(a.size), effect))[:k]
    idx = [int(i) for i in idx if math.isfinite(effect[i]) and effect[i] < 0]
    return {"indices": idx}


def handle(request):
    op = request.get("op") if isinstance(request, dict) else None
    if op == "reset":
        seed = request["seed"]
        if type(seed) is not int or seed < 0:
            raise ValueError("seed must be a non-negative integer")
        _STATE["seed"] = seed
        _STATE["rng"] = np.random.default_rng(seed)
        return {"ok": True}
    if op == "propose":
        return _propose(request)
    raise ValueError("unknown op")
