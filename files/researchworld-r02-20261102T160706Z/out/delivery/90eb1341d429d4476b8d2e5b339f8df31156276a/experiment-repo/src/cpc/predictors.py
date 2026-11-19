import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax
from sklearn.ensemble import RandomForestRegressor
from .simplex import closure


class SoftmaxLinear:
    """Multinomial-logit regression on soft labels (cross-entropy), i.e. Dirichlet-mean GLM."""

    def __init__(self, l2=1e-3):
        self.l2 = l2

    def fit(self, X, Y):
        n, p = X.shape
        D = Y.shape[1]
        Xa = np.c_[X, np.ones(n)]

        def f(w):
            W = w.reshape(p + 1, D)
            P = softmax(Xa @ W, axis=1)
            loss = -(Y * np.log(P + 1e-12)).sum() / n + self.l2 * (W[:-1] ** 2).sum()
            g = Xa.T @ (P - Y) / n
            g[:-1] += 2 * self.l2 * W[:-1]
            return loss, g.ravel()

        self.W = minimize(f, np.zeros((p + 1) * D), jac=True, method="L-BFGS-B", options={"maxiter": 300}).x.reshape(p + 1, D)
        return self

    def predict(self, X):
        return softmax(np.c_[X, np.ones(len(X))] @ self.W, axis=1)


class RF:
    def __init__(self, seed=0, n_estimators=100, leaf=5):
        self.m = RandomForestRegressor(n_estimators=n_estimators, min_samples_leaf=leaf, n_jobs=1, random_state=seed)

    def fit(self, X, Y):
        self.m.fit(X, Y)
        return self

    def predict(self, X):
        return closure(np.maximum(self.m.predict(X), 0) + 1e-12)


def make_predictor(name, seed=0):
    return SoftmaxLinear() if name == "linear" else RF(seed)
