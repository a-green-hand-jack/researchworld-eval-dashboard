"""Bradley-Terry maximum-likelihood fitting (Newton / IRLS) with a tiny ridge.

Supports an optional per-record home-advantage covariate via `fit_bt_home`.
All fits report a `converged` flag; callers must check it.
"""
import numpy as np


class BradleyTerry:
    """Convex BT MLE on fractional win counts W (W[i,j] = wins of i over j).

    Identifiability: scores are centered to mean zero; a small L2 ridge keeps the
    Hessian positive definite on sparse / disconnected comparison graphs.
    """

    def __init__(self, l2=1e-4, max_iter=100, tol=1e-8):
        self.l2 = l2
        self.max_iter = max_iter
        self.tol = tol
        self.theta = None
        self.n_iter = 0
        self.converged = False

    @staticmethod
    def _grad_hess(theta, W, n, l2):
        M = len(theta)
        d = theta[:, None] - theta[None, :]
        p = 1.0 / (1.0 + np.exp(-d))                # P(i beats j)
        grad = (W - n * p).sum(1) - l2 * theta      # d loglik / d theta_i
        w = n * p * (1.0 - p)                       # symmetric weights
        H = -np.diag(w.sum(1)) + w                  # Hessian of loglik (neg. semidef.)
        H -= l2 * np.eye(M)
        return grad, H

    @staticmethod
    def _solve(A, b):
        """Solve A x = b, falling back to least squares if A is singular."""
        try:
            return np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            return np.linalg.lstsq(A, b, rcond=None)[0]

    def fit(self, W, theta0=None):
        W = np.asarray(W, dtype=np.float64)
        n = W + W.T
        np.fill_diagonal(n, 0.0)
        M = W.shape[0]
        theta = np.zeros(M) if theta0 is None else np.array(theta0, dtype=np.float64)
        self.n_iter = 0
        self.converged = False
        for it in range(self.max_iter):
            g, H = self._grad_hess(theta, W, n, self.l2)
            step = self._solve(-H, g)               # ascent step on concave loglik
            mx = np.max(np.abs(step))
            if mx > 3.0:
                step = step * (3.0 / mx)
            theta = theta + step
            theta = theta - theta.mean()
            self.n_iter = it + 1
            if np.max(np.abs(step)) < self.tol:
                self.converged = True
                break
        self.theta = theta
        return theta

    def fisher_cov(self, W):
        """Inverse observed Fisher information at the fitted theta (Wald covariance).

        The null direction (1-vector) is handled by projecting onto the
        mean-zero subspace: we invert on the orthogonal complement of 1 and
        return a covariance that is exactly zero along 1. Contrasts such as
        e = (1, -1) are unaffected.
        """
        if self.theta is None:
            raise RuntimeError('fisher_cov called before fit')
        W = np.asarray(W, dtype=np.float64)
        n = W + W.T
        np.fill_diagonal(n, 0.0)
        _, H = self._grad_hess(self.theta, W, n, self.l2)
        M = H.shape[0]
        P = np.eye(M) - np.ones((M, M)) / M
        A = P @ (-H) @ P + np.ones((M, M)) / M      # identity-like on the null direction
        try:
            C = np.linalg.inv(A)
        except np.linalg.LinAlgError:
            C = np.linalg.pinv(A)
        C = P @ C @ P
        return 0.5 * (C + C.T)


def fit_bt(W, l2=1e-4, max_iter=100, tol=1e-8, theta0=None):
    """Returns (theta, model). Check `model.converged`."""
    m = BradleyTerry(l2, max_iter, tol)
    return m.fit(W, theta0), m


def fit_bt_home(ia, ib, y, home, M, l2=1e-4, max_iter=100, tol=1e-8):
    """BT with a scalar home-advantage term h: logit P(ia wins) = th[ia]-th[ib]+h*home.

    home in {-1, 0, +1}: +1 if ia is at home, -1 if ib is at home, 0 neutral/unknown.
    Returns (theta, h, converged). Newton on the stacked parameter (theta, h).
    """
    ia = np.asarray(ia)
    ib = np.asarray(ib)
    y = np.asarray(y, dtype=np.float64)
    home = np.asarray(home, dtype=np.float64)
    par = np.zeros(M + 1)
    converged = False
    for _ in range(max_iter):
        th, h = par[:M], par[M]
        s = th[ia] - th[ib] + h * home
        p = 1.0 / (1.0 + np.exp(-s))
        r = y - p
        g = np.zeros(M + 1)
        np.add.at(g, ia, r)
        np.add.at(g, ib, -r)
        g[M] = np.sum(r * home)
        g[:M] -= l2 * th
        w = p * (1.0 - p)
        H = np.zeros((M + 1, M + 1))
        np.add.at(H, (ia, ia), -w)
        np.add.at(H, (ib, ib), -w)
        np.add.at(H, (ia, ib), w)
        np.add.at(H, (ib, ia), w)
        np.add.at(H[:, M], ia, -w * home)
        np.add.at(H[:, M], ib, w * home)
        H[M, :M] = H[:M, M]
        H[M, M] = -np.sum(w * home * home)
        H[:M, :M] -= l2 * np.eye(M)
        H[M, M] -= l2
        try:
            step = np.linalg.solve(-H, g)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(-H, g, rcond=None)[0]
        mx = np.max(np.abs(step))
        if mx > 3.0:
            step *= 3.0 / mx
        par = par + step
        par[:M] -= par[:M].mean()
        if np.max(np.abs(step)) < tol:
            converged = True
            break
    return par[:M], par[M], converged


def adjacent_pairs(theta, top_m):
    """Adjacent (rank r, rank r+1) pairs among the top_m ranked participants."""
    order = np.argsort(-theta)
    top = order[:max(top_m, 2)]
    return [(int(top[r]), int(top[r + 1])) for r in range(len(top) - 1)]