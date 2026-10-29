"""Bradley-Terry fitting on aggregated comparison data, plus first-order influence.

Data model
----------
A comparison dataset is aggregated into *types*: unique (row-design, label) pairs.
Each type t has a design vector x_t in R^P (P = K players [+ optional home-advantage
coordinate]), a label y_t in {0, 0.5, 1} (1 = first listed player wins, 0.5 = tie)
and a non-negative count n_t.  Because identical observations have identical
influence, all perturbation searches operate on counts, which makes refits cheap
even for >100k comparisons.

Model: P(first wins) = sigmoid(x_t^T theta).  Ties enter as y=0.5 (half a win each),
which is the standard "ties as half wins" convention.
Loss: L(theta) = sum_t n_t * l(y_t, x_t^T theta) + lam/2 * ||theta_players||^2 ,
l(y,s) = -y log s(s) - (1-y) log s(-s).  The tiny ridge fixes the translation gauge
(minimiser has sum(theta_players)=0) and guards against separation.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from scipy.special import expit


@dataclass
class CompData:
    """Aggregated comparison data.

    i, j : int arrays (T,)  first / second player index of each type
    y    : float array (T,) label for the first player (1 win, 0 loss, 0.5 tie)
    n    : float array (T,) counts
    home : float array (T,) 1 if first player has home advantage (else 0); optional
    names: list of player names (K,)
    """
    i: np.ndarray
    j: np.ndarray
    y: np.ndarray
    n: np.ndarray
    names: list
    home: np.ndarray | None = None
    meta: dict = field(default_factory=dict)

    @property
    def K(self):
        return len(self.names)

    @property
    def P(self):
        return self.K + (1 if self.home is not None else 0)

    @property
    def N(self):
        return float(self.n.sum())

    def copy(self):
        return CompData(self.i.copy(), self.j.copy(), self.y.copy(), self.n.copy(),
                        list(self.names), None if self.home is None else self.home.copy(),
                        dict(self.meta))

    def design(self, idx=None):
        """Dense design matrix X (T x P)."""
        ii = self.i if idx is None else self.i[idx]
        jj = self.j if idx is None else self.j[idx]
        T = len(ii)
        X = np.zeros((T, self.P))
        X[np.arange(T), ii] += 1.0
        X[np.arange(T), jj] -= 1.0
        if self.home is not None:
            X[:, -1] = self.home if idx is None else self.home[idx]
        return X


def from_records(a, b, y, names=None, home=None, meta=None):
    """Aggregate per-comparison records into CompData.

    a, b : arrays of player identifiers (any hashable); y : 1 (a wins), 0 (b wins), 0.5 tie
    home : optional 0/1 array, 1 if `a` is at home.
    """
    a = np.asarray(a)
    b = np.asarray(b)
    y = np.asarray(y, dtype=float)
    if names is None:
        names = sorted(set(a.tolist()) | set(b.tolist()))
    idx = {nm: k for k, nm in enumerate(names)}
    ai = np.array([idx[v] for v in a])
    bi = np.array([idx[v] for v in b])
    if home is None:
        # canonical orientation i<j (label flipped accordingly)
        sw = ai > bi
        ii = np.where(sw, bi, ai)
        jj = np.where(sw, ai, bi)
        yy = np.where(sw, 1.0 - y, y)
        hh = None
        key = np.stack([ii, jj, (yy * 2).round().astype(int)], 1)
    else:
        home = np.asarray(home, dtype=float)
        ii, jj, yy, hh = ai, bi, y, home
        key = np.stack([ii, jj, (yy * 2).round().astype(int), hh.astype(int)], 1)
    uniq, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    d = CompData(i=uniq[:, 0].astype(int), j=uniq[:, 1].astype(int), y=uniq[:, 2] / 2.0,
                 n=cnt.astype(float), names=list(names),
                 home=None if home is None else uniq[:, 3].astype(float), meta=meta or {})
    return d


def expand_records(d: CompData):
    """Inverse of from_records: per-comparison arrays (i, j, y, home)."""
    reps = d.n.astype(int)
    i = np.repeat(d.i, reps)
    j = np.repeat(d.j, reps)
    y = np.repeat(d.y, reps)
    h = None if d.home is None else np.repeat(d.home, reps)
    return i, j, y, h


@dataclass
class Fit:
    theta: np.ndarray          # (P,)
    H: np.ndarray              # Hessian of the penalised loss (P x P)
    Hinv: np.ndarray
    p: np.ndarray              # fitted P(first wins) per type
    X: np.ndarray              # design (T x P)
    converged: bool
    iters: int

    def scores(self, K):
        return self.theta[:K]

    def ranking(self, K):
        """Player indices sorted from best to worst."""
        return np.argsort(-self.theta[:K], kind="stable")


def fit_bt(d: CompData, lam: float = 1e-2, theta0=None, tol=1e-10, max_iter=100, X=None) -> Fit:
    """Penalised maximum likelihood by damped Newton's method."""
    if X is None:
        X = d.design()
    P = d.P
    pen = np.full(P, lam)
    if d.home is not None:
        pen[-1] = lam  # ridge on home advantage too (negligible)
    theta = np.zeros(P) if theta0 is None else theta0.copy()
    w_n = d.n
    yv = d.y

    def loss(th):
        s = X @ th
        # -y log sig(s) - (1-y) log sig(-s) = log(1+e^s) - y s
        return float(np.sum(w_n * (np.logaddexp(0.0, s) - yv * s)) + 0.5 * np.sum(pen * th * th))

    f = loss(theta)
    conv = False
    it = 0
    for it in range(1, max_iter + 1):
        s = X @ theta
        p = expit(s)
        g = X.T @ (w_n * (p - yv)) + pen * theta
        W = w_n * p * (1 - p)
        H = (X * W[:, None]).T @ X + np.diag(pen)
        step = np.linalg.solve(H, g)
        t = 1.0
        while True:
            th_new = theta - t * step
            f_new = loss(th_new)
            if f_new <= f + 1e-12 * abs(f) or t < 1e-8:
                break
            t *= 0.5
        theta, f_old, f = th_new, f, f_new
        if np.max(np.abs(t * step)) < tol or abs(f_old - f) < tol * max(1.0, abs(f)) * 1e-3:
            conv = True
            break
    s = X @ theta
    p = expit(s)
    W = w_n * p * (1 - p)
    H = (X * W[:, None]).T @ X + np.diag(pen)
    Hinv = np.linalg.inv(H)
    return Fit(theta=theta, H=H, Hinv=Hinv, p=p, X=X, converged=conv, iters=it)


def gap_se(fit: Fit, a: int, b: int, sandwich_d: CompData | None = None):
    """Model-based standard error of theta_a - theta_b (optionally sandwich)."""
    c = np.zeros(len(fit.theta))
    c[a] += 1
    c[b] -= 1
    if sandwich_d is None:
        return float(np.sqrt(c @ fit.Hinv @ c))
    r = sandwich_d.y - fit.p
    # per-observation score variance: for ties y=0.5 the empirical score is used
    M = (fit.X * (sandwich_d.n * r * r)[:, None]).T @ fit.X
    V = fit.Hinv @ M @ fit.Hinv
    return float(np.sqrt(c @ V @ c))
