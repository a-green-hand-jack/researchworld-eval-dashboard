"""Core library: data loading, latent-factor (multidimensional IRT) model, item samplers, estimators.

All randomness is controlled by explicit numpy Generators / seeds.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import numpy as np
import joblib
from threadpoolctl import threadpool_limits
threadpool_limits(1)
from scipy.optimize import minimize
from scipy.special import expit, logit

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "scores")
BENCHMARKS = ["arc_challenge", "bbh", "gpqa", "ifeval", "mmlu_pro", "musr", "openllm_math",
              "commonsense", "gsm", "legalbench", "math", "med_qa", "mmlu"]


def load(name):
    Y = np.asarray(joblib.load(os.path.join(DATA, name + ".jbl"))).astype(np.float64)
    assert set(np.unique(Y)) <= {0.0, 1.0}
    return Y  # models x items


# ----------------------------------------------------------------------------------------
# Latent factor model: P(y_ij=1) = sigmoid(a_j . theta_i + b_j)   (multidimensional 2PL IRT)
# ----------------------------------------------------------------------------------------
class LatentModel:
    def __init__(self, A, b, mu, Sigma_inv, theta_src):
        self.A, self.b, self.mu, self.Pinv, self.theta_src = A, b, mu, Sigma_inv, theta_src

    def with_prior_scale(self, s):
        return LatentModel(self.A, self.b, self.mu, self.Pinv / s, self.theta_src)

    def prob_items(self, theta):  # theta: T x d -> T x N
        return expit(theta @ self.A.T + self.b[None, :])

    def fit_targets(self, items, Yt, iters=12):
        """Batched MAP / Newton for the ability vector of every target model from responses
        Yt (T x n) on the given item indices (prior N(mu, Sigma_src))."""
        A = self.A[items]; b = self.b[items]
        T, d = Yt.shape[0], A.shape[1]
        th = np.tile(self.mu, (T, 1))
        for _ in range(iters):
            p = expit(th @ A.T + b)
            g = (Yt - p) @ A - (th - self.mu) @ self.Pinv
            W = p * (1 - p)  # T x n
            H = np.einsum("tn,nd,ne->tde", W, A, A) + self.Pinv[None]
            step = np.linalg.solve(H, g[..., None])[..., 0]
            step = np.clip(step, -2, 2)
            th = th + step
            if np.abs(step).max() < 1e-4:
                break
        return th


def fit_latent(Y, d, seed=0, l2_theta=1.0, l2_a=0.1, l2_b=0.01, maxiter=300):
    M, N = Y.shape
    rng = np.random.default_rng(seed)
    m = np.clip(Y.mean(0), 0.02, 0.98)
    b0 = logit(m)
    th0 = rng.normal(0, 0.3, (M, d))
    # SVD-based init of loadings
    Z = Y - Y.mean(0, keepdims=True)
    U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    th0 = U[:, :d] * np.sqrt(M) * 0.5
    A0 = Vt[:d].T * (S[:d] / np.sqrt(M)) * 0.5 + rng.normal(0, 0.02, (N, d))
    x0 = np.concatenate([th0.ravel(), A0.ravel(), b0])

    def unpack(x):
        return x[:M * d].reshape(M, d), x[M * d:M * d + N * d].reshape(N, d), x[M * d + N * d:]

    def fg(x):
        th, A, b = unpack(x)
        z = th @ A.T + b[None]
        # BCE with logits
        ex = np.exp(-np.abs(z))
        l1 = np.log1p(ex)
        loss = np.sum(np.maximum(z, 0) + l1 - Y * z)
        sig = np.where(z >= 0, 1.0, ex) / (1.0 + ex)
        r = sig - Y
        gth = r @ A + l2_theta * th
        gA = r.T @ th + l2_a * A
        gb = r.sum(0) + l2_b * b
        loss += 0.5 * (l2_theta * (th ** 2).sum() + l2_a * (A ** 2).sum() + l2_b * (b ** 2).sum())
        return loss, np.concatenate([gth.ravel(), gA.ravel(), gb])

    res = minimize(fg, x0, jac=True, method="L-BFGS-B", options=dict(maxiter=maxiter, maxcor=20))
    th, A, b = unpack(res.x)
    mu = th.mean(0)
    C = np.cov(th.T).reshape(d, d) + 1e-3 * np.eye(d)
    return LatentModel(A, b, mu, np.linalg.inv(C), th), res


# ----------------------------------------------------------------------------------------
# Item samplers.  All return (indices, inclusion probabilities pi for ALL items)
# ----------------------------------------------------------------------------------------
def uniform_pi(N, n):
    return np.full(N, n / N)


def systematic_sample(pi, order, rng):
    """Fixed-size systematic sampling along `order` with exact inclusion probabilities pi
    (requires sum(pi) == n integer, pi<=1)."""
    p = pi[order]
    c = np.cumsum(p)
    n = int(round(c[-1]))
    u = rng.uniform(0, 1)
    pts = u + np.arange(n)
    idx = np.searchsorted(c, pts, side="right")
    idx = np.minimum(idx, len(order) - 1)
    return order[idx]


def sample_random(N, n, rng):
    return np.sort(rng.choice(N, n, replace=False)), uniform_pi(N, n)


def sample_sorted(N, n, diff, rng):
    """Systematic sampling after sorting by source difficulty: implicit stratification."""
    order = np.lexsort((rng.uniform(size=N), diff))
    return np.sort(systematic_sample(uniform_pi(N, n), order, rng)), uniform_pi(N, n)


def pps_pi(w, n, mix=0.5):
    """Inclusion probabilities (sum = n, each <= 1): mixture of uniform and proportional-to-w."""
    N = len(w)
    q = mix / N + (1 - mix) * w / max(w.sum(), 1e-12)
    pi = n * q
    capped = np.zeros(N, bool)
    for _ in range(100):
        over = (pi > 1 + 1e-12) & ~capped
        if not over.any():
            break
        capped |= over
        rest = ~capped
        pi[capped] = 1.0
        pi[rest] = (n - capped.sum()) * q[rest] / q[rest].sum()
    return pi


def sample_pps(N, n, w, diff, rng, mix=0.5):
    pi = pps_pi(w, n, mix)
    order = np.lexsort((rng.uniform(size=N), diff))
    return np.sort(systematic_sample(pi, order, rng)), pi


# ----------------------------------------------------------------------------------------
# Estimators.  Each returns predictions of the full-benchmark accuracy for every target.
# ----------------------------------------------------------------------------------------
def est_ht_mean(Yt_S, pi_S, N):
    """Horvitz-Thompson (Hajek-normalised) mean of the observed responses."""
    w = 1.0 / pi_S
    return (Yt_S * w).sum(1) / w.sum()


def est_plugin(model, S, Yt_S):
    th = model.fit_targets(S, Yt_S)
    return model.prob_items(th).mean(1)


def est_crossfit(model, S, pi_S, Yt_S, rng, K=5):
    """Cross-fitted model-assisted estimators.
    Returns (difference_estimator, greg_estimator, mean_beta)."""
    n = len(S); N = model.A.shape[0]
    K = min(K, n)
    perm = rng.permutation(n)
    folds = np.array_split(perm, K)
    T = Yt_S.shape[0]
    pool_means = np.zeros((K, T))          # mean prediction over all items for each fold model
    P_pool = []                              # we need g(p) means, so store pool predictions' moments
    oof_p = np.zeros((T, n))
    pools = []
    for k, f in enumerate(folds):
        tr = np.setdiff1d(np.arange(n), f)
        th = model.fit_targets(S[tr], Yt_S[:, tr])
        oof_p[:, f] = expit(th @ model.A[S[f]].T + model.b[S[f]])
        pr = model.prob_items(th)            # T x N
        pools.append((pr.mean(1), (pr ** 2).mean(1)))
    w = 1.0 / pi_S
    # --- difference estimator (g = identity)
    diff = np.zeros(T)
    for k, f in enumerate(folds):
        res = ((Yt_S[:, f] - oof_p[:, f]) * w[f]).sum(1) * len(folds) / N
        diff += pools[k][0] + res
    diff /= len(folds)
    # --- GREG: calibrate y ~ alpha + beta * p_oof (HT-weighted OLS per target), then residual correction
    ws = w / w.sum()
    pm = (oof_p * ws).sum(1, keepdims=True); ym = (Yt_S * ws).sum(1, keepdims=True)
    cov = ((oof_p - pm) * (Yt_S - ym) * ws).sum(1); var = ((oof_p - pm) ** 2 * ws).sum(1)
    beta = np.where(var > 1e-6, cov / np.maximum(var, 1e-6), 1.0)
    beta = np.clip(beta, 0.0, 2.0)
    alpha = ym[:, 0] - beta * pm[:, 0]
    greg = np.zeros(T)
    for k, f in enumerate(folds):
        pool_g = alpha + beta * pools[k][0]
        res = ((Yt_S[:, f] - (alpha[:, None] + beta[:, None] * oof_p[:, f])) * w[f]).sum(1) * len(folds) / N
        greg += pool_g + res
    greg /= len(folds)
    # --- standard errors (with-replacement style variance of the cross-fitted residual term,
    #     finite-population correction (1 - n/N); ignores any stratification gain => conservative)
    def _se(resid):
        z = resid * (n / N) * w[None, :]
        return np.sqrt(max(1 - n / N, 0.0) * z.var(1, ddof=1) / n)
    se_d = _se(Yt_S - oof_p)
    se_g = _se(Yt_S - (alpha[:, None] + beta[:, None] * oof_p))
    return diff, np.clip(greg, 0, 1), beta, se_d, se_g


def se_ht(Yt_S, pi_S, N):
    n = Yt_S.shape[1]
    z = Yt_S * (n / N) / pi_S[None, :]
    return np.sqrt(max(1 - n / N, 0.0) * z.var(1, ddof=1) / n)


def info_select(model, n):
    """Greedy D-optimal ('maximum Fisher information') item selection under the fitted latent model
    at the source-population mean ability (metabench / CAT style)."""
    A, b, mu, P = model.A, model.b, model.mu, model.Pinv
    p = expit(A @ mu + b); w = p * (1 - p)
    M = P.copy(); chosen = []
    avail = np.ones(len(b), bool)
    for _ in range(n):
        Minv = np.linalg.inv(M)
        gain = np.log1p(w * np.einsum("nd,de,ne->n", A, Minv, A))
        gain[~avail] = -np.inf
        j = int(np.argmax(gain)); chosen.append(j); avail[j] = False
        M = M + w[j] * np.outer(A[j], A[j])
    return np.array(chosen)  # greedy order: the first n entries are the n-item design


def anchor_select(Ysrc, k, seed, max_iter=40):
    """Anchor points: cluster items by their response vectors over source models (correlation
    distance) and take the medoid of each cluster; weights = cluster sizes."""
    from sklearn.cluster import KMeans
    X = Ysrc.T - Ysrc.T.mean(1, keepdims=True)
    nrm = np.linalg.norm(X, axis=1, keepdims=True)
    X = X / np.maximum(nrm, 1e-12)
    km = KMeans(n_clusters=k, n_init=1, max_iter=max_iter, random_state=seed).fit(X)
    anchors, weights = [], []
    for c in range(k):
        mem = np.where(km.labels_ == c)[0]
        if len(mem) == 0:
            continue
        d = ((X[mem] - km.cluster_centers_[c]) ** 2).sum(1)
        anchors.append(mem[np.argmin(d)]); weights.append(len(mem))
    return np.array(anchors), np.array(weights, float)


def est_ridge(Ysrc, S, Yt_S, alphas=(0.1, 1, 10, 100, 1000)):
    """Direct 'assessor' regression: full-benchmark accuracy of source models regressed on their
    responses on the subset (ridge, alpha by efficient leave-one-out CV on source models)."""
    from sklearn.linear_model import RidgeCV
    X = Ysrc[:, S]; y = Ysrc.mean(1)
    r = RidgeCV(alphas=alphas).fit(X, y)
    return np.clip(r.predict(Yt_S), 0, 1)
