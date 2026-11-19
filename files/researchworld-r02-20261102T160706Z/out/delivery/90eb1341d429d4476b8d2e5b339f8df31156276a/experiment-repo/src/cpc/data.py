"""Synthetic compositional-regression generators (fixed regression function per config, fresh samples per replicate)."""
import numpy as np
from scipy.special import softmax
from .simplex import closure

FAMILIES = ["dirichlet", "lognormal", "multinomial", "rounded"]


class World:
    """Conditional law of y | x on the simplex.  family in FAMILIES, hetero in {0,1}."""

    def __init__(self, family, D, hetero, p=4, seed=0, logit_sd=1.5, phi0=20.0, ln_sd=0.5, n_counts=30):
        r = np.random.default_rng(10_000 + seed)
        self.family, self.D, self.hetero, self.p = family, D, hetero, p
        self.B = r.normal(size=(p, D)) * logit_sd / np.sqrt(p)
        self.b = r.normal(size=D) * 0.5
        w = r.normal(size=p)
        self.w = w / np.linalg.norm(w)
        self.phi0, self.ln_sd, self.n_counts = phi0, ln_sd, n_counts

    def mean(self, X):
        return softmax(X @ self.B + self.b, axis=1)

    def scale(self, X):
        """Multiplicative heteroscedasticity factor h(x) (=1 if homoscedastic); larger = noisier for lognormal."""
        return np.exp(0.8 * X @ self.w) if self.hetero else np.ones(len(X))

    def sample_x(self, n, rng):
        return rng.normal(size=(n, self.p))

    def sample_y(self, X, rng):
        mu, h, D = self.mean(X), self.scale(X), self.D
        f = self.family
        if f == "dirichlet":  # noisier where precision is low
            phi = self.phi0 / h
            Y = rng.gamma(np.maximum(phi[:, None] * mu, 1e-3))
            return closure(np.maximum(Y, 1e-300))
        if f in ("lognormal", "rounded"):
            z = np.log(mu) + (self.ln_sd * h)[:, None] * rng.normal(size=mu.shape)
            Y = softmax(z, axis=1)
            if f == "rounded":  # detection-limit zeros: parts below 1% reported as exactly 0
                Y = np.where(Y < 0.01, 0.0, Y)
                Y = closure(Y)
            return Y
        if f == "multinomial":
            n = np.maximum(5, np.round(self.n_counts / h)).astype(int) if self.hetero else np.full(len(X), self.n_counts)
            return np.stack([rng.multinomial(k, m) for k, m in zip(n, mu)]) / n[:, None]
        raise ValueError(f)

    def sample(self, n, rng):
        X = self.sample_x(n, rng)
        return X, self.sample_y(X, rng)
