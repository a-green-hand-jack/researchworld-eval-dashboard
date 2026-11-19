"""Candidate: calibrated, low-MC-noise rerun simulation for single-run Kernel SHAP reliability.

Interface (python_rpc_v1:handle): ``handle(request) -> response`` with finite JSON-compatible
values only.  Candidate state lives only in this module's memory; nothing is read from or written
to evaluator paths.

Operations
----------
{"op": "reset", "seed": <int>}      -> exactly {"ok": true}; any non-negative integer seed.
{"op": "diagnose", "workload": {...}, "instances": [...]}
    workload: n_features d, n_masks B (4d or 16d, complement pairs adjacent), family
    ("logreg" | "random_forest" | "mlp"), k (=3), n_instances.
    instance keys: masks (bit-packed uint8, base64), weights (float64 [B]), values (float64 [B]),
    anchors {"empty", "full"}.
    Response: exactly {"r_hat": [float, ...]}, len == n_instances, finite, in [0, 1].

Method.  Same skeleton as the baseline: delete-one-group jackknife over complement pairs, then
simulate reruns by drawing attributions around the observed run and averaging the Jaccard overlap
of the simulated top-k sets with the observed one.  Differences from the baseline, each kept
separate and individually switchable so they can be ablated:
  1. Monte-Carlo noise reduction: 1000 draws (500 antithetic pairs) with common random numbers
     fixed per episode via np.random.default_rng(seed).
  2. A full-covariance simulator (``_jackknife_cov``; draws are phi + L z with L built from the
     centred delete-one-group replicates, so the sum(phi) constraint is preserved) next to the
     baseline diagonal simulator; spread multiplier ``mult`` is a parameter of ``_sim_jaccard``.
  3. A small monotone ``_calibrate`` map (``_CALIB_COEF``) over the simulated Jaccards at several
     spread multipliers, log2(B/d), a standardised top-k margin and the family, shrunk toward the
     baseline-equivalent diagonal simulator.  See NOTES.md for how the constants were chosen.
"""
import base64

import numpy as np

_STATE = {"rng": np.random.default_rng(0), "ready": False, "seed": 0}
_FOLDS = 8
_N_DRAWS = 1000  # even: antithetic pairs
_FALLBACK = 0.9
_SHRINK = 0.7  # weight of the calibrated map vs the baseline-equivalent simulator

# Calibration map: logit-free linear map on simulated Jaccards, clipped to [0, 1].
# Features: s_d10 (diag, mult 1.0), s_d07 (diag, mult 0.7), s_f10 (full cov, mult 1.0),
# s_f141 (full cov, mult sqrt(2)), lbd = log2(B/d) - 3 (0 at B=8d midpoint), mz = tanh(margin z / 3),
# and family indicators.  The constants are conservative PRIORS (see NOTES.md): they were NOT
# fitted on a local replica because no code could be executed while writing this candidate.
# Cycle-1 evidence (spread inflation > 1 lowered the score; labels skew high) motivates putting
# weight on the un-inflated / deflated simulators and none on the inflated one.
_CALIB_COEF = {
    "intercept": 0.0,
    "s_d10": 0.50,
    "s_d07": 0.20,
    "s_f10": 0.30,
    "s_f141": 0.0,
    "lbd": 0.0,
    "mz": 0.0,
    "fam_logreg": 0.0,
    "fam_random_forest": 0.0,
    "fam_mlp": 0.0,
}


def _decode(obj, dtype):
    raw = base64.b64decode(obj["data"].encode("ascii"))
    return np.frombuffer(raw, dtype=dtype).reshape(obj["shape"])


def _solve(Z, w, v, v0, v1):
    total = v1 - v0
    A = Z[:, :-1] - Z[:, -1:]
    t = (v - v0) - Z[:, -1] * total
    sw = np.sqrt(w)
    sol = np.linalg.lstsq(A * sw[:, None], t * sw, rcond=None)[0]
    return np.append(sol, total - sol.sum())


def _top(a, k):
    return np.argsort(-a, kind="stable")[:k]


def _jackknife_cov(Z, w, v, v0, v1, fold_of_row, n_folds):
    """Delete-one-group jackknife over complement pairs.

    Returns (phi, loo, dev, n): the full-data solution, the stacked leave-group-out solutions,
    their centred deviations scaled so that dev.T @ dev is the jackknife covariance, and n.
    """
    phi = _solve(Z, w, v, v0, v1)
    d = Z.shape[1]
    loo = []
    for f in range(n_folds):
        keep = fold_of_row != f
        if keep.sum() > d:
            loo.append(_solve(Z[keep], w[keep], v[keep], v0, v1))
    if len(loo) < 2:
        return phi, None, None, 0
    loo = np.array(loo)
    n = len(loo)
    dev = np.sqrt((n - 1) / n) * (loo - loo.mean(0))
    return phi, loo, dev, n


def _topk_mask(a, k):
    idx = np.argsort(-a, axis=1, kind="stable")[:, :k]
    m = np.zeros(a.shape, dtype=bool)
    np.put_along_axis(m, idx, True, axis=1)
    return m


def _sim_jaccard(phi, dev, mult, k, z_full, z_diag, full_cov):
    """Mean Jaccard of simulated top-k sets vs the observed top-k set.

    z_full: (N, n) common random numbers for the full-covariance draw; z_diag: (N, d) for the
    diagonal draw.  ``mult`` scales the simulated spread.
    """
    if full_cov:
        noise = z_full[:, : dev.shape[0]] @ dev
    else:
        sd = np.sqrt((dev ** 2).sum(0))
        noise = z_diag * sd[None, :]
    draws = phi[None, :] + mult * noise
    ref = np.zeros(phi.shape[0], dtype=bool)
    ref[_top(np.abs(phi), k)] = True
    sim = _topk_mask(np.abs(draws), k)
    c = (sim & ref[None, :]).sum(1).astype(float)
    return float(np.mean(c / (2 * k - c)))


def _margin_z(phi, loo, k):
    """Standardised gap between the k-th and (k+1)-th largest |phi| using the jackknife SE."""
    order = np.argsort(-np.abs(phi), kind="stable")
    if len(order) <= k:
        return 3.0
    a, b = order[k - 1], order[k]
    gap = abs(phi[a]) - abs(phi[b])
    g = np.abs(loo[:, a]) - np.abs(loo[:, b])
    n = len(g)
    se = np.sqrt((n - 1) / n * ((g - g.mean()) ** 2).sum())
    return float(gap / max(se, 1e-12))


def _calibrate(feats, B, d, family):
    c = _CALIB_COEF
    lbd = np.log2(B / d) - 3.0
    mz = np.tanh(feats["margin_z"] / 3.0)
    r = (c["intercept"] + c["s_d10"] * feats["s_d10"] + c["s_d07"] * feats["s_d07"]
         + c["s_f10"] * feats["s_f10"] + c["s_f141"] * feats["s_f141"]
         + c["lbd"] * lbd + c["mz"] * mz + c.get("fam_" + str(family), 0.0))
    return float(np.clip(r, 0.0, 1.0))


def _diagnose_one(inst, d, B, k, family, rng, z_full, z_diag):
    Z = np.unpackbits(_decode(inst["masks"], np.uint8), axis=1, count=d, bitorder="little").astype(float)
    w = _decode(inst["weights"], "<f8").astype(float)
    v = _decode(inst["values"], "<f8").astype(float)
    v0, v1 = float(inst["anchors"]["empty"]), float(inst["anchors"]["full"])
    pairs = (B + 1) // 2
    fold = rng.permutation(pairs) % _FOLDS
    fold_of_row = np.repeat(fold, 2)[:B]
    phi, loo, dev, n = _jackknife_cov(Z, w, v, v0, v1, fold_of_row, _FOLDS)
    if loo is None:
        return 0.5
    s_d10 = _sim_jaccard(phi, dev, 1.0, k, z_full, z_diag, False)
    s_d07 = _sim_jaccard(phi, dev, 0.7, k, z_full, z_diag, False)
    s_f10 = _sim_jaccard(phi, dev, 1.0, k, z_full, z_diag, True)
    s_f141 = _sim_jaccard(phi, dev, float(np.sqrt(2.0)), k, z_full, z_diag, True)
    feats = {"s_d10": s_d10, "s_d07": s_d07, "s_f10": s_f10, "s_f141": s_f141,
             "margin_z": _margin_z(phi, loo, k)}
    if not all(np.isfinite(x) for x in feats.values()):
        return _FALLBACK
    cal = _calibrate(feats, B, d, family)
    r = _SHRINK * cal + (1.0 - _SHRINK) * s_d10
    if not np.isfinite(r):
        return _FALLBACK
    return float(np.clip(r, 0.02, 1.0))


def _crn(seed, d):
    """Common random numbers fixed per episode (antithetic pairs)."""
    g = np.random.default_rng(seed)
    half = _N_DRAWS // 2
    zf = g.standard_normal((half, _FOLDS))
    zd = g.standard_normal((half, d))
    return np.concatenate([zf, -zf]), np.concatenate([zd, -zd])


def handle(request):
    op = request.get("op")
    if op == "reset":
        seed = int(request["seed"])
        _STATE["rng"] = np.random.default_rng(seed)
        _STATE["seed"] = seed
        _STATE["ready"] = True
        return {"ok": True}
    if op == "diagnose":
        wl = request["workload"]
        d, B, k = int(wl["n_features"]), int(wl["n_masks"]), int(wl["k"])
        family = wl.get("family", "")
        rng = _STATE["rng"]
        z_full, z_diag = _crn(_STATE["seed"], d)
        out = []
        for inst in request["instances"]:
            try:
                r = _diagnose_one(inst, d, B, k, family, rng, z_full, z_diag)
            except Exception:
                r = _FALLBACK
            if not np.isfinite(r):
                r = _FALLBACK
            out.append(float(np.clip(r, 0.0, 1.0)))
        return {"r_hat": out}
    raise ValueError("unsupported op")
