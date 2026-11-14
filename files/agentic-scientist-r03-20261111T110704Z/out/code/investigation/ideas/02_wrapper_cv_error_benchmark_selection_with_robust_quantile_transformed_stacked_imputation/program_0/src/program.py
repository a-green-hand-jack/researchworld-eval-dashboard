"""Candidate: greedy conditional-variance benchmark selection + Gaussian conditional-mean imputation.

Entry point: ``handle(request) -> response`` (contract interface ``python_rpc_v1:handle``). Wire contract is
identical to the starter candidate (ops ``reset`` / ``load_history`` / ``select`` / ``predict``; same response
keys). All state lives in this process' memory.

Method (numpy only, deterministic given the seed):
  * z-score every column by its observed history mean/std;
  * EM for a multivariate Gaussian with missing entries (``em_gaussian_covariance``), with diagonal shrinkage;
  * greedy forward selection of k benchmarks minimising the trace of the posterior (conditional) covariance of
    the remaining benchmarks, i.e. A-optimal design (``greedy_select_conditional_variance``), with a mild
    coverage weighting because a new model may lack a selected benchmark;
  * impute with the (ridge-regularised) Gaussian conditional mean E[x_U | x_S] conditioned only on the selected
    benchmarks a new model actually has (``conditional_gaussian_impute``);
  * covariance shrinkage, rank of a factor-analytic covariance and ridge lambda are picked by K-fold CV over
    HISTORY models only; a few candidate selections are compared by the same CV error.
No new-model information is used anywhere except through the observed inputs of ``predict``.
"""
import base64
import os
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

import numpy as np

EM_SHRINK = 0.02
EM_MAX_ITER = 60
EM_TOL = 1e-4
EM_TIME_BUDGET = 30.0
JITTER = 1e-4
CV_FOLDS = 5
SHRINK_GRID = (0.0, 0.05, 0.15, 0.3)
RANK_GRID = (2, 4, 6, 10, None)
LAM_GRID = (0.003, 0.03, 0.1, 0.3)
Z_CLIP = 8.0

_STATE = {}


def _fresh(seed):
    _STATE.clear()
    _STATE.update(seed=int(seed), rng=np.random.default_rng(int(seed)), chunks={}, n_chunks=None,
                  n_cols=None, selected=None, model=None)


def _decode(b64, dtype, shape):
    raw = base64.b64decode(b64.encode("ascii"), validate=True)
    return np.frombuffer(raw, dtype=dtype).reshape(shape)


def _encode(array):
    return base64.b64encode(np.ascontiguousarray(array).tobytes()).decode("ascii")


# ----------------------------------------------------------------------------------------------------------
# Gaussian machinery
# ----------------------------------------------------------------------------------------------------------
def _pattern_groups(mask):
    """Group rows by identical observation pattern -> list of (obs_idx, mis_idx, row_idx)."""
    uniq, inv = np.unique(mask, axis=0, return_inverse=True)
    inv = np.asarray(inv).reshape(-1)
    groups = []
    for g in range(uniq.shape[0]):
        rows = np.nonzero(inv == g)[0]
        obs = np.nonzero(uniq[g])[0]
        mis = np.nonzero(~uniq[g])[0]
        groups.append((obs, mis, rows))
    return groups


def _e_step(z, groups, mu, Sigma):
    """Expected completed data and summed conditional covariance under N(mu, Sigma)."""
    m, n = z.shape
    xhat = np.empty((m, n))
    csum = np.zeros((n, n))
    for obs, mis, rows in groups:
        g = len(rows)
        zr = z[rows]
        if len(mis) == 0:
            xhat[rows] = zr
            continue
        if len(obs) == 0:
            xhat[np.ix_(rows, mis)] = mu[mis]
            csum[np.ix_(mis, mis)] += g * Sigma[np.ix_(mis, mis)]
            continue
        A = Sigma[np.ix_(obs, obs)] + JITTER * np.eye(len(obs))
        B = Sigma[np.ix_(obs, mis)]
        K = np.linalg.solve(A, B)
        xo = zr[:, obs]
        xhat[np.ix_(rows, obs)] = xo
        xhat[np.ix_(rows, mis)] = mu[mis] + (xo - mu[obs]) @ K
        csum[np.ix_(mis, mis)] += g * (Sigma[np.ix_(mis, mis)] - B.T @ K)
    return xhat, csum


def em_gaussian_covariance(z, mask, shrink=EM_SHRINK, max_iter=EM_MAX_ITER, tol=EM_TOL,
                           time_budget=EM_TIME_BUDGET):
    """EM for N(mu, Sigma) with missing entries (z holds arbitrary values where mask is False).

    Diagonal shrinkage Sigma <- (1-shrink) Sigma + shrink diag(Sigma) is applied in every M-step (a MAP-style
    regulariser). Returns mu, Sigma, completed data (conditional means) and the per-row mean of conditional
    covariances (needed to recover an unbiased second-moment estimate from the completed data).
    """
    m, n = z.shape
    zz = np.where(mask, z, 0.0)
    both = mask.astype(np.float64)
    cnt = np.maximum(both.T @ both, 1.0)
    C = (zz.T @ zz) / cnt
    mu = np.zeros(n)
    Sigma = 0.7 * C + 0.3 * np.eye(n)
    w, V = np.linalg.eigh(0.5 * (Sigma + Sigma.T))
    Sigma = (V * np.maximum(w, 1e-2)) @ V.T
    groups = _pattern_groups(mask)
    t0 = time.time()
    for _ in range(max_iter):
        xhat, csum = _e_step(zz, groups, mu, Sigma)
        mu_new = xhat.mean(0)
        xc = xhat - mu_new
        S = (xc.T @ xc + csum) / m
        S = 0.5 * (S + S.T)
        d = np.diag(S)
        S = (1.0 - shrink) * S + shrink * np.diag(d)
        S[np.diag_indices(n)] = np.maximum(np.diag(S), 1e-3)
        delta = float(np.abs(S - Sigma).max())
        mu, Sigma = mu_new, S
        if delta < tol or (time.time() - t0) > time_budget:
            break
    xhat, csum = _e_step(zz, groups, mu, Sigma)
    return mu, Sigma, xhat, csum / m


def greedy_select_conditional_variance(Sigma, k, lam=0.05, weights=None):
    """Greedy A-optimal design: repeatedly add the benchmark j that most reduces the trace of the posterior
    covariance of the not-yet-selected benchmarks, given noisy observation of the chosen ones.

    R is the current posterior covariance; adding j gives R' = R - R[:, j] R[j, :] / (R[j, j] + lam) and the
    trace reduction over the remaining benchmarks is sum_{i in U, i != j} R[i, j]^2 / (R[j, j] + lam).
    """
    n = Sigma.shape[0]
    R = np.array(Sigma, dtype=np.float64, copy=True)
    avail = np.ones(n, dtype=bool)
    chosen = []
    for _ in range(int(k)):
        diag = np.diag(R).copy()
        col_sum = (R[avail] ** 2).sum(0)
        gain = (col_sum - diag ** 2) / (diag + lam)
        if weights is not None:
            gain = gain * weights
        gain[~avail] = -np.inf
        j = int(np.argmax(gain))
        chosen.append(j)
        avail[j] = False
        r = R[:, j].copy()
        R -= np.outer(r, r) / (diag[j] + lam)
        R = 0.5 * (R + R.T)
    return chosen


def conditional_gaussian_impute(mu, Sigma, selected, x_obs, obs_mask, lam=0.05):
    """Gaussian conditional mean E[x | x_S] = mu + Sigma[:, S] (Sigma_SS + lam I)^-1 (x_S - mu_S), conditioning
    for each row only on the selected benchmarks it actually has. x_obs is [B, k] in standardised units."""
    sel = np.asarray(selected, dtype=int)
    b, n = x_obs.shape[0], Sigma.shape[0]
    pred = np.tile(mu, (b, 1))
    obs_mask = np.asarray(obs_mask, dtype=bool)
    for obs_pos, _, rows in _pattern_groups(obs_mask):
        if len(obs_pos) == 0:
            continue
        cols = sel[obs_pos]
        A = Sigma[np.ix_(cols, cols)] + lam * np.eye(len(cols))
        W = np.linalg.solve(A, Sigma[cols, :])
        pred[rows] = mu + (x_obs[np.ix_(rows, obs_pos)] - mu[cols]) @ W
    return pred


def _build_sigma(S, shrink, rank):
    """Diagonal shrinkage, then optionally a factor-analytic (rank-r + diagonal) approximation that keeps the
    diagonal of the shrunk matrix."""
    S = (1.0 - shrink) * S + shrink * np.diag(np.diag(S))
    if rank is None or rank >= S.shape[0]:
        return S
    w, V = np.linalg.eigh(0.5 * (S + S.T))
    idx = np.argsort(w)[::-1][:rank]
    low = (V[:, idx] * np.maximum(w[idx], 0.0)) @ V[:, idx].T
    d = np.maximum(np.diag(S) - np.diag(low), 1e-3 * np.diag(S))
    out = low.copy()
    out[np.diag_indices(S.shape[0])] = np.diag(low) + d
    return out


# ----------------------------------------------------------------------------------------------------------
# Hyper-parameter tuning by K-fold CV over history models only
# ----------------------------------------------------------------------------------------------------------
def _cv_tune(z, mask, xhat, csum_mean, selected, rng):
    m, n = z.shape
    sel = np.asarray(selected, dtype=int)
    tmask_cols = np.ones(n, dtype=bool)
    tmask_cols[sel] = False
    folds = np.array_split(rng.permutation(m), min(CV_FOLDS, max(2, m // 2)))
    errs = {}
    for fi, va in enumerate(folds):
        tr = np.setdiff1d(np.arange(m), va)
        mu_tr = xhat[tr].mean(0)
        xc = xhat[tr] - mu_tr
        S_tr = xc.T @ xc / len(tr) + csum_mean
        zv = z[va]
        tgt = mask[va] & tmask_cols[None, :]
        groups = _pattern_groups(mask[va][:, sel])
        for a in SHRINK_GRID:
            for r in RANK_GRID:
                Sig = _build_sigma(S_tr, a, r)
                for lam in LAM_GRID:
                    tot = 0.0
                    for obs_pos, _, rows in groups:
                        if len(obs_pos) == 0:
                            pred = np.tile(mu_tr, (len(rows), 1))
                        else:
                            cols = sel[obs_pos]
                            A = Sig[np.ix_(cols, cols)] + lam * np.eye(len(cols))
                            W = np.linalg.solve(A, Sig[cols, :])
                            pred = mu_tr + (zv[np.ix_(rows, cols)] - mu_tr[cols]) @ W
                        tot += float((((pred - zv[rows]) ** 2) * tgt[rows]).sum())
                    errs[(a, r, lam)] = errs.get((a, r, lam), 0.0) + tot
    best = min(errs, key=errs.get)
    return best, errs[best]


def _prepare_history():
    n_chunks = _STATE["n_chunks"]
    parts = [_STATE["chunks"][i] for i in range(n_chunks)]
    values = np.concatenate([p[0] for p in parts]).astype(np.float64)
    mask = np.concatenate([p[1] for p in parts]).astype(bool)
    count = np.maximum(mask.sum(0), 1)
    mean = (values * mask).sum(0) / count
    var = (((values - mean) ** 2) * mask).sum(0) / count
    std = np.where(var > 1e-10, np.sqrt(np.maximum(var, 1e-10)), 1.0)
    z = np.where(mask, (values - mean) / std, 0.0)
    z = np.clip(z, -Z_CLIP, Z_CLIP)
    mu, Sigma, xhat, csum_mean = em_gaussian_covariance(z, mask)
    xc = xhat - xhat.mean(0)
    S_all = xc.T @ xc / z.shape[0] + csum_mean
    S_all = 0.5 * (S_all + S_all.T)
    cover = np.clip(mask.mean(0), 0.05, 1.0)
    _STATE["hist"] = {"mean": mean, "std": std, "z": z, "mask": mask, "xhat": xhat, "csum": csum_mean,
                      "S_all": S_all, "mu": xhat.mean(0), "cover": cover}


def _select_and_fit(k):
    h = _STATE["hist"]
    n = h["z"].shape[1]
    k = int(min(max(k, 1), n))
    # candidate selection recipes: (shrink, rank, selection lambda, coverage exponent)
    recipes = [(0.05, None, 0.05, 1.0), (0.05, None, 0.3, 1.0), (0.05, 5, 0.05, 1.0), (0.05, None, 0.05, 0.0)]
    best = None
    tried = []
    for shrink, rank, lam_sel, cexp in recipes:
        Sig0 = _build_sigma(h["S_all"], shrink, rank)
        sel = greedy_select_conditional_variance(Sig0, k, lam=lam_sel, weights=h["cover"] ** cexp)
        if sel in tried:
            continue
        tried.append(sel)
        rng = np.random.default_rng(_STATE["seed"] + 1000)
        params, err = _cv_tune(h["z"], h["mask"], h["xhat"], h["csum"], sel, rng)
        if best is None or err < best[2]:
            best = (sel, params, err)
    sel, (a, r, lam), _ = best
    Sigma = _build_sigma(h["S_all"], a, r)
    _STATE["model"] = {"mu": h["mu"], "Sigma": Sigma, "lam": lam}
    return [int(j) for j in sel]


def handle(request):
    op = request.get("op")
    if op == "reset":
        _fresh(request["seed"])
        return {"ok": True}
    if op == "load_history":
        shape = tuple(request["shape"])
        _STATE["chunks"][int(request["chunk_index"])] = (
            _decode(request["values_b64"], "<f4", shape), _decode(request["mask_b64"], np.uint8, shape))
        _STATE["n_chunks"] = int(request["n_chunks"])
        _STATE["n_cols"] = int(request["n_cols"])
        return {"ok": True}
    if op == "select":
        k = int(request["k"])
        if "hist" not in _STATE:
            _prepare_history()
        selected = _select_and_fit(k)
        _STATE["selected"] = selected
        return {"selected": selected}
    if op == "predict":
        selected = [int(j) for j in request["selected"]]
        if _STATE.get("selected") != selected:
            raise ValueError("selection mismatch")
        b, k = (int(v) for v in request["shape"])
        values = _decode(request["observed_values_b64"], "<f4", (b, k)).astype(np.float64)
        mask = _decode(request["observed_mask_b64"], np.uint8, (b, k)).astype(bool)
        hist, model = _STATE["hist"], _STATE["model"]
        sel = np.asarray(selected)
        z = (values - hist["mean"][sel]) / hist["std"][sel]
        z = np.clip(np.nan_to_num(z, nan=0.0, posinf=Z_CLIP, neginf=-Z_CLIP), -Z_CLIP, Z_CLIP)
        pred_z = conditional_gaussian_impute(model["mu"], model["Sigma"], selected, z, mask, model["lam"])
        pred = pred_z * hist["std"] + hist["mean"]
        pred = np.nan_to_num(pred, nan=0.0, posinf=0.0, neginf=0.0)
        return {"predictions_b64": _encode(pred.astype("<f4")), "dtype": "float32",
                "shape": [b, int(pred.shape[1])], "encoding": "base64"}
    raise ValueError("unknown op")
