"""Bradley-Terry fitting on aggregated comparison cells.

A dataset is reduced to *cells*: unique (a, b, h, y) combinations with an integer
count w.  a, b are entity indices, h in {0,1} is a home indicator (only used for
sports; 1 means `a` played at home), y in {0, 0.5, 1} is the outcome for `a`
(1 = a wins, 0 = b wins, 0.5 = tie, counted as half a win for each side, the
convention used by the Chatbot Arena notebooks).

Model: P(a beats b) = sigmoid(theta_a - theta_b + eta * h).
Estimator: maximiser of  sum_n w_n [y_n log p_n + (1-y_n) log(1-p_n)] - lam/2 ||theta||^2
(eta is unpenalised).  The tiny ridge only fixes the translation invariance
(it forces sum(theta)=0) and keeps undefeated entities finite.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field


@dataclass
class Cells:
    a: np.ndarray          # int
    b: np.ndarray          # int
    h: np.ndarray          # float (0/1)
    y: np.ndarray          # float in {0, .5, 1}
    w: np.ndarray          # float counts
    m: int                 # number of entities
    names: list = field(default_factory=list)
    home: bool = False     # whether to fit a home-advantage parameter

    @property
    def n(self) -> float:
        return float(self.w.sum())

    @property
    def dim(self) -> int:
        return self.m + (1 if self.home else 0)

    def copy(self, w=None):
        return Cells(self.a, self.b, self.h, self.y, self.w.copy() if w is None else w,
                     self.m, self.names, self.home)


def cells_from_frame(df, names=None, home=False):
    """df has integer columns a, b, float y, optional h. Returns Cells with a full
    outcome grid per observed (a, b, h) key (zero-count cells included so that
    label flips have somewhere to go)."""
    import pandas as pd
    d = df.copy()
    if "h" not in d:
        d["h"] = 0.0
    if not home:
        # canonical orientation a < b for neutral-site comparisons
        sw = d.a > d.b
        d.loc[sw, ["a", "b"]] = d.loc[sw, ["b", "a"]].values
        d.loc[sw, "y"] = 1.0 - d.loc[sw, "y"]
    keys = d[["a", "b", "h"]].drop_duplicates()
    outs = [0.0, 0.5, 1.0]
    grid = keys.merge(pd.DataFrame({"y": outs}), how="cross")
    cnt = d.groupby(["a", "b", "h", "y"]).size().rename("w").reset_index()
    grid = grid.merge(cnt, on=["a", "b", "h", "y"], how="left").fillna({"w": 0.0})
    grid = grid.sort_values(["a", "b", "h", "y"]).reset_index(drop=True)
    m = int(max(d.a.max(), d.b.max()) + 1) if names is None else len(names)
    return Cells(grid.a.values.astype(int), grid.b.values.astype(int), grid.h.values.astype(float),
                 grid.y.values.astype(float), grid.w.values.astype(float), m, list(names or []), home)


def _lin(c: Cells, theta):
    z = theta[c.a] - theta[c.b]
    if c.home:
        z = z + theta[c.m] * c.h
    return z


def sigmoid(z):
    return 0.5 * (1.0 + np.tanh(0.5 * z))


def grad_hess(c: Cells, theta, lam):
    """Gradient of the penalised log-lik and the (positive definite) negative Hessian."""
    m, d = c.m, c.dim
    p = sigmoid(_lin(c, theta))
    r = c.w * (c.y - p)                       # weighted residuals
    v = c.w * p * (1.0 - p)                   # weighted variances
    g = np.bincount(c.a, r, minlength=d) - np.bincount(c.b, r, minlength=d)
    H = np.zeros((d, d))
    diag = np.bincount(c.a, v, minlength=d) + np.bincount(c.b, v, minlength=d)
    off = np.bincount(c.a * d + c.b, v, minlength=d * d).reshape(d, d)
    H -= off + off.T
    H[np.arange(d), np.arange(d)] += diag
    if c.home:
        hv = v * c.h
        hr = r * c.h
        g[m] = hr.sum()
        col = np.bincount(c.a, hv, minlength=d) - np.bincount(c.b, hv, minlength=d)
        H[:m, m] = col[:m]
        H[m, :m] = col[:m]
        H[m, m] = hv.sum()
    pen = np.full(d, lam)
    if c.home:
        pen[m] = 1e-8
    g -= pen * theta
    H[np.arange(d), np.arange(d)] += pen
    return g, H, p


def objective(c: Cells, theta, lam):
    z = _lin(c, theta)
    # y log p + (1-y) log(1-p) = y z - log(1+e^z)
    ll = (c.w * (c.y * z - np.logaddexp(0.0, z))).sum()
    pen = np.full(c.dim, lam)
    if c.home:
        pen[c.m] = 1e-8
    return ll - 0.5 * (pen * theta * theta).sum()


def fit(c: Cells, lam=1e-2, theta0=None, tol=1e-9, max_iter=200):
    """Newton's method with backtracking line search on the (strictly concave)
    penalised log-likelihood; stops when the max-abs gradient is below tol."""
    theta = np.zeros(c.dim) if theta0 is None else theta0.copy()
    f = objective(c, theta, lam)
    for _ in range(max_iter):
        g, H, _ = grad_hess(c, theta, lam)
        if np.abs(g).max() < tol:
            break
        step = np.linalg.solve(H, g)
        t = 1.0
        while True:
            cand = theta + t * step
            fc = objective(c, cand, lam)
            if fc >= f - 1e-12 * abs(f) or t < 1e-8:
                break
            t *= 0.5
        if t < 1e-8:
            break
        theta, f = cand, fc
    return theta


def scores(theta, c: Cells):
    return theta[: c.m]


def ranking(theta, c: Cells):
    """Entity indices sorted best-first."""
    return np.argsort(-theta[: c.m], kind="stable")


def fisher_cov(c: Cells, theta, lam=1e-2):
    _, H, _ = grad_hess(c, theta, lam)
    return np.linalg.inv(H)


def pair_z(c: Cells, theta, i, j, cov=None, lam=1e-2):
    if cov is None:
        cov = fisher_cov(c, theta, lam)
    d = theta[i] - theta[j]
    se = np.sqrt(cov[i, i] + cov[j, j] - 2 * cov[i, j])
    return d / se, se
