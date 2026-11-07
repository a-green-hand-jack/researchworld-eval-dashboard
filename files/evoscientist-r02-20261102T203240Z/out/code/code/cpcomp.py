"""cpcomp: split-conformal prediction regions for compositional (simplex-valued) responses.

Contents
  * simplex utilities (closure, clr, Gini, entropy, Dirichlet sampling)
  * synthetic data-generating processes (DGPs)
  * softmax-regression predictor trained with soft labels
  * nonconformity scores (plain, learned-scale, Mondrian)
  * split / Mondrian / weighted conformal calibration
  * evaluation metrics (coverage, geometry-free efficiency, conditional coverage)
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import gammaln, logsumexp, xlogy, softmax

TINY = 1e-300

# ----------------------------------------------------------------------------
# simplex utilities
# ----------------------------------------------------------------------------

def closure(a, floor=0.0):
    a = np.maximum(np.asarray(a, float), floor)
    return a / a.sum(-1, keepdims=True)


def gini(h):
    return 1.0 - (h ** 2).sum(-1)


def entropy(h):
    return -xlogy(h, h).sum(-1)


def clr(p, delta):
    """centred log-ratio after additive zero replacement  (p+delta)/(1+K delta)."""
    q = (p + delta)
    q = q / q.sum(-1, keepdims=True)
    l = np.log(q)
    return l - l.mean(-1, keepdims=True)


def hfeats(h):
    return np.hstack([h, np.log(h + 1e-3), gini(h)[:, None], entropy(h)[:, None]])


def rdirichlet_rows(rng, alpha):
    """one Dirichlet draw per row of alpha (n,K); underflow-safe."""
    g = rng.gamma(alpha)
    g = np.maximum(g, TINY)
    return g / g.sum(-1, keepdims=True)


def rmultinomial_rows(rng, N, p):
    """vectorised multinomial(N,p_i)/N, one draw per row."""
    n, K = p.shape
    c = np.cumsum(p, 1)
    c[:, -1] = 1.0
    u = rng.random((n, N))
    idx = (u[:, :, None] > c[:, None, :]).sum(-1)  # (n,N) in 0..K-1
    out = np.zeros((n, K))
    for k in range(K):
        out[:, k] = (idx == k).sum(1)
    return out / N

# ----------------------------------------------------------------------------
# synthetic DGPs
# ----------------------------------------------------------------------------

class DGP:
    """x ~ N(mu_x, I_d); mean logits eta(x); noise model `kind`.

    kinds: dir (Dirichlet), lnorm (logistic-normal), mult (multinomial counts / N)
    het   : noise level depends on x[0]  (not a function of the predicted mean only)
    nl    : mean function has a nonlinear component the linear predictor cannot fit
    """

    def __init__(self, kind="dir", het=False, nl=False, K=5, d=5, phi=20.0, N=50,
                 sigma=0.5, struct_seed=12345, name=None):
        self.kind, self.het, self.nl, self.K, self.d = kind, het, nl, K, d
        self.phi, self.N, self.sigma = phi, N, sigma
        r = np.random.default_rng(struct_seed)
        self.A = r.normal(0, 0.9, (d, K))
        self.b = r.normal(0, 0.5, K)
        self.B = r.normal(0, 1.0, (d, K))
        L = r.normal(0, 1, (K, K)) * 0.5 + np.eye(K)
        self.L = L / np.sqrt((L ** 2).sum(1, keepdims=True).mean())
        self.name = name or f"{kind}{'_het' if het else ''}{'_nl' if nl else ''}"

    def eta(self, x):
        e = x @ self.A + self.b
        if self.nl:
            e = e + 1.5 * np.sin(x @ self.B)
        return e

    def mean(self, x):
        return softmax(self.eta(x), -1)

    def sample_x(self, rng, n, shift=0.0):
        x = rng.normal(0, 1, (n, self.d))
        x[:, 0] += shift
        return x

    def sample_y(self, rng, x):
        e = self.eta(x)
        n = len(x)
        if self.kind == "dir":
            phi = self.phi * (np.exp(1.2 * x[:, 0]) if self.het else 1.0)
            mu = softmax(e, -1)
            return rdirichlet_rows(rng, mu * phi[:, None] if np.ndim(phi) else mu * phi)
        if self.kind == "lnorm":
            s = self.sigma * (np.exp(0.5 * x[:, 0]) if self.het else np.ones(n))
            eps = rng.normal(0, 1, (n, self.K)) @ self.L.T
            return softmax(e + s[:, None] * eps, -1)
        if self.kind == "mult":
            return rmultinomial_rows(rng, self.N, softmax(e, -1))
        raise ValueError(self.kind)


DGPS = {
    "dir_homo": lambda: DGP("dir"),
    "dir_het": lambda: DGP("dir", het=True),
    "dir_sparse": lambda: DGP("dir", phi=3.0),
    "dir_nl": lambda: DGP("dir", nl=True),
    "lnorm_het": lambda: DGP("lnorm", het=True),
    "mult50": lambda: DGP("mult", N=50),
}

# ----------------------------------------------------------------------------
# predictor: softmax regression fitted to soft labels (cross-entropy)
# ----------------------------------------------------------------------------

class SoftmaxReg:
    def __init__(self, lam=1e-3):
        self.lam = lam

    def fit(self, X, Y):
        n, p = X.shape
        K = Y.shape[1]
        F = np.hstack([np.ones((n, 1)), X])

        def fg(w):
            W = w.reshape(p + 1, K)
            Z = F @ W
            lse = logsumexp(Z, 1, keepdims=True)
            P = np.exp(Z - lse)
            loss = -(Y * (Z - lse)).sum() / n + 0.5 * self.lam * (W[1:] ** 2).sum()
            G = F.T @ (P - Y) / n
            G[1:] += self.lam * W[1:]
            return loss, G.ravel()

        r = minimize(fg, np.zeros((p + 1) * K), jac=True, method="L-BFGS-B",
                     options=dict(maxiter=500))
        self.W = r.x.reshape(p + 1, K)
        return self

    def predict(self, X):
        F = np.hstack([np.ones((len(X), 1)), X])
        return softmax(F @ self.W, -1)

# ----------------------------------------------------------------------------
# nonconformity scores
# ----------------------------------------------------------------------------

class Score:
    """s(h, y, z) = raw(h, y) / scale(h, z); optional Mondrian grouping.
    Arrays broadcast over leading dims; h,y have last dim K."""
    name = "base"
    mondrian = None  # None | 'argmax' | 'gini'

    def fit(self, Yh, Y, Z):
        return self

    def raw(self, h, y):
        raise NotImplementedError

    def scale(self, h, z):
        return np.ones(len(h))

    def group(self, h, z):
        if self.mondrian is None:
            return np.zeros(len(h), int)
        if self.mondrian == "argmax":
            return h.argmax(-1)
        if self.mondrian == "gini":
            return np.searchsorted(self.gedges, gini(h))
        raise ValueError

    ng = 1  # number of Mondrian groups (set in fit for grouped scores)

    def pair(self, h, z, U):
        """scores of all (h_i, U_m): shape (T,M)."""
        return self.raw(h[:, None, :], U[None, :, :]) / self.scale(h, z)[:, None]

    def __call__(self, h, y, z):
        return self.raw(h, y) / self.scale(h, z)


class L2(Score):
    name = "L2"
    def raw(self, h, y): return np.sqrt(((h - y) ** 2).sum(-1))

class L1(Score):
    name = "L1"
    def raw(self, h, y): return np.abs(h - y).sum(-1)

class Linf(Score):
    name = "Linf"
    def raw(self, h, y): return np.abs(h - y).max(-1)

class Hellinger(Score):
    name = "Hellinger"
    def raw(self, h, y): return np.sqrt(((np.sqrt(h) - np.sqrt(y)) ** 2).sum(-1))

class KL(Score):
    """KL(y || h): for one-hot y equals -log h_c (the 'LAC' score)."""
    name = "KL"
    def raw(self, h, y):
        hh = np.maximum(h, 1e-8)
        return (xlogy(y, y) - y * np.log(hh)).sum(-1)

class Aitchison(Score):
    def __init__(self, delta=1e-3):
        self.delta = delta
        self.name = "Aitchison" if delta == 1e-3 else f"Aitchison(d={delta:g})"
    def raw(self, h, y):
        return np.sqrt(((clr(h, self.delta) - clr(y, self.delta)) ** 2).sum(-1))

class Mahalanobis(Score):
    """ellipsoid in clr space; covariance of aux-split clr residuals."""
    def __init__(self, delta=1e-3):
        self.delta = delta
        self.name = "Mahal-clr"
    def fit(self, Yh, Y, Z):
        R = clr(Y, self.delta) - clr(Yh, self.delta)
        S = np.cov(R.T)
        K = S.shape[0]
        P = np.eye(K) - 1.0 / K
        S = S + 1e-3 * np.trace(S) / K * P
        self.Sinv = np.linalg.pinv(S)
        return self
    def raw(self, h, y):
        r = clr(h, self.delta) - clr(y, self.delta)
        return np.sqrt(np.einsum("...i,ij,...j->...", r, self.Sinv, r))

class DirNLL(Score):
    """negative log density of Dirichlet(phi * h) at y (HPD-type region)."""
    def __init__(self, delta=1e-3):
        self.delta = delta
        self.name = "DirNLL"
    def _z(self, p):
        q = p + self.delta
        return q / q.sum(-1, keepdims=True)
    def fit(self, Yh, Y, Z):
        h, y = self._z(Yh), self._z(Y)
        ly = np.log(y)
        def nll(lp):
            phi = np.exp(lp)
            return -(gammaln(phi) - gammaln(phi * h).sum(1) + ((phi * h - 1) * ly).sum(1)).mean()
        self.phi = float(np.exp(minimize_scalar(nll, bounds=(-3, 8), method="bounded").x))
        return self
    def raw(self, h, y):
        h, y = self._z(h), self._z(y)
        a = self.phi * h
        return -(gammaln(self.phi) - gammaln(a).sum(-1) + ((a - 1) * np.log(y)).sum(-1))

class L2Gini(Score):
    """L2 divided by sqrt(Gini(h)): first-order variance stabiliser for Dirichlet noise."""
    name = "L2/sqrtGini"
    def raw(self, h, y): return np.sqrt(((h - y) ** 2).sum(-1))
    def scale(self, h, z): return np.sqrt(gini(h) + 1e-3)

class L2Learned(Score):
    """locally weighted L2 (Lei et al. 2018): sigma_hat(x) = exp(ridge fit of log residual on aux split)."""
    name = "L2/learned-sigma"
    def fit(self, Yh, Y, Z):
        s = np.sqrt(((Yh - Y) ** 2).sum(-1))
        F = np.hstack([np.ones((len(Z), 1)), Z])
        self.mu, self.sd = F[:, 1:].mean(0), F[:, 1:].std(0) + 1e-9
        F[:, 1:] = (F[:, 1:] - self.mu) / self.sd
        t = np.log(s + 1e-3)
        self.w = np.linalg.solve(F.T @ F + 1.0 * np.eye(F.shape[1]), F.T @ t)
        return self
    def raw(self, h, y): return np.sqrt(((h - y) ** 2).sum(-1))
    def scale(self, h, z):
        F = (z - self.mu) / self.sd
        return np.exp(F @ self.w[1:] + self.w[0])

class L2Mond(L2):
    def __init__(self, kind):
        self.mondrian = kind
        self.name = f"L2-Mondrian({kind})"
    def fit(self, Yh, Y, Z):
        self.gedges = np.quantile(gini(Yh), [0.25, 0.5, 0.75])
        self.ng = Yh.shape[1] if self.mondrian == "argmax" else 4
        return self


def make_scores(names, delta=1e-3):
    reg = {
        "L2": L2, "L1": L1, "Linf": Linf, "Hellinger": Hellinger, "KL": KL,
        "Aitchison": lambda: Aitchison(delta), "Mahal-clr": lambda: Mahalanobis(delta),
        "DirNLL": lambda: DirNLL(delta), "L2/sqrtGini": L2Gini, "L2/learned-sigma": L2Learned,
        "L2-Mondrian(argmax)": lambda: L2Mond("argmax"), "L2-Mondrian(gini)": lambda: L2Mond("gini"),
    }
    return [reg[n]() for n in names]

ALL_SCORES = ["L2", "L1", "Linf", "Hellinger", "KL", "Aitchison", "Mahal-clr", "DirNLL",
              "L2/sqrtGini", "L2/learned-sigma", "L2-Mondrian(argmax)", "L2-Mondrian(gini)"]

# ----------------------------------------------------------------------------
# conformal calibration
# ----------------------------------------------------------------------------

def conf_quantile(s, alpha):
    n = len(s)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    if k > n:
        return np.inf
    return np.sort(s)[k - 1]


def calibrate(sc: Score, s_cal, g_cal, alpha, ng=None):
    ng = ng or sc.ng
    q = np.full(max(ng, 1), np.inf)
    for g in np.unique(g_cal):
        q[g] = conf_quantile(s_cal[g_cal == g], alpha)
    return q


def get_q(q, g):
    g = np.minimum(g, len(q) - 1)
    return q[g]


def weighted_thresholds(s_cal, w_cal, w_test, alpha):
    """per-test-point weighted conformal threshold (Tibshirani et al. 2019).
    returns q_i = smallest s such that sum_{j: s_j<=s} w_j >= (1-alpha)(W + w_i)."""
    o = np.argsort(s_cal)
    ss, cw = s_cal[o], np.cumsum(w_cal[o])
    W = cw[-1]
    target = (1 - alpha) * (W + w_test)
    idx = np.searchsorted(cw, target, side="left")
    out = np.full(len(w_test), np.inf)
    ok = idx < len(ss)
    out[ok] = ss[idx[ok]]
    return out

# ----------------------------------------------------------------------------
# evaluation
# ----------------------------------------------------------------------------

REF_A = (0.1, 0.3, 1.0, 3.0)


def evaluate(sc, q, h, y, z, rng, alpha, full=True, Tvol=600, Mvol=200, Mx=10, U=None,
             gedges=None):
    """metrics for the set C(x) = {u : s(h(x),u,z) <= q[g(x)]} over test arrays."""
    g = sc.group(h, z)
    qt = get_q(q, g)
    s = sc(h, y, z)
    cov = s <= qt
    out = dict(cov=cov.mean(), q=float(np.median(q[np.isfinite(q)])) if np.isfinite(q).any() else np.inf)
    T = len(h)
    G = gini(h)
    edges = np.quantile(G, [0.2, 0.4, 0.6, 0.8]) if gedges is None else gedges
    b = np.searchsorted(edges, G)
    cb = np.array([cov[b == i].mean() if (b == i).any() else np.nan for i in range(5)])
    for i in range(5):
        out[f"covG{i}"] = cb[i]
    out["gapG_max"] = np.nanmax(np.abs(cb - (1 - alpha)))
    out["gapG_mean"] = np.nanmean(np.abs(cb - (1 - alpha)))
    out["minG"] = np.nanmin(cb)
    am = h.argmax(-1)
    K = h.shape[1]
    cc = np.array([cov[am == k].mean() for k in range(K) if (am == k).sum() >= 100])
    out["gapC_max"] = np.abs(cc - (1 - alpha)).max() if len(cc) else np.nan
    out["minC"] = cc.min() if len(cc) else np.nan
    if full:
        # geometry-free "cross coverage": x_i paired with y_j of unrelated test points
        idx = rng.integers(0, T, (T, Mx))
        ii = np.arange(T)[:, None]
        idx = np.where(idx == ii, (idx + 1) % T, idx)
        sx = sc.raw(h[:, None, :], y[idx]) / sc.scale(h, z)[:, None]
        out["xc"] = float((sx <= qt[:, None]).mean())
        # reference-measure volume fractions under Dirichlet(a,...,a)
        sel = rng.choice(T, min(Tvol, T), replace=False)
        for a in REF_A:
            Uu = rdirichlet_rows(rng, np.full((Mvol, K), a))
            sp = sc.pair(h[sel], z[sel], Uu)
            out[f"vf{a:g}"] = float((sp <= qt[sel][:, None]).mean())
    return out

# ----------------------------------------------------------------------------
# one replicate on a synthetic DGP
# ----------------------------------------------------------------------------

def make_split(dgp, rng, n_tr=1000, n_aux=500, n_cal=2000, n_te=4000, shift_te=0.0):
    out = {}
    for nm, n, sh in [("tr", n_tr, 0.0), ("aux", n_aux, 0.0), ("cal", n_cal, 0.0), ("te", n_te, shift_te)]:
        x = dgp.sample_x(rng, n, sh)
        out[nm] = (x, dgp.sample_y(rng, x))
    return out


def fit_predictor(split, lam=1e-3):
    pred = SoftmaxReg(lam).fit(*split["tr"])
    H = {k: pred.predict(split[k][0]) for k in split}
    return pred, H


def zfeat(x, h):
    return np.hstack([x, hfeats(h)])
