"""Core library: data loading, latent-factor (multidimensional 2PL IRT) model, subset selectors, estimators, metrics."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import spearmanr, kendalltau

DATA = '/work/data'
BENCHES = ['arc_challenge', 'bbh', 'gpqa', 'ifeval', 'mmlu_pro', 'musr', 'openllm_math',
           'commonsense', 'gsm', 'legalbench', 'math', 'med_qa', 'mmlu']


def load_bench(name):
    """Return binary matrix X (models x items) with duplicate-name model rows removed (first kept)."""
    z = np.load(f'{DATA}/{name}.npz', allow_pickle=False)
    X = z['X']; models = list(z['models'])
    if len(models) == 0:
        models = [f'helm_{i}' for i in range(X.shape[0])]
    keep, seen = [], set()
    for i, m in enumerate(models):
        if m in seen:
            continue
        seen.add(m); keep.append(i)
    return X[keep].astype(np.float64), [models[i] for i in keep]

# ---------------------------------------------------------------- latent factor model
def _sig(z): return expit(z)

def fit_irt(X, d, lam_item=0.5, lam_theta=1.0, maxiter=300, seed=0):
    """MAP fit of z_si = b_i + a_i . theta_s; theta_s~N(0,I/lam_theta); a_i~N(0,I/lam_item), b_i~N(0,1/lam_item^?).
    Returns dict(A (n,d), b (n,), Theta (m,d))."""
    m, n = X.shape
    rng = np.random.default_rng(seed)
    p0 = np.clip(X.mean(0), 0.02, 0.98)
    b0 = np.log(p0 / (1 - p0))
    # init from SVD of centred logit-ish matrix
    Xc = X - X.mean(0, keepdims=True)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    Th0 = U[:, :d] * np.sqrt(m) * 0.5
    A0 = Vt[:d].T * (S[:d] / np.sqrt(m) / 0.5) * 0.5
    Th0 = Th0 + 0.01 * rng.standard_normal(Th0.shape)
    x0 = np.concatenate([Th0.ravel(), A0.ravel(), b0])

    def unpack(x):
        return x[:m*d].reshape(m, d), x[m*d:m*d+n*d].reshape(n, d), x[m*d+n*d:]

    def f(x):
        Th, A, b = unpack(x)
        Z = Th @ A.T + b
        # BCE with logits
        loss = np.sum(np.logaddexp(0, Z) - X * Z)
        R = _sig(Z) - X
        gTh = R @ A + lam_theta * Th
        gA = R.T @ Th + lam_item * A
        gb = R.sum(0) + lam_item * b
        loss += 0.5 * lam_theta * np.sum(Th**2) + 0.5 * lam_item * (np.sum(A**2) + np.sum(b**2))
        return loss, np.concatenate([gTh.ravel(), gA.ravel(), gb])
    res = minimize(f, x0, jac=True, method='L-BFGS-B', options=dict(maxiter=maxiter, maxfun=maxiter*2))
    Th, A, b = unpack(res.x)
    return dict(A=A, b=b, Theta=Th, d=d)


def est_theta(A, b, S, Y, lam_theta=1.0, iters=8):
    """MAP ability for T target models given observed items S (idx array) and outcomes Y (T x |S|).
    Batched Newton. Returns Theta (T,d)."""
    T = Y.shape[0]; d = A.shape[1]
    AS = A[S]; bS = b[S]
    Th = np.zeros((T, d))
    I = np.eye(d)
    for _ in range(iters):
        P = _sig(Th @ AS.T + bS)
        g = (P - Y) @ AS + lam_theta * Th
        W = P * (1 - P)
        H = np.einsum('tk,ki,kj->tij', W, AS, AS) + lam_theta * I
        step = np.linalg.solve(H, g[..., None])[..., 0]
        Th = Th - np.clip(step, -3, 3)
    return Th


def predict_probs(model, Th):
    return _sig(Th @ model['A'].T + model['b'])

# ---------------------------------------------------------------- selectors (return idx, weights summing to 1)
def sel_random(Xs, k, rng, model=None):
    n = Xs.shape[1]
    S = np.sort(rng.choice(n, k, replace=False))
    return S, np.full(k, 1.0 / k)


def sel_strat(Xs, k, rng, model=None):
    """Systematic sampling along items sorted by source difficulty (random start): equal inclusion prob k/n."""
    n = Xs.shape[1]
    diff = Xs.mean(0) + 1e-6 * rng.standard_normal(n)  # random tie-breaking
    order = np.argsort(diff)
    step = n / k
    pos = (rng.uniform(0, step) + step * np.arange(k)).astype(int)
    S = np.sort(order[np.minimum(pos, n - 1)])
    return S, np.full(k, 1.0 / k)


def _kmeans_anchor(F, k, rng):
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=k, n_init=1, max_iter=50, random_state=int(rng.integers(1 << 30))).fit(F)
    S, w = [], []
    for c in range(k):
        idx = np.where(km.labels_ == c)[0]
        if len(idx) == 0:
            continue
        dd = ((F[idx] - km.cluster_centers_[c]) ** 2).sum(1)
        S.append(idx[np.argmin(dd)]); w.append(len(idx))
    S = np.array(S); w = np.array(w, float) / F.shape[0]
    o = np.argsort(S)
    return S[o], w[o]


def _rsvd(F, r, rng, q=2):
    Om = rng.standard_normal((F.shape[1], r + 10))
    Y = F @ Om
    for _ in range(q):
        Y = F @ (F.T @ Y)
    Q, _ = np.linalg.qr(Y)
    U2, S_, Vt = np.linalg.svd(Q.T @ F, full_matrices=False)
    return Q @ U2, S_, Vt


def sel_anchor(Xs, k, rng, model=None):
    """Anchor points (Vivek et al.-style): cluster items by their source-model response vectors."""
    F = Xs.T - Xs.T.mean(1, keepdims=True)
    if F.shape[1] > 50:  # cluster in a 50-dim SVD embedding of the response vectors (speed)
        U, S_, Vt = np.linalg.svd(F, full_matrices=False) if F.shape[0] < 2000 else _rsvd(F, 50, rng)
        F = U[:, :50] * S_[:50]
    return _kmeans_anchor(F, k, rng)


def sel_anchor_irt(Xs, k, rng, model=None):
    """tinyBenchmarks-style: cluster items in IRT-parameter space (alpha_i, beta_i)."""
    F = np.concatenate([model['A'], model['b'][:, None]], 1)
    return _kmeans_anchor(F, k, rng)


def sel_maxvar(Xs, k, rng, model=None):
    """items with source mean closest to 0.5 (most 'uncertain'), random tie-breaking."""
    p = Xs.mean(0)
    sc = -np.abs(p - 0.5) + 1e-9 * rng.standard_normal(len(p))
    S = np.sort(np.argsort(-sc)[:k])
    return S, np.full(k, 1.0 / k)


def sel_dopt(Xs, k, rng, model=None):
    """Greedy Bayesian D-optimal design for ability estimation under the fitted IRT, information averaged
    over the source abilities."""
    A, b, Th = model['A'], model['b'], model['Theta']
    d = A.shape[1]
    if len(Th) > 60:
        Th = Th[rng.choice(len(Th), 60, replace=False)]
    P = _sig(Th @ A.T + b)
    w = (P * (1 - P)).mean(0)  # n
    M = np.eye(d)  # prior precision
    Minv = np.eye(d)
    chosen = []
    avail = np.ones(A.shape[0], bool)
    for _ in range(k):
        q = np.einsum('ij,jk,ik->i', A, Minv, A)
        gain = np.log1p(w * q)
        gain[~avail] = -np.inf
        gain = gain + 1e-9 * rng.standard_normal(len(gain))
        i = int(np.argmax(gain))
        chosen.append(i); avail[i] = False
        v = Minv @ A[i]
        Minv = Minv - (w[i] / (1 + w[i] * (A[i] @ v))) * np.outer(v, v)
    return np.sort(np.array(chosen)), np.full(k, 1.0 / k)

SELECTORS = dict(rand=sel_random, strat=sel_strat, anchor=sel_anchor, anchor_irt=sel_anchor_irt,
                 maxvar=sel_maxvar, dopt=sel_dopt)

# ---------------------------------------------------------------- estimators
# Each takes Y (T x k) observed outcomes on S, returns predicted full-benchmark score for each of T targets.
def est_mean(Y, S, w, n):
    return Y @ w


def est_pirt(Y, S, w, n, model, lam_theta=1.0, weights_on=True):
    """p-IRT (Maia Polo et al. 2024): lambda*weighted mean of observed + (1-lambda)*mean of IRT predictions on rest."""
    Th = est_theta(model['A'], model['b'], S, Y, lam_theta)
    P = predict_probs(model, Th)
    rest = np.ones(n, bool); rest[S] = False
    lam = len(S) / n
    return lam * (Y @ w) + (1 - lam) * P[:, rest].mean(1)


def est_plugin(Y, S, w, n, model, lam_theta=1.0):
    """observed items counted exactly, unobserved replaced by IRT probability (== p-IRT with equal weights)."""
    Th = est_theta(model['A'], model['b'], S, Y, lam_theta)
    P = predict_probs(model, Th)
    rest = np.ones(n, bool); rest[S] = False
    return (Y.sum(1) + P[:, rest].sum(1)) / n


def est_irt_only(Y, S, w, n, model, lam_theta=1.0):
    """mean of IRT predicted probabilities over *all* items (pure model-based)."""
    Th = est_theta(model['A'], model['b'], S, Y, lam_theta)
    return predict_probs(model, Th).mean(1)


def est_gpirt(Y, S, w, n, model, lam, lam_theta=1.0):
    """gp-IRT: lam*weighted observed mean + (1-lam)*p-IRT, lam given."""
    return lam * (Y @ w) + (1 - lam) * est_pirt(Y, S, w, n, model, lam_theta)


def cf_parts(Y, S, rng, n, model, K=5, lam_theta=1.0, return_resid=False):
    """Cross-fitted pieces. Returns base (T,) = averaged cross-fit plug-in, corr (T,) = averaged residual correction,
    var (T,) = estimated sampling variance of corr. Estimator CF = base + corr (see est_cf)."""
    k = len(S)
    perm = rng.permutation(k)
    folds = np.array_split(perm, K)
    T = Y.shape[0]
    base = np.zeros(T); corr = np.zeros(T)
    R = np.zeros_like(Y)
    for fj in folds:
        tr = np.setdiff1d(np.arange(k), fj)
        Th = est_theta(model['A'], model['b'], S[tr], Y[:, tr], lam_theta)
        P = predict_probs(model, Th)               # T x n
        inT = np.zeros(n, bool); inT[S[tr]] = True
        res = Y[:, fj] - P[:, S[fj]]
        R[:, fj] = res
        base += (Y[:, tr].sum(1) + P[:, ~inT].sum(1)) / n
        corr += (n - len(tr)) * res.mean(1) / n
    base /= len(folds); corr /= len(folds)
    fac = (1 - (K - 1) / K * k / n)
    var = (fac * R.std(1, ddof=1)) ** 2 / k
    if return_resid:
        return base, corr, var, R
    return base, corr, var


def est_cf(Y, S, rng, n, model, K=5, lam_theta=1.0):
    """Cross-fitted difference ('model-assisted') estimator for equal-probability samples.
    Sample S is split at random into K folds. For fold j the ability is fitted on the other folds T_j (|T_j|=k-k_j),
    the target score is estimated as
        (1/n)[ sum_{i in T_j} y_i + sum_{i notin T_j} p_i^{(-j)} + (n-|T_j|) * mean_{i in S_j}(y_i - p_i^{(-j)}) ]
    and the K fold estimates are averaged. Under simple random sampling each fold estimate is exactly unbiased for the
    full-benchmark mean whatever the quality of p (S_j is an SRS of the n-|T_j| items outside T_j)."""
    b, c, v = cf_parts(Y, S, rng, n, model, K, lam_theta)
    return b + c


def eb_shrink(base, corr, var, trend=False):
    """Empirical-Bayes shrinkage of the estimated plug-in bias `corr` (noise variance `var`) across the cohort of targets.
    trend=False: prior b_t ~ N(0, tau2) (shrink toward 0 => plug-in).
    trend=True : prior b_t ~ N(alpha+beta*base_t, tau2) (shrink toward a cohort-level linear calibration of the bias)."""
    T = len(corr)
    if trend and T >= 6:
        Z = np.stack([np.ones(T), base], 1)
        w = 1.0 / (var + np.median(var) * 0 + 1e-12)
        w = np.minimum(w, 100 * np.median(w))
        beta = np.linalg.solve(Z.T @ (Z * w[:, None]) + 1e-9 * np.eye(2), Z.T @ (w * corr))
        mu = Z @ beta
        dof = T - 2
    else:
        mu = np.zeros(T); dof = T
    tau2 = max(0.0, np.sum((corr - mu) ** 2) / dof - var.mean())
    c = tau2 / (tau2 + var + 1e-18)
    return base + mu + c * (corr - mu)


def est_ridge(Xs, S, Y, alpha=None):
    """Direct regression of full score on subset outcomes, trained on source models (Zhang et al.-style baseline)."""
    from sklearn.linear_model import RidgeCV
    ys = Xs.mean(1)
    r = RidgeCV(alphas=np.logspace(-2, 3, 11)).fit(Xs[:, S], ys)
    return r.predict(Y)


def est_knn(Xs, S, Y, kn=10):
    """predict by average full score of kn source models most similar on S (Hamming)."""
    ys = Xs.mean(1)
    D = (Y[:, None, :] != Xs[None, :, S]).sum(2)
    idx = np.argsort(D, 1)[:, :kn]
    return ys[idx].mean(1)

# ---------------------------------------------------------------- metrics
def metrics(pred, true):
    e = pred - true
    sp = spearmanr(pred, true).statistic if np.std(pred) > 0 else 0.0
    kt = kendalltau(pred, true).statistic if np.std(pred) > 0 else 0.0
    sp = 0.0 if np.isnan(sp) else sp  # constant predictions => no rank information
    kt = 0.0 if np.isnan(kt) else kt
    return dict(mae=np.mean(np.abs(e)), rmse=np.sqrt(np.mean(e**2)), bias=np.mean(e), spearman=sp, kendall=kt)


# ---------------------------------------------------------------- source-internal model selection
def cv_select(Xs, rng, ds=(1, 2, 4, 8), k=50, frac_val=0.25):
    """Choose latent dimension d by held-out log-loss of *source* models (pseudo-targets, iid hold-out), and estimate
    the quantities needed by gp-IRT (sigma^2 and IRT bias b^2, following the recipe of Maia Polo et al. 2024)."""
    m, n = Xs.shape
    perm = rng.permutation(m); nv = max(5, int(frac_val * m))
    va, tr = perm[:nv], perm[nv:]
    Sk = np.sort(rng.choice(n, min(k, n // 2), replace=False))
    rest = np.setdiff1d(np.arange(n), Sk)
    best, bestmod, scores = None, None, {}
    for d in ds:
        mod = fit_irt(Xs[tr], d, maxiter=200, seed=0)
        Th = est_theta(mod['A'], mod['b'], Sk, Xs[va][:, Sk])
        P = np.clip(predict_probs(mod, Th)[:, rest], 1e-4, 1 - 1e-4)
        Yv = Xs[va][:, rest]
        ll = -np.mean(Yv * np.log(P) + (1 - Yv) * np.log(1 - P))
        scores[d] = ll
        if best is None or ll < scores[best]:
            best, bestmod = d, mod
    # gp-IRT bias: observe a random half of the items for held-out models, predict the other half
    half = np.sort(rng.choice(n, n // 2, replace=False)); oth = np.setdiff1d(np.arange(n), half)
    Th = est_theta(bestmod['A'], bestmod['b'], half, Xs[va][:, half])
    pred = predict_probs(bestmod, Th)[:, oth].mean(1)
    b2 = float(np.mean(np.abs(pred - Xs[va][:, oth].mean(1))) ** 2)
    sig2 = float(np.mean(Xs.mean(1) * (1 - Xs.mean(1))))
    return best, b2, sig2, scores


# ---------------------------------------------------------------- target-level recalibrated predictor (supplementary)
def fit_target(model, S, Y, lam=(0.1, 1.0, 1.0), iters=10):
    """Per-target logistic fit with free intercept/difficulty-slope: logit_i = b_i + alpha + delta*b_i + theta.a_i,
    ridge penalties lam=(alpha, delta, theta) towards (0,0,0); lam=(1e9,1e9,1) recovers est_theta."""
    A, b = model['A'], model['b']; d = A.shape[1]
    F = np.concatenate([np.ones((len(S), 1)), b[S, None], A[S]], 1)
    off = b[S]
    prec = np.diag(np.array([lam[0], lam[1]] + [lam[2]] * d))
    T = Y.shape[0]; w = np.zeros((T, d + 2))
    for _ in range(iters):
        P = _sig(w @ F.T + off)
        g = (P - Y) @ F + w @ prec
        W = P * (1 - P)
        H = np.einsum('tk,ki,kj->tij', W, F, F) + prec
        w = w - np.clip(np.linalg.solve(H, g[..., None])[..., 0], -3, 3)
    return w


def pred_target(model, w):
    A, b = model['A'], model['b']
    F = np.concatenate([np.ones((len(b), 1)), b[:, None], A], 1)
    return _sig(w @ F.T + b)


def cf_parts_cal(Y, S, rng, n, model, K=5, lam=(0.1, 1.0, 1.0)):
    """Same as cf_parts but with the recalibrated per-target predictor. Returns base, corr, var."""
    k = len(S)
    folds = np.array_split(rng.permutation(k), K)
    T = Y.shape[0]
    base = np.zeros(T); corr = np.zeros(T); R = np.zeros_like(Y)
    for fj in folds:
        tr = np.setdiff1d(np.arange(k), fj)
        P = pred_target(model, fit_target(model, S[tr], Y[:, tr], lam))
        inT = np.zeros(n, bool); inT[S[tr]] = True
        R[:, fj] = Y[:, fj] - P[:, S[fj]]
        base += (Y[:, tr].sum(1) + P[:, ~inT].sum(1)) / n
        corr += (n - len(tr)) * R[:, fj].mean(1) / n
    fac = (1 - (K - 1) / K * k / n)
    return base / K, corr / K, (fac * R.std(1, ddof=1)) ** 2 / k


def est_pirt_cal(Y, S, w, n, model, lam=(0.1, 1.0, 1.0)):
    """p-IRT with the recalibrated per-target predictor (same combination rule as est_pirt)."""
    P = pred_target(model, fit_target(model, S, Y, lam))
    rest = np.ones(n, bool); rest[S] = False
    l = len(S) / n
    return l * (Y @ w) + (1 - l) * P[:, rest].mean(1)


def est_greg(Y, S, Z, ridge=1e-2):
    """Classical regression (GREG) estimator with item covariates Z (n x q) known for all items:
    per-target ridge regression of y on [1, Z] over the sample; the estimate is the fitted value at the population mean of Z.
    Z is standardised over all n items; ridge applies to the slopes only."""
    n = Z.shape[0]
    Zs = (Z - Z.mean(0)) / (Z.std(0) + 1e-9)          # population mean of Zs is 0 -> estimate = intercept
    F = Zs[S]; k, q = F.shape
    Fc = F - F.mean(0)
    G = Fc.T @ Fc + ridge * k * np.eye(q)
    beta = np.linalg.solve(G, Fc.T @ (Y - Y.mean(1, keepdims=True)).T)   # q x T
    return Y.mean(1) - F.mean(0) @ beta + 0.0 * beta.sum(0)
