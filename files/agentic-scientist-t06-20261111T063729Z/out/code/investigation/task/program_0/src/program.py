"""Starter candidate: influence-guided data removal for Bradley-Terry leaderboards.

The evaluator calls ``handle(request) -> response`` once per operation with finite JSON values.
One episode is: ``reset`` -> ``load_chunk`` x n_chunks -> ``analyze``. Every request is a dict with
an ``op`` key; every response is a dict. All state lives in this process's memory. The evaluator
and this process share no filesystem; never rely on paths.

Operations
----------
{"op": "reset", "seed": int}
    Clear ALL state (table, caches, RNG) and seed the RNG. The seed only initializes randomness
    (tie-breaking, restarts); it never identifies the dataset or the workload.
    Response: exactly {"ok": true}.

{"op": "load_chunk", "chunk_index": int, "n_chunks": int, "n_rows_total": int, "n_models": int,
 "a": ARR, "b": ARR, "y": ARR}
    One slice of the comparison table (chunks arrive in order 0..n_chunks-1; at most 65536 rows per
    chunk; at most 4 chunks). Row j of the concatenated table is "model a[j] vs model b[j]" with
    outcome y[j]: 0 = A wins, 1 = B wins, 2 = tie. Model indices are anonymized integers in
    [0, n_models); rows and model ids are shuffled per episode, so no name, dataset or time order is
    available. ARR = {"dtype": "uint16" | "uint8", "shape": [n], "encoding": "base64-le",
    "data": <base64 of little-endian bytes>}  (a, b: uint16; y: uint8).
    Response: exactly {"ok": true}.

{"op": "analyze", "hi": int, "lo": int, "k_cap": int, "tie_as_half_win": true, "ridge": float,
 "deadline_seconds": float}
    Rating definition used by the evaluator (it is the only judge): Bradley-Terry logistic MLE
    P(a beats b) = sigmoid(theta_a - theta_b), a tie counts as half a win for each side (when
    tie_as_half_win), objective  sum_rows [log(1+exp(d)) - s*d] + ridge/2 * |theta|^2 with
    d = theta_a - theta_b and s in {1, 0, 0.5}; models are ranked by theta, descending.
    Model ``hi`` is currently ranked directly above model ``lo``. Propose a set of at most
    ``k_cap`` rows (global row indices into the concatenated table, unique) whose removal makes the
    evaluator's exact refit rank ``lo`` strictly above ``hi``. Smaller sets score higher
    (score = 1 - k / k_cap when the refit flips, else 0). Answer within ``deadline_seconds``.
    Response: {"removed": {"dtype": "uint32", "shape": [k], "encoding": "base64-le",
    "data": <base64 of little-endian uint32 row indices>},
    "diagnostics": {<name>: <finite number>, ...}}   # "diagnostics" is optional (<= 32 numbers),
    ignored for scoring. No other keys are allowed; any malformed, over-cap, duplicate or
    out-of-range proposal scores 0 for the episode.
"""
import base64
import math
import time

import numpy as np

_STATE = {}


def _fresh(seed):
    return {"seed": int(seed), "rng": np.random.default_rng(int(seed)), "chunks": [], "n_chunks": None,
            "n_rows": None, "n_models": None}


def _decode(arr, dtype, n_expected=None):
    if (type(arr) is not dict or arr.get("encoding") != "base64-le" or arr.get("dtype") != np.dtype(dtype).name):
        raise ValueError("bad array")
    out = np.frombuffer(base64.b64decode(arr["data"]), dtype=np.dtype(dtype).newbyteorder("<"))
    if list(arr["shape"]) != [len(out)] or (n_expected is not None and len(out) != n_expected):
        raise ValueError("bad shape")
    return out


def _encode_u32(idx):
    idx = np.asarray(idx, dtype="<u4")
    return {"dtype": "uint32", "shape": [int(len(idx))], "encoding": "base64-le",
            "data": base64.b64encode(idx.tobytes()).decode("ascii")}


def _scores(y):
    return np.where(y == 0, 1.0, np.where(y == 1, 0.0, 0.5))


def _fit(a, b, s, m, ridge, theta0=None, tol=1e-9, max_iter=60):
    th = np.zeros(m) if theta0 is None else theta0.copy()
    ab = a * m + b

    def obj(t):
        d = t[a] - t[b]
        return float(np.sum(np.logaddexp(0.0, d) - s * d) + 0.5 * ridge * float(t @ t))

    f = obj(th)
    for _ in range(max_iter):
        p = 1.0 / (1.0 + np.exp(-(th[a] - th[b])))
        r = p - s
        g = np.bincount(a, r, m) - np.bincount(b, r, m) + ridge * th
        if np.max(np.abs(g)) < tol:
            break
        w = p * (1.0 - p)
        h = np.bincount(ab, w, m * m).reshape(m, m)
        h = -(h + h.T)
        h[np.diag_indices(m)] += np.bincount(a, w, m) + np.bincount(b, w, m) + ridge
        step = np.linalg.solve(h, g)
        t = 1.0
        while True:
            fn = obj(th - t * step)
            if fn <= f + 1e-12 * abs(f) or t < 1e-6:
                break
            t *= 0.5
        th = th - t * step
        f = fn
    return th


def _influence(a, b, s, theta, hi, lo, m, ridge):
    """First-order change of theta[hi]-theta[lo] when each row is removed (negative closes the gap)."""
    p = 1.0 / (1.0 + np.exp(-(theta[a] - theta[b])))
    w = p * (1.0 - p)
    h = np.bincount(a * m + b, w, m * m).reshape(m, m)
    h = -(h + h.T)
    h[np.diag_indices(m)] += np.bincount(a, w, m) + np.bincount(b, w, m) + ridge
    e = np.zeros(m)
    e[hi], e[lo] = 1.0, -1.0
    v = np.linalg.solve(h, e)
    return -(s - p) * (v[a] - v[b])


def _analyze(req, st):
    a = np.concatenate([c[0] for c in st["chunks"]]).astype(np.int64)
    b = np.concatenate([c[1] for c in st["chunks"]]).astype(np.int64)
    y = np.concatenate([c[2] for c in st["chunks"]])
    n, m = len(y), int(st["n_models"])
    ridge = float(req["ridge"])
    s = _scores(y) if req.get("tie_as_half_win", True) else np.where(y == 0, 1.0, 0.0)
    hi, lo, cap = int(req["hi"]), int(req["lo"]), int(req["k_cap"])
    stop_at = time.monotonic() + 0.7 * float(req["deadline_seconds"])
    refits = 0
    theta0 = _fit(a, b, s, m, ridge)

    def flips(removed):
        nonlocal refits
        refits += 1
        keep = np.ones(n, bool)
        keep[removed] = False
        th = _fit(a[keep], b[keep], s[keep], m, ridge, theta0)
        return th[hi] < th[lo]

    def min_prefix(order):
        top = min(cap, len(order))
        if top < 1 or time.monotonic() > stop_at or not flips(order[:top]):
            return None
        lo_k, hi_k = 0, top
        while hi_k - lo_k > 1 and time.monotonic() < stop_at:
            mid = (lo_k + hi_k) // 2
            if flips(order[:mid]):
                hi_k = mid
            else:
                lo_k = mid
        return order[:hi_k]

    # Strategy A: one-shot first-order influence ranking, refit-verified prefix bisection.
    order = np.argsort(_influence(a, b, s, theta0, hi, lo, m, ridge), kind="stable")[:cap]
    best = min_prefix(order)
    # Strategy B: batched re-linearization (recompute influence at the refit after every batch).
    if best is None:
        keep = np.ones(n, bool)
        theta = theta0
        removed = []
        batch = max(1, int(math.ceil(cap / 16)))
        while len(removed) < cap and time.monotonic() < stop_at:
            rows = np.flatnonzero(keep)
            g = _influence(a[rows], b[rows], s[rows], theta, hi, lo, m, ridge)
            take = rows[np.argsort(g, kind="stable")[:min(batch, cap - len(removed))]]
            keep[take] = False
            removed.extend(int(i) for i in take)
            theta = _fit(a[keep], b[keep], s[keep], m, ridge, theta)
            refits += 1
            if theta[hi] < theta[lo]:
                break
        best = min_prefix(np.asarray(removed, dtype=np.int64)) if removed else None
    chosen = np.zeros(0, dtype=np.int64) if best is None else np.asarray(best, dtype=np.int64)
    return {"removed": _encode_u32(chosen), "diagnostics": {"refits": float(refits), "k": float(len(chosen))}}


def handle(request):
    op = request.get("op")
    if op == "reset":
        _STATE.clear()
        _STATE.update(_fresh(request["seed"]))
        return {"ok": True}
    if not _STATE:
        raise RuntimeError("reset required")
    if op == "load_chunk":
        a = _decode(request["a"], np.uint16)
        b = _decode(request["b"], np.uint16, len(a))
        y = _decode(request["y"], np.uint8, len(a))
        if request["chunk_index"] != len(_STATE["chunks"]):
            raise ValueError("chunk out of order")
        _STATE["chunks"].append((a, b, y))
        _STATE.update(n_chunks=request["n_chunks"], n_rows=request["n_rows_total"], n_models=request["n_models"])
        return {"ok": True}
    if op == "analyze":
        if len(_STATE["chunks"]) != _STATE["n_chunks"]:
            raise ValueError("table incomplete")
        return _analyze(request, _STATE)
    raise ValueError("unknown op")
