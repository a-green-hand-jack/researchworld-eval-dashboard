"""Baseline candidate: single-run reliability diagnostic for stochastic Kernel SHAP.

Interface (python_rpc_v1:handle): ``handle(request) -> response`` with finite JSON-compatible
values only.  Candidate state lives only in this module's memory; there is no shared file system
with the evaluator, so nothing may be read from or written to evaluator paths.

Task.  The evaluator trains a tabular classifier (logistic regression, random forest or sklearn
MLP) and runs a *stochastic Kernel SHAP* explainer (interventional value function, 32 background
rows, fixed coalition budget n_masks per run) on explained instances.  For every instance you are
shown ONE run of the explainer.  Predict, for each instance, the probability-like reliability
score r_hat in [0, 1] that independent reruns of the same explainer (same model, same instance,
same budget, fresh coalition sampling) reproduce this run's top-k attribution set.  The evaluator
scores r_hat against y = mean over 8 hidden reruns of Jaccard(top-k(|phi|) of this run, top-k(|phi|)
of the rerun) with k = 3, using squared error.  You never see labels, reruns, model internals
or dataset identities.

Operations
----------
{"op": "reset", "seed": <int>}
    Start a fresh episode; seeds candidate-side randomness only.  Any non-negative integer seed
    must be accepted.  The seed never identifies the workload.  Response: exactly {"ok": true}.

{"op": "diagnose", "workload": {...}, "instances": [...]}
    Exactly one diagnose call follows each reset.
    workload (same field names in every plane):
        "n_features": int d (number of ORIGINAL features, coalition masks have d columns)
        "n_masks": int B (coalitions in the run; B = 4*d or 16*d, complement pairs adjacent)
        "family": "logreg" | "random_forest" | "mlp"
        "k": 3 (size of the top-k attribution set)
        "n_instances": int, equals len(instances) (<= 20)
    each instance is a dict with exactly the keys
        "masks":   array object, uint8, bit-packed along axis 1 with numpy.packbits(...,
                   bitorder="little"); fields {"dtype": "uint8", "encoding": "base64",
                   "bitorder": "little", "shape": [B, ceil(d/8)], "unpacked_shape": [B, d],
                   "data": <base64 str>}.  numpy.unpackbits(..., axis=1, count=d, bitorder="little")
                   recovers the {0,1} coalition matrix Z (1 = feature present).
        "weights": array object, float64 little-endian, fields {"dtype": "float64",
                   "encoding": "base64", "byteorder": "little", "shape": [B], "data": ...};
                   Kernel SHAP regression weights of the B coalitions (sum to 1).
        "values":  same encoding, shape [B]: v(S) = mean over the background rows of the model's
                   class-1 probability with the features in S taken from the explained instance.
        "anchors": {"empty": float v(empty set), "full": float v(all features) = model output}
    Coalitions are never the empty or full set.  Kernel SHAP attribution of the run:
        minimise sum_i w_i (v_i - v_empty - Z_i . phi)^2  subject to sum(phi) = v_full - v_empty.
    Response: exactly {"r_hat": [float, ...]} with len == n_instances, in instance order, each
    finite and in [0, 1].  Extra keys are rejected, a malformed response gets the worst-case
    error (1.0) for the whole episode.

This candidate (program_1) simulates reruns with a delete-one-group jackknife over complement
pairs that keeps the FULL covariance of the attribution estimate (including the sum(phi)
constraint), and draws reruns from the predictive distribution N(phi_hat, 2*Sigma): the observed
run is itself a noisy draw around the unknown true attribution, so a fresh rerun differs from it
by noise of both runs (posterior of phi_true given phi_hat is N(phi_hat, Sigma) under a flat
prior, plus the rerun's own Sigma).  The score is the mean Jaccard of simulated top-k(|phi|) sets
with the observed top-k set, computed with common random numbers.
"""
import base64

import numpy as np

_STATE = {"rng": np.random.default_rng(0), "ready": False}
_GROUPS = 48  # max number of complement-pair groups left out in the jackknife
_DRAWS = 400
_INFL = float(np.sqrt(2.0))  # predictive spread: observed-run noise + rerun noise


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


def _diagnose_one(inst, d, B, k, rng):
    Z = np.unpackbits(_decode(inst["masks"], np.uint8), axis=1, count=d, bitorder="little").astype(float)
    w = _decode(inst["weights"], "<f8").astype(float)
    v = _decode(inst["values"], "<f8").astype(float)
    v0, v1 = float(inst["anchors"]["empty"]), float(inst["anchors"]["full"])
    phi = _solve(Z, w, v, v0, v1)
    pairs = (B + 1) // 2
    groups = min(pairs, _GROUPS)
    grp = rng.permutation(pairs) % groups
    grp_of_row = np.repeat(grp, 2)[:B]
    loo = []
    for g in range(groups):
        keep = grp_of_row != g
        if keep.sum() > d:
            loo.append(_solve(Z[keep], w[keep], v[keep], v0, v1))
    if len(loo) < 2:
        return 0.5
    loo = np.array(loo)
    n = len(loo)
    dev = loo - loo.mean(0)
    # Delete-one-group jackknife covariance: Sigma = (n-1)/n * dev^T dev.  Drawing
    # e = sqrt((n-1)/n) * z^T dev with z ~ N(0, I_n) has exactly this covariance, keeps the
    # sum(phi) constraint, and needs no factorisation of a rank-deficient matrix.
    z = rng.standard_normal((_DRAWS, n))
    noise = np.sqrt((n - 1) / n) * (z @ dev)
    draws = phi[None, :] + _INFL * noise
    order = np.argsort(-np.abs(draws), axis=1, kind="stable")[:, :k]
    sel = np.zeros((_DRAWS, d), dtype=bool)
    np.put_along_axis(sel, order, True, axis=1)
    ref = np.zeros(d, dtype=bool)
    ref[_top(np.abs(phi), k)] = True
    c = (sel & ref[None, :]).sum(1).astype(float)
    r = float(np.mean(c / (2 * k - c)))
    return float(min(1.0, max(0.0, r))) if np.isfinite(r) else 0.5


def handle(request):
    op = request.get("op")
    if op == "reset":
        _STATE["rng"] = np.random.default_rng(int(request["seed"]))
        _STATE["ready"] = True
        return {"ok": True}
    if op == "diagnose":
        wl = request["workload"]
        d, B, k = int(wl["n_features"]), int(wl["n_masks"]), int(wl["k"])
        rng = _STATE["rng"]
        out = [_diagnose_one(inst, d, B, k, rng) for inst in request["instances"]]
        return {"r_hat": out}
    raise ValueError("unsupported op")
