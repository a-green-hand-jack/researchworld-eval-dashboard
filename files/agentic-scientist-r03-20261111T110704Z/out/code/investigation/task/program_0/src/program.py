"""Starter candidate: cold-start benchmark-subset selection + score imputation.

Entry point: ``handle(request) -> response`` (contract interface ``python_rpc_v1:handle``). Requests and
responses are finite JSON-compatible dicts. All state lives in this process' memory; there is no file,
network, or shared-filesystem access, and no path or handle is ever passed through RPC. Binary arrays are
sent inline as base64 with explicit dtype/shape/encoding metadata. The evaluator is the only caller.

Problem. A history matrix of M anonymous models x N anonymous benchmarks (scores in each benchmark's native
scale, some cells missing) is streamed in row chunks. The candidate must then commit to ``k`` benchmark
indices (non-adaptively, before seeing any new-model score), and afterwards predict, for batches of NEW
models, their scores on all N benchmarks from their observed scores on the selected ones. Error is measured
by the evaluator on held-out scored cells that are not selected, in units of the historical column std.

Operations (every episode follows exactly this order; the first request is always ``reset``):

1. ``{"op": "reset", "seed": int}`` -> ``{"ok": true}`` (exactly this key).
   Clears ALL state (history, selection, RNG) and seeds the candidate's randomness. Any non-negative seed
   must be accepted; the seed never identifies a plane, dataset, or workload.

2. ``{"op": "load_history", "chunk_index": int, "n_chunks": int, "row_start": int, "n_rows": int,
   "n_cols": int, "dtype": "float32", "byte_order": "little", "layout": "row_major",
   "shape": [n_rows, n_cols], "values_b64": str, "mask_b64": str}`` -> ``{"ok": true}``.
   Chunks arrive in order 0..n_chunks-1 and together form the M x N history. ``values_b64`` is float32
   (little-endian, row-major) with missing cells zero-filled; ``mask_b64`` is uint8 of the same shape with
   1 = observed. Rows are anonymous models, columns are opaque benchmark indices 0..N-1 (ordered by
   decreasing historical coverage in MTEB-style data; no names are provided).

3. ``{"op": "select", "k": int, "n_cols": int}`` -> ``{"selected": [k distinct ints in [0, n_cols)]}``
   (exactly this key). Called exactly once, after the history is complete and before any new-model score
   is sent. ``k`` is chosen by the evaluator. The selection is final and cannot use new-model scores.

4. ``{"op": "predict", "batch_index": int, "n_batches": int, "n_models": B, "selected": [k ints],
   "dtype": "float32", "byte_order": "little", "layout": "row_major", "shape": [B, k],
   "observed_values_b64": str, "observed_mask_b64": str}`` ->
   ``{"predictions_b64": str, "dtype": "float32", "shape": [B, N], "encoding": "base64"}``.
   ``observed_values_b64`` (float32 [B, k], columns in the order of ``selected``) holds each new model's
   score on the selected benchmarks and ``observed_mask_b64`` (uint8 [B, k]) is 0 where that model has no
   score there (value zero-filled; the pick is still consumed). The response must contain
   ``predictions_b64`` (float32 little-endian row-major [B, N], all values finite, raw benchmark scale);
   ``dtype``, ``shape``, ``encoding`` ("base64"), ``byte_order``, ``layout`` are optional and, if present,
   must match; any other key is rejected. Values on selected columns are ignored by the scorer. Predict is
   called for batches 0..n_batches-1 (<= 64 models per batch in production), possibly repeated across
   episodes with different observed inputs; predictions must depend only on the history and the observed
   inputs (the evaluator also sends permuted/constant observed inputs in the same format as controls and
   expects real inputs to be used).

Any malformed response, exception, or timeout makes that whole episode count as the worst case. The
evaluator allows roughly 85 s of candidate work per episode; keep BLAS threads <= 2.

Baseline method implemented here (deterministic, lightweight, numpy only):
  * z-score each column by its observed history mean/std; complete the matrix with iterative low-rank SVD;
  * choose k columns by greedy residual-variance (pivoted Gram-Schmidt) on the completed matrix;
  * impute with multi-output ridge regression (intercept, lambda picked by leave-one-model-out on history).
"""
import base64
import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

import numpy as np

RANK = 5
ITERS = 40
RIDGE_GRID = (1e-3, 1e-2, 1e-1, 1.0)

_STATE = {}


def _fresh(seed):
    _STATE.clear()
    _STATE.update(seed=int(seed), rng=np.random.default_rng(int(seed)), chunks={}, n_chunks=None,
                  n_cols=None, selected=None, model=None)


def _decode(b64, dtype, shape):
    raw = base64.b64decode(b64.encode("ascii"), validate=True)
    return np.frombuffer(raw, dtype=dtype).reshape(shape)


def _encode(array):
    return base64.b64encode(np.ascontiguousarray(array).tobytes()).decode("ascii")


def _prepare_history():
    n_chunks = _STATE["n_chunks"]
    parts = [_STATE["chunks"][i] for i in range(n_chunks)]
    values = np.concatenate([p[0] for p in parts]).astype(np.float64)
    mask = np.concatenate([p[1] for p in parts]).astype(bool)
    count = np.maximum(mask.sum(0), 1)
    mean = (values * mask).sum(0) / count
    var = (((values - mean) ** 2) * mask).sum(0) / count
    std = np.sqrt(np.maximum(var, 1e-12))
    z = np.where(mask, (values - mean) / std, 0.0)
    completed = z
    if not mask.all():
        rank = max(1, min(RANK, z.shape[1] - 1))
        for _ in range(ITERS):
            u, s, vt = np.linalg.svd(completed, full_matrices=False)
            low = (u[:, :rank] * s[:rank]) @ vt[:rank]
            completed = np.where(mask, z, low)
    _STATE["hist"] = {"mean": mean, "std": std, "completed": completed}


def _select(k):
    completed = _STATE["hist"]["completed"]
    residual = completed - completed.mean(0)
    chosen = []
    for _ in range(k):
        norms = (residual ** 2).sum(0)
        norms[chosen] = -1.0
        j = int(np.argmax(norms))
        chosen.append(j)
        v = residual[:, j] / max(np.sqrt((residual[:, j] ** 2).sum()), 1e-12)
        residual = residual - np.outer(v, v @ residual)
    return chosen


def _fit(selected):
    hist = _STATE["hist"]
    comp = hist["completed"]
    m = comp.shape[0]
    x, y = comp[:, selected], comp
    mx, my = x.mean(0), y.mean(0)
    xc, yc = x - mx, y - my
    u, s, vt = np.linalg.svd(xc, full_matrices=False)
    uty = u.T @ yc
    best = None
    for g in RIDGE_GRID:
        lam = g * m
        d = s ** 2 / (s ** 2 + lam)
        h = (u ** 2) @ d
        loo = (yc - u @ (d[:, None] * uty)) / (1.0 - h)[:, None]
        err = float(np.mean(loo ** 2))
        if best is None or err < best[0]:
            best = (err, lam)
    lam = best[1]
    w = vt.T @ ((s / (s ** 2 + lam))[:, None] * uty)
    _STATE["model"] = {"mx": mx, "my": my, "w": w}


def handle(request):
    op = request.get("op")
    if op == "reset":
        _fresh(request["seed"])
        return {"ok": True}
    if op == "load_history":
        shape = tuple(request["shape"])
        _STATE["chunks"][int(request["chunk_index"])] = (
            _decode(request["values_b64"], "<f4", shape), _decode(request["mask_b64"], np.uint8, shape))
        _STATE["n_chunks"] = int(request["n_chunks"])
        _STATE["n_cols"] = int(request["n_cols"])
        return {"ok": True}
    if op == "select":
        k = int(request["k"])
        if "hist" not in _STATE:
            _prepare_history()
        selected = _select(k)
        _fit(selected)
        _STATE["selected"] = selected
        return {"selected": selected}
    if op == "predict":
        selected = [int(j) for j in request["selected"]]
        if _STATE.get("selected") != selected:
            raise ValueError("selection mismatch")
        b, k = (int(v) for v in request["shape"])
        values = _decode(request["observed_values_b64"], "<f4", (b, k)).astype(np.float64)
        mask = _decode(request["observed_mask_b64"], np.uint8, (b, k)).astype(bool)
        hist, model = _STATE["hist"], _STATE["model"]
        sel = np.asarray(selected)
        z = (values - hist["mean"][sel]) / hist["std"][sel]
        z = np.where(mask, z, model["mx"])
        pred_z = model["my"] + (z - model["mx"]) @ model["w"]
        pred = pred_z * hist["std"] + hist["mean"]
        return {"predictions_b64": _encode(pred.astype("<f4")), "dtype": "float32",
                "shape": [b, int(pred.shape[1])], "encoding": "base64"}
    raise ValueError("unknown op")
