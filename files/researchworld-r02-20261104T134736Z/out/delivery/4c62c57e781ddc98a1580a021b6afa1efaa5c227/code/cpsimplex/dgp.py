"""Synthetic simplex-valued regression DGPs with known conditional laws.

x ~ N(0, I_d).  Conditional mean mu(x) = softmax(W x + b).
 - 'dirichlet':  y | x ~ Dir(phi(x) * mu(x)),  phi(x)= exp(a + h * g(x))   (precision)
 - 'logisticnormal': clr(y) | x = clr-centre + sigma(x) * eps,  eps ~ N(0, I) in an orthonormal ilr basis,
        sigma(x) = exp(s + h * g(x))
g(x) = x_0 ('linear') or x_0**2 - 1 ('quad') or 0 if h = 0.
For heteroscedasticity in Dirichlet, larger phi = smaller spread, so we use phi = exp(a - h*g).
"""
from dataclasses import dataclass
import numpy as np
from scipy.special import softmax
from .simplex import sample_dirichlet, dirichlet_logpdf, inv_clr, clr, closure


@dataclass(frozen=True)
class DGP:
    kind: str = "dirichlet"      # 'dirichlet' | 'logisticnormal'
    K: int = 3
    d: int = 4
    hetero: float = 0.0          # strength h
    form: str = "linear"         # 'linear' | 'quad'
    a: float = np.log(20.0)      # log precision (dirichlet) / -log sigma (LN uses s)
    s: float = np.log(0.5)       # log sigma for LN
    wscale: float = 0.4
    coef_seed: int = 12345       # fixed across replications: the DGP is a fixed population
    nl: float = 0.0              # mean misspecification: logit mean = X W + b + nl * (X**2 - 1) V (the fitted mean model is linear in X)

    def coefs(self):
        r = np.random.default_rng(self.coef_seed)
        W = self.wscale * r.standard_normal((self.d, self.K))
        b = 0.3 * r.standard_normal(self.K)
        return W, b

    def eta(self, X):
        """location on the logit / clr scale"""
        W, b = self.coefs()
        e = X @ W + b
        if self.nl:
            r = np.random.default_rng(self.coef_seed + 1)
            V = self.wscale * r.standard_normal((self.d, self.K))     # drawn from its own stream: W, b are unchanged by nl
            e = e + self.nl * (X ** 2 - 1.0) @ V
        return e

    def g(self, X):
        if self.hetero == 0:
            return np.zeros(len(X))
        return X[:, 0] if self.form == "linear" else X[:, 0] ** 2 - 1.0

    def mean(self, X):
        return softmax(self.eta(X), axis=-1)

    def alpha(self, X):
        phi = np.exp(self.a - self.hetero * self.g(X))
        return phi[:, None] * self.mean(X)

    def sigma(self, X):
        return np.exp(self.s + self.hetero * self.g(X))

    def sample_x(self, rng, n):
        return rng.standard_normal((n, self.d))

    def sample_y(self, rng, X, reps=None):
        """returns (n,K) or (reps,n,K)"""
        n = len(X)
        if self.kind == "dirichlet":
            return sample_dirichlet(rng, self.alpha(X), size=reps)
        c = self.eta(X)
        c = c - c.mean(-1, keepdims=True)
        shape = (reps, n, self.K) if reps else (n, self.K)
        eps = rng.standard_normal(shape)
        eps = eps - eps.mean(-1, keepdims=True)      # noise in the clr hyperplane, isotropic there
        # eps is N(0,I) in an orthonormal ilr basis (||eps||^2 ~ chi2_{K-1})
        return inv_clr(c + self.sigma(X)[..., :, None] * eps)

    def neglogdens(self, X, Y):
        """-log density w.r.t. Lebesgue on the simplex (up to additive consts that depend on x only
        through the HPD level set -- constants cancel in threshold comparisons at fixed x).
        X: (n,d); Y: (n,K) or (r,n,K)."""
        if self.kind == "dirichlet":
            return -dirichlet_logpdf(Y, self.alpha(X))
        c = self.eta(X)
        c = c - c.mean(-1, keepdims=True)
        sg = self.sigma(X)
        z = clr(Y) - c
        q = (z ** 2).sum(-1) / (2 * sg ** 2)
        # Jacobian of the ilr map w.r.t. Lebesgue on the simplex is const / prod(y_i)
        return q + np.log(np.maximum(Y, 1e-300)).sum(-1) + (self.K - 1) * np.log(sg)
