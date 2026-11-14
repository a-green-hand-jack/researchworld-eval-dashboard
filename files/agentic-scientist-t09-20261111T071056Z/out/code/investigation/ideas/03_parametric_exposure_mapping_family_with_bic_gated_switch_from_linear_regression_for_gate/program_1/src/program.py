"""Regression-based GATE estimator under network interference (starter candidate).

Interface: ``python_rpc_v1:handle``.  ``handle(request) -> response`` takes and returns
finite JSON-compatible values only.  The candidate owns all of its state in memory; it
shares no filesystem with the evaluator and must not read or write evaluator paths.

Operations
----------
``{"op": "reset", "seed": <int >= 0>}``
    Clears ALL candidate state and seeds the candidate RNG.  The seed only initializes
    randomness; it never identifies a plane, case or workload.  Any non-negative integer
    is valid.  Response: exactly ``{"ok": true}`` (no other keys).

``{"op": "estimate", ...}``
    One full dataset from one randomized experiment on a network.  The evaluator sends
    exactly one ``reset`` per episode and then four ``estimate`` requests in an
    evaluator-private order.  All four have the identical format and size and the same
    budget; the candidate must treat every request as an ordinary dataset and must not
    try to detect which one is which.  Each ``estimate`` is independent: return the best
    estimate for the request in hand.

    Request fields (all present, no others):
      op         "estimate"
      n          int, number of nodes (nodes are 0..n-1)
      edges      array object, undirected unique edges (u < v), dtype int32, shape [E, 2]
      covariates array object, node covariates, dtype float64, shape [n, 2]
      treatment  array object, realized treatment assignment, dtype uint8 (0/1), shape [n]
      outcomes   array object, observed outcomes, dtype float64, shape [n]
      design     {"kind": "bernoulli" | "cluster",
                  "probability": float,   # marginal treatment probability of the design
                  "cluster_labels": array object (int32, shape [n]) or null}
                 "bernoulli": each node treated independently with ``probability``.
                 "cluster":   whole clusters (``cluster_labels``) are treated together;
                              exactly round(K*probability) of the K clusters are treated,
                              chosen uniformly at random.
      workload   {"max_op_seconds": float,  # soft per-request time budget (hard cap is a
                                            # little larger; exceeding it fails the episode)
                  "ci_level": float}        # nominal level of the requested interval

    Array objects are ``{"dtype": "<name>", "shape": [...], "encoding": "base64-le",
    "data": "<base64 of the C-order little-endian buffer>"}``; see ``decode_array``.

    Target: the global average treatment effect (GATE), i.e. the mean over nodes of
    Y_i(all nodes treated) - Y_i(all nodes control) for the (hidden) potential outcomes.
    The interference mechanism, its parameters and the true GATE are never revealed.

    Response (JSON object): required keys ``estimate``, ``ci_low``, ``ci_high``
    (finite numbers with ci_low <= estimate <= ci_high); optional key ``diagnostics``
    (a JSON object, at most 4096 bytes serialized; ignored for scoring).  Any other key,
    a non-finite number, a malformed type or an interval that does not contain the
    estimate makes that request invalid (the episode keeps its worst-case contribution).

Limits (enforced by the evaluator; a violation is a failed request, never retried):
  * ``reset`` must answer within 4 s (it includes process/import start-up);
  * each ``estimate`` must answer within 3 s wall clock (``workload.max_op_seconds`` = 2.5 s
    is the soft budget to aim for); at most 4 threads of CPU are available;
  * a complete request is below 0.5 MiB and a complete response must stay far below the
    64 MiB wire limit (a valid response is < 5 KiB);
  * no filesystem or network is shared with the evaluator; do not read or write evaluator paths.
Determinism: all candidate randomness must derive from the ``reset`` seed, because the evaluator
replays one episode after a fresh ``reset`` and requires the primary estimate to agree to 1e-6
(relative to max(1, |estimate|)).

Scoring (evaluator-owned): per episode relative error min(|estimate - GATE| / |GATE|, 2),
a failed/invalid request counts as 2 (and as "not covered" with worst-case width);
RMSE over seeds per case, mean over the 8 cases, ``combined_score`` = -that mean.
The evaluator additionally runs matched negative controls (permuted outcomes, node-relabelled
graph, constant outcome) through the same operation; a constant-outcome request must
return an estimate within 1e-4 of 0, and the run must be deterministic given the reset seed.
"""

import base64

import numpy as np
import scipy.sparse as sp

_STATE = {"rng": None, "seed": None}

_DTYPES = {"int32": "<i4", "float64": "<f8", "uint8": "u1"}


def decode_array(obj):
    """Decode an array object (see module docstring) into a numpy array."""
    if obj is None:
        return None
    if obj["encoding"] != "base64-le" or obj["dtype"] not in _DTYPES:
        raise ValueError("unsupported array encoding")
    buf = base64.b64decode(obj["data"])
    return np.frombuffer(buf, dtype=np.dtype(_DTYPES[obj["dtype"]])).reshape(obj["shape"]).copy()


def _adjacency(n, edges):
    if len(edges) == 0:
        return sp.csr_matrix((n, n))
    u, v = edges[:, 0], edges[:, 1]
    rows = np.concatenate([u, v])
    cols = np.concatenate([v, u])
    return sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))


def _features(adj, deg, z, x, treated_all):
    """Design matrix [1, own treatment, neighbour-treated fraction, covariates]."""
    if treated_all is None:
        frac = (adj @ z) / np.maximum(deg, 1.0)
        own = z
    else:
        frac = np.where(deg > 0, float(treated_all), 0.0)
        own = np.full(len(z), float(treated_all))
    return np.column_stack([np.ones(len(z)), own, frac, x])


def _parse(request):
    n = int(request["n"])
    edges = decode_array(request["edges"])
    x = decode_array(request["covariates"])
    z = decode_array(request["treatment"]).astype(np.float64)
    y = decode_array(request["outcomes"])
    adj = _adjacency(n, edges)
    deg = np.asarray(adj.sum(axis=1)).ravel()
    return n, x, z, y, adj, deg


ZCRIT = 1.959963984540054  # normal quantile for ci_level = 0.95 (the only level requested)


def _exposure_states(adj, deg, z):
    """Exposure summaries for the observed, all-treated and all-control worlds.

    Two-hop quantities use repeated sparse matrix-vector products only (never adj @ adj).
    """
    n = len(z)
    ones = np.ones(n)
    walks2 = adj @ (adj @ ones)  # number of length-2 walks starting at each node
    s1 = adj @ z
    obs = {
        "own": z,
        "s1": s1,
        "f1": s1 / np.maximum(deg, 1.0),
        "f2": (adj @ (adj @ z)) / np.maximum(walks2, 1.0),
    }
    all1 = {
        "own": ones,
        "s1": deg.astype(np.float64),
        "f1": (deg > 0).astype(np.float64),
        "f2": (walks2 > 0).astype(np.float64),
    }
    all0 = {"own": np.zeros(n), "s1": np.zeros(n), "f1": np.zeros(n), "f2": np.zeros(n)}
    return obs, all1, all0


def candidate_designs(deg, x):
    """Library of few-parameter exposure mappings.

    Returns {name: (builder, count_cols)}; builder(state) -> design matrix with columns
    [1, own, exposure features..., (x or interactions)].  ``count_cols`` marks columns that
    are unbounded treated-neighbour counts (all-treated values get winsorised).
    """
    n = len(deg)
    pos = deg[deg > 0]
    median_deg = max(float(np.median(pos)), 1.0) if len(pos) else 1.0
    mean_deg = max(float(np.mean(deg)), 1.0)
    ld = np.log1p(deg)
    ldc = ld - ld.mean()
    xc = x - x.mean(axis=0, keepdims=True)
    one = np.ones(n)

    def lin(s):
        return np.column_stack([one, s["own"], s["f1"], x])

    specs = {"M0_linear": (lin, ())}

    specs["M1_count"] = (
        lambda s: np.column_stack([one, s["own"], s["s1"] / mean_deg, x]),
        (2,),
    )
    specs["M2_twohop"] = (
        lambda s: np.column_stack([one, s["own"], s["f1"], s["f2"], x]),
        (),
    )
    specs["M3_interact"] = (
        lambda s: np.column_stack(
            [one, s["own"], s["f1"], x, ldc, s["own"] * ldc, s["own"] * xc,
             s["f1"] * ldc]
        ),
        (),
    )
    specs["M3b_own_deg_frac_deg"] = (
        lambda s: np.column_stack(
            [one, s["own"], s["f1"], x, ldc, s["own"] * ldc, s["f1"] * ldc]
        ),
        (),
    )
    specs["M3c_frac_x"] = (
        lambda s: np.column_stack([one, s["own"], s["f1"], x, s["f1"] * xc]),
        (),
    )
    for k in (1.0, 3.0, 8.0):
        specs["M4_sat_k%g" % k] = (
            (lambda s, k=k: np.column_stack([one, s["own"], 1.0 - np.exp(-k * s["f1"]), x])),
            (),
        )
    for t in (0.25, 0.5, 0.75):
        specs["M5_sig_t%g" % t] = (
            (lambda s, t=t: np.column_stack(
                [one, s["own"], 1.0 / (1.0 + np.exp(-(s["f1"] - t) / 0.1)), x])),
            (),
        )
    for k in (0.5, 1.0, 2.0):
        specs["M6_satcount_k%g" % k] = (
            (lambda s, k=k: np.column_stack(
                [one, s["own"], 1.0 - np.exp(-s["s1"] / (k * median_deg)), x])),
            (),
        )
    return specs


def sandwich_se(x_obs, resid, contrast, n):
    """HC1 sandwich delta-method standard error of contrast @ beta."""
    bread = np.linalg.pinv(x_obs.T @ x_obs)
    meat = (x_obs * resid[:, None] ** 2).T @ x_obs
    cov = bread @ meat @ bread * n / max(n - x_obs.shape[1], 1)
    return float(np.sqrt(max(contrast @ cov @ contrast, 0.0)))


def _fit_candidate(builder, count_cols, states, y):
    obs, all1, all0 = states
    n = len(y)
    x_obs = builder(obs)
    x1 = builder(all1)
    x0 = builder(all0)
    for c in count_cols:  # winsorise count-type all-treated features
        cap = 3.0 * float(np.percentile(x_obs[:, c], 99.5))
        if cap > 0:
            x1[:, c] = np.minimum(x1[:, c], cap)
    if not (np.all(np.isfinite(x_obs)) and np.all(np.isfinite(x1)) and np.all(np.isfinite(x0))):
        return None
    beta, _, rank, _ = np.linalg.lstsq(x_obs, y, rcond=None)
    resid = y - x_obs @ beta
    rss = float(resid @ resid)
    contrast = (x1 - x0).mean(axis=0)
    est = float(contrast @ beta)
    se = sandwich_se(x_obs, resid, contrast, n)
    if not (np.isfinite(est) and np.isfinite(se)):
        return None
    return {"est": est, "se": se, "rss": rss, "p": int(rank)}


def bic_gate(fits, n, y_var, bic_margin=10.0):
    """Keep the linear fit unless a candidate beats it by BIC > bic_margin.

    Passing candidates are averaged with BIC weights.  Returns (est, se, est0, se0).
    """
    base = fits["M0_linear"]
    est0, se0 = base["est"], base["se"]
    floor = 1e-12 * y_var

    def bic(f):
        return n * np.log(np.maximum(f["rss"] / n, floor)) + f["p"] * np.log(n)

    bic0 = bic(base)
    passing = []
    for name, f in fits.items():
        if name == "M0_linear" or f is None:
            continue
        b = bic(f)
        if bic0 - b > bic_margin:
            passing.append((b, f))
    if not passing:
        return est0, se0, est0, se0
    bmin = min(b for b, _ in passing)
    w = np.array([np.exp(-0.5 * (b - bmin)) for b, _ in passing])
    w = w / w.sum()
    ests = np.array([f["est"] for _, f in passing])
    ses = np.array([f["se"] for _, f in passing])
    est = float(w @ ests)
    spread = float(np.sqrt(w @ (ests - est) ** 2))
    se = float(w @ ses) + spread
    # sanity guard: do not stray far from the linear estimate
    if abs(est - est0) > 3.0 * max(abs(est0), se0) or not (np.isfinite(est) and np.isfinite(se)):
        return est0, se0, est0, se0
    return est, se, est0, se0


def _estimate(request):
    try:
        n, x, z, y, adj, deg = _parse(request)
        y_var = float(np.var(y))
        if y_var == 0.0:
            return {"estimate": 0.0, "ci_low": 0.0, "ci_high": 0.0}
        states = _exposure_states(adj, deg, z)
        fits = {}
        for name, (builder, count_cols) in candidate_designs(deg, x).items():
            try:
                fits[name] = _fit_candidate(builder, count_cols, states, y)
            except Exception:
                fits[name] = None
        if fits.get("M0_linear") is None:
            raise ValueError("linear fit failed")
        est, se, est0, se0 = bic_gate(fits, n, y_var, bic_margin=10.0)
        half = ZCRIT * se + abs(est - est0)
        if not (np.isfinite(est) and np.isfinite(half)):
            raise ValueError("non-finite")
        return {"estimate": est, "ci_low": est - half, "ci_high": est + half}
    except Exception:
        return _estimate_linear(request)


def _estimate_linear(request):
    n, x, z, y, adj, deg = _parse(request)

    x_obs = _features(adj, deg, z, x, None)
    beta, *_ = np.linalg.lstsq(x_obs, y, rcond=None)
    resid = y - x_obs @ beta
    # GATE = mean over nodes of prediction(all treated) - prediction(all control).
    contrast = (_features(adj, deg, z, x, 1) - _features(adj, deg, z, x, 0)).mean(axis=0)
    est = float(contrast @ beta)

    # Heteroskedasticity-robust (HC1) sandwich interval for the linear functional.
    bread = np.linalg.pinv(x_obs.T @ x_obs)
    meat = (x_obs * resid[:, None] ** 2).T @ x_obs
    cov = bread @ meat @ bread * n / max(n - x_obs.shape[1], 1)
    se = float(np.sqrt(max(contrast @ cov @ contrast, 0.0)))
    zcrit = 1.959963984540054  # normal quantile for ci_level = 0.95 (the only level requested)
    return {"estimate": est, "ci_low": est - zcrit * se, "ci_high": est + zcrit * se}


def handle(request):
    op = request.get("op")
    if op == "reset":
        seed = int(request["seed"])
        _STATE["seed"] = seed
        _STATE["rng"] = np.random.default_rng(seed)
        return {"ok": True}
    if op == "estimate":
        return _estimate(request)
    raise ValueError("unknown op")
