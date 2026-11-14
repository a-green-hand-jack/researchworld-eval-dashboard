"""Candidate conformal prediction-set procedure for compositional (softmax) outputs.

Entry point: ``handle(request) -> response`` (``python_rpc_v1:handle``).  Requests and
responses are finite, JSON-compatible dicts.  All state is in-process memory; there is no
shared filesystem with the evaluator.  The only editable code root is ``program_0/src``.

Episode protocol (one episode = one ``reset``, then calibration, then prediction):

``{"op": "reset", "seed": int}``
    Clears ALL calibration state.  ``seed`` is any non-negative integer and may only be used
    to initialise the candidate's own randomness.  Response must be exactly ``{"ok": true}``.

``{"op": "calibrate", "chunk_index": i, "num_chunks": n, "rows": r, "K": K, "alpha": a,
   "n_cal": N, "n_test": M, "probs": ARR, "labels": ARR}``
    Delivers calibration chunk ``i`` (0-based, in order, ``num_chunks`` <= 2, ``rows`` <= 1000).
    ``K`` (2..100) is the number of classes, ``alpha`` the target miscoverage (sets should
    cover the true label with probability >= 1 - alpha), ``N`` the total calibration rows and
    ``M`` the total number of test rows that will follow.  ``probs`` encodes a float32 array of
    shape [rows, K] (non-negative rows summing to 1 up to float32 rounding); ``labels`` an int16
    array of shape [rows] with values in [0, K).  Response must be exactly ``{"ok": true}``.
    The workload (K, alpha, N, M) is supplied by the evaluator and is independent of the seed.

``{"op": "predict", "chunk_index": i, "num_chunks": n, "rows": r, "K": K, "alpha": a,
   "n_cal": N, "n_test": M, "probs": ARR}``
    Delivers unlabeled test chunk ``i`` (``num_chunks`` <= 4, ``rows`` <= 1000), always after
    all calibration chunks.  Response must be exactly ``{"sets": MASK}`` (no other keys) where
    ``MASK = {"dtype": "uint8", "shape": [rows, K], "encoding": "packbits_base64",
    "data": <base64 of numpy.packbits(bool_mask, axis=1) with shape [rows, ceil(K/8)]>}``;
    ``bool_mask[i, j]`` is true iff class ``j`` is in the prediction set of test row ``i``.
    Padding bits beyond column K-1 must be zero.  Empty sets are allowed.

``ARR`` is ``{"dtype": "float32" | "int16", "shape": [...], "encoding": "base64_le",
"data": <base64 of the C-contiguous little-endian array bytes>}``.

Every complete message stays far below the 64 MiB wire limit (largest request ~0.55 MB).
Per-episode work (all calibrate + predict calls together) is limited to about 20 s and each
call to 20 s; an episode that errors, times out or returns malformed output counts as a failed
episode with worst-case loss.  Candidate-reported numbers are never used for scoring.

The evaluator scores each episode only from the returned sets and its private test labels:
  loss = 0.5 * min(1, max(0, 1 - alpha - coverage) / alpha)
       + 0.25 * worst-slice undercoverage gap   (classes if K <= 10; set-size and
                                                  max-probability strata if K > 10)
       + 0.25 * mean |set| / K
and ``combined_score = 1 - mean loss`` (episodes -> mean over seeds -> equal-weight mean over
cases).  Search-eligibility additionally requires well-formed outputs, valid behaviour on the
three negative controls, and marginal coverage within a finite-sample tolerance of 1 - alpha on
the exchangeable cases.

This starter implements split LAC (threshold) conformal prediction: score = 1 - p[label],
set = {j : 1 - p_j <= q} with q the ceil((n + 1)(1 - alpha))-th smallest calibration score.
"""
import base64
import math

import numpy as np

_state = {}


def _decode(obj):
    dtype = np.dtype(obj["dtype"]).newbyteorder("<")
    arr = np.frombuffer(base64.b64decode(obj["data"]), dtype=dtype)
    return arr.reshape(obj["shape"])


def _encode_mask(mask):
    packed = np.packbits(mask.astype(np.uint8), axis=1)
    return {"dtype": "uint8", "shape": [int(mask.shape[0]), int(mask.shape[1])],
            "encoding": "packbits_base64", "data": base64.b64encode(packed.tobytes()).decode("ascii")}


def _quantile(scores, alpha):
    n = len(scores)
    k = math.ceil((n + 1) * (1.0 - alpha) - 1e-9)
    if n == 0 or k > n:
        return math.inf
    return float(np.sort(scores)[max(k, 1) - 1])


def handle(request):
    op = request["op"]
    if op == "reset":
        _state.clear()
        _state["rng"] = np.random.default_rng(int(request["seed"]))
        _state["scores"] = []
        return {"ok": True}
    if op == "calibrate":
        probs = _decode(request["probs"]).astype(np.float64)
        labels = _decode(request["labels"]).astype(np.int64)
        _state["scores"].append(1.0 - probs[np.arange(len(labels)), labels])
        if request["chunk_index"] == request["num_chunks"] - 1:
            _state["q"] = _quantile(np.concatenate(_state["scores"]), float(request["alpha"]))
        return {"ok": True}
    if op == "predict":
        probs = _decode(request["probs"]).astype(np.float64)
        return {"sets": _encode_mask((1.0 - probs) <= _state["q"])}
    raise ValueError("unknown op")
