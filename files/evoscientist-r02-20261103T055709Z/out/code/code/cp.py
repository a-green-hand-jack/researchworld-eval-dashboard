"""Core library: simplex-valued scores, conformal calibration, synthetic compositional data, metrics.

All targets/predictions are arrays of shape (..., K) with non-negative entries summing to 1.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax, gammaln

EPS = 1e-12

# ----------------------------------------------------------------------------- scores
def _clr(p, delta):
    q = (p + delta) / (1.0 + p.shape[-1] * delta)
    l = np.log(np.maximum(q, EPS))
    return l - l.mean(-1, keepdims=True)


def make_score(name, delta=1e-2):
    """Return f(Y, P) -> non-negative score, broadcasting over leading dims. Y: candidate/true target, P: prediction."""
    if name == "l2":
        return lambda Y, P: np.sqrt(((Y - P) ** 2).sum(-1))
    if name == "l1":  # total variation
        return lambda Y, P: 0.5 * np.abs(Y - P).sum(-1)
    if name == "linf":
        return lambda Y, P: np.abs(Y - P).max(-1)
    if name == "hell":  # Hellinger / angular (square-root) geometry
        return lambda Y, P: np.sqrt(((np.sqrt(Y) - np.sqrt(P)) ** 2).sum(-1) / 2)
    if name.startswith("aitch@"):  # Aitchison with explicit pseudo-count, e.g. "aitch@0.001"
        return make_score("aitch", float(name.split("@")[1]))
    if name == "aitch":  # Aitchison distance after additive pseudo-count delta
        return lambda Y, P: np.sqrt(((_clr(Y, delta) - _clr(P, delta)) ** 2).sum(-1))
    if name == "kl":  # KL(y || p), zeros in y allowed (0 log 0 = 0)
        def f(Y, P):
            Pc = np.maximum(P, EPS)
            ylogy = np.where(Y > 0, Y * np.log(np.maximum(Y, EPS)), 0.0)
            return np.maximum((ylogy - Y * np.log(Pc)).sum(-1), 0.0)
        return f
    raise ValueError(name)


SCORES = ["l2", "l1", "linf", "hell", "aitch", "kl"]

# ----------------------------------------------------------------------------- conformal
def conf_quantile(s, alpha):
    """Finite-sample conformal quantile: ceil((n+1)(1-alpha))-th smallest score (inf if > n)."""
    n = len(s)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    if k > n:
        return np.inf
    return np.partition(s, k - 1)[k - 1]


def mondrian_quantiles(s_cal, g_cal, g_test, alpha, min_n=1):
    """Per-group conformal quantile; test point in group g uses calibration points of group g."""
    q = np.full(len(g_test), np.inf)
    for g in np.unique(g_test):
        m = g_cal == g
        if m.sum() >= min_n:
            q[g_test == g] = conf_quantile(s_cal[m], alpha)
    return q


# ----------------------------------------------------------------------------- synthetic data
def gen_data(rng, n, K, kappa0, hetero, misspec, p=5, B=None, C=None):
    """x ~ N(0, I_p); mean m(x) = softmax(B x [+ C g(x)]); y ~ Dirichlet(kappa(x) m(x)), kappa = kappa0 exp(hetero*x1).
    Returns x, y, kappa. B, C fixed per scenario (drawn from a scenario-specific rng by caller)."""
    x = rng.standard_normal((n, p))
    eta = x @ B
    if misspec:
        g = np.stack([np.sin(2 * x[:, 0]) * x[:, 1], x[:, 2] ** 2 - 1, np.cos(2 * x[:, 3]), x[:, 0] * x[:, 4]], 1)
        eta = eta + g @ C
    m = softmax(eta, axis=1)
    kappa = kappa0 * np.exp(hetero * x[:, 0])
    a = np.maximum(kappa[:, None] * m, 1e-300)
    gm = rng.gamma(a)
    s = gm.sum(1, keepdims=True)
    y = gm / np.where(s > 0, s, 1.0)
    bad = (s[:, 0] == 0)  # all-underflow: put mass on argmax of m
    if bad.any():
        y[bad] = np.eye(K)[m[bad].argmax(1)]
    return x, y, kappa


def scenario_params(K, seed=12345, p=5):
    r = np.random.default_rng(seed + K)
    B = r.standard_normal((p, K)) * 0.9
    C = r.standard_normal((4, K)) * 0.9
    return B, C


# ----------------------------------------------------------------------------- mean model
def fit_softmax_reg(x, y, l2=1e-3):
    """Multinomial logistic regression with soft labels (cross-entropy), L-BFGS. Returns predict(x)."""
    n, p = x.shape; K = y.shape[1]
    X = np.hstack([np.ones((n, 1)), x])

    def fg(w):
        W = w.reshape(p + 1, K)
        P = softmax(X @ W, axis=1)
        loss = -(y * np.log(np.maximum(P, EPS))).sum() / n + 0.5 * l2 * (W[1:] ** 2).sum()
        G = X.T @ (P - y) / n
        G[1:] += l2 * W[1:]
        return loss, G.ravel()

    res = minimize(fg, np.zeros((p + 1) * K), jac=True, method="L-BFGS-B", options={"maxiter": 300})
    W = res.x.reshape(p + 1, K)
    return lambda xn: softmax(np.hstack([np.ones((len(xn), 1)), xn]) @ W, axis=1)


def fit_logscale(x, r, l2=1.0):
    """Ridge regression of log(r+tiny) on [1, x]; returns sigma_hat(x) = exp(fitted) (positive)."""
    X = np.hstack([np.ones((len(x), 1)), x]); t = np.log(np.maximum(r, 1e-6))
    A = X.T @ X + l2 * np.eye(X.shape[1]); A[0, 0] -= l2
    w = np.linalg.solve(A, X.T @ t)
    return lambda xn: np.exp(np.hstack([np.ones((len(xn), 1)), xn]) @ w)


# ----------------------------------------------------------------------------- metrics
def slice_cov(cov, bins, nb):
    """coverage per bin; returns (min coverage, max |cov-mean target| handled by caller)."""
    return np.array([cov[bins == b].mean() for b in range(nb) if (bins == b).any()])


def quantile_bins(v, nb):
    qs = np.quantile(v, np.linspace(0, 1, nb + 1)[1:-1])
    return np.searchsorted(qs, v, side="right")


def evaluate_sets(inside, cov_true, conf, oracle=None, nb=5):
    """inside: (n_test, n_ref) membership of reference targets; cov_true: (n_test,) bool coverage of own target.
    Returns dict of metrics."""
    out = {"cov": cov_true.mean(), "mm": inside.mean()}
    b = quantile_bins(conf, nb)
    sc = slice_cov(cov_true, b, nb)
    out["wsc_conf"] = sc.min()
    if oracle is not None:
        b2 = quantile_bins(oracle, nb)
        sc2 = slice_cov(cov_true, b2, nb)
        out["wsc_orac"] = sc2.min()
    return out
