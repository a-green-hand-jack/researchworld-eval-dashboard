"""Model-assisted difference estimator with D-optimal latent-space item selection (python_rpc_v1:handle).

Task.  An episode gives you the binary correct/incorrect matrix of SOURCE models on a benchmark
whose items are opaque column indices.  You choose at most ``k`` item columns; the evaluator then
reveals each TARGET model's responses on those columns only and you predict every target's accuracy
on the FULL benchmark.  Targets are either "random_targets" (look like the sources) or
"strong_targets" (stronger than every source, so predictions must extrapolate).

Protocol (unchanged from the starter): reset -> load_source (1-2 chunks) -> select -> predict, each with
the exact documented response dicts ({"ok": True}, {"indices": [...]}, {"predictions": [...]}).

Method (survey-estimation view)
-------------------------------
1. Latent model.  Centre the source matrix, take a low-rank SVD (np.linalg.svd on the small model x model
   Gram matrix) -> item means mu_i, item loadings W[:, i], prior variance of each ability coordinate and a
   per-item residual variance v_i.  A target's ability z solves a ridge/MAP weighted normal equation
   (np.linalg.solve) on its k answers; P(correct) on every item is clip(mu + z W, 0, 1).
2. Selection.  Several candidate designs of exactly k items are built: difficulty-stratified (the starter),
   greedy Bayesian D-optimal over item loadings (max log-det gain, Sherman-Morrison style updates, final
   np.linalg.slogdet check), hybrids with a stratified or latent-space k-means medoid half.
3. Estimator.  Model-assisted difference estimator
       (sum observed + sum_{unselected} P_hat [+ (n-k) * mean residual on the subset]) / n
   blended with the starter's source-calibrated subset mean:  alpha * B + (1 - alpha) * A.
4. All hyper-parameters (design, rank, prior strength, bias correction on/off, blend weight alpha) are chosen
   ONLY from source models, by pseudo-target validation inside the source set: random folds for
   "random_targets", hold-out of the strongest 20% / 10% source models for "strong_targets" (the
   ``split`` field supplied with load_source).  alpha = 0 (pure starter estimator on the stratified design)
   is always in the search space, so the method falls back to the starter where the latent model hurts.
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "8")

import base64
import math

import numpy as np

try:  # optional, used for the rank-aware part of validation / k-means medoid design
    import scipy.stats
except Exception:  # pragma: no cover
    scipy = None
try:
    from sklearn.cluster import KMeans
except Exception:  # pragma: no cover
    KMeans = None

_STATE = {}

RMAX = 12
R_GRID = (1, 2, 3, 5, 8, 12)
TAU_GRID = (1.0, 4.0, 16.0)
ALPHA_GRID = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
# (name, base design for the non-D-opt part, fraction of the budget chosen by D-optimality)
DESIGNS = (
    ("strat", "strat", 0.0),
    ("strat_dopt", "strat", 0.5),
    ("dopt", "strat", 1.0),
    ("kmeans_dopt", "kmeans", 0.5),
)


def _decode(b64, rows, cols):
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).reshape(rows, -1)
    return np.unpackbits(raw, axis=1)[:, :cols]


def _reset(seed):
    _STATE.clear()
    _STATE["rng"] = np.random.default_rng(int(seed))
    _STATE["chunks"] = {}
    return {"ok": True}


def _load_source(req):
    chunks = _STATE["chunks"]
    chunks[int(req["chunk_index"])] = _decode(req["data_b64"], int(req["row_count"]), int(req["n_items"]))
    _STATE["n_chunks"] = int(req["n_chunks"])
    _STATE["k"] = int(req["k"])
    _STATE["split"] = str(req.get("split", "random_targets"))
    if len(chunks) == _STATE["n_chunks"]:
        _STATE["src"] = np.concatenate([chunks[i] for i in sorted(chunks)], axis=0)
    return {"ok": True}


# ----------------------------------------------------------------------------------------------
# latent model
# ----------------------------------------------------------------------------------------------
def _fit_latent(S, rmax=RMAX):
    """Low-rank fit of the centred source matrix S (m x n, float64)."""
    m, n = S.shape
    mu = S.mean(axis=0)
    Sc = S - mu
    gram = Sc @ Sc.T  # m x m, symmetric PSD
    U, s2, _ = np.linalg.svd(gram)
    s_all = np.sqrt(np.maximum(s2, 0.0))
    r = int(min(rmax, max(m - 1, 1)))
    s = s_all[:r]
    keep = s > 1e-6 * max(float(s_all[0]), 1e-12)
    r = int(keep.sum())
    if r == 0:
        v = np.full(n, 0.05)
        return {"mu": mu, "W": np.zeros((1, n)), "pv": np.array([1e-6]), "v": v, "m": m}
    s = s[:r]
    U = U[:, :r]
    W = (U.T @ Sc) / s[:, None]  # r x n, orthonormal rows
    Z = U * s
    resid = Sc - Z @ W
    v = (resid ** 2).mean(axis=0)
    floor = max(0.02, float(np.percentile(v, 5)))
    v = np.maximum(v, floor)
    return {"mu": mu, "W": W, "pv": s ** 2 / m, "v": v, "m": m}


def predict_full_score(fit, idx, Y, r, tau):
    """Model-assisted estimates for targets with answers Y (t x k) on items idx.

    Returns (plain, bias_corrected): plain = (observed sum + sum of predicted P(correct) on unselected
    items)/n ; bias_corrected adds the mean residual (observed - predicted) of the subset on the remaining
    n - k items (generalised-regression correction)."""
    mu, W, pv, v = fit["mu"], fit["W"], fit["pv"], fit["v"]
    n = mu.shape[0]
    idx = np.asarray(idx, dtype=int)
    k = idx.size
    r = int(min(r, W.shape[0]))
    Ws = W[:r][:, idx]
    wts = 1.0 / v[idx]
    A = (Ws * wts) @ Ws.T + np.diag(1.0 / (tau * pv[:r]))
    b = (Ws * wts) @ (Y - mu[idx]).T
    z = np.linalg.solve(A, b)  # r x t
    P = np.clip(mu[None, :] + z.T @ W[:r], 0.0, 1.0)
    Psel = P[:, idx]
    unsel = P.sum(axis=1) - Psel.sum(axis=1)
    obs = Y.sum(axis=1)
    resid_mean = (Y - Psel).mean(axis=1)
    plain = (obs + unsel) / n
    corrected = (obs + unsel + (n - k) * resid_mean) / n
    return np.clip(plain, 0.0, 1.0), np.clip(corrected, 0.0, 1.0)


def _calibrated_mean(S, idx, Y):
    """Starter estimator: linear map fitted on sources, subset mean -> full accuracy."""
    tmean = Y.mean(axis=1)
    sub = S[:, idx].mean(axis=1)
    full = S.mean(axis=1)
    if sub.size >= 3 and np.ptp(sub) > 1e-9:
        slope, intercept = np.polyfit(sub, full, 1)
        return np.clip(slope * tmean + intercept, 0.0, 1.0)
    return np.clip(tmean, 0.0, 1.0)


# ----------------------------------------------------------------------------------------------
# item selection
# ----------------------------------------------------------------------------------------------
def _stratified(difficulty, n_pick, rng, exclude=()):
    if n_pick <= 0:
        return []
    n = difficulty.shape[0]
    order = np.argsort(difficulty + 1e-9 * rng.random(n), kind="stable")
    strata = np.array_split(order, min(n_pick, n))
    return [int(rng.choice(g)) for g in strata if len(g)]


def _kmeans_medoids(X, n_pick, rng):
    n = X.shape[0]
    if n_pick <= 0:
        return []
    if KMeans is None or n_pick >= n:
        return [int(i) for i in rng.choice(n, size=min(n_pick, n), replace=False)]
    km = KMeans(n_clusters=n_pick, n_init=1, max_iter=50, random_state=int(rng.integers(0, 2 ** 31 - 1)))
    labels = km.fit_predict(X)
    d = ((X - km.cluster_centers_[labels]) ** 2).sum(axis=1)
    picks = []
    for c in range(n_pick):
        members = np.flatnonzero(labels == c)
        if members.size:
            picks.append(int(members[np.argmin(d[members])]))
    return picks


def _item_features(fit, r):
    r = int(min(r, fit["W"].shape[0]))
    return (fit["W"][:r] / np.sqrt(fit["v"])).T  # n x r, noise-weighted loadings


def select_items_dopt(fit, r, n_pick, chosen):
    """Greedy Bayesian D-optimal design over item loadings.

    Maximises log det(M), M = prior precision + sum_i f_i f_i^T; the greedy gain of item i is
    log(1 + f_i^T M^{-1} f_i).  ``chosen`` items are already in the design.  Returns (new items, logdet)."""
    F = _item_features(fit, r)
    n, rr = F.shape
    M = np.diag(1.0 / fit["pv"][:rr])
    chosen = [int(i) for i in chosen]
    avail = np.ones(n, dtype=bool)
    for i in chosen:
        M += np.outer(F[i], F[i])
        avail[i] = False
    new = []
    for _ in range(int(min(n_pick, avail.sum()))):
        AF = np.linalg.solve(M, F.T).T
        gain = np.einsum("ij,ij->i", AF, F)
        gain[~avail] = -np.inf
        j = int(np.argmax(gain))
        M += np.outer(F[j], F[j])
        avail[j] = False
        new.append(j)
    sign, logdet = np.linalg.slogdet(M)
    return new, (float(logdet) if sign > 0 else -np.inf)


def _build_design(base, frac, fit, k, r_sel, difficulty, kmX, rng):
    n = difficulty.shape[0]
    n_d = int(round(frac * k))
    n_b = k - n_d
    if base == "kmeans":
        picks = _kmeans_medoids(kmX, n_b, rng)
    else:
        picks = _stratified(difficulty, n_b, rng)
    picks = list(dict.fromkeys(picks))
    logdet = 0.0
    if n_d > 0 or len(picks) < k:
        new, logdet = select_items_dopt(fit, r_sel, k - len(picks), picks)
        picks += new
    picks = list(dict.fromkeys(picks))
    if len(picks) < k:  # safety: top up with random unused items
        rest = np.setdiff1d(np.arange(n), np.array(picks, dtype=int))
        picks += [int(i) for i in rng.choice(rest, size=min(k - len(picks), rest.size), replace=False)]
    return np.array(picks[:k], dtype=int), logdet


# ----------------------------------------------------------------------------------------------
# validation inside the source set (no target information is used)
# ----------------------------------------------------------------------------------------------
def _make_folds(S, split, rng):
    m = S.shape[0]
    if m < 10:
        return []
    full = S.mean(axis=1)
    if split == "strong_targets":
        order = np.argsort(full, kind="stable")
        folds = []
        for frac in (0.2, 0.1):
            h = max(2, int(round(frac * m)))
            folds.append((order[:-h], order[-h:]))
        return folds
    perm = rng.permutation(m)
    parts = np.array_split(perm, 5)
    return [(np.concatenate([parts[j] for j in range(5) if j != i]), parts[i]) for i in range(5)]


def _rank_scores(pred, truth, fold_sizes):
    if scipy is None:
        return 1.0
    out, start = [], 0
    for sz in fold_sizes:
        p, t = pred[start:start + sz], truth[start:start + sz]
        start += sz
        if sz >= 3 and np.ptp(p) > 0 and np.ptp(t) > 0:
            rho = scipy.stats.spearmanr(p, t)[0]
            ken = scipy.stats.kendalltau(p, t)[0]
            out.append(0.5 * (rho + ken))
    return float(np.mean(out)) if out else 1.0


def _validate(S, split, designs, rng):
    """Pick (design, r, tau, bias_corr, alpha) minimising pseudo-target error."""
    folds = _make_folds(S, split, rng)
    if not folds:
        return None
    full = S.mean(axis=1)
    fits = [_fit_latent(S[tr]) for tr, _ in folds]
    truth = np.concatenate([full[te] for _, te in folds])
    sizes = [len(te) for _, te in folds]
    cands = []  # (name_index, r, tau, c, B-vector, A-vector)
    for di, (name, idx) in enumerate(designs):
        A_parts = []
        B_parts = {}
        for (tr, te), fit in zip(folds, fits):
            Y = S[te][:, idx].astype(np.float64)
            A_parts.append(_calibrated_mean(S[tr], idx, Y))
            for r in R_GRID:
                if r > fit["W"].shape[0] and r != R_GRID[0]:
                    continue
                for tau in TAU_GRID:
                    plain, corr = predict_full_score(fit, idx, Y, r, tau)
                    B_parts.setdefault((r, tau, 0), []).append(plain)
                    B_parts.setdefault((r, tau, 1), []).append(corr)
        A = np.concatenate(A_parts)
        for key, parts in B_parts.items():
            if len(parts) == len(folds):
                cands.append((di, key[0], key[1], key[2], np.concatenate(parts), A))
    scored = []
    for ci, (di, r, tau, c, B, A) in enumerate(cands):
        for alpha in ALPHA_GRID:
            pred = np.clip(alpha * B + (1 - alpha) * A, 0.0, 1.0)
            mse = float(np.mean((pred - truth) ** 2))
            scored.append((mse, ci, alpha, pred))
    scored.sort(key=lambda t: t[0])
    top = scored[:12]
    best_rmse = math.sqrt(max(top[0][0], 1e-18))
    best, best_obj = None, np.inf
    for mse, ci, alpha, pred in top:
        obj = math.sqrt(mse) / best_rmse + (1.0 - _rank_scores(pred, truth, sizes))
        if obj < best_obj:
            best_obj, best = obj, (ci, alpha, mse)
    ci, alpha, mse = best
    di, r, tau, c, _, _ = cands[ci]
    return {"design": di, "r": r, "tau": tau, "c": c, "alpha": float(alpha), "val_rmse": math.sqrt(mse)}


# ----------------------------------------------------------------------------------------------
# protocol ops
# ----------------------------------------------------------------------------------------------
def _select(req):
    src = _STATE["src"]
    rng = _STATE["rng"]
    n = src.shape[1]
    k = max(1, min(int(req["k"]), n))
    S = src.astype(np.float64)
    difficulty = S.mean(axis=0)
    default = {"r": 3, "tau": 4.0, "c": 1, "alpha": 0.0}
    try:
        fit = _fit_latent(S)
        _STATE["fit"] = fit
        r_sel = int(min(8, max(2, k // 10), fit["W"].shape[0]))
        F = _item_features(fit, r_sel)
        kmX = np.column_stack([difficulty, F])
        kmX = (kmX - kmX.mean(axis=0)) / (kmX.std(axis=0) + 1e-12)
        designs, kept = [], []
        for name, base, frac in DESIGNS:
            if base == "kmeans" and KMeans is None:
                continue
            idx, logdet = _build_design(base, frac, fit, k, r_sel, difficulty, kmX, rng)
            if frac > 0 and not np.isfinite(logdet):
                continue
            designs.append((name, idx))
            kept.append(name)
        cfg = None
        try:
            cfg = _validate(S, _STATE.get("split", "random_targets"), designs, rng)
        except Exception:
            cfg = None
        if cfg is None:  # too few source models to validate: conservative blend on the hybrid design
            di = kept.index("strat_dopt") if "strat_dopt" in kept else 0
            cfg = dict(default, design=di, alpha=0.3)
        idx = designs[cfg["design"]][1]
        _STATE["cfg"] = cfg
    except Exception:
        _STATE.pop("fit", None)
        idx = np.array(_stratified(difficulty, k, rng), dtype=int)
        _STATE["cfg"] = dict(default)
    picks = [int(i) for i in idx]
    _STATE["indices"] = picks
    return {"indices": picks}


def _predict(req):
    src = _STATE["src"]
    idx = [int(i) for i in req["indices"]]
    tgt = _decode(req["data_b64"], int(req["n_targets"]), len(idx)).astype(np.float64)
    S = src.astype(np.float64)
    pred = _calibrated_mean(S, idx, tgt)
    cfg = _STATE.get("cfg", {})
    fit = _STATE.get("fit")
    alpha = float(cfg.get("alpha", 0.0))
    if fit is not None and alpha > 0.0:
        try:
            plain, corr = predict_full_score(fit, idx, tgt, cfg["r"], cfg["tau"])
            B = corr if cfg["c"] else plain
            if np.all(np.isfinite(B)):
                pred = alpha * B + (1.0 - alpha) * pred
        except Exception:
            pass
    pred = np.clip(pred, 0.0, 1.0)
    return {"predictions": [float(p) if math.isfinite(float(p)) else 0.5 for p in pred]}


def handle(request):
    op = request.get("op")
    if op == "reset":
        return _reset(request["seed"])
    if op == "load_source":
        return _load_source(request)
    if op == "select":
        return _select(request)
    if op == "predict":
        return _predict(request)
    raise ValueError("unknown op")
