"""Starter candidate: few-item benchmark prediction (python_rpc_v1:handle).

Task.  An episode gives you the binary correct/incorrect matrix of SOURCE models on a benchmark
whose items are opaque column indices (no text, no names, shuffled rows).  You choose at most ``k``
item columns.  The evaluator then reveals each TARGET model's responses on those columns only and you
predict every target's accuracy on the FULL benchmark.  Targets never appear among the sources.
Scoring (evaluator-owned): MAE / RMSE and Spearman / Kendall of predictions against the targets' true
full-benchmark accuracy; a target regime may be "random_targets" (targets look like the sources) or
"strong_targets" (targets are stronger than every source model, so predictions must extrapolate).

Every request and response is a finite JSON dict with an "op" field in the request.  Per episode the
evaluator sends, in this order, exactly one reset, then 1-2 load_source calls, one select, one predict.
State lives only in this process and is cleared by reset.  Unknown ops, extra response keys, wrong types
or out-of-range values are protocol failures (the episode then scores as the worst case).

Operations
----------
reset        request  {"op": "reset", "seed": int >= 0}
             response {"ok": True}                     (exactly this dict)
             Clears all state; ``seed`` may only be used to initialise randomness.  Any valid seed
             must work; the seed does not identify the benchmark or the plane.

load_source  request  {"op": "load_source", "task_id": str (opaque label), "episode_id": str,
                       "n_source_models": int, "n_items": int, "k": int (item budget),
                       "split": "random_targets" | "strong_targets",
                       "n_chunks": int (1 or 2), "chunk_index": int, "row_start": int,
                       "row_count": int, "dtype": "uint8 bits", "shape": [row_count, n_items],
                       "encoding": "np.packbits axis=1 bitorder=big then base64",
                       "data_b64": str}
             Decode: np.unpackbits(np.frombuffer(base64.b64decode(data_b64), np.uint8)
                                   .reshape(row_count, -1), axis=1)[:, :n_items]
             gives a uint8 0/1 array (1 = the source model answered the item correctly) for rows
             row_start .. row_start+row_count-1 of the source matrix.  Chunks arrive in order.
             response {"ok": True}                     (exactly this dict)

select       request  {"op": "select", "episode_id": str, "k": int}
             response {"indices": [int, ...]}          (exactly this dict)
             1 <= len <= k, unique ints in [0, n_items).  The order you return is the column order
             of the matrix you will receive in predict.  No other item is ever revealed for targets.

predict      request  {"op": "predict", "episode_id": str, "indices": [the selected ints, echoed],
                       "n_targets": int, "dtype": "uint8 bits", "shape": [n_targets, len(indices)],
                       "encoding": "np.packbits axis=1 bitorder=big then base64", "data_b64": str}
             Decode as for load_source (use ``len(indices)`` columns).  Row order is arbitrary.
             response {"predictions": [float, ...]}    (exactly this dict)
             n_targets finite numbers in [0, 1]: the predicted full-benchmark accuracy per target.

Limits enforced by the evaluator: item budget ``k`` (hard), a per-episode wall clock, and a fixed total
RPC budget; every complete message is far below the 64 MiB wire limit.  Stay inside ~8 threads.
numpy is available; scipy and scikit-learn may be used if installed.

This starter stratifies items by source difficulty, picks one item per stratum, and maps the target's
mean accuracy on those items to a full-benchmark estimate with a linear calibration fitted on the
source models (source subset-mean -> source full accuracy).
"""

import base64
import math

import numpy as np

_STATE = {}


def _decode(b64, rows, cols):
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).reshape(rows, -1)
    return np.unpackbits(raw, axis=1)[:, :cols]


def _reset(seed):
    _STATE.clear()
    _STATE["rng"] = np.random.default_rng(int(seed))
    _STATE["chunks"] = {}
    return {"ok": True}


def _load_source(req):
    chunks = _STATE["chunks"]
    chunks[int(req["chunk_index"])] = _decode(req["data_b64"], int(req["row_count"]), int(req["n_items"]))
    _STATE["n_chunks"] = int(req["n_chunks"])
    _STATE["k"] = int(req["k"])
    if len(chunks) == _STATE["n_chunks"]:
        _STATE["src"] = np.concatenate([chunks[i] for i in sorted(chunks)], axis=0)
    return {"ok": True}


def _select(req):
    src = _STATE["src"]
    k = min(int(req["k"]), src.shape[1])
    difficulty = src.mean(axis=0)
    rng = _STATE["rng"]
    order = np.argsort(difficulty + 1e-9 * rng.random(src.shape[1]), kind="stable")
    strata = np.array_split(order, k)
    picks = [int(rng.choice(group)) for group in strata if len(group)]
    _STATE["indices"] = picks
    return {"indices": picks}


def _predict(req):
    src = _STATE["src"]
    idx = [int(i) for i in req["indices"]]
    tgt = _decode(req["data_b64"], int(req["n_targets"]), len(idx)).astype(np.float64)
    target_mean = tgt.mean(axis=1)
    sub = src[:, idx].astype(np.float64).mean(axis=1)
    full = src.astype(np.float64).mean(axis=1)
    if np.ptp(sub) > 1e-9:
        slope, intercept = np.polyfit(sub, full, 1)
        pred = slope * target_mean + intercept
    else:
        pred = target_mean
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
