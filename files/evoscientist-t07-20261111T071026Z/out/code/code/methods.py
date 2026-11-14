"""Benchmark-prediction methods.

All methods share one protocol.  Given the source-model score matrix S (m x N, binary),
a budget n and an RNG, a *design* chooses n items (and optionally inclusion
probabilities pi).  The target models are then evaluated on those items only, giving
Y (T x n), and an *estimator* maps Y to a prediction of each target's full-benchmark
accuracy.  Source scores are never used for targets other than through the design and
the item-level predictors.
"""
import numpy as np
from scipy.optimize import minimize
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.cluster import KMeans
import kmedoids


def sigmoid(z):
    return 0.5 * (1.0 + np.tanh(0.5 * z))


# ----------------------------------------------------------------------------- MIRT
class MIRT:
    """Multidimensional 2PL: P(y_mi=1)=sigmoid(theta_m . a_i + b_i), MAP via L-BFGS.

    Priors: theta_m ~ N(0, I); a_i ~ N(0, 1/lam_a); b_i flat.  Fitted on source models only.
    """

    def __init__(self, k=2, lam_a=0.1, maxiter=150):
        self.k, self.lam_a, self.maxiter = k, lam_a, maxiter

    def fit(self, S, seed=0):
        m, N = S.shape; k = self.k
        rng = np.random.default_rng(seed)
        p_item = np.clip(S.mean(0), 0.02, 0.98)
        p_mod = np.clip(S.mean(1), 0.02, 0.98)
        lg = np.log(p_mod / (1 - p_mod)); lg = (lg - lg.mean()) / (lg.std() + 1e-9)
        Th0 = 0.1 * rng.standard_normal((m, k)); Th0[:, 0] = lg
        A0 = 0.1 * rng.standard_normal((N, k)); A0[:, 0] = 1.0
        b0 = np.log(p_item / (1 - p_item))
        x0 = np.concatenate([Th0.ravel(), A0.ravel(), b0])
        lam_a = self.lam_a

        def f(x):
            Th = x[: m * k].reshape(m, k); A = x[m * k: m * k + N * k].reshape(N, k)
            b = x[m * k + N * k:]
            Z = Th @ A.T + b
            # BCE with logits, stable
            L = np.logaddexp(0, Z) - S * Z
            P = sigmoid(Z); R = P - S
            loss = L.sum() + 0.5 * (Th ** 2).sum() + 0.5 * lam_a * (A ** 2).sum()
            gTh = R @ A + Th; gA = R.T @ Th + lam_a * A; gb = R.sum(0)
            return loss, np.concatenate([gTh.ravel(), gA.ravel(), gb])

        res = minimize(f, x0, jac=True, method="L-BFGS-B", options=dict(maxiter=self.maxiter))
        x = res.x
        self.Theta = x[: m * k].reshape(m, k)
        self.A = x[m * k: m * k + N * k].reshape(N, k)
        self.b = x[m * k + N * k:]
        P = sigmoid(self.Theta @ self.A.T + self.b)
        self.resid_var = ((S - P) ** 2).mean(0)  # in-sample residual variance per item
        self.pbar = S.mean(0)
        return self

    def fit_theta(self, Y, idx, iters=30):
        """Batched MAP ability for target models from their responses Y (T x n) on items idx."""
        A, b = self.A[idx], self.b[idx]
        T, n = Y.shape; k = self.k
        th = np.zeros((T, k))
        for _ in range(iters):
            P = sigmoid(th @ A.T + b)
            g = (P - Y) @ A + th
            W = P * (1 - P)
            H = np.einsum("tn,nk,nl->tkl", W, A, A) + np.eye(k)
            step = np.linalg.solve(H, g[..., None])[..., 0]
            nrm = np.linalg.norm(step, axis=1, keepdims=True)
            step = step * np.minimum(1.0, 4.0 / np.maximum(nrm, 1e-12))
            th = th - step
            if np.abs(step).max() < 1e-6:
                break
        return th

    def predict_all(self, th):
        return sigmoid(th @ self.A.T + self.b)  # T x N


# ----------------------------------------------------------------------------- designs
def pps_probs(w, n):
    """Inclusion probabilities proportional to w, sum n, each <= 1."""
    w = np.asarray(w, float); N = len(w)
    pi = np.zeros(N); free = np.ones(N, bool); budget = float(n)
    while True:
        pi[free] = budget * w[free] / w[free].sum()
        over = free & (pi >= 1.0)
        if not over.any():
            break
        pi[over] = 1.0; free &= ~over; budget = n - (~free).sum()
    return pi


def systematic_pps(pi, rng):
    N = len(pi); n = int(round(pi.sum()))
    order = rng.permutation(N)
    c = np.cumsum(pi[order]); c[-1] = n  # guard fp error
    pts = rng.random() + np.arange(n)
    idx = np.searchsorted(c, pts, side="right")
    idx = np.clip(idx, 0, N - 1)
    sel = order[idx]
    assert len(np.unique(sel)) == n, "systematic PPS drew duplicate items"
    return np.sort(sel)


def design_uniform(S, n, rng, **kw):
    N = S.shape[1]
    return np.sort(rng.choice(N, n, replace=False)), np.full(N, n / N)


def design_strat(S, n, rng, **kw):
    """Equal-count strata on source difficulty (sorted by source mean, random tie-break),
    one uniformly drawn item per stratum -> pi_i = 1/|stratum|."""
    N = S.shape[1]
    key = S.mean(0) + 1e-9 * rng.random(N)
    order = np.argsort(key)
    strata = np.array_split(order, n)
    pi = np.zeros(N); sel = []
    for s in strata:
        sel.append(rng.choice(s)); pi[s] = 1.0 / len(s)
    return np.sort(np.array(sel)), pi


def design_pps(S, n, rng, scores, gamma=0.3, **kw):
    """Defensive Neyman-type design: pi_i ∝ (1-gamma)*sqrt(v_i)/sum sqrt(v) + gamma/N."""
    N = S.shape[1]
    s = np.sqrt(np.maximum(scores, 1e-6)); s = s / s.sum()
    w = (1 - gamma) * s + gamma / N
    pi = pps_probs(w, n)
    return systematic_pps(pi, rng), pi


# ----------------------------------------------------------------------------- estimators
def hajek_mean(Y, pi_s):
    w = 1.0 / pi_s
    return (Y * w).sum(1) / w.sum()


def dr_estimate(Y, pi_s, F_all, F_s):
    """Difference (model-assisted) estimator with Hajek-normalised correction.
    F_all: T x N predictions for every item; F_s: T x n predictions on the sampled items."""
    w = 1.0 / pi_s
    corr = ((Y - F_s) * w).sum(1) / w.sum()
    return F_all.mean(1) + corr


def ridge_predictor(S, idx, Y, alpha=10.0):
    """Per-target ridge from source-model responses on an item to the target's response.
    Features X_i = S[:, i] (m-dim).  Returns T x N predictions (clipped to [0,1])."""
    Xs = S[:, idx].T; Xall = S.T
    mdl = Ridge(alpha=alpha).fit(Xs, Y.T)  # multi-output
    F_all = mdl.predict(Xall).T
    return np.clip(F_all, 0, 1)


# ----------------------------------------------------------------------------- driver
class Runner:
    """Holds source-side fitted objects for one (dataset, split, seed) task."""

    def __init__(self, S_src, seed, k=2, extra_ks=(8,)):
        self.S = S_src; self.seed = seed; self.N = S_src.shape[1]
        self.mirt = {k: MIRT(k=k).fit(S_src, seed)}
        for kk in extra_ks:
            self.mirt[kk] = MIRT(k=kk).fit(S_src, seed)
        self.k = k
        self._corr_diss = None

    def corr_diss(self):
        if self._corr_diss is None:
            with np.errstate(divide="ignore", invalid="ignore"):
                C = np.corrcoef(self.S, rowvar=False).astype(np.float32)
            C[np.isnan(C)] = 0.0
            D = 1.0 - C; np.fill_diagonal(D, 0.0)
            self._corr_diss = np.ascontiguousarray(D, dtype=np.float32)
        return self._corr_diss

    # -- design selection -------------------------------------------------------
    def design(self, kind, n, rng, gamma=0.3, k=None):
        k = k or self.k
        if kind == "uniform":
            return design_uniform(self.S, n, rng)
        if kind == "strat":
            return design_strat(self.S, n, rng)
        if kind == "pps_resid":
            return design_pps(self.S, n, rng, self.mirt[k].resid_var, gamma=gamma)
        if kind == "pps_bern":
            p = self.mirt[k].pbar
            return design_pps(self.S, n, rng, p * (1 - p), gamma=gamma)
        raise ValueError(kind)

    def anchors_kmedoids(self, n, seed):
        r = kmedoids.fasterpam(self.corr_diss(), n, init="random", random_state=seed, max_iter=100)
        med = np.array(r.medoids); labels = np.array(r.labels)
        w = np.bincount(labels, minlength=n) / self.N
        return med, w

    def anchors_irt(self, n, seed, k):
        X = np.hstack([self.mirt[k].A, self.mirt[k].b[:, None]])
        km = KMeans(n_clusters=n, n_init=1, random_state=seed).fit(X)
        cent = km.cluster_centers_
        idx = np.array([np.argmin(((X - c) ** 2).sum(1)) for c in cent])
        w = np.bincount(km.labels_, minlength=n) / self.N
        return idx, w


# ----------------------------------------------------------------------------- predictors
def predict_all_items(kind, Ssrc, mirt, idx_tr, Y_tr, knn_k=10):
    """T x N predictions of each target's response on *every* item, given the target's
    responses Y_tr on items idx_tr.  Only source scores and Y_tr are used."""
    if kind == "ridge":
        return ridge_predictor(Ssrc, idx_tr, Y_tr)
    if kind == "lat":
        th = mirt.fit_theta(Y_tr, idx_tr)
        return mirt.predict_all(th)
    if kind == "knn":
        Xs = Ssrc[:, idx_tr]                      # m x n
        # disagreement between each target and each source model on the training items
        D = (Y_tr[:, None, :] != Xs[None, :, :]).mean(2)   # T x m
        K = min(knn_k, Ssrc.shape[0])
        nn = np.argsort(D, axis=1, kind="stable")[:, :K]   # T x K
        return Ssrc[nn].mean(1)                            # T x N
    raise ValueError(kind)


def dr_insample(kind, Ssrc, mirt, idx, pis, Y):
    F = predict_all_items(kind, Ssrc, mirt, idx, Y)
    return dr_estimate(Y, pis, F, F[:, idx])


def dr_crossfit(kind, Ssrc, mirt, idx, pis, Y, rng, folds=5):
    """Cross-fitted difference estimator: residuals on sampled items come from predictors
    that did not see those items; plug-in term uses the predictor fitted on the full coreset."""
    n = len(idx)
    F_full = predict_all_items(kind, Ssrc, mirt, idx, Y)
    f = min(folds, n)
    parts = np.array_split(rng.permutation(n), f)
    F_s = np.zeros_like(Y)
    for te in parts:
        tr = np.setdiff1d(np.arange(n), te)
        Fj = predict_all_items(kind, Ssrc, mirt, idx[tr], Y[:, tr])
        F_s[:, te] = Fj[:, idx[te]]
    return dr_estimate(Y, pis, F_full, F_s)
