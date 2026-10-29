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
import time

import numpy as np

RIDGE = 1e-3  # matches the public evaluator specification
_STATE = {"seed": None, "rng": None}
_TIME_BUDGET = 13.0  # seconds of search per call (hard limit is 30 s)


def _decode(arr):
    if (type(arr) is not dict or arr.get("encoding") != "base64-le"
            or arr.get("dtype") not in ("int16", "int8")):
        raise ValueError("bad array")
    out = np.frombuffer(base64.b64decode(arr["data"]), dtype="<i2" if arr["dtype"] == "int16" else "i1")
    if list(arr["shape"]) != [out.size]:
        raise ValueError("bad shape")
    return out.astype(np.int64)


def _win_matrix(a, b, yv, w, k):
    """Weighted win-credit matrix W[i, j] = credit of i over j (ties = half)."""
    flat = np.bincount(a * k + b, weights=w * yv, minlength=k * k)
    flat += np.bincount(b * k + a, weights=w * (1.0 - yv), minlength=k * k)
    return flat.reshape(k, k)


def _objective(theta, wm, n):
    d = theta[:, None] - theta[None, :]
    return -np.sum(wm * np.logaddexp(0.0, -d)) + 0.5 * RIDGE * np.sum(theta ** 2)


def _fit_w(wm, theta0):
    """Damped Newton solve of the ridge-penalised BT MLE from a win matrix."""
    k = wm.shape[0]
    n = wm + wm.T
    theta = theta0.copy()
    for _ in range(100):
        p = 1.0 / (1.0 + np.exp(-(theta[:, None] - theta[None, :])))
        g = (wm - n * p).sum(1) - RIDGE * theta
        if np.max(np.abs(g)) < 1e-10:
            break
        h = n * p * (1.0 - p)
        a_mat = np.diag(h.sum(1) + RIDGE) - h
        step = np.linalg.solve(a_mat, g)
        f0 = _objective(theta, wm, n)
        t = 1.0
        for _ in range(30):
            cand = theta + t * step
            if _objective(cand, wm, n) >= f0 - 1e-12 * max(1.0, abs(f0)):
                break
            t *= 0.5
        theta = theta + t * step
    p = 1.0 / (1.0 + np.exp(-(theta[:, None] - theta[None, :])))
    h = n * p * (1.0 - p)
    return theta, np.diag(h.sum(1) + RIDGE) - h


def _gap(theta, top):
    others = np.delete(theta, top)
    return float(theta[top] - others.max())


def _search(a, b, y, k_models, budget, mode, theta0, top, rival0, rounds, adaptive, deadline):
    """Iteratively re-linearised greedy edit search. Returns (gap_after, chosen_idx)."""
    n = a.size
    yv0 = np.where(y == 0, 0.5, (y + 1) / 2.0)
    yv = yv0.copy()
    w = np.ones(n)
    chosen = np.zeros(n, dtype=bool)
    eligible_base = np.ones(n, dtype=bool) if mode == "drop" else (y != 0)
    theta = theta0
    wm = _win_matrix(a, b, yv, w, k_models)
    theta, a_mat = _fit_w(wm, theta)
    rival = rival0
    used = 0
    gap = _gap(theta, top)
    for r in range(rounds):
        if used >= budget or gap <= 0 or time.monotonic() > deadline:
            break
        if adaptive and r > 0:
            masked = theta.copy()
            masked[top] = -np.inf
            rival = int(np.argmax(masked))
        remaining = budget - used
        chunk = int(math.ceil(remaining / (rounds - r)))
        ainv = np.linalg.inv(a_mat)
        e = np.zeros(k_models)
        e[top], e[rival] = 1.0, -1.0
        v = ainv @ e
        s = v[a] - v[b]
        p = 1.0 / (1.0 + np.exp(-(theta[a] - theta[b])))
        if mode == "drop":
            quad = ainv[a, a] + ainv[b, b] - 2.0 * ainv[a, b]
            lev = np.clip(p * (1.0 - p) * quad, 0.0, 0.95)
            effect = -s * (yv - p) / (1.0 - lev)
        else:
            effect = s * (1.0 - 2.0 * yv)
        ok = eligible_base & ~chosen & (effect < 0)
        effect = np.where(ok, effect, np.inf)
        cand = np.lexsort((np.arange(n), effect))[:chunk]
        cand = cand[np.isfinite(effect[cand])]
        if cand.size == 0:
            break
        chosen[cand] = True
        used += int(cand.size)
        if mode == "drop":
            w[cand] = 0.0
        else:
            yv[cand] = 1.0 - yv[cand]
        wm = _win_matrix(a, b, yv, w, k_models)
        theta, a_mat = _fit_w(wm, theta)
        gap = _gap(theta, top)
    return gap, np.flatnonzero(chosen)


def _propose(req):
    t_start = time.monotonic()
    deadline = t_start + _TIME_BUDGET
    mode, budget = req["mode"], int(req["budget"])
    a, b, y = _decode(req["model_a"]), _decode(req["model_b"]), _decode(req["outcome"])
    k_models = int(req["n_models"])
    yv0 = np.where(y == 0, 0.5, (y + 1) / 2.0)
    wm0 = _win_matrix(a, b, yv0, np.ones(a.size), k_models)
    theta0, _ = _fit_w(wm0, np.zeros(k_models))
    order = np.argsort(-theta0, kind="stable")
    top = int(order[0])
    if k_models < 2:
        return {"indices": []}
    n_riv = min(k_models - 1, 6)
    rivals = [int(j) for j in order[1:1 + n_riv]]
    # (rounds, adaptive) schemes in rough order of expected value; a coarse pass first
    schemes = [(6, True), (6, False), (1, False), (16, True), (16, False), (40, True)]
    best_gap, best_idx = math.inf, np.zeros(0, dtype=np.int64)
    for rounds, adaptive in schemes:
        rounds = max(1, min(rounds, budget))
        for ri, rv in enumerate(rivals):
            if adaptive and ri > 0 and rounds > 1:
                # adaptive variant re-targets each round; only the closest rival seeds it
                # plus a couple of alternative seeds for diversity
                if ri > 2:
                    continue
            if time.monotonic() > deadline:
                break
            gap, idx = _search(a, b, y, k_models, budget, mode, theta0, top, rv,
                               rounds, adaptive, deadline)
            if idx.size and gap < best_gap:
                best_gap, best_idx = gap, idx
        if best_gap <= 0 or time.monotonic() > deadline:
            break
    idx = [int(i) for i in best_idx[:budget]]
    return {"indices": sorted(set(idx))}


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
