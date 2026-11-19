"""Starter candidate: PPI++ (power-tuned prediction-powered) confidence interval for a mean.

Interface: ``handle(request) -> response`` over finite JSON-compatible values
(``python_rpc_v1:handle``). The candidate runs in an isolated process with no
filesystem or network access shared with the evaluator; all data arrive inline.

Task. A fixed predictor, a small labeled sample and a larger unlabeled sample are given.
Return a confidence interval [lo, hi] for the population mean E[Y] at level 1 - alpha.
Nominal coverage must hold in repeated sampling; the score rewards narrower intervals than
the PPI++ interval (``ppi_py.ppi_mean_ci`` default power tuning) at maintained coverage.
No extra labels, no predictor change, no extra unlabeled data exist.

Operations (every request is a dict with an ``"op"`` key):

``{"op": "reset", "seed": int}``
    Sent exactly once at the start of every episode (and the process may be restarted
    first). Must clear ALL cross-episode state and seed only the candidate's own
    randomness. Any non-negative integer seed is valid; the seed never selects a dataset,
    plane or workload. Response: exactly ``{"ok": True}``.

``{"op": "estimate", "n": int, "N": int, "alpha": float,
   "Y_labeled": ARR, "Yhat_labeled": ARR, "Yhat_unlabeled": ARR}``
    One independent labeled/unlabeled draw per episode (one estimate call per episode).
    ``ARR`` is ``{"dtype": "float64", "shape": [length], "encoding": "base64-le",
    "data": <base64 of little-endian float64 bytes>}``. ``len(Y_labeled) ==
    len(Yhat_labeled) == n`` and ``len(Yhat_unlabeled) == N``. All values are finite.
    The labeled and unlabeled records are i.i.d. draws from one population; the labeled
    Yhat are the predictor outputs on the labeled records. alpha is 0.05 in every plane.
    Response: exactly ``{"lo": float, "hi": float}`` (finite, lo <= hi); no other keys
    are allowed. A malformed, non-finite, reversed or late response counts as a miss
    with a worst-case width (10x the classical interval).
    Per-call wall deadline: 3 seconds (enforced). Keep BLAS threads at 1.
    The dataset or family name, population truth, baseline outputs and scores are never
    sent. Requests of up to N = 20000 unlabeled and n = 500 labeled records occur
    (about 225 KB base64 per request).

Any other op, or an estimate before reset, is an error.
"""

import base64
import math
import os
from statistics import NormalDist

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np  # noqa: E402

_STATE = {"ready": False, "seed": None, "rng": None}


def _decode(arr, name):
    if (type(arr) is not dict or arr.get("dtype") != "float64"
            or arr.get("encoding") != "base64-le" or type(arr.get("data")) is not str):
        raise ValueError(f"bad array {name}")
    raw = base64.b64decode(arr["data"].encode("ascii"), validate=True)
    out = np.frombuffer(raw, dtype="<f8").astype(np.float64)
    if list(arr.get("shape", [])) != [out.size] or not np.all(np.isfinite(out)):
        raise ValueError(f"bad array {name}")
    return out


def classical_ci(y, alpha):
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    half = z * y.std() / math.sqrt(y.size)
    return y.mean() - half, y.mean() + half


def ppi_pp_ci(y, yhat, yhat_unl, alpha):
    """PPI++ mean interval with the closed-form power-tuning parameter, clipped to [0, 1]."""
    n, big_n = y.size, yhat_unl.size
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    pooled_var = np.concatenate([yhat, yhat_unl]).var(ddof=1)
    if pooled_var > 1e-24:
        cov = float(np.mean((y - y.mean()) * (yhat - yhat.mean())))
        lam = min(1.0, max(0.0, cov / ((1.0 + n / big_n) * pooled_var)))
    else:
        lam = 0.0
    center = (lam * yhat_unl).mean() + (y - lam * yhat).mean()
    se = math.hypot((lam * yhat_unl).std() / math.sqrt(big_n),
                    (y - lam * yhat).std() / math.sqrt(n))
    return center - z * se, center + z * se


def _estimate(request):
    n, big_n, alpha = request["n"], request["N"], request["alpha"]
    y = _decode(request["Y_labeled"], "Y_labeled")
    yhat = _decode(request["Yhat_labeled"], "Yhat_labeled")
    yhat_unl = _decode(request["Yhat_unlabeled"], "Yhat_unlabeled")
    if y.size != n or yhat.size != n or yhat_unl.size != big_n or not 0.0 < alpha < 1.0:
        raise ValueError("inconsistent estimate request")
    lo, hi = ppi_pp_ci(y, yhat, yhat_unl, alpha)
    if not (math.isfinite(lo) and math.isfinite(hi)):
        lo, hi = classical_ci(y, alpha)
    return {"lo": float(lo), "hi": float(hi)}


def handle(request):
    op = request.get("op") if isinstance(request, dict) else None
    if op == "reset":
        seed = request["seed"]
        if type(seed) is not int or seed < 0:
            raise ValueError("bad seed")
        _STATE.update(ready=True, seed=seed, rng=np.random.default_rng(seed))
        return {"ok": True}
    if op == "estimate":
        if not _STATE["ready"]:
            raise RuntimeError("estimate before reset")
        return _estimate(request)
    raise ValueError("unknown op")
