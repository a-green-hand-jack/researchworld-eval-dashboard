"""Point/scale predictors for simplex targets."""
import numpy as np
import torch
from .simplex import clr, inv_clr, replace_zeros
from .scores import SCORES


def _design(X):
    return np.hstack([np.ones((len(X), 1)), X])


class ClrOLS:
    """Linear regression in CLR space (ridge), yhat = inv_clr(prediction)."""
    def __init__(self, ridge=1e-3):
        self.ridge = ridge

    def fit(self, X, Y):
        A = _design(X)
        Z = clr(Y)
        self.B = np.linalg.solve(A.T @ A + self.ridge * np.eye(A.shape[1]), A.T @ Z)
        return self

    def predict(self, X):
        return inv_clr(_design(X) @ self.B)


class ConstClr:
    """Intercept-only mean model (geometric-mean composition of the training targets): predictions do not depend on x,
    so rounded compositions give tied scores (used by the A2 tie case)."""
    def fit(self, X, Y):
        self.z = clr(Y).mean(0)
        return self

    def predict(self, X):
        return np.tile(inv_clr(self.z), (len(X), 1))


class LogScale:
    """sigma_s(x) = exp(linear(x)) fitted on log training scores of base score s (optionally with
    quadratic features: `quad=True`)."""
    def __init__(self, quad=False, ridge=1e-3):
        self.quad, self.ridge = quad, ridge

    def _f(self, X):
        A = _design(X)
        if self.quad:
            A = np.hstack([A, X ** 2])
        return A

    def fit(self, X, s):
        A = self._f(X)
        t = np.log(np.maximum(s, 1e-8))
        self.B = np.linalg.solve(A.T @ A + self.ridge * np.eye(A.shape[1]), A.T @ t)
        return self

    def predict(self, X):
        return np.exp(np.clip(self._f(X) @ self.B, -20, 20))


class DirichletReg:
    """log alpha_k(x) = [1,x] W_k, fitted by maximum likelihood (LBFGS)."""
    def __init__(self, l2=1e-3, iters=100):
        self.l2, self.iters = l2, iters

    def fit(self, X, Y, init=None):
        A = torch.tensor(_design(X))
        L = torch.log(torch.tensor(np.maximum(Y, 1e-10)))
        W = torch.zeros(A.shape[1], Y.shape[1], dtype=torch.float64)
        W[0] = np.log(5.0)
        W.requires_grad_(True)
        opt = torch.optim.LBFGS([W], lr=1.0, max_iter=self.iters, line_search_fn="strong_wolfe")

        def closure():
            opt.zero_grad()
            la = A @ W
            al = torch.exp(la.clamp(-10, 12))
            ll = torch.lgamma(al.sum(-1)) - torch.lgamma(al).sum(-1) + ((al - 1) * L).sum(-1)
            loss = -ll.mean() + self.l2 * (W[1:] ** 2).sum()
            loss.backward()
            return loss
        opt.step(closure)
        self.W = W.detach().numpy()
        return self

    def alpha(self, X):
        return np.exp(np.clip(_design(X) @ self.W, -10, 12))

    def predict(self, X):
        a = self.alpha(X)
        return a / a.sum(-1, keepdims=True)
