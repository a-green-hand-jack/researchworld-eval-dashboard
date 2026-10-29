"""Pair-class aggregated, multi-rival, exact-refit search for Bradley-Terry leaderboards.

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

Method
------
The Bradley-Terry fit depends on the data only through per-pair outcome counts, so rows
are aggregated into (unordered pair, outcome) classes and the search allocates integer
unit counts to classes.  A batched greedy re-linearises the top-vs-rival gap after each
exact refit; several rival objectives are tried and the final edit is chosen by the
exact local refit score.  The plain first-order selection of the starter is always the
first candidate, so the result is never worse than it (by exact local score).
"""
import base64
import math
import time

import numpy as np

try:
    from scipy.special import expit as _sigmoid
except Exception:  # pragma: no cover - scipy is documented as available
    def _sigmoid(x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -700.0, 700.0)))

RIDGE = 1e-3  # matches the public evaluator specification
_TIME_BUDGET = 12.0  # seconds of search per propose call (hard limit is 30 s)
_MAX_RIVALS = 4
_STATE = {"seed": None, "rng": None}


def _decode(arr):
    if (type(arr) is not dict or arr.get("encoding") != "base64-le"
            or arr.get("dtype") not in ("int16", "int8")):
        raise ValueError("bad array")
    out = np.frombuffer(base64.b64decode(arr["data"]), dtype="<i2" if arr["dtype"] == "int16" else "i1")
    if list(arr["shape"]) != [out.size]:
        raise ValueError("bad shape")
    return out.astype(np.int64)


# ---------------------------------------------------------------------------
# Exact Bradley-Terry refit on count matrices
# ---------------------------------------------------------------------------

def _objective(w, theta):
    d = theta[:, None] - theta[None, :]
    return -np.sum(w * np.logaddexp(0.0, -d)) - 0.5 * RIDGE * np.sum(theta * theta)


def _newton(w, theta0):
    """Damped Newton solve of the ridge-penalised BT MLE; w[i, j] = wins of i over j."""
    n = w + w.T
    theta = np.array(theta0, dtype=np.float64)
    for _ in range(100):
        p = _sigmoid(theta[:, None] - theta[None, :])
        g = (w - n * p).sum(1) - RIDGE * theta
        if np.max(np.abs(g)) < 1e-10:
            break
        h = n * p * (1.0 - p)
        a_mat = np.diag(h.sum(1) + RIDGE) - h
        step = np.linalg.solve(a_mat, g)
        f0 = _objective(w, theta)
        t = 1.0
        new = theta + step
        for _ in range(30):
            new = theta + t * step
            if _objective(w, new) >= f0 - 1e-9:
                break
            t *= 0.5
        theta = new
        if np.max(np.abs(t * step)) < 1e-14:
            break
    p = _sigmoid(theta[:, None] - theta[None, :])
    h = n * p * (1.0 - p)
    return theta, np.diag(h.sum(1) + RIDGE) - h


# ---------------------------------------------------------------------------
# Pair-class aggregation
# ---------------------------------------------------------------------------

def _aggregate_pair_classes(a, b, y, n_models):
    """Group rows into (unordered pair i<j, outcome) classes.

    Outcome code relative to the orientation i<j: 0 = i wins, 1 = j wins, 2 = tie.
    Row indices of class c are rows[starts[c]:starts[c] + cnt[c]] (stable order), so x
    chosen units of a class map to its first x rows.
    """
    k = int(n_models)
    valid = np.flatnonzero(a != b)
    av, bv, yv = a[valid], b[valid], y[valid]
    lo, hi = np.minimum(av, bv), np.maximum(av, bv)
    swapped = av > bv
    code = np.where(yv == 0, 2, np.where((yv == 1) != swapped, 0, 1))
    key = (lo * k + hi) * 3 + code
    srt = np.argsort(key, kind="stable")
    rows = valid[srt]
    uniq, starts, cnt = np.unique(key[srt], return_index=True, return_counts=True)
    pair = uniq // 3
    ci, cj, cc = pair // k, pair % k, uniq % 3
    ctx = {
        "K": k, "rows": rows, "starts": starts, "cnt": cnt.astype(np.float64),
        "ci": ci, "cj": cj, "cc": cc,
        "f_ij": ci * k + cj, "f_ji": cj * k + ci,
        "m0": cc == 0, "m1": cc == 1, "m2": cc == 2,
        "yv": np.where(cc == 0, 1.0, np.where(cc == 1, 0.0, 0.5)),
    }
    ctx["w0"] = _counts(ctx, None, "drop")
    return ctx


def _counts(ctx, x, mode):
    """Count matrix after applying x units per class (x=None: unedited data)."""
    k = ctx["K"]
    cnt = ctx["cnt"]
    m0, m1, m2 = ctx["m0"], ctx["m1"], ctx["m2"]
    f_ij, f_ji = ctx["f_ij"], ctx["f_ji"]
    if x is None:
        idx = np.concatenate([f_ij[m0], f_ji[m1], f_ij[m2], f_ji[m2]])
        wts = np.concatenate([cnt[m0], cnt[m1], 0.5 * cnt[m2], 0.5 * cnt[m2]])
        return np.bincount(idx, weights=wts, minlength=k * k).reshape(k, k)
    if mode == "drop":
        idx = np.concatenate([f_ij[m0], f_ji[m1], f_ij[m2], f_ji[m2]])
        wts = np.concatenate([-x[m0], -x[m1], -0.5 * x[m2], -0.5 * x[m2]])
    else:
        idx = np.concatenate([f_ij[m0], f_ji[m0], f_ji[m1], f_ij[m1]])
        wts = np.concatenate([-x[m0], x[m0], -x[m1], x[m1]])
    return ctx["w0"] + np.bincount(idx, weights=wts, minlength=k * k).reshape(k, k)


def _gap(theta, top):
    other = np.delete(theta, top)
    return float(theta[top] - other.max())


def _exact_refit_score(ctx, x, mode, theta_warm, top, gap_before):
    """Exact local mirror of the public scoring rule for an edit given as class units.

    Returns (displaced, gap_after / gap_before, new_top).
    """
    theta, _ = _newton(_counts(ctx, x, mode), theta_warm)
    new_top = int(np.argmax(theta))
    return new_top != top, _gap(theta, top) / gap_before, new_top


def _level_score(displaced, ratio):
    return 1.0 if displaced else float(min(1.0, max(0.0, 1.0 - ratio)))


# ---------------------------------------------------------------------------
# Greedy allocation over class units
# ---------------------------------------------------------------------------

def _class_level_greedy(ctx, mode, k, theta0, a0, top, gap0, rival, n_batches, tau_frac, deadline):
    """Batched, re-linearised greedy allocation of the unit budget to classes.

    rival: int (fixed rival competitor), "strong" (current strongest non-top competitor)
    or "soft" (soft-min weights over all rivals with temperature tau_frac * gap0).
    Returns the integer unit vector x over classes.
    """
    kk = ctx["K"]
    ci, cj, cnt, yv = ctx["ci"], ctx["cj"], ctx["cnt"], ctx["yv"]
    x = np.zeros(cnt.size)
    theta, a_mat = theta0, a0
    remaining = int(k)
    n_batches = max(1, min(int(n_batches), remaining))
    if mode == "drop":
        eligible = np.ones(cnt.size, dtype=bool)
    else:
        eligible = ~ctx["m2"]
    for b in range(n_batches):
        if remaining <= 0 or time.perf_counter() > deadline:
            break
        size = int(math.ceil(remaining / (n_batches - b)))
        e = np.zeros(kk)
        e[top] = 1.0
        if rival == "soft":
            gaps = theta[top] - theta
            gaps[top] = np.inf
            wts = np.exp(-(gaps - gaps.min()) / max(tau_frac * gap0, 1e-9))
            wts[top] = 0.0
            e -= wts / wts.sum()
        else:
            if rival == "strong":
                others = theta.copy()
                others[top] = -np.inf
                r = int(np.argmax(others))
            else:
                r = int(rival)
            e[r] = -1.0
        v = np.linalg.solve(a_mat, e)
        p = _sigmoid(theta[ci] - theta[cj])
        s = v[ci] - v[cj]
        if mode == "drop":
            effect = -s * (yv - p)
        else:
            effect = s * ((1.0 - yv) - yv)
        avail = cnt - x
        cand = np.flatnonzero((effect < 0) & (avail > 0) & eligible)
        if cand.size == 0:
            break
        cand = cand[np.lexsort((cand, effect[cand]))]
        av = avail[cand]
        before = np.cumsum(av) - av
        take = np.minimum(av, np.maximum(0.0, size - before))
        x[cand] += take
        remaining -= int(round(take.sum()))
        theta, a_mat = _newton(_counts(ctx, x, mode), theta)
        if int(np.argmax(theta)) != top:
            break
    return x


def _multi_rival_search(ctx, mode, k, theta0, a0, top, gap0, deadline):
    """Try several rival objectives / batch schedules; keep the best by exact local score.

    The starter-equivalent single first-order pass against rank 2 is evaluated first and
    stays as the fallback.  Returns (score, x).
    """
    order = np.argsort(-theta0)
    rivals = [int(r) for r in order[1:1 + _MAX_RIVALS]]
    configs = [(rivals[0], 1, 0.0)]
    configs += [("strong", 6, 0.0), ("soft", 6, 0.3), ("soft", 6, 0.1)]
    configs += [(r, 6, 0.0) for r in rivals]
    configs += [("strong", 16, 0.0), ("soft", 16, 0.3), ("strong", 3, 0.0)]
    configs += [(r, 16, 0.0) for r in rivals]
    configs += [("strong", 32, 0.0), ("soft", 32, 0.1), ("soft", 32, 0.3)]
    configs += [("strong", 64, 0.0), ("soft", 64, 0.2)]
    best_score, best_x = -1.0, None
    seen = set()
    for rival, nb, tau in configs:
        if best_x is not None and time.perf_counter() > deadline:
            break
        nb_eff = max(1, min(nb, k))
        sig = (rival, nb_eff, tau)
        if sig in seen:
            continue
        seen.add(sig)
        x = _class_level_greedy(ctx, mode, k, theta0, a0, top, gap0, rival, nb_eff, tau, deadline)
        displaced, ratio, _ = _exact_refit_score(ctx, x, mode, theta0, top, gap0)
        score = _level_score(displaced, ratio)
        if score > best_score:
            best_score, best_x = score, x
        if best_score >= 1.0:
            break
    return best_score, best_x


def _units_to_rows(ctx, x, k):
    rows, starts = ctx["rows"], ctx["starts"]
    out = []
    for c in np.flatnonzero(x > 0.5):
        u = int(round(x[c]))
        out.extend(int(r) for r in rows[starts[c]:starts[c] + u])
    return out[:k]


def _search(a, b, y, n_models, mode, k, t_start):
    ctx = _aggregate_pair_classes(a, b, y, n_models)
    if ctx["cnt"].size == 0 or n_models < 2:
        return []
    theta0, a0 = _newton(ctx["w0"], np.zeros(n_models))
    top = int(np.argmax(theta0))
    gap0 = _gap(theta0, top)
    if not gap0 > 1e-12:
        return None
    deadline = t_start + _TIME_BUDGET
    _, x = _multi_rival_search(ctx, mode, k, theta0, a0, top, gap0, deadline)
    if x is None:
        return None
    return _units_to_rows(ctx, x, k)


# ---------------------------------------------------------------------------
# Starter first-order selection (kept as an independent fallback)
# ---------------------------------------------------------------------------

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


def _starter_select(a, b, y, n_models, mode, k):
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
    return [int(i) for i in idx if math.isfinite(effect[i]) and effect[i] < 0]


def _valid(idx, y, mode, k, n):
    if len(idx) > k or len(set(idx)) != len(idx):
        return False
    for i in idx:
        if type(i) is not int or i < 0 or i >= n:
            return False
        if mode == "flip" and y[i] == 0:
            return False
    return True


def _propose(req):
    t_start = time.perf_counter()
    mode, k = req["mode"], int(req["budget"])
    a, b, y = _decode(req["model_a"]), _decode(req["model_b"]), _decode(req["outcome"])
    n_models = int(req["n_models"])
    idx = None
    try:
        idx = _search(a, b, y, n_models, mode, k, t_start)
        if idx is not None:
            idx = [int(i) for i in idx]
            if not _valid(idx, y, mode, k, a.size):
                idx = None
    except Exception:
        idx = None
    if idx is None:
        idx = _starter_select(a, b, y, n_models, mode, k)
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
