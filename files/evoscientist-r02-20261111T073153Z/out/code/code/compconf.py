"""compconf: split / Mondrian / cross conformal prediction regions for simplex-valued
(compositional) targets, with several nonconformity scores and evaluation utilities.

All regions are of the form C(x) = {y in simplex : s(y, f(x)) <= q(x)}.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax, logsumexp

TINY = 1e-12


# ----------------------------------------------------------------------------
# compositional geometry
# ----------------------------------------------------------------------------
def helmert_basis(K):
    """(K, K-1) orthonormal basis of the hyperplane orthogonal to 1 (ilr basis)."""
    V = np.zeros((K, K - 1))
    for j in range(1, K):
        V[:j, j - 1] = 1.0 / j
        V[j, j - 1] = -1.0
        V[:, j - 1] *= np.sqrt(j / (j + 1.0))
    return V


def clr(p):
    l = np.log(np.maximum(p, TINY))
    return l - l.mean(-1, keepdims=True)


def repl(y, eps):
    """Additive zero replacement followed by closure."""
    K = y.shape[-1]
    return (y + eps) / (1.0 + K * eps)


def gini(F):
    return 1.0 - (F ** 2).sum(-1)


def entropy(F):
    return -(F * np.log(np.maximum(F, TINY))).sum(-1)


# ----------------------------------------------------------------------------
# scores
# ----------------------------------------------------------------------------
def _sqdist(A, B):
    """pairwise squared euclidean distance, rows of A (n,d) vs rows of B (m,d) -> (n,m)."""
    d = (A ** 2).sum(1)[:, None] + (B ** 2).sum(1)[None, :] - 2.0 * A @ B.T
    return np.maximum(d, 0.0)


class Score:
    """Nonconformity score s(y, f). `paired(Y,F)`: row-wise (n,). `pair(F,Y)`: (nF,nY)."""

    def __init__(self, name, K, eps=1e-3, aux=None):
        self.name, self.K, self.eps = name, K, eps
        self.aux = aux or {}
        self.V = helmert_basis(K)
        if name == "mah":
            S = self.aux["ilr_cov"]
            L = np.linalg.cholesky(np.linalg.inv(S + 1e-6 * np.eye(K - 1)))
            self.L = L
        if name == "l2n":
            self.coef = self.aux["sig_coef"]
            self.sig_floor = self.aux["sig_floor"]

    # embeddings for euclidean-type scores --------------------------------
    def _ey(self, Y):
        n = self.name
        if n in ("l2", "l2n"):
            return Y
        if n == "hell":
            return np.sqrt(Y)
        if n == "ait":
            return clr(repl(Y, self.eps))
        if n == "mah":
            return (clr(repl(Y, self.eps)) @ self.V) @ self.L
        raise ValueError(n)

    def _ef(self, F):
        n = self.name
        if n in ("l2", "l2n"):
            return F
        if n == "hell":
            return np.sqrt(F)
        if n == "ait":
            return clr(F)
        if n == "mah":
            return (clr(F) @ self.V) @ self.L
        raise ValueError(n)

    def sigma(self, F):
        s = self.coef[0] + self.coef[1] * gini(F)
        return np.maximum(s, self.sig_floor)

    def paired(self, Y, F):
        n = self.name
        if n in ("l2", "l2n", "hell", "ait", "mah"):
            d = np.sqrt(((self._ey(Y) - self._ef(F)) ** 2).sum(-1))
            if n == "l2n":
                d = d / self.sigma(F)
            return d
        if n == "l1":
            return 0.5 * np.abs(Y - F).sum(-1)
        if n == "linf":
            return np.abs(Y - F).max(-1)
        if n == "kl":
            Fc = np.maximum(F, TINY)
            with np.errstate(divide="ignore", invalid="ignore"):
                t = np.where(Y > 0, Y * np.log(np.maximum(Y, TINY)), 0.0).sum(-1)
            return np.maximum(t - (Y * np.log(Fc)).sum(-1), 0.0)
        raise ValueError(n)

    def pair(self, F, Y, chunk=200):
        n = self.name
        if n in ("l2", "l2n", "hell", "ait", "mah"):
            d = np.sqrt(_sqdist(self._ef(F), self._ey(Y)))
            if n == "l2n":
                d = d / self.sigma(F)[:, None]
            return d
        if n == "kl":
            Fc = np.log(np.maximum(F, TINY))
            hy = np.where(Y > 0, Y * np.log(np.maximum(Y, TINY)), 0.0).sum(-1)
            return np.maximum(hy[None, :] - Fc @ Y.T, 0.0)
        out = np.empty((F.shape[0], Y.shape[0]))
        for i in range(0, F.shape[0], chunk):
            D = np.abs(Y[None, :, :] - F[i:i + chunk, None, :])
            out[i:i + chunk] = 0.5 * D.sum(-1) if n == "l1" else D.max(-1)
        return out


# ----------------------------------------------------------------------------
# predictor: softmax regression with soft labels
# ----------------------------------------------------------------------------
def fit_softmax_reg(X, Ysoft, l2=1e-3):
    n, d = X.shape
    K = Ysoft.shape[1]
    Xa = np.hstack([X, np.ones((n, 1))])

    def fg(w):
        W = w.reshape(d + 1, K)
        Z = Xa @ W
        lse = logsumexp(Z, axis=1, keepdims=True)
        logP = Z - lse
        loss = -(Ysoft * logP).sum() / n + 0.5 * l2 * (W[:-1] ** 2).sum()
        G = Xa.T @ (np.exp(logP) - Ysoft) / n
        G[:-1] += l2 * W[:-1]
        return loss, G.ravel()

    r = minimize(fg, np.zeros((d + 1) * K), jac=True, method="L-BFGS-B", options={"maxiter": 300})
    W = r.x.reshape(d + 1, K)
    return lambda Xn: softmax(np.hstack([Xn, np.ones((len(Xn), 1))]) @ W, axis=1)


# ----------------------------------------------------------------------------
# aux fitting (uses a held-out "aux" fold; validity does not depend on it)
# ----------------------------------------------------------------------------
def fit_aux(Yaux, Faux, eps):
    K = Yaux.shape[1]
    V = helmert_basis(K)
    R = (clr(repl(Yaux, eps)) - clr(Faux)) @ V
    ilr_cov = R.T @ R / len(R)
    r2 = np.sqrt(((Yaux - Faux) ** 2).sum(1))
    A = np.stack([np.ones(len(Faux)), gini(Faux)], 1)
    coef = np.linalg.lstsq(A, r2, rcond=None)[0]
    return dict(ilr_cov=ilr_cov, sig_coef=coef, sig_floor=0.2 * r2.mean())


# ----------------------------------------------------------------------------
# conformal calibration
# ----------------------------------------------------------------------------
def conf_quantile(scores, alpha):
    n = len(scores)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    if k > n:
        return np.inf
    return np.partition(scores, k - 1)[k - 1]


def group_of(F, edges):
    """Entropy-tercile group index from edges (2 thresholds)."""
    return np.searchsorted(edges, entropy(F))


def mondrian_thresholds(scores, groups_cal, groups_test, alpha, ngroups=3):
    q = np.full(ngroups, np.inf)
    for g in range(ngroups):
        m = groups_cal == g
        if m.sum() > 0:
            q[g] = conf_quantile(scores[m], alpha)
    return q[groups_test]


# ----------------------------------------------------------------------------
# DGPs
# ----------------------------------------------------------------------------
def make_world(rng, K, d=5, scale=0.6):
    return rng.normal(0, scale, size=(d, K))


def gen_data(rng, W, n, dgp, K, **kw):
    d = W.shape[0]
    X = rng.normal(size=(n, d))
    eta = X @ W
    m = softmax(eta, axis=1)
    if dgp == "ln":
        sig = kw.get("sigma", 0.5)
        Z = eta + sig * rng.normal(size=eta.shape)
        Y = softmax(Z, axis=1)
    elif dgp == "ln_het":
        sig = (0.35 * np.exp(0.5 * X[:, [0]]))
        Z = eta + sig * rng.normal(size=eta.shape)
        Y = softmax(Z, axis=1)
    elif dgp == "dir":
        c = kw.get("conc", 20.0)
        G = rng.gamma(np.maximum(c * m, 1e-3))
        Y = G / G.sum(1, keepdims=True)
        bad = ~np.isfinite(Y).all(1)
        Y[bad] = m[bad]
    elif dgp == "mult":
        N = kw.get("N", 20)
        Y = np.stack([rng.multinomial(N, p) for p in m]) / N
    else:
        raise ValueError(dgp)
    return X, Y, m


# ----------------------------------------------------------------------------
# evaluation of regions given thresholds
# ----------------------------------------------------------------------------
def ent_edges(F):
    h = entropy(F)
    return np.quantile(h, [1 / 3, 2 / 3])


def evaluate(score, Ft, Yt, qt, pool, unif=None, grp_edges=None, chunk=250):
    """Coverage and size diagnostics for regions {y: s(y,F_t) <= qt}.

    Returns dict with per-test-point covered flags (T,), pool size (T,), uniform size (T,) or None.
    """
    cov = (score.paired(Yt, Ft) <= qt)
    sp = np.empty(len(Ft))
    su = None if unif is None else np.empty(len(Ft))
    for i in range(0, len(Ft), chunk):
        sl = slice(i, i + chunk)
        sp[sl] = (score.pair(Ft[sl], pool) <= qt[sl, None]).mean(1)
        if unif is not None:
            su[sl] = (score.pair(Ft[sl], unif) <= qt[sl, None]).mean(1)
    return cov, sp, su


def group_summary(cov, Ft, Yt, edges, K):
    """Group-wise coverage counts: entropy terciles (3), argmax class (K), zeros-in-Y (2)."""
    out = {}
    g = np.searchsorted(edges, entropy(Ft))
    for j in range(3):
        m = g == j
        out[f"ent{j}"] = (cov[m].sum(), m.sum())
    a = Ft.argmax(1)
    for j in range(K):
        m = a == j
        out[f"arg{j}"] = (cov[m].sum(), m.sum())
    z = (Yt <= 0).any(1)
    for j, m in enumerate([~z, z]):
        out[f"zero{j}"] = (cov[m].sum(), m.sum())
    return out
