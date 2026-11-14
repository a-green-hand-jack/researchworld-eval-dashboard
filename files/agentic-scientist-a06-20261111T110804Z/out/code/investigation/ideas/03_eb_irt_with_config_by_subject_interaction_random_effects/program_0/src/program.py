"""Empirical-Bayes latent-difficulty posterior interval reporter.

Interface (python_rpc_v1:handle): ``handle(request) -> response`` over finite JSON values.

``{"op": "reset", "seed": <int>}``  seeds candidate randomness only; response ``{"ok": True}``.
``{"op": "report", ...}``           response has exactly ``estimate``, ``lower``, ``upper`` with
                                    0 <= lower <= estimate <= upper <= 1 (finite floats).

Method.  All logged (question, config, outcome) triples are modelled by a hierarchical
logistic latent-difficulty model  P(correct) = sigmoid(a[config] - b[question]),
a ~ N(0, tau2), b[q] ~ N(m[subject(q)], s2).  tau2 and s2 are set by empirical Bayes (EM-style
updates with a Laplace/Schur-complement posterior-variance correction) using vectorised
bincount-based damped Newton sweeps on the sparse log, so the exhaustive and the successive
halving searchers share one code path (selection uses only observed outcomes, hence is
ignorable for the likelihood).  The posterior of the selected config's fresh-question accuracy
theta = E_b[sigmoid(a_k - b)] is obtained from posterior draws of (a_k, level shift, log s)
and Gauss-Hermite integration over fresh difficulties (mixing over the empirical subject
distribution); the report is the 5% / 95% quantiles, widened around the estimate by a
calibration factor kappa.  Degenerate worlds (all-zero outcomes, unobserved selected config,
tau2 at its lower clamp) and a wall-clock guard are handled explicitly.
"""
import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "4")

import base64
import math
import time

import numpy as np

_Z90 = 1.6448536269514722
_STATE = {"seed": None, "rng": None}

_FIT_BUDGET_S = 1.5       # wall-clock guard for the EB fit
_N_DRAWS = 400            # posterior draws of (a_k, shift, log s)
_N_GH = 21                # Gauss-Hermite nodes over fresh difficulties
_TAU2_MIN, _TAU2_MAX = 1e-4, 4.0
_S2_MIN, _S2_MAX = 1e-2, 25.0
_SUBJ_SHRINK = 5.0        # pseudo-questions shrinking subject means to the global mean
_ZERO_UPPER_CAP = 0.02    # cap on the rule-of-three upper bound in all-zero worlds


def _decode(field, dtype):
    raw = base64.b64decode(field["data"])
    return np.frombuffer(raw, dtype=np.dtype(dtype).newbyteorder("<")).astype(np.int64)


def _expit(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -35.0, 35.0)))


def _wilson(p, n, z=_Z90):
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(max(p * (1.0 - p) / n + z * z / (4.0 * n * n), 0.0)) / denom
    return max(0.0, min(center - half, p)), min(1.0, max(center + half, p))


def _fit_irt(q, c, y, sj, N, K, nsub, t0):
    """Empirical-Bayes MAP fit of logit P = a[c] - b[q] on sparse triples.

    Returns dict with a, b, m (per-subject difficulty mean), tau2, s2, Hb and the
    Schur-complement precision of each a_k with and without the tau2 prior.
    """
    yf = y.astype(np.float64)
    pbar = min(max(yf.mean(), 0.01), 0.99)
    a = np.zeros(K)
    b = np.full(N, -math.log(pbar / (1.0 - pbar)))
    nsq = np.bincount(sj, minlength=nsub).astype(np.float64)
    nsq = np.maximum(nsq, 1e-9)
    m = np.full(nsub, b[0])
    tau2, s2 = 0.25, 1.0
    prev = (tau2, s2)
    for it in range(30):
        for _ in range(3):
            p = _expit(a[c] - b[q])
            r = yf - p
            w = p * (1.0 - p)
            ga = np.bincount(c, r, K) - a / tau2
            Ha = np.bincount(c, w, K) + 1.0 / tau2
            a = a + np.clip(ga / Ha, -1.0, 1.0)
            p = _expit(a[c] - b[q])
            r = yf - p
            w = p * (1.0 - p)
            gb = -np.bincount(q, r, N) - (b - m[sj]) / s2
            Hb = np.bincount(q, w, N) + 1.0 / s2
            b = b + np.clip(gb / Hb, -1.0, 1.0)
        p = _expit(a[c] - b[q])
        w = p * (1.0 - p)
        Hb = np.bincount(q, w, N) + 1.0 / s2
        Ha0 = np.bincount(c, w, K)
        # Schur complement: marginal precision of a_k after integrating out the b[q]
        S0 = np.maximum(Ha0 - np.bincount(c, (w * w) / Hb[q], K), 1e-6)
        S = S0 + 1.0 / tau2
        # subject means of difficulty, shrunk to the global mean
        mg = b.mean()
        m = (np.bincount(sj, b, nsub) + _SUBJ_SHRINK * mg) / (nsq + _SUBJ_SHRINK)
        # empirical-Bayes variance updates with Laplace (posterior variance) correction
        tau2 = float(np.clip((np.sum(a * a) + np.sum(1.0 / S)) / K, _TAU2_MIN, _TAU2_MAX))
        s2 = float(np.clip((np.sum((b - m[sj]) ** 2) + np.sum(1.0 / Hb)) / N, _S2_MIN, _S2_MAX))
        if it >= 5 and abs(tau2 - prev[0]) < 1e-3 * prev[0] and abs(s2 - prev[1]) < 1e-3 * prev[1]:
            break
        prev = (tau2, s2)
        if time.perf_counter() - t0 > _FIT_BUDGET_S:
            break
    # final quantities at the returned parameters
    p = _expit(a[c] - b[q])
    w = p * (1.0 - p)
    Hb = np.bincount(q, w, N) + 1.0 / s2
    S0 = np.maximum(np.bincount(c, w, K) - np.bincount(c, (w * w) / Hb[q], K), 1e-6)
    return {"a": a, "b": b, "m": m, "tau2": tau2, "s2": s2, "S0": S0}


def _kappa(N, K, real):
    """Width-calibration factor (>= 1) applied around the estimate."""
    base = 1.20 if real else 1.12
    small_n = 1.0 + 0.25 * min(1.0, math.sqrt(50.0 / max(N, 1)))
    many_k = 1.0 + 0.03 * math.log2(max(K, 2) / 2.0)
    return base * small_n * many_k


def _fallback(p_sel, p_pool, n_sel):
    """Conservative interval used only if the model fit fails."""
    if n_sel <= 0:
        est = p_pool
        return est, max(0.0, est - 0.25), min(1.0, est + 0.25)
    est = max(0.0, p_sel - 0.5 * max(p_sel - p_pool, 0.0))
    lo, hi = _wilson(p_sel, n_sel, z=2.3)
    lo = max(0.0, min(lo, est) - 0.5 * max(p_sel - p_pool, 0.0))
    return est, lo, max(hi, est)


def _finalize(est, lo, hi):
    est = float(min(max(est, 0.0), 1.0))
    lo = float(min(max(lo, 0.0), 1.0))
    hi = float(min(max(hi, 0.0), 1.0))
    if not (math.isfinite(est) and math.isfinite(lo) and math.isfinite(hi)):
        return {"estimate": 0.5, "lower": 0.0, "upper": 1.0}
    lo = min(lo, est)
    hi = max(hi, est)
    return {"estimate": est, "lower": lo, "upper": hi}


def _report(request, t0):
    N = int(request["n_questions"])
    K = int(request["n_configs"])
    k = int(request["selected_config"])
    q = _decode(request["log"]["question_idx"], np.uint16)
    c = _decode(request["log"]["config_idx"], np.uint8)
    y = _decode(request["log"]["outcome"], np.uint8)
    if "subject_code" in request and request["subject_code"] is not None:
        subj = _decode(request["subject_code"], np.uint8)
    else:
        subj = np.zeros(N, dtype=np.int64)
    if subj.shape[0] != N:
        subj = np.zeros(N, dtype=np.int64)
    M = y.shape[0]
    if M == 0:
        return {"estimate": 0.5, "lower": 0.0, "upper": 1.0}
    N = max(N, int(q.max()) + 1)
    if subj.shape[0] < N:
        subj = np.concatenate([subj, np.zeros(N - subj.shape[0], dtype=np.int64)])
    K = max(K, int(c.max()) + 1, k + 1)

    sel = c == k
    n_sel = int(sel.sum())
    p_pool = float(y.mean())
    p_sel = float(y[sel].mean()) if n_sel else p_pool
    real = bool(np.any(subj != 0))

    # degenerate: every outcome is 0 -> rule-of-three style capped upper bound
    if not np.any(y):
        denom = n_sel if n_sel > 0 else M
        return _finalize(0.0, 0.0, min(3.0 / denom, _ZERO_UPPER_CAP))
    # degenerate: selected config never observed -> pooled mean with a wide interval
    if n_sel == 0:
        return _finalize(p_pool, p_pool - 0.25, p_pool + 0.25)

    usub, sj_all = np.unique(subj[:N], return_inverse=True)
    sj_all = sj_all.astype(np.int64)
    nsub = usub.shape[0]
    fit = _fit_irt(q, c, y, sj_all, N, K, nsub, t0)

    a_hat = float(fit["a"][k])
    tau2 = fit["tau2"]
    s2 = fit["s2"]
    S0 = fit["S0"]
    # tau2 near its lower clamp (all configs ~equal): keep a floor on the prior variance so
    # that the pooled-mean interval still reflects the config's own sampling noise.
    tau2_eff = max(tau2, 0.3 * float(np.median(1.0 / S0)))
    prec_old = S0[k] + 1.0 / tau2
    prec_new = S0[k] + 1.0 / tau2_eff
    a_mean = a_hat * prec_old / prec_new
    a_sd = math.sqrt(1.0 / prec_new)

    rng = _STATE["rng"]
    if rng is None:
        rng = np.random.default_rng(0)
        _STATE["rng"] = rng
    S = _N_DRAWS
    s_hat = math.sqrt(s2)
    a_d = a_mean + a_sd * rng.standard_normal(S)
    s_d = s_hat * np.exp(rng.standard_normal(S) / math.sqrt(2.0 * max(N, 2)))
    shift_d = s_hat * rng.standard_normal(S) / math.sqrt(max(N, 1))

    x, wq = np.polynomial.hermite_e.hermegauss(_N_GH)
    wq = wq / wq.sum()
    pi = np.bincount(sj_all, minlength=nsub).astype(np.float64)
    pi = pi / pi.sum()
    m = fit["m"]
    # logit grid: (draw, subject, node)
    z = (a_d[:, None, None] - m[None, :, None] - shift_d[:, None, None]
         - s_d[:, None, None] * x[None, None, :])
    theta = np.einsum("dsj,j,s->d", _expit(z), wq, pi)

    est = float(theta.mean())
    lo = float(np.quantile(theta, 0.05))
    hi = float(np.quantile(theta, 0.95))
    kappa = _kappa(N, K, real)
    lower = est - kappa * max(est - lo, 0.0)
    upper = est + kappa * max(hi - est, 0.0)
    return _finalize(est, lower, upper)


def handle(request):
    op = request.get("op")
    if op == "reset":
        _STATE["seed"] = int(request["seed"])
        _STATE["rng"] = np.random.default_rng(_STATE["seed"])
        return {"ok": True}
    if op != "report":
        raise ValueError("unknown op")
    t0 = time.perf_counter()
    try:
        return _report(request, t0)
    except Exception:
        # keep the replication valid with a conservative naive-based interval
        try:
            k = int(request["selected_config"])
            config = _decode(request["log"]["config_idx"], np.uint8)
            outcome = _decode(request["log"]["outcome"], np.uint8)
            sel = config == k
            n_sel = int(sel.sum())
            p_pool = float(outcome.mean()) if outcome.size else 0.5
            p_sel = float(outcome[sel].mean()) if n_sel else p_pool
            return _finalize(*_fallback(p_sel, p_pool, n_sel))
        except Exception:
            return {"estimate": 0.5, "lower": 0.0, "upper": 1.0}
