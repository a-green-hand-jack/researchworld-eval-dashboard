"""Outcome model, randomisation designs, estimators, and theory for GATE estimation under interference."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp

# --------------------------------------------------------------------------------------
# Outcome model
# --------------------------------------------------------------------------------------


def h_s(f, s):
    """Normalised sigmoid response h_s: [0,1]->[0,1], h(0)=0, h(1)=1; s=0 is the identity (linear)."""
    f = np.asarray(f, dtype=float)
    if s == 0:
        return f
    sig = lambda x: 1.0 / (1.0 + np.exp(-x))
    return (sig(s * (f - 0.5)) - sig(-s / 2)) / (sig(s / 2) - sig(-s / 2))


def h_s_prime(f, s):
    if s == 0:
        return np.ones_like(np.asarray(f, dtype=float))
    sig = lambda x: 1.0 / (1.0 + np.exp(-x))
    x = sig(s * (np.asarray(f, dtype=float) - 0.5))
    return s * x * (1 - x) / (sig(s / 2) - sig(-s / 2))


@dataclass
class OutcomeSpec:
    delta: float = 1.0       # direct effect
    beta: float = 1.0        # total spillover effect at full saturation
    s: float = 0.0           # nonlinearity of exposure response (0 = linear in neighbour fraction)
    channel: str = "frac"    # 'frac' | 'count' | 'twohop'
    omega: float = 0.0       # weight of two-hop exposure (channel='twohop')
    sigma: float = 1.0       # sd of idiosyncratic baseline noise
    comm_sd: float = 1.0     # sd of community-level baseline effect
    deg_coef: float = 0.5    # baseline loading on standardised log degree


class Population:
    """Fixed finite population: graph, baseline outcomes (incl. fixed noise) and potential-outcome map."""

    def __init__(self, A: sp.csr_matrix, labels: np.ndarray, spec: OutcomeSpec, rng: np.random.Generator,
                 A_true: sp.csr_matrix | None = None):
        self.A = A                      # graph seen by the analyst
        self.At = A if A_true is None else A_true   # graph that actually carries interference
        self.n = A.shape[0]
        self.labels = labels
        self.spec = spec
        self.deg = np.asarray(A.sum(1)).ravel()
        self.degt = np.asarray(self.At.sum(1)).ravel()
        self.dbar_t = self.degt.mean()
        ld = np.log(self.degt)
        K = labels.max() + 1
        u = rng.normal(size=K)
        self.base = (spec.comm_sd * u[labels] + spec.deg_coef * (ld - ld.mean()) / ld.std()
                     + spec.sigma * rng.normal(size=self.n))
        self._A2 = None
        if spec.channel == "twohop":
            B = (self.At @ self.At).tocsr()
            B.setdiag(0)
            B.eliminate_zeros()
            B = B - B.multiply(self.At)    # distance exactly two
            B.data = (B.data > 0).astype(float)
            B.eliminate_zeros()
            self._A2 = B
            self.deg2 = np.asarray(B.sum(1)).ravel()

    def exposure(self, Z, A=None):
        A = self.At if A is None else A
        deg = self.degt if A is self.At else self.deg
        return (A @ Z) / deg[:, None]

    def outcome(self, Z: np.ndarray) -> np.ndarray:
        """Z: n x R (0/1). Returns noiseless-given-population outcomes n x R."""
        sp_ = self.spec
        F = (self.At @ Z) / self.degt[:, None]
        if sp_.channel == "frac":
            g = sp_.beta * h_s(F, sp_.s)
        elif sp_.channel == "count":
            g = sp_.beta * (self.At @ Z) / self.dbar_t
        elif sp_.channel == "twohop":
            d2 = np.maximum(self.deg2, 1)[:, None]
            F2 = np.where(self.deg2[:, None] > 0, (self._A2 @ Z) / d2, F)
            g = sp_.beta * ((1 - sp_.omega) * h_s(F, sp_.s) + sp_.omega * h_s(F2, sp_.s))
        else:
            raise ValueError(sp_.channel)
        return self.base[:, None] + sp_.delta * Z + g

    def gate(self) -> float:
        Z = np.stack([np.ones(self.n), np.zeros(self.n)], axis=1)
        Y = self.outcome(Z)
        return float(np.mean(Y[:, 0] - Y[:, 1]))


# --------------------------------------------------------------------------------------
# Designs
# --------------------------------------------------------------------------------------


@dataclass
class Design:
    kind: str = "bernoulli"     # 'bernoulli' | 'cluster' | 'rsat'
    p: float = 0.5

    def draw(self, n, labels, R, rng):
        if self.kind == "bernoulli":
            return (rng.random((n, R)) < self.p).astype(np.float64)
        K = labels.max() + 1
        if self.kind == "cluster":
            zc = (rng.random((K, R)) < self.p).astype(np.float64)
            return zc[labels]
        if self.kind == "rsat":
            q = rng.random((K, R))               # cluster saturation ~ U(0,1) (mean 0.5)
            return (rng.random((n, R)) < q[labels]).astype(np.float64)
        raise ValueError(self.kind)

    def log_pi(self, A, labels):
        """log P(unit and all its neighbours treated); log P(all control) (Hajek exposure 'full neighbourhood')."""
        n = A.shape[0]
        deg = np.asarray(A.sum(1)).ravel()
        if self.kind == "bernoulli":
            return (deg + 1) * np.log(self.p), (deg + 1) * np.log(1 - self.p)
        K = labels.max() + 1
        onehot = sp.csr_matrix((np.ones(n), (np.arange(n), labels)), shape=(n, K))
        M = ((A + sp.identity(n, format="csr")) @ onehot).tocsr()
        if self.kind == "cluster":
            k = np.diff(M.indptr)
            return k * np.log(self.p), k * np.log(1 - self.p)
        if self.kind == "rsat":
            M.data = np.log(M.data + 1.0)
            ls = -np.asarray(M.sum(1)).ravel()
            return ls, ls
        raise ValueError(self.kind)


# --------------------------------------------------------------------------------------
# Estimators
# --------------------------------------------------------------------------------------

REGRESSION = ["lin_frac", "lin_count", "lin_both", "quad_frac", "spline", "oracle_h", "two_hop"]


@dataclass
class Ctx:
    deg: np.ndarray
    dbar: float
    dstd: np.ndarray
    s_oracle: float = 0.0


def phi(name, z, f, ctx: Ctx, f2=None):
    one = np.ones_like(z)
    cnt = f * ctx.deg / ctx.dbar
    if name == "lin_frac":
        cols = [one, z, f]
    elif name == "lin_count":
        cols = [one, z, cnt]
    elif name == "lin_both":
        cols = [one, z, f, cnt, ctx.dstd]
    elif name == "quad_frac":
        cols = [one, z, f, f ** 2]
    elif name == "spline":
        r = lambda x: np.maximum(x, 0)
        cols = [one, z, f, r(f - .25), r(f - .5), r(f - .75)]
    elif name == "oracle_h":
        cols = [one, z, h_s(f, ctx.s_oracle)]
    elif name == "two_hop":
        cols = [one, z, f, f2]
    else:
        raise ValueError(name)
    return np.stack(cols, axis=1)


def ols_gate(name, y, z, f, ctx, f2=None, f2_all=None, B=None):
    """Regression-based GATE estimate with HC1 and (optionally) 2-hop network-HAC standard errors."""
    n = len(y)
    X = phi(name, z, f, ctx, f2)
    one = np.ones(n)
    zero = np.zeros(n)
    X1 = phi(name, one, one, ctx, one)
    X0 = phi(name, zero, zero, ctx, zero)
    a = X1.mean(0) - X0.mean(0)
    XtX = X.T @ X
    bread = np.linalg.pinv(XtX, rcond=1e-10)
    beta = bread @ (X.T @ y)
    r = y - X @ beta
    est = float(a @ beta)
    S = X * r[:, None]
    k = np.linalg.matrix_rank(X)
    V = bread @ (S.T @ S) @ bread * n / max(n - k, 1)
    se_hc = float(np.sqrt(max(a @ V @ a, 0)))
    se_hac = np.nan
    if B is not None:
        Vh = bread @ (S.T @ (B @ S)) @ bread * n / max(n - k, 1)
        se_hac = float(np.sqrt(max(a @ Vh @ a, 0)))
    # model-based (homoskedastic) variance with plug-in residual variance
    s2 = float(r @ r / max(n - k, 1))
    se_mb = float(np.sqrt(max(s2 * (a @ bread @ a), 0)))
    return est, se_hc, se_hac, se_mb, s2


def dm_gate(y, z):
    t = z > 0.5
    if t.all() or (~t).all():
        return np.nan
    return float(y[t].mean() - y[~t].mean())


def hajek_gate(y, z, cnt, deg, lpi1, lpi0):
    t1 = (z > 0.5) & (cnt >= deg - 1e-9)
    t0 = (z < 0.5) & (cnt <= 1e-9)
    if t1.sum() == 0 or t0.sum() == 0:
        return np.nan, int(t1.sum()), int(t0.sum())
    w1 = np.exp(-lpi1[t1])
    w0 = np.exp(-lpi0[t0])
    return float((w1 * y[t1]).sum() / w1.sum() - (w0 * y[t0]).sum() / w0.sum()), int(t1.sum()), int(t0.sum())


def gbm_gate(y, z, f, ctx):
    from sklearn.ensemble import HistGradientBoostingRegressor
    n = len(y)
    mk = lambda zz, ff: np.stack([zz, ff, ff * ctx.deg / ctx.dbar, ctx.dstd], axis=1)
    m = HistGradientBoostingRegressor(max_iter=100, learning_rate=0.1, max_depth=4, random_state=0)
    m.fit(mk(z, f), y)
    return float(np.mean(m.predict(mk(np.ones(n), np.ones(n))) - m.predict(mk(np.zeros(n), np.zeros(n)))))


# --------------------------------------------------------------------------------------
# Theory helpers
# --------------------------------------------------------------------------------------


def harmonic_degree(deg):
    return float(1.0 / np.mean(1.0 / deg))


def var_law(deg, p, sigma2_res):
    """Asymptotic variance of the linear [1,z,f] regression GATE estimator under Bernoulli(p):
    sigma2 (1 + d_H) / (n p (1-p)),  d_H = harmonic mean degree."""
    n = len(deg)
    return sigma2_res * (1.0 + harmonic_degree(deg)) / (n * p * (1 - p))


def bern_frac_pseudotrue(deg, p, spec: OutcomeSpec):
    """Probability limit of the linear [1,z,f] estimator for channel='frac' under Bernoulli(p):
    delta + Cov(f, g(f))/Var(f), pooled over units, with f_i = Bin(d_i,p)/d_i exactly."""
    from scipy.stats import binom
    num = den = 0.0
    ds, cs = np.unique(deg.astype(int), return_counts=True)
    for d, c in zip(ds, cs):
        k = np.arange(d + 1)
        pm = binom.pmf(k, d, p)
        f = k / d
        num += c * np.sum(pm * (f - p) * h_s(f, spec.s))
        den += c * np.sum(pm * (f - p) ** 2)
    return spec.delta + spec.beta * num / den


def local_slope(p, spec):
    return spec.delta + spec.beta * float(h_s_prime(p, spec.s))
