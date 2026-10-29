"""Baseline candidate: ridge regression of log cover time on cheap graph statistics.

Task: predict the start-averaged expected cover time of the simple random walk on small
connected undirected graphs (6 <= n <= 30). The evaluator owns the Monte Carlo ground
truth; this candidate only sees labelled training graphs (via ``fit``) and unlabeled
graphs to predict (via ``predict``).

Interface: ``handle(request) -> response`` over finite JSON values. Every request is a
dict with an ``"op"`` key. Exactly one ``reset`` is sent at the start of every episode
(the process may also be restarted before it); a reset clears all candidate state.

Operations
----------
``{"op": "reset", "seed": int}``
    ``seed`` >= 0 initializes randomness only. Response must be exactly ``{"ok": true}``.

``{"op": "fit", "graphs": [G, ...]}``
    1..16 labelled training graphs per call; several calls per episode, accumulate them.
    ``G = {"id": int, "n": int, "edges": [[u, v], ...], "target": float, "se": float}``
    Vertices are ``0..n-1``; edges are undirected, listed once, in arbitrary order and
    with arbitrary orientation. ``target`` is the Monte Carlo estimate of the
    start-averaged cover time (positive); ``se`` is its Monte Carlo standard error.
    Family names, test targets and any other metadata are never sent.
    Response must be exactly ``{"ok": true}``.

``{"op": "predict", "graphs": [G, ...]}``
    1..16 unlabeled graphs per call, ``G = {"id": int, "n": int, "edges": [[u, v], ...]}``.
    Response must be exactly ``{"predictions": {"<id>": float, ...}}`` with one key per
    requested id (the decimal string of the id, no extras) and every value a finite
    positive number. A malformed response, a missing id or a non-positive/non-finite
    value fails the whole episode. Vertex numbering and edge order carry no information
    (the evaluator also sends randomly relabeled / edge-shuffled copies of the test
    graphs and requires predictions equal up to a relative 1e-6), so use only
    relabeling-invariant graph statistics.

``predict`` may be called after any number of ``fit`` calls (including zero). Calls
within an episode arrive in the order reset, fit*, predict*. Responses must not contain
additional keys. Any other op, or an invalid request, should raise an exception.

Method: features are log n, log m, log mean degree, log max degree, log diameter
(standardised); ridge regression (intercept unpenalised) on log(target). Fallback when
no training data was supplied: the generic bound 2 m (n - 1).
"""

import math
from collections import deque

_FEATURES = 5
_RIDGE = 1.0

_state = {"seed": None, "rows": [], "model": None}


def _stats(graph):
    n = int(graph["n"])
    adj = [set() for _ in range(n)]
    for u, v in graph["edges"]:
        u, v = int(u), int(v)
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    m = sum(len(a) for a in adj) // 2
    dmax = max(len(a) for a in adj)
    diam = 0
    for s in range(n):
        dist = {s: 0}
        queue = deque([s])
        while queue:
            x = queue.popleft()
            for y in adj[x]:
                if y not in dist:
                    dist[y] = dist[x] + 1
                    queue.append(y)
        diam = max(diam, max(dist.values()))
    return n, m, dmax, max(diam, 1)


def _features(graph):
    n, m, dmax, diam = _stats(graph)
    mean_deg = 2.0 * m / n
    return [math.log(n), math.log(m), math.log(mean_deg), math.log(dmax), math.log(diam)]


def _bound(graph):
    n, m, _, _ = _stats(graph)
    return 2.0 * m * (n - 1)


def _solve(a, b):
    k = len(b)
    mat = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(mat[r][c]))
        mat[c], mat[p] = mat[p], mat[c]
        piv = mat[c][c]
        for r in range(c + 1, k):
            f = mat[r][c] / piv
            for j in range(c, k + 1):
                mat[r][j] -= f * mat[c][j]
    x = [0.0] * k
    for r in range(k - 1, -1, -1):
        x[r] = (mat[r][k] - sum(mat[r][j] * x[j] for j in range(r + 1, k))) / mat[r][r]
    return x


def _fit_model(rows):
    count = len(rows)
    xs = [r[0] for r in rows]
    ys = [r[1] for r in rows]
    mean = [sum(x[j] for x in xs) / count for j in range(_FEATURES)]
    std = [math.sqrt(sum((x[j] - mean[j]) ** 2 for x in xs) / count) or 1.0 for j in range(_FEATURES)]
    z = [[(x[j] - mean[j]) / std[j] for j in range(_FEATURES)] for x in xs]
    ybar = sum(ys) / count
    a = [[sum(z[i][p] * z[i][q] for i in range(count)) + (_RIDGE if p == q else 0.0)
          for q in range(_FEATURES)] for p in range(_FEATURES)]
    b = [sum(z[i][p] * (ys[i] - ybar) for i in range(count)) for p in range(_FEATURES)]
    return {"mean": mean, "std": std, "w": _solve(a, b), "b": ybar}


def _predict_one(graph):
    model = _state["model"]
    if model is None:
        return _bound(graph)
    f = _features(graph)
    z = sum(model["w"][j] * (f[j] - model["mean"][j]) / model["std"][j] for j in range(_FEATURES))
    return max(math.exp(model["b"] + z), 1e-9)


def handle(request):
    op = request["op"]
    if op == "reset":
        _state["seed"] = int(request["seed"])
        _state["rows"] = []
        _state["model"] = None
        return {"ok": True}
    if op == "fit":
        for g in request["graphs"]:
            _state["rows"].append((_features(g), math.log(float(g["target"]))))
        _state["model"] = _fit_model(_state["rows"])
        return {"ok": True}
    if op == "predict":
        return {"predictions": {str(int(g["id"])): float(_predict_one(g)) for g in request["graphs"]}}
    raise ValueError("unknown op")
