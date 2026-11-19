"""Candidate: wrapper (CV-error) benchmark selection + rank-Gauss transformed, stacked Gaussian imputation.

Entry point: ``handle(request) -> response`` (contract interface ``python_rpc_v1:handle``). Wire contract is
identical to the starter candidate (ops ``reset`` / ``load_history`` / ``select`` / ``predict``; same response
keys). All state lives in this process' memory. numpy only, deterministic given the seed.

Method:
  * two candidate representations of the history matrix: z-scoring and an empirical rank-Gauss (quantile
    normal) map per benchmark (``quantile_normal_transform``); predictions are returned to raw units with
    ``inverse_quantile_transform`` (np.interp over the stored sorted history values) and clipped to the observed
    history range of every benchmark;
  * EM for a multivariate Gaussian with missing entries on each representation (``em_gaussian_covariance``);
  * benchmark selection: candidates from the covariance-trace greedy A-optimal rule
    (``greedy_select_conditional_variance``) and from a greedy forward WRAPPER (``wrapper_forward_select_cv``)
    that minimises K-fold held-out-model error of the conditional-Gaussian predictor (candidates weighted by
    observation coverage). Representation and selection are chosen by history-only CV error in raw units;
  * prediction: per-target non-negative stack (``stack_predictors_nnls``) of Gaussian conditional means at
    several shrinkage levels, per-target ridge on the selected benchmarks (``ridge_selected_predict``), kNN over
    history models (``knn_model_predict``) and the column median (implicit remaining weight), with weights
    fitted on out-of-fold history predictions and regularised toward a pooled global weight vector; a
    calibrated median shrinkage is the fallback when the CV error of the stack exceeds the median baseline.
Every tuned quantity uses HISTORY models only (K-fold over history rows). No new-model information is used
except the observed inputs of ``predict``.

Cycle-3 additions (all optional, wrapped so that any failure/timeout degrades to the incumbent pipeline):
  * a low-rank latent-skill model  T_ij ~ g_j(u_i . v_j + b_j) + eps_j  on the observed history cells, with a
    per-benchmark monotone piecewise-linear link g_j (``monotone_link_fit``), per-benchmark noise variances and a
    Gaussian ridge/prior on u (``fit_latent_skill_model``); rank / ridge / link family are chosen by K-fold
    held-out-model error (``choose_latent_rank_cv``);
  * MAP inference of a new model's latent vector under a Huber (or Student-t) IRLS likelihood and the history-fitted
    Gaussian prior, with a Laplace covariance (``posterior_latent_new_model``); predictions go through the links
    and are clipped to the history range;
  * the latent prediction is an additional member of the per-target NNLS stack (kept only if its CV error beats the
    stack without it);
  * a greedy A-optimal selector on the latent posterior (``select_a_optimal_latent``), a further candidate next to
    the trace and wrapper selectors (chosen by history-only CV error like the others).
"""
import base64
import os
import time
from statistics import NormalDist

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

import numpy as np

EM_SHRINK = 0.02
EM_MAX_ITER = 60
EM_TOL = 1e-4
EM_TIME_BUDGET = 25.0
JITTER = 1e-4
CV_FOLDS = 5
SHRINK_GRID = (0.0, 0.05, 0.15, 0.3)
RANK_GRID = (2, 4, 6, 10, None)
LAM_GRID = (0.003, 0.03, 0.1, 0.3)
QUICK_SHRINKS = (0.05, 0.2)
QUICK_RANKS = (None,)
QUICK_LAMS = (0.03, 0.15, 0.5)
Z_CLIP = 8.0
WRAP_LAM = 0.1
GAUSS_SHRINKS = (0.0, 0.15, 0.3)
KNN_NEIGHBORS = (5, 15)
RIDGE_LAM = 5.0
BASE_NAMES = ("gauss_s0", "gauss_s15", "gauss_s30", "ridge", "knn5", "knn15")  # + implicit column median
STACK_TAUS = (0.0, 0.05, 0.25, 1.0, 5.0, 1e5)
# candidate selections: ("trace", (shrink, rank, lambda, coverage exponent)) or ("wrap", coverage exponent)
CANDIDATES = (("trace", (0.05, None, 0.05, 1.0)), ("wrap", 0.0), ("trace", (0.05, None, 0.3, 1.0)),
              ("wrap", 1.0), ("trace", (0.05, 5, 0.05, 1.0)), ("trace", (0.05, None, 0.05, 0.0)),
              ("alat", (2, 1.0, 1.0)), ("alat", (3, 1.0, 1.0)))  # ("alat", (rank, ridge, coverage exponent))
PLAN = ((("q", 0), ("q", 1), ("z", 0), ("z", 1), ("q", 6)),
        (("z", 6), ("q", 2), ("q", 3), ("z", 2), ("z", 3), ("q", 7), ("q", 4), ("q", 5), ("z", 4), ("z", 5)))
# latent-skill member ------------------------------------------------------------------------------------------
LAT_KNOTS = 5
LAT_ITERS = 8
LAT_LINK_RHO = 3.0
LAT_MIN_OBS = 12
LAT_SIG_FLOOR = 0.02
LAT_POST_ITERS = 8
LAT_GRID = ((2, 1.0, "monotone"), (1, 1.0, "monotone"), (3, 1.0, "monotone"), (2, 1.0, "linear"),
            (2, 4.0, "monotone"), (3, 4.0, "monotone"))  # (rank, ridge on u/v, link family)
LAT_BUDGET = 60.0          # seconds for the whole latent stage inside the stack fit
LAT_MIN_GAIN = 0.002       # relative CV-error gain required to keep the latent member in the stack
HUBER_C = 1.345
STUDENT_NU = 4.0
LATENT_OPTS = {"enabled": True, "links": None, "likelihood": "huber"}  # offline ablation switches
SELECT_CAND_BUDGET = 70.0   # seconds after which optional candidates are skipped
FULL_TUNE_BUDGET = 150.0    # after this many seconds the final tuning uses the quick grid
STACK_BUDGET = 210.0        # after this many seconds stacking is skipped (Gaussian-only model)

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
# per-benchmark transforms
# ----------------------------------------------------------------------------------------------------------
def zscore_transform(values, mask):
    """z-score every column by its observed mean/std. Returns T (0 at missing cells) and per-column params
    ("z", mean, std)."""
    n = values.shape[1]
    count = np.maximum(mask.sum(0), 1)
    mean = (values * mask).sum(0) / count
    var = (((values - mean) ** 2) * mask).sum(0) / count
    std = np.where(var > 1e-10, np.sqrt(np.maximum(var, 1e-10)), 1.0)
    T = np.where(mask, np.clip((values - mean) / std, -Z_CLIP, Z_CLIP), 0.0)
    params = [("z", float(mean[j]), float(std[j])) for j in range(n)]
    return T, params


def quantile_normal_transform(values, mask, min_obs=8):
    """Empirical rank-Gauss map per benchmark: average ranks, p=(r-0.5)/n, Phi^-1(p). The unique sorted observed
    values and their normal scores are stored so that the map can be applied to new values and inverted with
    np.interp. Columns with < min_obs observations, < 4 distinct values or ~zero variance fall back to z-scoring."""
    n = values.shape[1]
    T, params = zscore_transform(values, mask)
    nd = NormalDist()
    for j in range(n):
        obs = values[mask[:, j], j]
        if obs.size < min_obs or float(np.var(obs)) < 1e-10:
            continue
        uv, inv, cnt = np.unique(obs, return_inverse=True, return_counts=True)
        if uv.size < 4:
            continue
        inv = np.asarray(inv).reshape(-1)
        avg_rank = (np.cumsum(cnt) - cnt) + (cnt + 1.0) / 2.0
        p = (avg_rank - 0.5) / obs.size
        us = np.array([nd.inv_cdf(float(q)) for q in p])
        T[mask[:, j], j] = us[inv]
        params[j] = ("q", uv.astype(np.float64), us)
    return T, params


def _forward_columns(params, cols, x):
    """Apply the stored transform of benchmark cols[c] to column c of x (finite values assumed)."""
    out = np.zeros(x.shape)
    for c, j in enumerate(cols):
        p = params[int(j)]
        if p[0] == "q":
            out[:, c] = np.interp(x[:, c], p[1], p[2])
        else:
            out[:, c] = np.clip((x[:, c] - p[1]) / p[2], -Z_CLIP, Z_CLIP)
    return out


def inverse_quantile_transform(params, t):
    """Map transformed predictions [B, N] back to raw benchmark units: np.interp over the stored (score ->
    sorted history value) grid for quantile columns (so outputs stay inside the history range), affine for
    z-scored columns."""
    out = np.empty(t.shape)
    for j, p in enumerate(params):
        if p[0] == "q":
            out[:, j] = np.interp(t[:, j], p[2], p[1])
        else:
            out[:, j] = t[:, j] * p[2] + p[1]
    return out


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
    for each row only on the selected benchmarks it actually has. x_obs is [B, k] in transformed units."""
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
# representation of the history matrix
# ----------------------------------------------------------------------------------------------------------
def build_rep(values, mask, kind, em_budget=EM_TIME_BUDGET):
    """Transform the history (kind 'q' = rank-Gauss, 'z' = z-score), fit the EM Gaussian and store everything
    needed for selection, CV and prediction."""
    values = np.asarray(values, dtype=np.float64)
    mask = np.asarray(mask, dtype=bool)
    values = np.where(mask, values, 0.0)
    if kind == "q":
        T, params = quantile_normal_transform(values, mask)
    else:
        T, params = zscore_transform(values, mask)
    mu, Sigma, xhat, csum = em_gaussian_covariance(T, mask, time_budget=em_budget)
    xc = xhat - xhat.mean(0)
    S_all = xc.T @ xc / T.shape[0] + csum
    S_all = 0.5 * (S_all + S_all.T)
    n = T.shape[1]
    nobs = mask.sum(0)
    count = np.maximum(nobs, 1)
    mean = (values * mask).sum(0) / count
    var = (((values - mean) ** 2) * mask).sum(0) / count
    std = np.where(var > 1e-10, np.sqrt(np.maximum(var, 1e-10)), 1.0)
    lo = np.where(nobs > 0, np.where(mask, values, np.inf).min(0), 0.0)
    hi = np.where(nobs > 0, np.where(mask, values, -np.inf).max(0), 0.0)
    rawmed = np.zeros(n)
    med = np.zeros(n)
    for j in range(n):
        if nobs[j] > 0:
            rawmed[j] = float(np.median(values[mask[:, j], j]))
            med[j] = float(np.median(T[mask[:, j], j]))
    return {"kind": kind, "values": values, "T": T, "mask": mask, "params": params, "xhat": xhat, "csum": csum,
            "S_all": S_all, "mu": xhat.mean(0), "med": med, "rawmed": rawmed, "lo": lo, "hi": hi, "mean": mean,
            "std": std, "cover": np.clip(mask.mean(0), 0.05, 1.0)}


def _make_folds(m, seed, n_folds=CV_FOLDS):
    rng = np.random.default_rng(int(seed))
    return np.array_split(rng.permutation(m), min(n_folds, max(2, m // 2)))


def _fold_cov(rp, rows):
    """Mean and covariance of the EM-completed data restricted to training rows."""
    xh = rp["xhat"][rows]
    mu = xh.mean(0)
    xc = xh - mu
    S = xc.T @ xc / len(rows) + rp["csum"]
    return mu, 0.5 * (S + S.T)


# ----------------------------------------------------------------------------------------------------------
# wrapper (CV-error) forward selection
# ----------------------------------------------------------------------------------------------------------
def wrapper_forward_select_cv(rp, k, alpha=0.0, lam=WRAP_LAM, shrink=0.05, seed=0, deadline=None,
                              max_cand=250, n_folds=CV_FOLDS):
    """Greedy forward selection of k benchmarks minimising the K-fold held-out-model squared error of the
    conditional-Gaussian predictor. For each fold the training-fold covariance gives the posterior covariance R;
    held-out residuals E (zero at unobserved cells) are updated sequentially. Adding candidate j changes the
    residual of target i on validation row r by -g_ij v_rj with g_ij = R_ij / (R_jj + lam) and v_rj = E_rj, so the
    summed squared error after adding j is  sum_i [A_i - 2 g_ij B_ij + g_ij^2 C_ij]  with
    A = sum_r E^2, B = E^T E, C = M^T E^2 (M = observation mask) -- all candidates are scored with batched matrix
    products. A validation row that lacks j contributes no innovation, so poorly covered benchmarks gain less;
    candidate gains are additionally weighted by cover**alpha. Returns None if ``deadline`` is exceeded."""
    T, M = rp["T"], rp["mask"]
    m, n = T.shape
    k = int(min(k, n))
    cover = rp["cover"] ** alpha
    S0 = _build_sigma(rp["S_all"], shrink, None)
    if n > max_cand:  # pre-filter candidates by coverage-weighted covariance-trace gain
        d0 = np.diag(S0)
        g0 = ((S0 ** 2).sum(0) - d0 ** 2) / (d0 + lam) * rp["cover"]
        cand = np.sort(np.argsort(g0)[::-1][:max_cand])
    else:
        cand = np.arange(n)
    ar = np.arange(len(cand))
    states = []
    for va in _make_folds(m, seed + 3000, n_folds):
        tr = np.setdiff1d(np.arange(m), va)
        mu, S = _fold_cov(rp, tr)
        R = _build_sigma(S, shrink, None)
        Mv = M[va].astype(np.float64)
        E = Mv * (T[va] - mu)
        states.append([R, E, Mv])
    avail = np.ones(n, dtype=bool)
    chosen = []
    for _ in range(k):
        if deadline is not None and time.time() > deadline:
            return None
        gain = np.zeros(len(cand))
        for R, E, Mv in states:
            dj = np.diag(R)[cand] + lam
            G = R[:, cand] / dj[None, :]
            Ec = E[:, cand]
            Bm = E.T @ Ec
            Cm = Mv.T @ (Ec ** 2)
            term = 2.0 * G * Bm - G * G * Cm
            term[~avail, :] = 0.0
            term[cand, ar] = 0.0
            gain += term.sum(0) + (Ec ** 2).sum(0)
        gain = gain * cover[cand]
        gain[~avail[cand]] = -np.inf
        if not np.isfinite(gain.max()):
            break
        j = int(cand[int(np.argmax(gain))])
        chosen.append(j)
        avail[j] = False
        for st in states:
            R, E, Mv = st
            r = R[:, j].copy()
            den = r[j] + lam
            E -= Mv * (E[:, j].copy()[:, None] * (r / den)[None, :])
            R -= np.outer(r, r) / den
            st[0] = 0.5 * (R + R.T)
    if len(chosen) < k:  # candidate pool exhausted: fill with the best-covered remaining benchmarks
        rest = [int(j) for j in np.argsort(-rp["cover"]) if avail[j]]
        chosen.extend(rest[:k - len(chosen)])
    return chosen


# ----------------------------------------------------------------------------------------------------------
# hyper-parameter tuning by K-fold CV over history models only
# ----------------------------------------------------------------------------------------------------------
def _cv_tune(rp, selected, folds, shrinks=SHRINK_GRID, ranks=RANK_GRID, lams=LAM_GRID):
    """Pick (shrink, rank, lambda) of the Gaussian conditional mean by held-out-model error (transformed
    space)."""
    z, mask = rp["T"], rp["mask"]
    m, n = z.shape
    sel = np.asarray(selected, dtype=int)
    tmask_cols = np.ones(n, dtype=bool)
    tmask_cols[sel] = False
    errs = {}
    for va in folds:
        tr = np.setdiff1d(np.arange(m), va)
        mu_tr, S_tr = _fold_cov(rp, tr)
        zv = z[va]
        tgt = mask[va] & tmask_cols[None, :]
        groups = _pattern_groups(mask[va][:, sel])
        for a in shrinks:
            for r in ranks:
                Sig = _build_sigma(S_tr, a, r)
                for lam in lams:
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


def _cv_raw_error(rp, selected, params, folds):
    """Held-out-model error of the Gaussian predictor in RAW benchmark units (divided by the history std of
    each benchmark, clipped to the history range) -- comparable across representations and selections."""
    a, r, lam = params
    sel = np.asarray(selected, dtype=int)
    m = rp["T"].shape[0]
    tot, cnt = 0.0, 0.0
    for va in folds:
        tr = np.setdiff1d(np.arange(m), va)
        mu, S = _fold_cov(rp, tr)
        Sig = _build_sigma(S, a, r)
        pred_t = conditional_gaussian_impute(mu, Sig, sel, rp["T"][va][:, sel], rp["mask"][va][:, sel], lam)
        pred = np.clip(inverse_quantile_transform(rp["params"], pred_t), rp["lo"], rp["hi"])
        tgt = rp["mask"][va].copy()
        tgt[:, sel] = False
        err = ((pred - rp["values"][va]) / rp["std"]) ** 2
        tot += float((err * tgt).sum())
        cnt += float(tgt.sum())
    return tot / max(cnt, 1.0)


# ----------------------------------------------------------------------------------------------------------
# monotone-link latent-skill model
# ----------------------------------------------------------------------------------------------------------
def _pav(c, w):
    """Weighted pool-adjacent-violators: the non-decreasing sequence closest to c in weighted least squares."""
    vals, wts, cnt = [], [], []
    for ci, wi in zip(c, w):
        vals.append(float(ci))
        wts.append(float(wi))
        cnt.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            wt = wts[-2] + wts[-1]
            v = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / wt
            cn = cnt[-2] + cnt[-1]
            vals[-2:] = [v]
            wts[-2:] = [wt]
            cnt[-2:] = [cn]
    return np.repeat(np.asarray(vals), cnt)


def monotone_link_fit(s, y, knots=LAT_KNOTS, rho=LAT_LINK_RHO, monotone=True):
    """Fit a piecewise-linear link y ~ g(s) on ``knots`` quantile knots of s. The knot values solve a ridge
    least-squares problem pulled toward the OLS line (strength rho), are projected to a non-decreasing sequence with
    PAV and blended 80/20 with the line so that every slope stays strictly positive. monotone=False returns the
    OLS line (positive slope) on the same knots. Returns (knot positions t [K], knot values c [K])."""
    K = int(knots)
    t = np.quantile(s, np.linspace(0.0, 1.0, K))
    gap = 0.02 * float(t[-1] - t[0]) + 1e-3
    for i in range(1, K):
        t[i] = max(t[i], t[i - 1] + gap)
    sm, ym = float(s.mean()), float(y.mean())
    vs = float(((s - sm) ** 2).mean())
    slope = float(np.clip(((s - sm) * (y - ym)).mean() / max(vs, 1e-9), 0.1, 5.0))
    c_lin = ym + slope * (t - sm)
    if not monotone:
        return t, c_lin
    pos = np.clip(np.searchsorted(t, s, side="right") - 1, 0, K - 2)
    lam = np.clip((s - t[pos]) / (t[pos + 1] - t[pos]), 0.0, 1.0)
    H = np.zeros((s.size, K))
    rr = np.arange(s.size)
    H[rr, pos] = 1.0 - lam
    H[rr, pos + 1] = lam
    HtH = H.T @ H
    c = np.linalg.solve(HtH + rho * np.eye(K), H.T @ y + rho * c_lin)
    c = _pav(c, np.diag(HtH) + 1e-6)
    return t, 0.8 * c + 0.2 * c_lin


def _finish_links(t, c):
    sl = np.clip(np.diff(c, axis=1) / np.maximum(np.diff(t, axis=1), 1e-6), 0.02, 8.0)
    return {"t": t, "c": c, "sl": sl}


def _fit_links(S, T, M, monotone=True):
    """Fit every benchmark's link on its observed cells; sparse columns keep the identity link."""
    n = T.shape[1]
    ident = np.linspace(-4.0, 4.0, LAT_KNOTS)
    t = np.tile(ident, (n, 1))
    c = t.copy()
    for j in range(n):
        idx = M[:, j]
        if idx.sum() >= LAT_MIN_OBS:
            t[j], c[j] = monotone_link_fit(S[idx, j], T[idx, j], LAT_KNOTS, monotone=monotone)
    return _finish_links(t, c)


def _link_eval(links, s, cols=None):
    """Evaluate the piecewise-linear links (linear extrapolation with the end slopes) and their slopes at s
    [B, nc] (column c of s belongs to benchmark cols[c], default all)."""
    t, c, sl = links["t"], links["c"], links["sl"]
    if cols is not None:
        t, c, sl = t[cols], c[cols], sl[cols]
    idx = (s[:, :, None] > t[None, :, 1:-1]).sum(axis=2)
    jj = np.arange(t.shape[0])[None, :]
    slope = sl[jj, idx]
    return c[jj, idx] + slope * (s - t[jj, idx]), slope


def _svd_init(X):
    mean = X.mean(0)
    Uf, sv, Vt = np.linalg.svd(X - mean, full_matrices=False)
    return mean, Uf, sv, Vt


def fit_latent_skill_model(T, M, rank, lam=1.0, link="monotone", n_iter=LAT_ITERS, deadline=None, X0=None,
                           svd=None):
    """Alternating Gauss-Newton fit of  T_ij ~ g_j(u_i . v_j + b_j) + eps_j,  eps_j ~ N(0, sigma_j^2),  on the
    observed cells (M). Initialised from the SVD of the completed matrix X0 (or ``svd`` = _svd_init output), g_j
    starts as the OLS line. Each sweep: (1) linearise the links and solve the weighted ridge problems for every
    u_i (weights g'^2 / sigma_j^2), (2) the same for every [v_j, b_j], (3) refit the monotone links, (4) update
    sigma_j^2 from the residuals. Ridge lam acts as a N(0, 1/lam I) prior on u and v. link = "linear" keeps the
    links affine (ablation). Raises TimeoutError past ``deadline``."""
    T = np.asarray(T, dtype=np.float64)
    M = np.asarray(M, dtype=bool)
    m, n = T.shape
    Mf = M.astype(np.float64)
    if svd is None:
        svd = _svd_init(T if X0 is None else X0)
    mean, Uf, sv, Vt = svd
    r = int(max(1, min(rank, len(sv), m - 1)))
    U = Uf[:, :r] * np.sqrt(m)
    V = Vt[:r].T * (sv[:r] / np.sqrt(m))[None, :]
    b = mean.copy()
    monotone = link != "linear"
    S = U @ V.T + b
    links = _fit_links(S, T, M, monotone)
    sig2 = np.full(n, 0.3)
    eye = np.eye(r)
    pen = np.diag(np.r_[np.full(r, float(lam)), 1e-3])[None]
    for _ in range(int(n_iter)):
        if deadline is not None and time.time() > deadline:
            raise TimeoutError("latent fit deadline")
        g, gp = _link_eval(links, S)
        w = Mf * gp ** 2 / sig2[None, :]
        z = S + (T - g) / gp
        A = np.einsum("ij,jr,jc->irc", w, V, V, optimize=True) + float(lam) * eye[None]
        rhs = np.einsum("ij,jr->ir", w * (z - b[None, :]), V, optimize=True)
        U = np.linalg.solve(A, rhs[:, :, None])[:, :, 0]
        S = U @ V.T + b
        g, gp = _link_eval(links, S)
        w = Mf * gp ** 2 / sig2[None, :]
        z = S + (T - g) / gp
        U1 = np.hstack([U, np.ones((m, 1))])
        A = np.einsum("ij,ir,ic->jrc", w, U1, U1, optimize=True) + pen
        rhs = np.einsum("ij,ir->jr", w * z, U1, optimize=True)
        rhs[:, r] += 1e-3 * mean
        sol = np.linalg.solve(A, rhs[:, :, None])[:, :, 0]
        V, b = sol[:, :r], sol[:, r]
        S = U @ V.T + b
        links = _fit_links(S, T, M, monotone)
        g, _ = _link_eval(links, S)
        sig2 = np.maximum(((Mf * (T - g) ** 2).sum(0) + 0.4) / (Mf.sum(0) + 2.0), LAT_SIG_FLOOR)
    g, gp = _link_eval(links, S)
    cnt = Mf.sum(0)
    slope = np.where(cnt > 0, (gp * Mf).sum(0) / np.maximum(cnt, 1.0), 1.0)
    nobs = cnt > 0
    tlo = np.where(nobs, np.where(M, T, np.inf).min(0), -Z_CLIP)
    thi = np.where(nobs, np.where(M, T, -np.inf).max(0), Z_CLIP)
    Lam = U.T @ U / m + 1e-3 * eye
    return {"U": U, "V": V, "b": b, "links": links, "sig2": sig2, "Lam": 0.5 * (Lam + Lam.T), "slope": slope,
            "tlo": tlo, "thi": thi, "rank": r, "lam": float(lam), "link": link}


def _robust_terms(res, likelihood):
    """IRLS weights and per-cell loss of standardised residuals: huber (c=1.345), student (nu=4), or gaussian."""
    a = np.abs(res)
    if likelihood == "huber":
        w = np.where(a <= HUBER_C, 1.0, HUBER_C / np.maximum(a, 1e-12))
        loss = np.where(a <= HUBER_C, 0.5 * a * a, HUBER_C * (a - 0.5 * HUBER_C))
    elif likelihood == "student":
        w = (STUDENT_NU + 1.0) / (STUDENT_NU + res * res)
        loss = 0.5 * (STUDENT_NU + 1.0) * np.log1p(res * res / STUDENT_NU)
    else:
        w = np.ones_like(res)
        loss = 0.5 * res * res
    return w, loss


def posterior_latent_new_model(model, sel, xq, qmask, likelihood=None, n_iter=LAT_POST_ITERS):
    """MAP latent vector u of each new model from its observed selected benchmarks.

    Penalised objective  sum_j rho((x_j - g_j(u.v_j + b_j)) / sigma_j) + 1/2 u' Lambda^-1 u  with rho the Huber
    (or Student-t / Gaussian) loss and Lambda the history-fitted prior covariance of u. Solved by Gauss-Newton on
    the link with IRLS weights and a backtracking line search; the Laplace covariance is the inverse of the final
    weighted Gauss-Newton Hessian. xq [B, k] holds the (transformed) observed values, qmask [B, k] their
    availability. Returns (pred_t [B, N] in transformed units, clipped to each benchmark's history range;
    cov [B, r, r]; U [B, r])."""
    likelihood = likelihood or LATENT_OPTS.get("likelihood", "huber")
    sel = np.asarray(sel, dtype=int)
    V, b, links, sig2 = model["V"], model["b"], model["links"], model["sig2"]
    Lam = model["Lam"]
    B, r = xq.shape[0], V.shape[1]
    Linv = np.linalg.inv(Lam)
    eye = np.eye(r)
    U = np.zeros((B, r))
    cov = np.tile(Lam, (B, 1, 1))
    for i in range(B):
        have = np.asarray(qmask[i], dtype=bool)
        if not have.any():
            continue
        cols = sel[have]
        x = np.asarray(xq[i, have], dtype=np.float64)
        Vc, bc, sg = V[cols], b[cols], np.sqrt(sig2[cols])

        def objective(u):
            gg, _ = _link_eval(links, (Vc @ u + bc)[None, :], cols)
            _, lo = _robust_terms((x - gg[0]) / sg, likelihood)
            return float(lo.sum() + 0.5 * u @ Linv @ u)

        u = np.zeros(r)
        f0 = objective(u)
        A = Linv.copy()
        for _ in range(int(n_iter)):
            gg, gp = _link_eval(links, (Vc @ u + bc)[None, :], cols)
            res = (x - gg[0]) / sg
            w, _ = _robust_terms(res, likelihood)
            J = (gp[0] / sg)[:, None] * Vc
            A = Linv + J.T @ (w[:, None] * J)
            step = np.linalg.solve(A + 1e-8 * eye, J.T @ (w * res) - Linv @ u)
            moved = False
            for a in (1.0, 0.5, 0.25):
                f1 = objective(u + a * step)
                if f1 <= f0:
                    u, f0, moved = u + a * step, f1, True
                    break
            if not moved or float(np.abs(step).max()) < 1e-4:
                break
        gg, gp = _link_eval(links, (Vc @ u + bc)[None, :], cols)
        w, _ = _robust_terms((x - gg[0]) / sg, likelihood)
        J = (gp[0] / sg)[:, None] * Vc
        A = Linv + J.T @ (w[:, None] * J)
        U[i] = u
        cov[i] = np.linalg.inv(A + 1e-8 * eye)
    g_all, _ = _link_eval(links, U @ V.T + b[None, :])
    pred_t = np.clip(g_all, model["tlo"][None, :], model["thi"][None, :])
    return pred_t, cov, U


def _full_latent(rp, cfg, deadline=None):
    """Latent model fitted on all history rows of representation rp (cached per configuration)."""
    cache = rp.setdefault("lat_cache", {})
    if cfg not in cache:
        rank, lam, link = cfg
        cache[cfg] = fit_latent_skill_model(rp["T"], rp["mask"], rank, lam, link, deadline=deadline, X0=rp["xhat"])
    return cache[cfg]


def choose_latent_rank_cv(rp, sel, folds, deadline, grid=None):
    """Pick (rank, ridge, link) of the latent model by K-fold held-out-model error: every held-out model reveals
    only its selected cells; the error is the squared error in transformed units over its observed non-selected
    cells. Returns (best cfg, its out-of-fold predictions [m, N], {cfg: error}); (None, None, errs) if no
    configuration finished before ``deadline``."""
    grid = LAT_GRID if grid is None else grid
    links_ok = LATENT_OPTS.get("links")
    if links_ok is not None:
        grid = tuple(c for c in grid if c[2] in links_ok)
    T, M = rp["T"], rp["mask"]
    m, n = T.shape
    sel = np.asarray(sel, dtype=int)
    tmask = M.copy()
    tmask[:, sel] = False
    trs = [np.setdiff1d(np.arange(m), va) for va in folds]
    svds = [_svd_init(rp["xhat"][tr]) for tr in trs]
    best, errs = None, {}
    for cfg in grid:
        if time.time() > deadline:
            break
        rank, lam, link = cfg
        P = np.zeros((m, n))
        try:
            for f, va in enumerate(folds):
                mod = fit_latent_skill_model(T[trs[f]], M[trs[f]], rank, lam, link, deadline=deadline, svd=svds[f])
                P[va] = posterior_latent_new_model(mod, sel, T[va][:, sel], M[va][:, sel])[0]
        except TimeoutError:
            break
        err = float((((P - T) ** 2) * tmask).sum())
        if not np.isfinite(err):
            continue
        errs[cfg] = err
        if best is None or err < best[0]:
            best = (err, cfg, P)
    if best is None:
        return None, None, errs
    return best[1], best[2], errs


def select_a_optimal_latent(lat, k, cover=None, cexp=1.0):
    """Greedy A-optimal design on the latent posterior. With effective loadings L_j = g'_j v_j (mean link slope) and
    noise precisions N_j = cover_j^cexp / sigma_j^2, the posterior covariance of u after observing S is
    P_S = (Lambda^-1 + L_S' N_S L_S)^-1; the criterion is the target-weighted prediction-variance trace
    sum_{i not in S} w_i L_i' P_S L_i (w_i = coverage of benchmark i). Each step adds the benchmark with the largest
    exact reduction (Sherman-Morrison rank-one update of P and of the target second-moment matrix W)."""
    V = lat["V"]
    L = V * lat["slope"][:, None]
    n, r = L.shape
    cov = np.ones(n) if cover is None else np.asarray(cover, dtype=np.float64)
    Ne = cov ** cexp / lat["sig2"]
    wt = cov
    P = lat["Lam"].copy()
    W = (L * wt[:, None]).T @ L
    avail = np.ones(n, dtype=bool)
    chosen = []
    for _ in range(int(min(k, n))):
        PL = P @ L.T
        q = np.einsum("jr,rj->j", L, PL)
        den = 1.0 + Ne * q
        quad = np.einsum("rj,rj->j", PL, W @ PL)
        gain = (Ne * quad + wt * q) / den
        gain[~avail] = -np.inf
        j = int(np.argmax(gain))
        chosen.append(j)
        avail[j] = False
        P = P - Ne[j] * np.outer(PL[:, j], PL[:, j]) / den[j]
        P = 0.5 * (P + P.T)
        W = W - wt[j] * np.outer(L[j], L[j])
    return chosen


# ----------------------------------------------------------------------------------------------------------
# base predictors and the NNLS stack
# ----------------------------------------------------------------------------------------------------------
def ridge_selected_fit(Xs, T, M, lam=RIDGE_LAM):
    """Per-target ridge regression of every benchmark on the (completed) selected benchmarks, fitted on the rows
    where the target is observed. Batched through np.linalg.solve. Returns beta [k+1, N] (last row = intercept)."""
    m, k = Xs.shape
    n = T.shape[1]
    X1 = np.hstack([Xs, np.ones((m, 1))])
    Mf = M.astype(np.float64)
    outer = (X1[:, :, None] * X1[:, None, :]).reshape(m, (k + 1) ** 2)
    G = (Mf.T @ outer).reshape(n, k + 1, k + 1)
    rhs = (Mf * T).T @ X1
    pen = np.full(k + 1, float(lam))
    pen[-1] = 0.5
    G = G + np.diag(pen)[None]
    beta = np.linalg.solve(G, rhs[:, :, None])[:, :, 0]
    return beta.T


def ridge_selected_predict(beta, Xq):
    """Apply ridge coefficients [k+1, N] to selected-benchmark inputs Xq [B, k]."""
    return np.hstack([Xq, np.ones((Xq.shape[0], 1))]) @ beta


def knn_model_predict(Xq, qmask, Xtr, Ttr, Mtr, n_neighbors, med, chunk=128):
    """Distance-weighted kNN over history models. Distance = mean squared difference over the selected
    benchmarks the query model has (training rows use their EM-completed selected values); the prediction for
    benchmark i averages the neighbours that observed i (weights 1/(d+0.05)); falls back to the column median
    when no neighbour observed i or the query has no observed selected benchmark."""
    b, k = Xq.shape
    m, n = Ttr.shape
    out = np.tile(med, (b, 1))
    nn = int(min(max(n_neighbors, 1), m))
    TM = Ttr * Mtr
    Mf = Mtr.astype(np.float64)
    qm = qmask.astype(np.float64)
    nobs = qm.sum(1)
    for s in range(0, b, chunk):
        e = min(b, s + chunk)
        D = np.zeros((e - s, m))
        for c in range(k):
            D += qm[s:e, c][:, None] * (Xq[s:e, c][:, None] - Xtr[None, :, c]) ** 2
        D /= np.maximum(nobs[s:e], 1.0)[:, None]
        if nn < m:
            idx = np.argpartition(D, nn - 1, axis=1)[:, :nn]
        else:
            idx = np.tile(np.arange(m), (e - s, 1))
        dn = np.take_along_axis(D, idx, axis=1)
        w = 1.0 / (dn + 0.05)
        num = np.einsum("bj,bjn->bn", w, TM[idx])
        den = np.einsum("bj,bjn->bn", w, Mf[idx])
        pred = np.where(den > 1e-9, num / np.maximum(den, 1e-12), med[None, :])
        out[s:e] = np.where((nobs[s:e] > 0)[:, None], pred, med[None, :])
    return out


def _fit_base(rp, rows, sel, params):
    """Fit all base predictors on the given history rows."""
    a, r, lam = params
    mu, S = _fold_cov(rp, rows)
    sigmas = [_build_sigma(S, sh, r) for sh in GAUSS_SHRINKS]
    Xs = rp["xhat"][rows][:, sel]
    beta = ridge_selected_fit(Xs, rp["T"][rows], rp["mask"][rows])
    return {"mu": mu, "sigmas": sigmas, "lam": lam, "beta": beta, "Xs": Xs, "T": rp["T"][rows],
            "M": rp["mask"][rows], "sel": np.asarray(sel, dtype=int), "med": rp["med"]}


def _base_predictions(fit, xq, qmask):
    """Base predictions [len(BASE_NAMES), B, N] in transformed space (column median is implicit)."""
    sel = fit["sel"]
    pg = [conditional_gaussian_impute(fit["mu"], S, sel, xq, qmask, fit["lam"]) for S in fit["sigmas"]]
    xin = np.where(qmask, xq, pg[1][:, sel])  # missing selected inputs <- Gaussian conditional means
    pr = ridge_selected_predict(fit["beta"], xin)
    pk = [knn_model_predict(xq, qmask, fit["Xs"], fit["T"], fit["M"], nn, fit["med"]) for nn in KNN_NEIGHBORS]
    return np.stack(pg + [pr] + pk, axis=0)


def _nnls_cd(G, c, w0, rho, sweeps=80):
    """Batched coordinate descent for  min_w>=0  1/2 w'(G + rho I)w - (c + rho w0)'w  (a ridge pull toward w0),
    followed by a rescale so that sum(w) <= 1. G [n,B,B], c [n,B], w0 [B] or [n,B], rho [n]."""
    n, B = c.shape
    A = G + rho[:, None, None] * np.eye(B)[None]
    lin = c + rho[:, None] * w0
    dg = np.maximum(np.einsum("ibb->ib", A), 1e-12)
    w = np.maximum(np.broadcast_to(w0, (n, B)).copy(), 0.0)
    for _ in range(sweeps):
        for b in range(B):
            num = lin[:, b] - np.einsum("ic,ic->i", A[:, b, :], w) + dg[:, b] * w[:, b]
            w[:, b] = np.maximum(num / dg[:, b], 0.0)
    tot = w.sum(1)
    return w * np.minimum(1.0, 1.0 / np.maximum(tot, 1e-12))[:, None]


def stack_predictors_nnls(P, Y, tmask, folds, taus=STACK_TAUS, names=BASE_NAMES):
    """Per-target non-negative stacking weights for the base predictors, from out-of-fold predictions.

    P [B, m, n] and Y [m, n] are deviations from the column median (so the median predictor is the zero vector
    and receives the remaining weight 1 - sum(w)); tmask [m, n] marks observed non-selected target cells. Each
    target's weights solve a non-negative least-squares problem regularised toward the pooled global weights
    (strength tau * trace(G_i)/B); tau is chosen by cross-validation over the row folds (the Gram matrices are
    additive over rows, so this is cheap). If the pooled CV error of the stack exceeds the median baseline, the
    weights are shrunk toward the median by the CV-optimal calibrated factor; if the best single base predictor
    beats the stack in CV, it is used alone. Returns (W [n, B], info)."""
    B, m, n = P.shape
    tm = tmask.astype(np.float64)
    Pm = P * tm[None]
    Ym = Y * tm
    Gs, cs = [], []
    yy = 0.0
    for f in folds:
        Pf = Pm[:, f, :]
        Gs.append(np.einsum("bri,cri->ibc", Pf, Pf, optimize=True))
        cs.append(np.einsum("bri,ri->ib", Pf, Ym[f], optimize=True))
        yy += float((Ym[f] ** 2).sum())
    Gsum = sum(Gs)
    csum = sum(cs)

    def pooled_w(Gt, ct):
        return _nnls_cd(Gt.sum(0, keepdims=True), ct.sum(0, keepdims=True), np.zeros(B), np.array([1e-9]))[0]

    def rho_for(Gt, tau):
        return tau * np.einsum("ibb->i", Gt) / B + 1e-9

    glob = [pooled_w(Gsum - Gs[g], csum - cs[g]) for g in range(len(folds))]
    stats = {}
    for tau in taus:
        A1, A2 = 0.0, 0.0
        for g in range(len(folds)):
            Gtr, ctr = Gsum - Gs[g], csum - cs[g]
            W = _nnls_cd(Gtr, ctr, glob[g], rho_for(Gtr, tau))
            A2 += float(np.einsum("ib,ibc,ic->", W, Gs[g], W, optimize=True))
            A1 += float((cs[g] * W).sum())
        stats[tau] = (A1, A2)
    best_tau = min(stats, key=lambda t: stats[t][1] - 2.0 * stats[t][0])
    A1, A2 = stats[best_tau]
    err_stack = A2 - 2.0 * A1 + yy
    s = 1.0
    if err_stack > yy and A2 > 1e-12:  # worse than the median baseline: calibrated shrinkage toward the median
        s = float(np.clip(A1 / A2, 0.0, 1.0))
        err_stack = s * s * A2 - 2.0 * s * A1 + yy
    single = [float((Gsum[:, b, b] - 2.0 * csum[:, b]).sum()) + yy for b in range(B)]
    b_best = int(np.argmin(single))
    W = _nnls_cd(Gsum, csum, pooled_w(Gsum, csum), rho_for(Gsum, best_tau)) * s
    used = "stack"
    if single[b_best] < err_stack:
        W = np.zeros((n, B))
        W[:, b_best] = 1.0
        used = "single:" + names[b_best]
    info = {"tau": float(best_tau), "shrink": s, "err_stack": err_stack, "err_median": yy,
            "err_single": single, "used": used}
    return W, info


def _effective_stack_error(info):
    """CV error actually achieved by the stack decision (stack, calibrated shrink, or best single member)."""
    return min(float(info["err_stack"]), float(min(info["err_single"])))


def _fit_stack(rp, sel, params, seed, lat_budget=0.0):
    """Out-of-fold base predictions over history rows -> stacking weights. If lat_budget > 0 the latent-skill
    predictor is added as an extra member (config chosen by ``choose_latent_rank_cv`` on the same folds) and kept
    only if the stack's CV error improves by LAT_MIN_GAIN (relative). Returns (W, info, latent model or None)."""
    T, M = rp["T"], rp["mask"]
    m, n = T.shape
    sel = np.asarray(sel, dtype=int)
    folds = _make_folds(m, seed + 2000)
    P = np.zeros((len(BASE_NAMES), m, n))
    for va in folds:
        tr = np.setdiff1d(np.arange(m), va)
        fit = _fit_base(rp, tr, sel, params)
        P[:, va, :] = _base_predictions(fit, T[va][:, sel], M[va][:, sel])
    med = rp["med"]
    tmask = M.copy()
    tmask[:, sel] = False
    Pd, Yd = P - med[None, None, :], T - med[None, :]
    W, info = stack_predictors_nnls(Pd, Yd, tmask, folds)
    lat = None
    if lat_budget > 0 and LATENT_OPTS.get("enabled", True):
        try:
            lat_deadline = time.time() + lat_budget
            cfg, Plat, errs = choose_latent_rank_cv(rp, sel, folds, lat_deadline)
            if cfg is not None:
                names = BASE_NAMES + ("latent",)
                P7 = np.concatenate([Pd, (Plat - med[None, :])[None]], axis=0)
                W7, info7 = stack_predictors_nnls(P7, Yd, tmask, folds, names=names)
                info7["latent_cfg"], info7["latent_cv_errs"] = cfg, errs
                if _effective_stack_error(info7) < _effective_stack_error(info) * (1.0 - LAT_MIN_GAIN):
                    lat = _full_latent(rp, cfg, deadline=lat_deadline + 20.0)
                    W, info = W7, info7
        except Exception:  # latent member is optional: keep the incumbent stack
            lat = None
    return W, info, lat


def _latent_member(lat, sel, xq, qmask):
    """Latent-skill prediction [B, N] in transformed units for query rows."""
    return posterior_latent_new_model(lat, sel, xq, qmask)[0]


def fit_model(rp, sel, params, seed, with_stack=True, deadline=None):
    """Final model: simple tuned Gaussian conditional mean (always) plus the stack (if time allows)."""
    a, r, lam = params
    sel = np.asarray(sel, dtype=int)
    model = {"rep": rp, "sel": sel, "params": params, "W": None, "fit": None, "info": None, "lat": None,
             "simple": {"mu": rp["mu"], "Sigma": _build_sigma(rp["S_all"], a, r), "lam": lam}}
    if with_stack and (deadline is None or time.time() < deadline):
        try:
            lat_budget = LAT_BUDGET if (deadline is None or time.time() < deadline - 20.0) else 0.0
            W, info, lat = _fit_stack(rp, sel, params, seed, lat_budget)
            model["fit"] = _fit_base(rp, np.arange(rp["T"].shape[0]), sel, params)
            model["W"], model["info"], model["lat"] = W, info, lat
        except Exception:  # degrade gracefully to the Gaussian-only model
            model["W"], model["fit"], model["lat"] = None, None, None
    return model


def predict_raw(model, values, mask, use_stack=True, clip=True):
    """Predict all N benchmarks in raw units from the observed values [B, k] / mask of the selected ones."""
    rp, sel = model["rep"], model["sel"]
    values = np.nan_to_num(np.asarray(values, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)
    mask = np.asarray(mask, dtype=bool)
    xq = np.where(mask, _forward_columns(rp["params"], sel, values), 0.0)
    if use_stack and model["W"] is not None:
        P = _base_predictions(model["fit"], xq, mask)
        if model.get("lat") is not None and model["W"].shape[1] == P.shape[0] + 1:
            try:
                P = np.concatenate([P, _latent_member(model["lat"], sel, xq, mask)[None]], axis=0)
            except Exception:  # latent member failed at predict time: reuse the incumbent stack weights
                P = np.concatenate([P, np.zeros((1,) + P.shape[1:])], axis=0)
                P[-1] = rp["med"][None, :]
        med = rp["med"]
        pred_t = med[None, :] + np.einsum("bri,ib->ri", P - med[None, None, :], model["W"])
    else:
        sm = model["simple"]
        pred_t = conditional_gaussian_impute(sm["mu"], sm["Sigma"], sel, xq, mask, sm["lam"])
    pred = inverse_quantile_transform(rp["params"], pred_t)
    if clip:
        pred = np.clip(pred, rp["lo"], rp["hi"])
    none = ~mask.any(1)
    if none.any():
        pred[none] = rp["rawmed"][None, :]
    for c, j in enumerate(sel):
        have = mask[:, c]
        pred[have, int(j)] = values[have, c]
    return np.nan_to_num(pred, nan=0.0, posinf=0.0, neginf=0.0)


# ----------------------------------------------------------------------------------------------------------
# selection driver
# ----------------------------------------------------------------------------------------------------------
def _candidate_selection(rp, ci, k, seed, deadline=None):
    kind, arg = CANDIDATES[ci]
    if kind == "wrap":
        return wrapper_forward_select_cv(rp, k, alpha=arg, seed=seed, deadline=deadline)
    if kind == "alat":
        rank, lam_lat, cexp = arg
        lat = _full_latent(rp, (rank, lam_lat, "monotone"), deadline)
        return select_a_optimal_latent(lat, k, rp["cover"], cexp)
    shrink, rank, lam_sel, cexp = arg
    Sig0 = _build_sigma(rp["S_all"], shrink, rank)
    return greedy_select_conditional_variance(Sig0, k, lam=lam_sel, weights=rp["cover"] ** cexp)


def _prepare_history():
    n_chunks = _STATE["n_chunks"]
    parts = [_STATE["chunks"][i] for i in range(n_chunks)]
    values = np.concatenate([p[0] for p in parts]).astype(np.float64)
    mask = np.concatenate([p[1] for p in parts]).astype(bool)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    reps = {"z": build_rep(values, mask, "z")}
    try:
        reps["q"] = build_rep(values, mask, "q")
    except Exception:
        pass
    _STATE["hist"] = {"reps": reps}


def _select_and_fit(k):
    t0 = time.time()
    reps = _STATE["hist"]["reps"]
    seed = _STATE["seed"]
    m, n = reps["z"]["T"].shape
    k = int(min(max(k, 1), n))
    folds = _make_folds(m, seed + 1000)
    plan = [step for phase in PLAN for step in phase]
    seen = set()
    best = None
    for pi, (kind, ci) in enumerate(plan):
        if kind not in reps:
            continue
        if pi >= len(PLAN[0]) and best is not None and time.time() - t0 > SELECT_CAND_BUDGET:
            break
        rp = reps[kind]
        try:
            sel = _candidate_selection(rp, ci, k, seed, t0 + 1.5 * SELECT_CAND_BUDGET)
            if sel is None or len(set(sel)) != len(sel):
                continue
            key = (kind, tuple(sel))
            if key in seen:
                continue
            seen.add(key)
            params, _ = _cv_tune(rp, sel, folds, QUICK_SHRINKS, QUICK_RANKS, QUICK_LAMS)
            err = _cv_raw_error(rp, sel, params, folds)
        except Exception:
            continue
        if best is None or err < best[0]:
            best = (err, kind, [int(j) for j in sel])
    if best is None:  # safety net: cycle-1 style selection on the z-score representation
        rp = reps["z"]
        sel = greedy_select_conditional_variance(_build_sigma(rp["S_all"], 0.05, None), k, lam=0.05,
                                                 weights=rp["cover"])
        best = (np.inf, "z", [int(j) for j in sel])
    _, kind, sel = best
    rp = reps[kind]
    if time.time() - t0 > FULL_TUNE_BUDGET:
        params, _ = _cv_tune(rp, sel, folds, QUICK_SHRINKS, QUICK_RANKS, QUICK_LAMS)
    else:
        params, _ = _cv_tune(rp, sel, folds)
    _STATE["model"] = fit_model(rp, sel, params, seed, True, deadline=t0 + STACK_BUDGET)
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
        pred = predict_raw(_STATE["model"], values, mask)
        return {"predictions_b64": _encode(pred.astype("<f4")), "dtype": "float32",
                "shape": [b, int(pred.shape[1])], "encoding": "base64"}
    raise ValueError("unknown op")
