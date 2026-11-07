"""Synthetic compositional regression problems with a known conditional centre mu(x)."""
import numpy as np
from .geometry import softmax, clr

FAMILIES = ["dirichlet", "logistic_normal", "additive", "dirmult"]


class SynthProblem:
    """X ~ N(0, I_p);  mu(x) = softmax(tau * (A x + B sin(C x)))  (smooth nonlinear map).
    Y | X=x is drawn from `family` centred at mu(x) with noise level controlled by `kappa`
    (Dirichlet concentration) or the matched-MSE sigma for the other families."""

    def __init__(self, D=3, p=5, tau=1.0, family="dirichlet", kappa=100.0, seed=0,
                 mu_floor=0.0, match_mse=True, het=0.0, n_ann=20):
        rng = np.random.default_rng(10_000 + seed)
        self.D, self.p, self.tau, self.family, self.kappa = D, p, tau, family, kappa
        self.A = rng.normal(size=(p, D)) / np.sqrt(p)
        self.B = rng.normal(size=(p, D)) / np.sqrt(p)
        self.C = rng.normal(size=(p, p)) / np.sqrt(p)
        self.mu_floor = mu_floor
        self.het = het
        self.n_ann = n_ann
        v = rng.normal(size=p)
        self.v = v / np.linalg.norm(v)
        self.sigma = None
        if family not in ("dirichlet", "dirmult"):
            self.sigma = self._match_sigma(rng)

    def mu(self, X):
        z = X @ self.A + np.sin(X @ self.C) @ self.B
        m = softmax(self.tau * z)
        if self.mu_floor > 0:
            m = (1 - self.mu_floor) * m + self.mu_floor / self.D
        return m

    def noise_scale(self, X):
        """Multiplier of the noise SD at x (1 when het=0)."""
        return np.exp(self.het * np.tanh(X @ self.v))

    def sample_X(self, n, rng):
        return rng.normal(size=(n, self.p))

    def _draw(self, mu, rng, sigma=None, scale=None):
        D = self.D
        n = mu.shape[0]
        scale = np.ones(n) if scale is None else scale
        if self.family == "dirichlet":
            g = rng.gamma(np.maximum((self.kappa / scale ** 2)[:, None] * mu, 1e-8))
            g = np.maximum(g, 1e-300)
            return g / g.sum(-1, keepdims=True)
        if self.family == "dirmult":   # p ~ Dir(kappa mu), counts ~ Multinomial(n_ann, p), y = counts / n_ann (lattice-valued, many zeros)
            g = rng.gamma(np.maximum((self.kappa / scale ** 2)[:, None] * mu, 1e-8))
            p = g / np.maximum(g.sum(-1, keepdims=True), 1e-300)
            return rng.multinomial(self.n_ann, p) / self.n_ann
        s = self.sigma if sigma is None else sigma
        if self.family == "logistic_normal":
            e = rng.normal(size=(n, D)) * s * scale[:, None]
            e -= e.mean(-1, keepdims=True)
            return softmax(np.log(mu) + e)
        if self.family == "additive":
            y = np.empty_like(mu)
            todo = np.arange(n)
            for _ in range(500):
                e = rng.normal(size=(len(todo), D)) * s * scale[todo][:, None]
                e -= e.mean(-1, keepdims=True)
                cand = mu[todo] + e
                ok = (cand > 1e-6).all(-1)
                y[todo[ok]] = cand[ok]
                todo = todo[~ok]
                if len(todo) == 0:
                    break
            self.n_fallback = getattr(self, "n_fallback", 0) + len(todo)
            if len(todo):  # fall back to the centre; the fraction is asserted to be tiny by callers
                y[todo] = mu[todo]
            return y
        raise ValueError(self.family)

    def _match_sigma(self, rng):
        """Choose sigma so that E||Y - mu||^2 equals the Dirichlet(kappa) value averaged over X."""
        X = self.sample_X(4000, rng)
        mu = self.mu(X)
        target = ((1 - (mu ** 2).sum(-1)) / (self.kappa + 1)).mean()
        lo, hi = 1e-4, 3.0
        for _ in range(40):
            mid = np.sqrt(lo * hi)
            y = self._draw(mu, np.random.default_rng(1), sigma=mid)
            mse = ((y - mu) ** 2).sum(-1).mean()
            lo, hi = (mid, hi) if mse < target else (lo, mid)
        return np.sqrt(lo * hi)

    def sample(self, n, rng):
        X = self.sample_X(n, rng)
        mu = self.mu(X)
        return X, mu, self._draw(mu, rng, scale=self.noise_scale(X))
