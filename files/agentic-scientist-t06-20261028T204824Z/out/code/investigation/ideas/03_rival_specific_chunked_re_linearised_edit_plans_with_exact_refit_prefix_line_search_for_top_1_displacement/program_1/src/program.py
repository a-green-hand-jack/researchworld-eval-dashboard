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
from scipy.special import expit

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


_TIME_BUDGET = 10.0  # seconds per propose call (hard limit is 30 s)
_N_RIVALS = 4
_N_CHUNKS = 8
_PREFIX_FRACS = (1.0, 0.75, 0.5, 0.35, 0.25, 0.15)


def _build_counts(a, b, y, n_models):
    w = np.zeros((n_models, n_models))
    win_a, win_b, tie = y == 1, y == -1, y == 0
    np.add.at(w, (a[win_a], b[win_a]), 1.0)
    np.add.at(w, (b[win_b], a[win_b]), 1.0)
    np.add.at(w, (a[tie], b[tie]), 0.5)
    np.add.at(w, (b[tie], a[tie]), 0.5)
    return w


def _refit_counts(w_counts, n_models, theta0=None):
    """Damped Newton on the K x K win-count matrix; returns (theta, Hessian matrix)."""
    w = w_counts
    wt = w + w.T
    theta = np.zeros(n_models) if theta0 is None else np.array(theta0, dtype=float)

    def objective(t):
        d = t[:, None] - t[None, :]
        return float(np.sum(w * -np.logaddexp(0.0, -d)) - 0.5 * RIDGE * np.sum(t * t))

    f_cur = None
    for _ in range(100):
        p = expit(theta[:, None] - theta[None, :])
        g = (w - wt * p).sum(1) - RIDGE * theta
        if np.max(np.abs(g)) < 1e-10:
            break
        h = wt * p * (1.0 - p)
        a_mat = np.diag(h.sum(1) + RIDGE) - h
        step = np.linalg.solve(a_mat, g)
        if f_cur is None:
            f_cur = objective(theta)
        t_len, cand, f_new = 1.0, None, None
        for _ in range(30):
            cand = theta + t_len * step
            f_new = objective(cand)
            if f_new >= f_cur - 1e-10 * max(1.0, abs(f_cur)):
                break
            t_len *= 0.5
        else:
            break  # no ascent possible at working precision
        theta, f_cur = cand, f_new
        if np.max(np.abs(t_len * step)) < 1e-14:
            break
    p = expit(theta[:, None] - theta[None, :])
    h = wt * p * (1.0 - p)
    return theta, np.diag(h.sum(1) + RIDGE) - h


def _apply_edits(ctx, edit_idx, mode, base=None):
    """Return the count matrix after applying the edits as sparse count deltas."""
    w = (ctx["w0"] if base is None else base).copy()
    idx = np.asarray(edit_idx, dtype=np.int64)
    if idx.size == 0:
        return w
    a, b, y = ctx["a"][idx], ctx["b"][idx], ctx["y"][idx]
    win_a, win_b, tie = y == 1, y == -1, y == 0
    if mode == "drop":
        np.add.at(w, (a[win_a], b[win_a]), -1.0)
        np.add.at(w, (b[win_b], a[win_b]), -1.0)
        np.add.at(w, (a[tie], b[tie]), -0.5)
        np.add.at(w, (b[tie], a[tie]), -0.5)
    else:  # flip (decisive rows only)
        np.add.at(w, (a[win_a], b[win_a]), -1.0)
        np.add.at(w, (b[win_a], a[win_a]), 1.0)
        np.add.at(w, (b[win_b], a[win_b]), -1.0)
        np.add.at(w, (a[win_b], b[win_b]), 1.0)
    return w


def _rank_stats(ctx, theta):
    """(score, displaced, gap_after) by the evaluator's rule."""
    top = ctx["top"]
    others = np.delete(theta, top)
    gap_after = float(theta[top] - np.max(others))
    displaced = int(np.argmax(theta)) != top
    if displaced:
        return 1.0, True, gap_after
    score = min(1.0, max(0.0, 1.0 - gap_after / ctx["gap0"]))
    return float(score), False, gap_after


def _score_plan(ctx, edit_idx, mode):
    """Exact refit of the edited data; returns (score, displaced, gap_after)."""
    w = _apply_edits(ctx, edit_idx, mode)
    theta, _ = _refit_counts(w, ctx["k_models"], ctx["theta0"])
    return _rank_stats(ctx, theta)


def _row_effects(ctx, theta, v, mode):
    """First-order change of the target gap per row at the current optimum."""
    a, b, y = ctx["a"], ctx["b"], ctx["y"]
    p = expit(theta[a] - theta[b])
    yv = (y + 1) / 2.0
    s = v[a] - v[b]
    if mode == "drop":
        effect = -s * (yv - p)
        eligible = np.ones(a.size, dtype=bool)
    else:
        effect = s * ((1.0 - yv) - yv)
        eligible = y != 0
    return np.where(eligible, effect, np.inf)


def _starter_plan(ctx, mode, k):
    """Single-shot first-order top-k plan at the unedited optimum (starter selection)."""
    e = np.zeros(ctx["k_models"])
    e[ctx["top"]], e[ctx["order"][1]] = 1.0, -1.0
    v = np.linalg.solve(ctx["a0"], e)
    effect = _row_effects(ctx, ctx["theta0"], v, mode)
    idx = np.lexsort((np.arange(effect.size), effect))[:k]
    return [int(i) for i in idx if math.isfinite(effect[i]) and effect[i] < 0]


def _rival_plan(ctx, rivals, mode, k, n_chunks, deadline):
    """Chunked plan against a rival (int) or the uniform mix of rivals (list):
    exact refit and re-linearisation between chunks; stops once rank 1 is displaced."""
    if isinstance(rivals, (int, np.integer)):
        rivals = [int(rivals)]
    n_models = ctx["k_models"]
    e = np.zeros(n_models)
    e[ctx["top"]] = 1.0
    for j in rivals:
        e[j] -= 1.0 / len(rivals)
    chunk = max(1, int(math.ceil(k / float(max(1, min(n_chunks, k))))))
    w = ctx["w0"].copy()
    theta, a_mat = ctx["theta0"], ctx["a0"]
    chosen = np.zeros(ctx["a"].size, dtype=bool)
    plan = []
    while len(plan) < k and time.perf_counter() < deadline:
        v = np.linalg.solve(a_mat, e)
        effect = _row_effects(ctx, theta, v, mode)
        effect[chosen] = np.inf
        m = min(chunk, k - len(plan))
        if m < effect.size:
            cand = np.argpartition(effect, m - 1)[:m]
        else:
            cand = np.arange(effect.size)
        cand = cand[np.lexsort((cand, effect[cand]))]
        cand = cand[np.isfinite(effect[cand]) & (effect[cand] < 0)]
        if cand.size == 0:
            break
        chosen[cand] = True
        plan.extend(int(i) for i in cand)
        w = _apply_edits(ctx, cand, mode, w)
        theta, a_mat = _refit_counts(w, n_models, theta)
        if int(np.argmax(theta)) != ctx["top"]:
            break
    return plan


def _prefix_line_search(ctx, plan, mode, k, best, deadline):
    """Exact-refit scores of prefixes of ``plan``; ``best`` = (key, plan) is updated."""
    if not plan:
        return best
    lengths = {len(plan)}
    for f in _PREFIX_FRACS:
        lengths.add(min(len(plan), max(1, int(round(f * k)))))
    for m in sorted(lengths, reverse=True):
        if time.perf_counter() >= deadline:
            break
        score, _, gap_after = _score_plan(ctx, plan[:m], mode)
        key = (score, -gap_after, -m)  # higher score, bigger margin, then fewer edits
        if best is None or key > best[0]:
            best = (key, list(plan[:m]))
    return best


def _search_propose(req):
    t_start = time.perf_counter()
    deadline = t_start + _TIME_BUDGET
    mode, k = req["mode"], int(req["budget"])
    a, b, y = _decode(req["model_a"]), _decode(req["model_b"]), _decode(req["outcome"])
    n_models = int(req["n_models"])
    w0 = _build_counts(a, b, y, n_models)
    theta0, a0 = _refit_counts(w0, n_models)
    order = np.argsort(-theta0)
    ctx = {"a": a, "b": b, "y": y, "k_models": n_models, "w0": w0, "theta0": theta0,
           "a0": a0, "order": order, "top": int(order[0]),
           "gap0": max(float(theta0[order[0]] - theta0[order[1]]), 1e-12)}
    # candidate 0: starter first-order plan (always kept as the fallback)
    starter = _starter_plan(ctx, mode, k)
    s_score, _, s_gap = _score_plan(ctx, starter, mode)
    best = ((s_score, -s_gap, -len(starter)), list(starter))
    best = _prefix_line_search(ctx, starter, mode, k, best, deadline)
    rival_ids = [int(j) for j in order[1:1 + _N_RIVALS]]
    targets = list(rival_ids)
    if len(rival_ids) > 1:
        targets.append(list(rival_ids))  # soft direction over all candidate rivals
    for target in targets:
        if time.perf_counter() >= deadline:
            break
        plan = _rival_plan(ctx, target, mode, k, _N_CHUNKS, deadline)
        best = _prefix_line_search(ctx, plan, mode, k, best, deadline)
    return best[1]


def _validate(idx, req):
    n = int(req["n_comparisons"])
    k = int(req["budget"])
    out, seen = [], set()
    y = _decode(req["outcome"]) if req["mode"] == "flip" else None
    for i in idx:
        i = int(i)
        if i in seen or i < 0 or i >= n:
            continue
        if y is not None and y[i] == 0:
            continue
        seen.add(i)
        out.append(i)
        if len(out) >= k:
            break
    return out


def _propose(req):
    try:
        idx = _validate(_search_propose(req), req)
        return {"indices": idx}
    except Exception:
        return _starter_propose(req)


def _starter_propose(req):
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
