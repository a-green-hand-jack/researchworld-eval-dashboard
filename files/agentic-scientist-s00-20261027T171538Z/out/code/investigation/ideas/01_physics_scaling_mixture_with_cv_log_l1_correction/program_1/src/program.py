"""Candidate physmix_cv_v1: physics scaling mixture + CV log-L1 correction for cover time.

Interface (``python_rpc_v1:handle``): ``handle(request) -> response`` over finite,
JSON-compatible values only (no NaN/Infinity, no files, no paths). The evaluator and
this candidate share no filesystem; all inputs arrive inline in the request.

Episode transcript (identical in smoke, search and final; exactly one episode per reset):

1. ``{"op": "reset", "seed": int}`` -> ``{"ok": True}`` (exactly this one key).
   Clears all state. ``seed`` is any non-negative integer and only seeds candidate-internal
   randomness; it never identifies the plane, data or workload.
   Timeout: 5 s (includes process start and imports).

2. ``{"op": "fit", "feature_names": [str]*6, "X": [[float]*6]*N_train, "y": [float]*N_train,
   "y_se": [float]*N_train, "n_walks": int}`` -> ``{"ok": True}`` with optional
   ``"method": str`` (<= 256 chars). No other keys are allowed.
   ``feature_names`` is ``["n", "m", "mean_degree", "max_degree", "min_degree", "diameter"]``
   (mean_degree = 2m/n, diameter by BFS). Each row of ``X`` describes one connected graph
   with 5 <= n <= 30 from the training pool. ``y`` is the evaluator's Monte Carlo estimate of
   the uniform-start expected cover time (steps until a simple random walk, started at a
   uniformly random vertex, has visited every vertex), ``y_se`` its standard error, and
   ``n_walks`` the number of walks per label. N_train is conveyed only by the row count
   (roughly 20-130). Timeout: 45 s.

3. ``{"op": "predict", "X": [[float]*6]*N}`` -> ``{"pred": [float]*N}`` (exactly this one key):
   one strictly positive finite predicted expected cover time per row, in request order.
   Each episode issues exactly three predict calls after fit, on held-out graphs (rows may
   be reordered or re-paired between calls); predictions should be a pure function of the
   six statistics of each row. Timeout: 10 s per call.

Any other response shape (wrong keys, wrong length, non-numeric or non-finite values, an
exception) fails the whole episode. Non-positive predictions are scored as worst case.
Scoring (evaluator-side): per-graph error min(|ln pred - ln C|, ln 1000), averaged per graph
family with equal family weights; lower error is better. Requests never contain graph
identifiers, family labels, adjacency, held-out labels or scores.
"""

# physmix_cv_v1: positive mixture of cover-time scaling terms (n*H_n, m*diam/min_deg, ...)
# fit with a pseudo-Huber loss on ln(pred) - ln(y), plus a ridge residual correction on
# log-features; deterministic K-fold CV (log-L1) chooses between the starter ridge, the
# mixture alone and mixture+residual. The starter ridge is always kept as a fallback.

import math

import numpy as np

_STATE = {}

_LOG_CAP = math.log(1000.0)
_LAMBDAS = (0.3, 1.0, 3.0, 10.0, 30.0)
_EULER = 0.5772156649015329
_H_TABLE = np.cumsum(1.0 / np.arange(1, 65))  # H_1 .. H_64


# ----------------------------------------------------------------------------- baseline
def _design(X):
    X = np.asarray(X, dtype=float).reshape(-1, 6)
    n, m, mean_deg, max_deg, min_deg, diam = (X[:, i] for i in range(6))
    cols = [np.ones(len(X)), np.log(n), np.log(m), np.log(mean_deg), np.log(max_deg),
            np.log(min_deg), np.log(diam), np.log(n) * np.log(diam)]
    return np.column_stack(cols)


def _fit_baseline(X, lny):
    A = _design(X)
    mu = A[:, 1:].mean(axis=0)
    sd = A[:, 1:].std(axis=0)
    sd[sd < 1e-12] = 1.0
    Z = np.column_stack([A[:, 0], (A[:, 1:] - mu) / sd])
    ridge = 1e-3 * np.eye(Z.shape[1])
    ridge[0, 0] = 0.0
    beta = np.linalg.solve(Z.T @ Z + ridge, Z.T @ lny)
    return {"mu": mu, "sd": sd, "beta": beta}


def _predict_baseline(model, X):
    A = _design(X)
    Z = np.column_stack([A[:, 0], (A[:, 1:] - model["mu"]) / model["sd"]])
    return Z @ model["beta"]


# ------------------------------------------------------------------------ physics basis
def _harmonic(n):
    n = np.asarray(n, dtype=float)
    nn = np.maximum(n, 1.0)
    k = np.clip(np.rint(nn), 1, 64).astype(int)
    approx = np.log(nn) + _EULER + 0.5 / nn - 1.0 / (12.0 * nn * nn)
    is_int = (nn <= 64) & (np.abs(nn - np.rint(nn)) < 1e-9)
    return np.where(is_int, _H_TABLE[k - 1], approx)


def _stats(X):
    X = np.asarray(X, dtype=float).reshape(-1, 6)
    n = np.maximum(X[:, 0], 1.0)
    m = np.maximum(X[:, 1], 1.0)
    mean_deg = np.maximum(X[:, 2], 1.0)
    max_deg = np.maximum(X[:, 3], 1.0)
    min_deg = np.maximum(X[:, 4], 1.0)
    diam = np.maximum(X[:, 5], 1.0)
    return n, m, mean_deg, max_deg, min_deg, diam


def _physics_basis(X):
    n, m, mean_deg, max_deg, min_deg, diam = _stats(X)
    h = _harmonic(n)
    cols = [
        n * _harmonic(n),      # coupon collector: complete graph, expanders
        m * diam / min_deg,    # commute-time / bottleneck: path, lollipop (~n^3)
        m * diam / mean_deg,   # cycle, grid
        n ** 2,                # path/cycle-like
        m * diam,              # Matthews-type m*R scale
        n * h * diam,          # star-like (diam 2 doubles the coupon collector)
        m * h / min_deg,       # leaf-heavy trees / star: 2m*H_n/min_deg ~ 2nH_n
    ]
    return np.column_stack(cols)


def _log_features(X):
    n, m, mean_deg, max_deg, min_deg, diam = _stats(X)
    return np.column_stack([np.log(n), np.log(m), np.log(mean_deg), np.log(max_deg),
                            np.log(min_deg), np.log(diam), np.log(max_deg / min_deg)])


# ---------------------------------------------------------------------- mixture fitting
def _pseudo_huber(r, delta=0.1):
    """Smooth |r| surrogate: returns (value, d value / d r)."""
    q = np.sqrt(1.0 + (r / delta) ** 2)
    return delta * delta * (q - 1.0), r / q


def _fit_positive_mixture(Phi, lny, delta=0.1, steps=1500, lr=0.05):
    """C_hat = sum_k exp(theta_k) * phi_k, minimising mean pseudo-Huber(ln C_hat - ln y)."""
    Phi = np.asarray(Phi, dtype=float)
    N, p = Phi.shape
    scale = np.median(Phi, axis=0)
    scale = np.where(np.isfinite(scale) & (scale > 0), scale, 1.0)
    P = Phi / scale
    shift = float(np.mean(lny))
    t = lny - shift
    lnP = np.log(P)
    single = np.median(t[:, None] - lnP, axis=0)
    inits = []
    for k in range(p):
        th = np.full(p, single[k] - 7.0)
        th[k] = single[k]
        inits.append(th)
    inits.append(np.full(p, float(np.median(t - np.log(P.sum(axis=1))))))
    Theta = np.clip(np.array(inits), -30.0, 10.0)
    K = Theta.shape[0]
    m1 = np.zeros_like(Theta)
    v1 = np.zeros_like(Theta)
    b1, b2, eps = 0.9, 0.999, 1e-8
    best_loss = np.full(K, np.inf)
    best_theta = Theta.copy()
    for step in range(steps + 1):
        W = np.exp(Theta)
        pred = P @ W.T                       # (N, K)
        R = np.log(pred) - t[:, None]
        val, d = _pseudo_huber(R, delta)
        loss = val.mean(axis=0)
        improved = loss < best_loss
        best_loss[improved] = loss[improved]
        best_theta[improved] = Theta[improved]
        if step == steps:
            break
        S = d / pred / N
        G = (P.T @ S).T * W                  # (K, p)
        m1 = b1 * m1 + (1.0 - b1) * G
        v1 = b2 * v1 + (1.0 - b2) * G * G
        mh = m1 / (1.0 - b1 ** (step + 1))
        vh = v1 / (1.0 - b2 ** (step + 1))
        lr_t = lr * (0.1 + 0.45 * (1.0 + math.cos(math.pi * step / steps)))
        Theta = np.clip(Theta - lr_t * mh / (np.sqrt(vh) + eps), -30.0, 10.0)
    k = int(np.argmin(best_loss))
    return {"scale": scale, "shift": shift, "theta": best_theta[k].copy()}


def _predict_mixture(model, Phi):
    P = np.asarray(Phi, dtype=float) / model["scale"]
    return np.log(P @ np.exp(model["theta"])) + model["shift"]


def _fit_log_residual(F, r, lam, irls=4, eps=0.05):
    """Ridge (IRLS-robustified towards L1) of log residual on standardized log-features."""
    mu = F.mean(axis=0)
    sd = F.std(axis=0)
    sd[sd < 1e-12] = 1.0
    Z = np.column_stack([np.ones(len(F)), (F - mu) / sd])
    pen = lam * np.eye(Z.shape[1])
    pen[0, 0] = 0.0
    w = np.ones(len(F))
    beta = np.zeros(Z.shape[1])
    for _ in range(irls + 1):
        Zw = Z * w[:, None]
        beta = np.linalg.solve(Z.T @ Zw + pen, Zw.T @ r)
        e = r - Z @ beta
        w = 1.0 / np.maximum(np.abs(e), eps)
        w = w / w.mean()
    return {"mu": mu, "sd": sd, "beta": beta}


def _predict_log_residual(model, F):
    Z = np.column_stack([np.ones(len(F)), (F - model["mu"]) / model["sd"]])
    return Z @ model["beta"]


# ------------------------------------------------------------------------ CV selection
def _log_l1(log_pred, lny):
    e = np.abs(log_pred - lny)
    e = np.where(np.isfinite(e), np.minimum(e, _LOG_CAP), _LOG_CAP)
    return float(e.mean())


def _candidate_names():
    return ["baseline", "mix"] + ["res%g" % lam for lam in _LAMBDAS]


def _cv_log_l1(X, lny, seed, n_folds=5):
    """Deterministic K-fold CV; returns (mean |ln pred - ln y| per candidate, OOF preds)."""
    N = len(lny)
    k = int(min(n_folds, N))
    if k < 2:
        return None, None
    # Fold assignment is invariant to the order of training rows.
    order = np.lexsort(np.column_stack([X, lny]).T)
    folds = np.empty(N, dtype=int)
    folds[order] = np.random.default_rng(seed).permutation(N) % k
    Phi = _physics_basis(X)
    F = _log_features(X)
    names = _candidate_names()
    oof = {name: np.zeros(N) for name in names}
    for f in range(k):
        te = folds == f
        tr = ~te
        b = _fit_baseline(X[tr], lny[tr])
        oof["baseline"][te] = _predict_baseline(b, X[te])
        mix = _fit_positive_mixture(Phi[tr], lny[tr])
        mtr = _predict_mixture(mix, Phi[tr])
        mte = _predict_mixture(mix, Phi[te])
        oof["mix"][te] = mte
        for lam in _LAMBDAS:
            res = _fit_log_residual(F[tr], lny[tr] - mtr, lam)
            oof["res%g" % lam][te] = mte + _predict_log_residual(res, F[te])
    errs = {name: _log_l1(oof[name], lny) for name in names}
    return errs, oof


def _select_and_refit(X, lny, seed, base):
    errs, oof = _cv_log_l1(X, lny, seed)
    if errs is None:
        return None
    names = _candidate_names()
    ranked = sorted(names, key=lambda s: (errs[s], names.index(s)))
    members = [ranked[0]]
    avg_err = _log_l1(0.5 * (oof[ranked[0]] + oof[ranked[1]]), lny)
    if avg_err < errs[ranked[0]]:
        members.append(ranked[1])
    choice = {"members": members, "base": base}
    if any(name != "baseline" for name in members):
        Phi = _physics_basis(X)
        mix = _fit_positive_mixture(Phi, lny)
        choice["mix"] = mix
        mfit = _predict_mixture(mix, Phi)
        F = _log_features(X)
        for lam in _LAMBDAS:
            name = "res%g" % lam
            if name in members:
                choice[name] = _fit_log_residual(F, lny - mfit, lam)
    return choice


def _predict_choice(choice, X):
    parts = []
    mlog = None
    for name in choice["members"]:
        if name == "baseline":
            parts.append(_predict_baseline(choice["base"], X))
            continue
        if mlog is None:
            mlog = _predict_mixture(choice["mix"], _physics_basis(X))
        if name == "mix":
            parts.append(mlog)
        else:
            parts.append(mlog + _predict_log_residual(choice[name], _log_features(X)))
    return np.mean(parts, axis=0)


# --------------------------------------------------------------------------- interface
def _reset(request):
    seed = request.get("seed")
    if type(seed) is not int or seed < 0:
        raise ValueError("invalid seed")
    _STATE.clear()
    _STATE["seed"] = seed
    return {"ok": True}


def _fit(request):
    with np.errstate(all="ignore"):
        X = np.asarray(request["X"], dtype=float).reshape(-1, 6)
        lny = np.log(np.asarray(request["y"], dtype=float))
        finite = lny[np.isfinite(lny)]
        fallback = float(finite.mean()) if finite.size else 5.0
        base = _fit_baseline(X, lny)
        _STATE.update(base=base, fallback=fallback, choice=None)
        try:
            _STATE["choice"] = _select_and_refit(X, lny, int(_STATE.get("seed", 0)), base)
        except Exception:
            _STATE["choice"] = None
    return {"ok": True, "method": "physmix_cv_v1"}


def _predict(request):
    if "base" not in _STATE:
        raise RuntimeError("predict before fit")
    with np.errstate(all="ignore"):
        X = np.asarray(request["X"], dtype=float).reshape(-1, 6)
        base_lp = _predict_baseline(_STATE["base"], X)
        base_lp = np.where(np.isfinite(base_lp), base_lp, _STATE["fallback"])
        log_pred = base_lp
        if _STATE.get("choice") is not None:
            try:
                lp = np.asarray(_predict_choice(_STATE["choice"], X), dtype=float)
                if lp.shape == base_lp.shape:
                    log_pred = np.where(np.isfinite(lp), lp, base_lp)
            except Exception:
                log_pred = base_lp
        log_pred = np.clip(log_pred, -50.0, 50.0)
        log_pred = np.where(np.isfinite(log_pred), log_pred, _STATE["fallback"])
    return {"pred": [float(math.exp(v)) for v in log_pred]}


def handle(request):
    op = request.get("op") if isinstance(request, dict) else None
    if op == "reset":
        return _reset(request)
    if op == "fit":
        return _fit(request)
    if op == "predict":
        return _predict(request)
    raise ValueError("unknown op")
