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

Method: Matthews-type offset log(h_max * H_{n-1}) with exact hitting times obtained from
effective resistances (Laplacian pseudo-inverse, Tetali's formula). Ridge regression
(penalty chosen by closed-form leave-one-out) of the residual log(target) - offset on five
standardised shape features (hitting-time ratios, degree heterogeneity, diameter/n, log n).
Fallback when no training data was supplied: min(2 m (n - 1), Matthews scale).
"""

import math
from collections import deque

try:  # optional fast path for the Laplacian pseudo-inverse
    import numpy as np
except Exception:  # pragma: no cover
    np = None

_RIDGES = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0)

_state = {"seed": None, "rows": [], "model": None}


def _adjacency(graph):
    n = int(graph["n"])
    adj = [set() for _ in range(n)]
    for u, v in graph["edges"]:
        u, v = int(u), int(v)
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    return n, adj


def _diameter(n, adj):
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
    return max(diam, 1)


def _inverse(a):
    """Gauss-Jordan inverse with partial pivoting (pure-python fallback)."""
    k = len(a)
    mat = [list(map(float, a[i])) + [1.0 if i == j else 0.0 for j in range(k)] for i in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(mat[r][c]))
        mat[c], mat[p] = mat[p], mat[c]
        piv = mat[c][c]
        mat[c] = [x / piv for x in mat[c]]
        for r in range(k):
            if r != c and mat[r][c] != 0.0:
                f = mat[r][c]
                mat[r] = [x - f * y for x, y in zip(mat[r], mat[c])]
    return [row[k:] for row in mat]


def _effective_resistances(n, adj):
    """Full effective-resistance matrix from the Laplacian pseudo-inverse."""
    if np is not None:
        lap = np.zeros((n, n))
        for i in range(n):
            lap[i, i] = len(adj[i])
            for j in adj[i]:
                lap[i, j] = -1.0
        lp = np.linalg.pinv(lap)
        d = np.diag(lp)
        return (d[:, None] + d[None, :] - 2.0 * lp).tolist()
    # (L + J/n)^{-1} = L^+ + J/n for a connected graph
    a = [[(len(adj[i]) if i == j else (-1.0 if j in adj[i] else 0.0)) + 1.0 / n for j in range(n)]
         for i in range(n)]
    inv = _inverse(a)
    return [[inv[u][u] + inv[v][v] - 2.0 * inv[u][v] for v in range(n)] for u in range(n)]


def _harmonic(k):
    return sum(1.0 / i for i in range(1, k + 1))


def _stats(graph):
    """Relabeling-invariant statistics, incl. exact hitting times via resistances."""
    n, adj = _adjacency(graph)
    deg = [len(a) for a in adj]
    m = sum(deg) // 2
    dmax = max(deg)
    diam = _diameter(n, adj)
    res = _effective_resistances(n, adj)
    # Tetali: h(u,v) = 1/2 sum_w d_w (R_uv + R_vw - R_uw)
    hit = [[0.0] * n for _ in range(n)]
    for u in range(n):
        ru = res[u]
        for v in range(n):
            if u == v:
                continue
            rv = res[v]
            s = sum(deg[w] * (rv[w] - ru[w]) for w in range(n))
            hit[u][v] = max(0.5 * (2.0 * m * ru[v] + s), 1e-12)
    h_max = max(max(row) for row in hit)
    ecc_mean = sum(max(row) for row in hit) / n  # start-averaged max_v h(u, v)
    pairs = n * (n - 1)
    h_mean = sum(sum(row) for row in hit) / pairs
    r_max = max(max(row) for row in res)
    return {"n": n, "m": m, "dmax": dmax, "diam": diam, "h_max": h_max, "ecc_mean": ecc_mean,
            "h_mean": h_mean, "r_max": r_max}


def _offset(st):
    """Matthews-type scale: h_max * H_{n-1} (<= m R_max H_{n-1} * 2)."""
    return math.log(st["h_max"] * _harmonic(st["n"] - 1))


def _features(st):
    n, m = st["n"], st["m"]
    mean_deg = 2.0 * m / n
    return [
        math.log(st["h_mean"] / st["h_max"]),
        math.log(st["ecc_mean"] / st["h_max"]),
        math.log(st["dmax"] / mean_deg),
        math.log(st["diam"] / n),
        math.log(n),
    ]


def _bound(st):
    n, m = st["n"], st["m"]
    return 2.0 * m * (n - 1)


def _ridge_fit(z, y, lam):
    """Centered ridge; returns weights and LOO mean-absolute error (closed form)."""
    count, k = len(z), len(z[0])
    ybar = sum(y) / count
    a = [[sum(z[i][p] * z[i][q] for i in range(count)) + (lam if p == q else 0.0)
          for q in range(k)] for p in range(k)]
    b = [sum(z[i][p] * (y[i] - ybar) for i in range(count)) for p in range(k)]
    ainv = _inverse(a)
    w = [sum(ainv[p][q] * b[q] for q in range(k)) for p in range(k)]
    loo = 0.0
    for i in range(count):
        pred = ybar + sum(w[p] * z[i][p] for p in range(k))
        lev = 1.0 / count + sum(z[i][p] * sum(ainv[p][q] * z[i][q] for q in range(k)) for p in range(k))
        loo += abs((y[i] - pred) / max(1.0 - lev, 1e-6))
    return w, ybar, loo / count


def _fit_model(rows):
    """Residual regression: log CT - log(h_max H_{n-1}) on standardized shape features."""
    count = len(rows)
    xs = [r[0] for r in rows]
    ys = [r[1] for r in rows]  # log target minus Matthews offset
    ybar = sum(ys) / count
    if count < 8:
        return {"mean": None, "std": None, "w": None, "b": ybar}
    k = len(xs[0])
    mean = [sum(x[j] for x in xs) / count for j in range(k)]
    std = [math.sqrt(sum((x[j] - mean[j]) ** 2 for x in xs) / count) or 1.0 for j in range(k)]
    z = [[(x[j] - mean[j]) / std[j] for j in range(k)] for x in xs]
    best = None
    for lam in _RIDGES:
        w, b, loo = _ridge_fit(z, ys, lam)
        if best is None or loo < best[0]:
            best = (loo, w, b)
    return {"mean": mean, "std": std, "w": best[1], "b": best[2]}


def _predict_one(graph):
    st = _stats(graph)
    model = _state["model"]
    if model is None:
        return max(min(_bound(st), math.exp(_offset(st))), 1e-9)
    z = model["b"]
    if model["w"] is not None:
        f = _features(st)
        z += sum(model["w"][j] * (f[j] - model["mean"][j]) / model["std"][j] for j in range(len(f)))
    return max(math.exp(_offset(st) + z), 1e-9)


def handle(request):
    op = request["op"]
    if op == "reset":
        _state["seed"] = int(request["seed"])
        _state["rows"] = []
        _state["model"] = None
        return {"ok": True}
    if op == "fit":
        for g in request["graphs"]:
            st = _stats(g)
            _state["rows"].append((_features(st), math.log(float(g["target"])) - _offset(st)))
        _state["model"] = _fit_model(_state["rows"])
        return {"ok": True}
    if op == "predict":
        return {"predictions": {str(int(g["id"])): float(_predict_one(g)) for g in request["graphs"]}}
    raise ValueError("unknown op")
