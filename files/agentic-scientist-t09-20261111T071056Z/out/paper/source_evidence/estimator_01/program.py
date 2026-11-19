"""Extrapolation-aware regression GATE estimator under network interference.

Interface: ``python_rpc_v1:handle``.  ``handle(request) -> response`` takes and returns
finite JSON-compatible values only.  All state lives in memory; nothing is read from or
written to the filesystem.

Operations
----------
``{"op": "reset", "seed": <int >= 0>}``  -> ``{"ok": True}`` (clears state, seeds RNG).
``{"op": "estimate", n, edges, covariates, treatment, outcomes, design, workload}``
    -> ``{"estimate", "ci_low", "ci_high"}`` (finite, ci_low <= estimate <= ci_high).
    ``design`` is ``{"kind": "bernoulli" | "cluster", "probability", "cluster_labels"}``.

Method
------
The GATE is estimated by fitting ridge regressions of the outcome on own treatment plus
neighbour-exposure features and predicting at the all-treated and all-control assignments
(the counterfactual points sit at the corners of the exposure space, neighbour fraction 1
and 0).  Because the corners are rarely covered by the training exposures, the fitted
models are chosen with an extrapolation-aware validation: besides K-fold CV we hold out the
units with the highest / lowest neighbour fraction and the highest degrees and score each
candidate on how well it extrapolates to them.  All candidates that are within one standard
error of the best on both criteria are averaged (the linear-in-neighbour-fraction model is
always a candidate).  The interval comes from a design-resampling wild (block) bootstrap
(re-draw the assignment from the design, perturb residuals by block), widened by the spread
of the candidate estimates.  Difference-in-means and a Hajek full-neighbourhood exposure
estimator are implemented as fallbacks / internal sanity diagnostics.
"""

import base64
import time
import zlib

import numpy as np
import scipy.sparse as sp
from scipy.special import ndtri

_STATE = {"rng": None, "seed": None, "last_diag": None}

_DTYPES = {"int32": "<i4", "float64": "<f8", "uint8": "u1"}

_RIDGE = 1e-3  # ridge strength relative to n on standardised columns
_TWO_HOP_MAX_WORK = 3.0e6  # max sum(deg^2) for exact two-hop matrix
_SOFT_DEADLINE = 1.5  # seconds after request start at which we stop bootstrapping
_N_REPS = 150  # max bootstrap replications (n_reps)


def decode_array(obj):
    """Decode an array object (see module docstring) into a numpy array."""
    if obj is None:
        return None
    if obj["encoding"] != "base64-le" or obj["dtype"] not in _DTYPES:
        raise ValueError("unsupported array encoding")
    buf = base64.b64decode(obj["data"])
    return np.frombuffer(buf, dtype=np.dtype(_DTYPES[obj["dtype"]])).reshape(obj["shape"]).copy()


# --------------------------------------------------------------------------- graph helpers
def _adjacency(n, edges):
    if len(edges) == 0:
        return sp.csr_matrix((n, n))
    u, v = edges[:, 0], edges[:, 1]
    rows = np.concatenate([u, v])
    cols = np.concatenate([v, u])
    return sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))


def neighbor_fraction(adj, deg, z):
    """Fraction of a node's neighbours that are treated (0 for isolated nodes)."""
    return (adj @ z) / np.maximum(deg, 1.0)


def two_hop_fraction(ctx, z):
    """Fraction of distance-two nodes that are treated (random-walk proxy if graph is big)."""
    if ctx["two_hop"] is not None:
        return (ctx["two_hop"] @ z) / np.maximum(ctx["deg2"], 1.0)
    p = ctx["walk"]
    return p @ (p @ z)


def corner_coverage(nf, deg, tol=0.1):
    """Share of non-isolated units whose neighbour fraction lies within tol of 0 or 1."""
    m = deg > 0
    if not m.any():
        return 1.0
    f = nf[m]
    return float(np.mean((f <= tol) | (f >= 1.0 - tol)))


def _context(n, edges, x):
    adj = _adjacency(n, edges)
    deg = np.asarray(adj.sum(axis=1)).ravel()
    xc = np.asarray(x, dtype=np.float64).reshape(n, -1)
    xc = xc - xc.mean(axis=0)
    ld = np.log1p(deg)
    walk = sp.diags(1.0 / np.maximum(deg, 1.0)) @ adj
    ctx = {"n": n, "adj": adj.tocsr(), "deg": deg, "xc": xc, "ldc": ld - ld.mean(),
           "walk": walk.tocsr(), "two_hop": None, "deg2": None}
    if float((deg ** 2).sum()) <= _TWO_HOP_MAX_WORK and len(edges) > 0:
        a2 = (adj @ adj).tocsr()
        a2.data[:] = 1.0
        m = a2 - adj.multiply(a2)
        m = m - sp.diags(m.diagonal())
        m = m.tocsr()
        m.eliminate_zeros()
        m.data[:] = 1.0
        ctx["two_hop"] = m
        ctx["deg2"] = np.asarray(m.sum(axis=1)).ravel()
    return ctx


# --------------------------------------------------------------------------- designs
def bernoulli_assign(rng, n, p):
    return (rng.random(n) < p).astype(np.float64)


def cluster_randomize(rng, labels, p):
    """Treat exactly round(K p) of the K clusters, chosen uniformly."""
    k = int(labels.max()) + 1
    n_t = int(round(k * p))
    chosen = rng.permutation(k)[:n_t]
    flag = np.zeros(k)
    flag[chosen] = 1.0
    return flag[labels]


# --------------------------------------------------------------------------- baselines
def difference_in_means(z, y):
    t, c = z > 0.5, z <= 0.5
    if not t.any() or not c.any():
        return 0.0
    return float(y[t].mean() - y[c].mean())


def hajek_exposure_estimate(adj, deg, z, y, p):
    """Hajek estimator of full-neighbourhood exposure (all nbrs + self treated vs control).

    Weights use the Bernoulli(p) exposure probabilities (an approximation for cluster
    designs).  Returns nan when either exposure class is empty.
    """
    p = float(np.clip(p, 1e-6, 1 - 1e-6))
    nbr = adj @ z
    full1 = (z > 0.5) & (nbr >= deg)
    full0 = (z <= 0.5) & (nbr <= 0)
    if not full1.any() or not full0.any():
        return float("nan")

    def mean_w(mask, logp):
        lw = -(1.0 + deg[mask]) * logp
        w = np.exp(lw - lw.max())
        return float((w * y[mask]).sum() / w.sum())

    return mean_w(full1, np.log(p)) - mean_w(full0, np.log(1.0 - p))


# --------------------------------------------------------------------------- feature sets
def _columns(ctx, z):
    """All candidate regression columns evaluated at assignment ``z``."""
    nf = neighbor_fraction(ctx["adj"], ctx["deg"], z)
    h = two_hop_fraction(ctx, z)
    cnt = ctx["adj"] @ z
    ld = ctx["ldc"]
    cols = {"z": z, "nf": nf, "h": h, "cnt": cnt, "ldc": ld, "zld": z * ld, "nfld": nf * ld,
            "znf": z * nf, "nf2": nf ** 2, "hg25": np.maximum(nf - 0.25, 0.0),
            "hg50": np.maximum(nf - 0.5, 0.0), "hg75": np.maximum(nf - 0.75, 0.0)}
    for j in range(ctx["xc"].shape[1]):
        xj = ctx["xc"][:, j]
        cols[f"x{j}"] = xj
        cols[f"zx{j}"] = z * xj
        cols[f"nfx{j}"] = nf * xj
    return cols


def _model_terms(d):
    xs = [f"x{j}" for j in range(d)]
    zx = [f"zx{j}" for j in range(d)]
    nfx = [f"nfx{j}" for j in range(d)]
    base = ["z", "nf"] + xs
    two_hop = ["h"]
    degree = ["ldc", "zld", "nfld", "cnt"]
    inter = ["znf"] + zx + nfx
    saturating = ["znf", "nf2", "hg25", "hg50", "hg75"]
    union = base + two_hop + degree + inter + [t for t in saturating if t not in inter]
    # ordered from simplest to most flexible
    return {
        "linear": base,
        "two_hop": base + two_hop,
        "degree": base + degree,
        "interact": base + inter,
        "saturating": base + saturating,
        "full": union,
    }


def _stack(cols, terms):
    return np.column_stack([cols[t] for t in terms])


# --------------------------------------------------------------------------- regression
def fit_regression_gate(phi, y, rows=None):
    """Ridge regression of outcomes on [own treatment, neighbour-exposure features, ...]."""
    if rows is not None:
        phi, y = phi[rows], y[rows]
    mu = phi.mean(axis=0)
    sd = phi.std(axis=0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    a = (phi - mu) / sd
    ym = float(y.mean())
    k = a.shape[1]
    gram = a.T @ a + _RIDGE * a.shape[0] * np.eye(k)
    beta = np.linalg.solve(gram, a.T @ (y - ym))
    return {"beta": beta, "mu": mu, "sd": sd, "ym": ym}


def predict_rows(fit, phi):
    return ((phi - fit["mu"]) / fit["sd"]) @ fit["beta"] + fit["ym"]


def predict_all_treated(fit, phi1):
    return float(predict_rows(fit, phi1).mean())


def predict_all_control(fit, phi0):
    return float(predict_rows(fit, phi0).mean())


def _gate(fit, phi1, phi0):
    return predict_all_treated(fit, phi1) - predict_all_control(fit, phi0)


# --------------------------------------------------------------------------- validation
def _cv_losses(phi, y, folds):
    loss = np.empty(len(y))
    n = len(y)
    for idx in folds:
        train = np.ones(n, dtype=bool)
        train[idx] = False
        fit = fit_regression_gate(phi, y, train)
        loss[idx] = (y[idx] - predict_rows(fit, phi[idx])) ** 2
    return loss


def _extrapolation_splits(ctx, nf, rng, frac=0.25):
    """Hold out top / bottom neighbour-fraction units and the highest-degree units."""
    n = len(nf)
    jit = rng.random(n) * 1e-9
    k = max(int(round(frac * n)), 5)
    splits = []
    for key, top in ((nf + jit, True), (nf + jit, False), (ctx["deg"] + jit, True)):
        order = np.argsort(key, kind="stable")
        test = order[-k:] if top else order[:k]
        train = np.ones(n, dtype=bool)
        train[test] = False
        if train.sum() >= 20:
            splits.append((train, test))
    return splits


def _extrap_losses(phi, y, splits):
    parts = []
    for train, test in splits:
        fit = fit_regression_gate(phi, y, train)
        parts.append((y[test] - predict_rows(fit, phi[test])) ** 2)
    return np.concatenate(parts)


def _within_one_se(loss_m, loss_best):
    d = loss_m - loss_best
    se = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else 0.0
    return d.mean() <= se + 1e-15


# --------------------------------------------------------------------------- uncertainty
def bias_variance_decomposition(boot, center):
    """Bootstrap bias (relative to the centre) and variance of the estimator."""
    boot = np.asarray(boot, dtype=np.float64)
    var = float(boot.var(ddof=1)) if len(boot) > 1 else 0.0
    return {"bias": float(boot.mean() - center) if len(boot) else 0.0, "var": var}


def meta_regression_spread(estimates):
    """Model-uncertainty spread: regress candidate estimates on their complexity rank.

    Returns the larger of the SD of the estimates and the fitted trend over the range.
    """
    e = np.asarray(estimates, dtype=np.float64)
    if len(e) < 2:
        return 0.0
    spread = float(e.std())
    if len(e) >= 3:
        rank = np.arange(len(e), dtype=np.float64)
        slope = np.polyfit(rank, e, 1)[0]
        spread = max(spread, abs(float(slope)) * 0.5 * (len(e) - 1))
    return spread


def block_bootstrap_ci(boot, est, extra_se, zcrit):
    """Normal-approximation interval from block-bootstrap draws plus model spread."""
    var = bias_variance_decomposition(boot, est)["var"]
    se = float(np.sqrt(var + extra_se ** 2))
    return est - zcrit * se, est + zcrit * se, se


def _hc_se(fit, phi, resid, phi1, phi0):
    a = np.column_stack([np.ones(len(phi)), (phi - fit["mu"]) / fit["sd"]])
    cvec = np.concatenate([[0.0], ((phi1 - phi0) / fit["sd"]).mean(axis=0)])
    bread = np.linalg.pinv(a.T @ a)
    meat = (a * resid[:, None] ** 2).T @ a
    cov = bread @ meat @ bread
    return float(np.sqrt(max(cvec @ cov @ cvec, 0.0)))


def _bootstrap_estimates(ctx, terms, accepted, best, fits, phi, phi1, phi0, y, assign, blocks,
                         rng, t_start):
    resid = y - predict_rows(fits[best], phi[best])
    needed = list(dict.fromkeys(list(accepted) + [best]))
    n = len(y)
    n_blocks = int(blocks.max()) + 1
    boot = []
    n_reps = _N_REPS
    for _ in range(n_reps):
        if len(boot) >= 8 and time.perf_counter() - t_start > _SOFT_DEADLINE:
            break
        zs = assign()
        cols = _columns(ctx, zs)
        phis = {m: _stack(cols, terms[m]) for m in needed}
        w = rng.choice(np.array([-1.0, 1.0]), size=n_blocks)[blocks]
        ys = predict_rows(fits[best], phis[best]) + resid * w
        gates = [_gate(fit_regression_gate(phis[m], ys), phi1[m], phi0[m]) for m in accepted]
        boot.append(float(np.mean(gates)))
    return np.array(boot), resid


# --------------------------------------------------------------------------- main pipeline
def _regression_pipeline(n, edges, x, z, y, kind, p, labels, zcrit, rng, t_start):
    ctx = _context(n, edges, x)
    terms = _model_terms(ctx["xc"].shape[1])
    names = list(terms)
    cols_obs = _columns(ctx, z)
    cols1 = _columns(ctx, np.ones(n))
    cols0 = _columns(ctx, np.zeros(n))
    phi = {m: _stack(cols_obs, terms[m]) for m in names}
    phi1 = {m: _stack(cols1, terms[m]) for m in names}
    phi0 = {m: _stack(cols0, terms[m]) for m in names}
    fits = {m: fit_regression_gate(phi[m], y) for m in names}
    gates = {m: _gate(fits[m], phi1[m], phi0[m]) for m in names}

    nf_obs = cols_obs["nf"]
    accepted = [names[0]]
    best = names[0]
    if n >= 40:
        perm = rng.permutation(n)
        folds = np.array_split(perm, 5)
        splits = _extrapolation_splits(ctx, nf_obs, rng)
        cv = {m: _cv_losses(phi[m], y, folds) for m in names}
        ex = {m: _extrap_losses(phi[m], y, splits) for m in names} if splits else None
        cv_ref = cv[names[0]].mean() + 1e-12
        crit = {}
        for m in names:
            c = cv[m].mean() / cv_ref
            if ex is not None:
                c += ex[m].mean() / (ex[names[0]].mean() + 1e-12)
            crit[m] = c
        best = min(names, key=lambda m: crit[m])
        accepted = []
        for m in names:
            ok = m == best or (
                _within_one_se(cv[m], cv[best])
                and (ex is None or _within_one_se(ex[m], ex[best])))
            if ok:
                accepted.append(m)
    est = float(np.mean([gates[m] for m in accepted]))

    # --- uncertainty: design-resampling wild block bootstrap
    if kind == "cluster" and labels is not None:
        _, blocks = np.unique(labels, return_inverse=True)
        blocks = blocks.astype(np.int64)

        def assign():
            return cluster_randomize(rng, blocks, p)
    else:
        blocks = np.arange(n, dtype=np.int64)

        def assign():
            return bernoulli_assign(rng, n, p)

    boot, resid = _bootstrap_estimates(ctx, terms, accepted, best, fits, phi, phi1, phi0, y,
                                       assign, blocks, rng, t_start)
    spread = meta_regression_spread([gates[m] for m in accepted])
    if len(boot) >= 8 and np.all(np.isfinite(boot)):
        lo, hi, se = block_bootstrap_ci(boot, est, spread, zcrit)
    else:
        se = np.sqrt(_hc_se(fits[best], phi[best], resid, phi1[best], phi0[best]) ** 2
                     + spread ** 2)
        lo, hi = est - zcrit * se, est + zcrit * se

    _STATE["last_diag"] = {
        "accepted": list(accepted), "best": best,
        "corner_coverage": corner_coverage(nf_obs, ctx["deg"]),
        "dim": difference_in_means(z, y),
        "hajek": hajek_exposure_estimate(ctx["adj"], ctx["deg"], z, y, p),
        "n_boot": int(len(boot)),
    }
    return est, lo, hi


def _fallback(z, y, zcrit):
    est = difference_in_means(z, y)
    t, c = z > 0.5, z <= 0.5
    if t.sum() > 1 and c.sum() > 1:
        se = float(np.sqrt(y[t].var(ddof=1) / t.sum() + y[c].var(ddof=1) / c.sum()))
    else:
        se = abs(est) + 1.0
    return est, est - zcrit * se, est + zcrit * se


def _estimate(request):
    t_start = time.perf_counter()
    n = int(request["n"])
    edges = decode_array(request["edges"])
    x = decode_array(request["covariates"])
    z = decode_array(request["treatment"]).astype(np.float64)
    y = decode_array(request["outcomes"])
    design = request["design"]
    kind = design.get("kind", "bernoulli")
    p = float(np.clip(float(design.get("probability", 0.5)), 1e-6, 1.0 - 1e-6))
    labels = decode_array(design.get("cluster_labels"))
    level = float(request.get("workload", {}).get("ci_level", 0.95))
    zcrit = float(ndtri(0.5 + 0.5 * level))

    seed = _STATE["seed"] if _STATE["seed"] is not None else 0
    rng = np.random.default_rng([int(seed), zlib.crc32(y.tobytes()),
                                 zlib.crc32(z.astype(np.uint8).tobytes())])
    try:
        est, lo, hi = _regression_pipeline(n, edges, x, z, y, kind, p, labels, zcrit, rng,
                                           t_start)
        if not (np.isfinite(est) and np.isfinite(lo) and np.isfinite(hi)):
            raise ValueError("non-finite regression output")
    except Exception:
        est, lo, hi = _fallback(z, y, zcrit)
    est = float(est)
    lo = float(min(lo, est))
    hi = float(max(hi, est))
    return {"estimate": est, "ci_low": lo, "ci_high": hi}


def handle(request):
    op = request.get("op")
    if op == "reset":
        seed = int(request["seed"])
        _STATE["seed"] = seed
        _STATE["rng"] = np.random.default_rng(seed)
        _STATE["last_diag"] = None
        return {"ok": True}
    if op == "estimate":
        return _estimate(request)
    raise ValueError("unknown op")
