"""Influence-guided minimal-removal search for Bradley-Terry leaderboard rank flips.

The evaluator calls ``handle(request) -> response`` once per operation with finite JSON values.
One episode is: ``reset`` -> ``load_chunk`` x n_chunks -> ``analyze``. Every request is a dict with
an ``op`` key; every response is a dict. All state lives in this process's memory. The evaluator
and this process share no filesystem; never rely on paths.

Operations
----------
{"op": "reset", "seed": int}
    Clear ALL state (table, caches, RNG) and seed the RNG. Response: exactly {"ok": true}.

{"op": "load_chunk", "chunk_index": int, "n_chunks": int, "n_rows_total": int, "n_models": int,
 "a": ARR, "b": ARR, "y": ARR}
    One slice of the comparison table (in order, <= 65536 rows per chunk, <= 4 chunks). Row j is
    "model a[j] vs model b[j]" with outcome y[j]: 0 = A wins, 1 = B wins, 2 = tie. ARR =
    {"dtype": "uint16" | "uint8", "shape": [n], "encoding": "base64-le", "data": <base64>}.
    Response: exactly {"ok": true}.

{"op": "analyze", "hi": int, "lo": int, "k_cap": int, "tie_as_half_win": true, "ridge": float,
 "deadline_seconds": float}
    Bradley-Terry logistic MLE with ridge; ``hi`` is ranked directly above ``lo``. Propose at most
    ``k_cap`` unique row indices whose removal makes the exact refit rank ``lo`` strictly above
    ``hi``. Score = 1 - k / k_cap if the refit flips, else 0.
    Response: {"removed": {"dtype": "uint32", "shape": [k], "encoding": "base64-le", "data": ...},
    "diagnostics": {<name>: <finite number>, ...}}  (optional, <= 32 numbers, ignored for scoring).

Method (this candidate)
-----------------------
1. ``fit_bradley_terry``: damped Newton with analytic gradient / dense Hessian.
2. ``influence_on_gap``: one-step Newton (influence-function) effect of deleting each row on the
   gap theta_hi - theta_lo, with the leave-one-out leverage correction 1/(1 - w_i x_i' H^-1 x_i).
3. ``greedy_flip_budget``: (a) one-shot influence ranking + refit-verified prefix bisection;
   (b) re-linearised greedy: after every batch refit and recompute influences, batch size = a
   fraction of the linearised remaining need (Newton-like geometric convergence), then prefix
   bisection over insertion order; (c) polish by drop-and-readd local search (drop the least useful
   rows of the incumbent, re-run (b) with a strictly smaller size limit).
4. ``verify_by_refit``: every candidate set is accepted only after an exact refit flips the pair by
   a small safety margin. ``random_removal_baseline`` is the random-removal control (diagnostic only).
"""
import base64
import math
import time

import numpy as np

_STATE = {}

MARGIN = 1e-5  # safety margin on theta_lo - theta_hi in our own exact refit
SHRINK = 0.6  # fraction of the linearised need removed per re-linearised round


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


def _hessian(a, b, w, m, ridge):
    h = np.bincount(a * m + b, w, m * m).reshape(m, m)
    h = -(h + h.T)
    h[np.diag_indices(m)] += np.bincount(a, w, m) + np.bincount(b, w, m) + ridge
    return h


def fit_bradley_terry(a, b, s, m, ridge, theta0=None, tol=1e-9, max_iter=60):
    """Ridge-regularised Bradley-Terry MLE (ties = half wins via s) by damped Newton."""
    th = np.zeros(m) if theta0 is None else theta0.copy()

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
        h = _hessian(a, b, p * (1.0 - p), m, ridge)
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


def influence_on_gap(a, b, s, theta, hi, lo, m, ridge, leverage=True):
    """Newton-step change of theta[hi]-theta[lo] if each row were deleted (negative closes the gap)."""
    p = 1.0 / (1.0 + np.exp(-(theta[a] - theta[b])))
    w = p * (1.0 - p)
    h = _hessian(a, b, w, m, ridge)
    e = np.zeros(m)
    e[hi], e[lo] = 1.0, -1.0
    if leverage:
        hinv = np.linalg.inv(h)
        v = hinv @ e
        d = np.diag(hinv)
        q = d[a] + d[b] - 2.0 * hinv[a, b]
        den = np.maximum(1.0 - w * q, 1e-3)
    else:
        v = np.linalg.solve(h, e)
        den = 1.0
    return (p - s) * (v[a] - v[b]) / den


def verify_by_refit(ctx, removed, theta_start=None):
    """Exact refit without ``removed``; returns (flipped, margin = theta_lo - theta_hi, theta)."""
    ctx["refits"] += 1
    keep = np.ones(ctx["n"], bool)
    if len(removed):
        keep[np.asarray(removed, dtype=np.int64)] = False
    th = fit_bradley_terry(ctx["a"][keep], ctx["b"][keep], ctx["s"][keep], ctx["m"], ctx["ridge"],
                           ctx["theta0"] if theta_start is None else theta_start)
    margin = float(th[ctx["lo"]] - th[ctx["hi"]])
    return margin > MARGIN, margin, th


def random_removal_baseline(ctx, k, rng):
    """Control: does removing k uniformly random rows flip the pair (exact refit)?"""
    k = int(min(k, ctx["n"]))
    rows = rng.choice(ctx["n"], size=k, replace=False)
    return verify_by_refit(ctx, rows)[0]


def _min_prefix(ctx, order, stop_at, known_flip=False):
    """Smallest refit-verified prefix of ``order`` (bisection); None if the full order does not flip."""
    order = np.asarray(order, dtype=np.int64)
    top = min(ctx["cap"], len(order))
    if top < 1:
        return None
    if not known_flip and (time.monotonic() > stop_at or not verify_by_refit(ctx, order[:top])[0]):
        return None
    lo_k, hi_k = 0, top
    while hi_k - lo_k > 1 and time.monotonic() < stop_at:
        mid = (lo_k + hi_k) // 2
        if verify_by_refit(ctx, order[:mid])[0]:
            hi_k = mid
        else:
            lo_k = mid
    return order[:hi_k]


def _relinearize(ctx, base, stop_at, limit):
    """Re-linearised greedy starting from removed set ``base``; None if it needs more than ``limit`` rows."""
    a, b, s, m, ridge, hi, lo = (ctx[k] for k in ("a", "b", "s", "m", "ridge", "hi", "lo"))
    keep = np.ones(ctx["n"], bool)
    removed = [int(i) for i in base]
    if removed:
        keep[removed] = False
    flipped, margin, theta = verify_by_refit(ctx, removed)
    while not flipped:
        if time.monotonic() > stop_at or len(removed) >= limit:
            return None
        rows = np.flatnonzero(keep)
        g = influence_on_gap(a[rows], b[rows], s[rows], theta, hi, lo, m, ridge)
        order = np.argsort(g, kind="stable")
        gs = g[order]
        neg = int(np.searchsorted(gs, 0.0))
        if neg == 0:
            return None
        red = -np.cumsum(gs[:neg])
        need = MARGIN - margin  # current gap theta_hi - theta_lo plus safety margin
        n_lin = min(int(np.searchsorted(red, need)) + 1, neg)
        batch = min(max(1, int(math.ceil(SHRINK * n_lin))), limit - len(removed))
        take = rows[order[:batch]]
        keep[take] = False
        removed.extend(int(i) for i in take)
        flipped, margin, theta = verify_by_refit(ctx, removed, theta)
    return _min_prefix(ctx, np.asarray(removed, dtype=np.int64), stop_at, known_flip=True)


def _polish(ctx, best, stop_at):
    """Drop-and-readd local search: drop the least useful rows of the incumbent, greedily refill."""
    frac = 0.25
    for _ in range(14):
        if len(best) <= 1 or time.monotonic() > stop_at:
            break
        d = max(1, int(round(frac * len(best))))
        _, _, theta = verify_by_refit(ctx, best)
        infl = influence_on_gap(ctx["a"], ctx["b"], ctx["s"], theta, ctx["hi"], ctx["lo"], ctx["m"], ctx["ridge"])
        useful_first = np.argsort(infl[best], kind="stable")
        base = best[useful_first[:len(best) - d]]
        cand = _relinearize(ctx, base, stop_at, limit=len(best) - 1)
        if cand is not None and len(cand) < len(best):
            best = cand
        else:
            if d == 1:
                break
            frac *= 0.5
    return best


def greedy_flip_budget(ctx, stop_at):
    """Smallest refit-verified removal set found by influence-guided greedy search (None if none)."""
    n, cap = ctx["n"], ctx["cap"]
    infl0 = influence_on_gap(ctx["a"], ctx["b"], ctx["s"], ctx["theta0"], ctx["hi"], ctx["lo"], ctx["m"],
                             ctx["ridge"])
    best = _min_prefix(ctx, np.argsort(infl0, kind="stable")[:cap], stop_at)
    cand = _relinearize(ctx, np.zeros(0, dtype=np.int64), stop_at, limit=(len(best) - 1 if best is not None else cap))
    if cand is not None and (best is None or len(cand) < len(best)):
        best = cand
    if best is not None:
        best = _polish(ctx, np.asarray(best, dtype=np.int64), stop_at)
    return best


def _analyze(req, st):
    t_start = time.monotonic()
    a = np.concatenate([c[0] for c in st["chunks"]]).astype(np.int64)
    b = np.concatenate([c[1] for c in st["chunks"]]).astype(np.int64)
    y = np.concatenate([c[2] for c in st["chunks"]])
    n, m = len(y), int(st["n_models"])
    ridge = float(req["ridge"])
    s = _scores(y) if req.get("tie_as_half_win", True) else np.where(y == 0, 1.0, 0.0)
    hi, lo, cap = int(req["hi"]), int(req["lo"]), int(req["k_cap"])
    stop_at = t_start + 0.6 * float(req["deadline_seconds"])
    theta0 = fit_bradley_terry(a, b, s, m, ridge)
    ctx = {"a": a, "b": b, "s": s, "n": n, "m": m, "ridge": ridge, "hi": hi, "lo": lo, "cap": cap,
           "theta0": theta0, "refits": 0}
    best = greedy_flip_budget(ctx, stop_at)
    chosen = np.zeros(0, dtype=np.int64) if best is None else np.asarray(best, dtype=np.int64)[:cap]
    diag = {"refits": float(ctx["refits"]), "k": float(len(chosen))}
    if len(chosen) and time.monotonic() < t_start + 0.8 * float(req["deadline_seconds"]):
        diag["random_flip"] = float(random_removal_baseline(ctx, len(chosen), st["rng"]))
    return {"removed": _encode_u32(chosen), "diagnostics": diag}


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
        return _analyze(req=request, st=_STATE)
    raise ValueError("unknown op")
