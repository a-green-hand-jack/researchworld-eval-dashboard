"""Starter perturbation finder for Bradley-Terry leaderboard stability (t06).

The evaluator calls ``handle(request) -> response`` with finite JSON-compatible dicts.  The
candidate runs isolated (no files, no network, no shared filesystem) and keeps all state in
process memory.  Every request/response must stay below 64 MiB of UTF-8 JSON.

Array encoding (both directions)
--------------------------------
``{"dtype": "int32" | "float32", "shape": [m], "encoding": "base64", "byte_order": "little",
"data": <base64 of the little-endian bytes>}`` -- exactly these five keys.

Episode protocol (one episode per case x seed; the process may be restarted before each reset)
-----------------------------------------------------------------------------------------------
1. ``{"op": "reset", "seed": int>=0}``
   Clear ALL state and seed any randomness.  The seed only initialises randomness; it never
   identifies the dataset, plane or workload.  Response: exactly ``{"ok": true}``.
2. ``{"op": "load_chunk", "case_token": str, "chunk_index": int, "n_chunks": int (1..4),
   "row_offset": int, "n_rows_total": int, "n_players": int, "player_a": int32[m],
   "player_b": int32[m], "outcome": float32[m]}``   (sent n_chunks times, chunk_index 0..n-1)
   Row r (global index row_offset + i) is one comparison between players ``player_a[r]`` and
   ``player_b[r]`` (ids 0..n_players-1, per-case relabelled); ``outcome`` is 1.0 if player_a
   won, 0.0 if player_b won and 0.5 for a tie.  At most 524,288 rows per chunk.  No names,
   text, dates, labels or scores are ever sent.  Response: exactly ``{"ok": true}``.
3. ``{"op": "propose", "perturbation": "drop" | "flip", "target": {"type": "top1"} |
   {"type": "topk_set", "k": int}, "estimator": {"model": "bradley_terry", "ties": "half",
   "ridge": float, "tol": float}, "max_size": int, "deadline_seconds": float}``
   Return a set of global row indices whose removal ("drop") or outcome reversal y -> 1-y
   ("flip"; tie rows are NOT flippable) changes the target of the fixed estimator:
     * estimator: maximise sum_r [y_r log s(t_a - t_b) + (1-y_r) log s(t_b - t_a)]
       - ridge/2 * ||t||^2 over log-strengths t (float64; s = logistic; ties count as half wins);
       the player set is fixed (players keep their ids even if all their rows are dropped);
     * top1 changes if some player j != leader has t_j > t_leader + tol after the change;
     * topk_set changes if max_{j outside S} t_j > min_{i in S} t_i + tol, S = original top-k.
   Response: ``{"indices": int32[s]}`` (array encoding above; strictly increasing, unique,
   0 <= index < n_rows_total, s <= max_size) plus optional ``"diagnostics"``: a dict of at most
   32 entries mapping names (``[A-Za-z0-9_-][A-Za-z0-9_.-]{0,79}``) to finite numbers.  No other
   keys are allowed; malformed responses score as failures.  The evaluator independently
   re-verifies the set with its own refit; claimed sizes/diagnostics are ignored.  Smaller
   verified sets score higher.  Respond before ``deadline_seconds`` (wall clock, measured by
   the evaluator from the request); late responses are failures.

Determinism: the same seed and inputs must give the same index set (a replay is checked).

This starter: one-step influence (AMIP-style) ranking of rows by their first-order effect on
the target margin, then the smallest verifying prefix found by exponential + binary search
with exact refits.  Deterministic and lightweight.
"""
import base64
import time

import numpy as np

_STATE = {}


def _decode(arr, dtype, expected_len):
    if (not isinstance(arr, dict) or arr.get("dtype") != dtype or arr.get("encoding") != "base64"
            or arr.get("byte_order") != "little"):
        raise ValueError("bad array")
    out = np.frombuffer(base64.b64decode(arr["data"]), dtype=np.dtype(dtype).newbyteorder("<"))
    if out.shape[0] != expected_len or list(arr["shape"]) != [expected_len]:
        raise ValueError("bad array shape")
    return out


def _encode_int32(values):
    arr = np.ascontiguousarray(np.asarray(values, dtype="<i4"))
    return {"dtype": "int32", "shape": [int(arr.shape[0])], "encoding": "base64",
            "byte_order": "little", "data": base64.b64encode(arr.tobytes()).decode("ascii")}


def _pair_stats(p, a, b, y):
    idx = a.astype(np.int64) * p + b.astype(np.int64)
    cnt = np.bincount(idx, minlength=p * p).reshape(p, p).astype(np.float64)
    won = np.bincount(idx, weights=y, minlength=p * p).reshape(p, p)
    lost = np.bincount(idx, weights=1.0 - y, minlength=p * p).reshape(p, p)
    return won + lost.T, cnt + cnt.T


def _fit(S, N, ridge, theta0=None, iters=200, gtol=1e-10):
    p = S.shape[0]
    theta = np.zeros(p) if theta0 is None else theta0.copy()
    score = S.sum(axis=1)

    def objective(t):
        d = t[:, None] - t[None, :]
        return -float((S * np.logaddexp(0.0, -d)).sum()) - 0.5 * ridge * float(t @ t)

    value = objective(theta)
    for _ in range(iters):
        d = theta[:, None] - theta[None, :]
        prob = 1.0 / (1.0 + np.exp(-d))
        grad = score - (N * prob).sum(axis=1) - ridge * theta
        if float(np.max(np.abs(grad))) < gtol:
            break
        w = N * prob * (1.0 - prob)
        hess = -w
        hess[np.diag_indices(p)] += w.sum(axis=1) + ridge
        step = np.linalg.solve(hess, grad)
        t = 1.0
        while True:
            cand = theta + t * step
            cv = objective(cand)
            if cv >= value - 1e-12 * max(1.0, abs(value)) or t < 1e-10:
                break
            t *= 0.5
        theta, value = cand, cv
    return theta


def _neg_hessian(N, theta, ridge):
    d = theta[:, None] - theta[None, :]
    prob = 1.0 / (1.0 + np.exp(-d))
    w = N * prob * (1.0 - prob)
    hess = -w
    hess[np.diag_indices(theta.shape[0])] += w.sum(axis=1) + ridge
    return hess


def _reset(request):
    seed = request.get("seed")
    if type(seed) is not int or seed < 0:
        raise ValueError("bad seed")
    _STATE.clear()
    _STATE["rng"] = np.random.default_rng(seed)
    return {"ok": True}


def _load_chunk(request):
    n_total, n_chunks, chunk = request["n_rows_total"], request["n_chunks"], request["chunk_index"]
    if chunk == 0:
        _STATE["case_token"] = request["case_token"]
        _STATE["n"] = n_total
        _STATE["p"] = request["n_players"]
        _STATE["a"] = np.zeros(n_total, dtype=np.int64)
        _STATE["b"] = np.zeros(n_total, dtype=np.int64)
        _STATE["y"] = np.zeros(n_total, dtype=np.float64)
        _STATE["loaded"] = set()
        _STATE["n_chunks"] = n_chunks
    if request["case_token"] != _STATE.get("case_token") or n_total != _STATE["n"]:
        raise ValueError("inconsistent chunk")
    m = request["player_a"]["shape"][0]
    lo = request["row_offset"]
    _STATE["a"][lo:lo + m] = _decode(request["player_a"], "int32", m)
    _STATE["b"][lo:lo + m] = _decode(request["player_b"], "int32", m)
    _STATE["y"][lo:lo + m] = _decode(request["outcome"], "float32", m)
    _STATE["loaded"].add(chunk)
    return {"ok": True}


def _propose(request):
    started = time.monotonic()
    budget = 0.8 * float(request["deadline_seconds"])
    if _STATE.get("loaded") != set(range(_STATE.get("n_chunks", -1))):
        raise ValueError("data not loaded")
    a, b, y, p = _STATE["a"], _STATE["b"], _STATE["y"], _STATE["p"]
    ridge, tol = float(request["estimator"]["ridge"]), float(request["estimator"]["tol"])
    drop = request["perturbation"] == "drop"
    k = 1 if request["target"]["type"] == "top1" else int(request["target"]["k"])
    S0, N0 = _pair_stats(p, a, b, y)
    theta0 = _fit(S0, N0, ridge)
    order = np.argsort(-theta0, kind="stable")
    top = np.zeros(p, dtype=bool)
    top[order[:k]] = True
    leader, challenger = int(order[k - 1]), int(order[k])

    def changed(idx):
        ia, ib, iy = a[idx], b[idx], y[idx]
        lin = ia * p + ib
        if drop:
            cnt = np.bincount(lin, minlength=p * p).reshape(p, p).astype(np.float64)
            won = np.bincount(lin, weights=iy, minlength=p * p).reshape(p, p)
            lost = np.bincount(lin, weights=1.0 - iy, minlength=p * p).reshape(p, p)
            S, N = S0 - won - lost.T, N0 - cnt - cnt.T
        else:
            delta = np.bincount(lin, weights=1.0 - 2.0 * iy, minlength=p * p).reshape(p, p)
            S, N = S0 + delta - delta.T, N0
        theta = _fit(np.maximum(S, 0.0), np.maximum(N, 0.0), ridge, theta0)
        return float(theta[~top].max()) > float(theta[top].min()) + tol

    # One-step influence of each eligible row on the margin t_leader - t_challenger.
    c = np.zeros(p)
    c[leader], c[challenger] = 1.0, -1.0
    v = np.linalg.solve(_neg_hessian(N0, theta0, ridge), c)
    elig = np.arange(a.shape[0]) if drop else np.flatnonzero(y != 0.5)
    dv = v[a[elig]] - v[b[elig]]
    if drop:
        resid = y[elig] - 1.0 / (1.0 + np.exp(-(theta0[a[elig]] - theta0[b[elig]])))
        effect = -resid * dv
    else:
        effect = (1.0 - 2.0 * y[elig]) * dv
    ranked = elig[np.argsort(effect, kind="stable")]
    n = min(len(ranked), int(request["max_size"]))
    refits = 0
    best = None
    size, last_fail = 1, 0
    while n > 0 and time.monotonic() - started < budget:
        refits += 1
        if changed(ranked[:size]):
            best = size
            break
        last_fail = size
        if size >= n:
            break
        size = min(2 * size, n)
    if best is not None:
        lo, hi = last_fail, best
        while hi - lo > 1 and time.monotonic() - started < budget:
            mid = (lo + hi) // 2
            refits += 1
            if changed(ranked[:mid]):
                hi = mid
            else:
                lo = mid
        best = hi
    chosen = np.sort(ranked[:best]) if best is not None else np.zeros(0, dtype=np.int64)
    return {"indices": _encode_int32(chosen), "diagnostics": {"refits": float(refits)}}


def handle(request):
    op = request.get("op") if isinstance(request, dict) else None
    if op == "reset":
        return _reset(request)
    if op == "load_chunk":
        return _load_chunk(request)
    if op == "propose":
        return _propose(request)
    raise ValueError("unknown op")
