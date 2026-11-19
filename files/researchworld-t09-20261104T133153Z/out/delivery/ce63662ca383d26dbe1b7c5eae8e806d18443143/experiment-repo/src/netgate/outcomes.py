"""Outcome (potential-outcome) models. Y_i(z) is a known function of the full assignment vector, so
the GATE = mean_i[Y_i(1) - Y_i(0)] is computed exactly and noise-free for every world.

Spillover shapes h:[0,1]->[0,1] with h(0)=0, h(1)=1 are applied to the treated-neighbour fraction.
  linear   h(f)=f                       (linear-in-means)
  concave  h(f)=(1-exp(-k f))/(1-exp(-k)) (saturating)
  convex   h(f)=(exp(k f)-1)/(exp(k)-1)  (increasing returns)
  sigmoid  h(f)=normalised logistic((f-.5)*s) (threshold / complex contagion)
"""
from dataclasses import dataclass

import numpy as np

SHAPE_K = 3.0
SIG_S = 10.0


def shape(f, kind, k=None, s_=None):
    SHAPE_K_ = SHAPE_K if k is None else k
    SIG_S_ = SIG_S if s_ is None else s_
    if kind == "linear":
        return f
    if kind == "concave":
        return (1 - np.exp(-SHAPE_K_ * f)) / (1 - np.exp(-SHAPE_K_))
    if kind == "convex":
        return (np.exp(SHAPE_K_ * f) - 1) / (np.exp(SHAPE_K_) - 1)
    if kind == "sigmoid":
        s = lambda x: 1 / (1 + np.exp(-SIG_S_ * (x - 0.5)))
        return (s(f) - s(0.0)) / (s(1.0) - s(0.0))
    raise ValueError(kind)


def shape_deriv(f, kind, eps=1e-5):
    return (shape(f + eps, kind) - shape(f - eps, kind)) / (2 * eps)


@dataclass
class Outcome:
    """mech: 'shape' (1-hop fraction, spillover shape `kind`), 'count' (neighbour count / mean degree,
    linear), 'twohop' (1-hop + 2-hop fraction), 'prop' (equilibrium propagation Y=(I-rho W)^-1(a+tau z)),
    'hetero' (direct effect varies with degree; linear spill), 'step' (threshold exposure 1[f>=kappa]; added after the freeze for e12)."""
    mech: str = "shape"
    kind: str = "linear"
    tau: float = 1.0       # direct effect
    gamma: float = 1.0     # interference strength (1-hop)
    gamma2: float = 0.5    # 2-hop strength (mech='twohop')
    rho: float = 0.5       # propagation (mech='prop')
    sigma: float = 1.0     # sd of idiosyncratic noise
    alpha_graph: float = 1.0  # sd of graph-smooth baseline component (homophily of baselines)
    alpha_deg: float = 0.5    # coefficient of standardised log-degree in baseline
    alpha_iid: float = 0.5    # sd of iid part of the baseline
    kappa: float = 0.75    # threshold (mech='step': spillover gamma * 1[neighbour fraction >= kappa])
    curv: float | None = None  # steepness of the concave/convex shape (default SHAPE_K); sigmoid slope if kind=sigmoid

    def world(self, g, rng):
        """Draw fixed baseline + noise for one world on graph g."""
        u = rng.standard_normal(g.n)
        for _ in range(3):
            u = g.W @ u
        u = u / u.std() * self.alpha_graph
        ld = np.log(g.deg)
        base = u + self.alpha_deg * (ld - ld.mean()) / (ld.std() or 1.0) + rng.standard_normal(g.n) * self.alpha_iid
        return {"base": base, "eps": rng.standard_normal(g.n) * self.sigma}

    def _h(self, f):
        return shape(f, self.kind, k=self.curv, s_=self.curv)

    def _f2(self, g, z):
        w = g.W @ (g.W @ z)
        return (w - g.diag2 * z) / (1 - g.diag2)

    def Y(self, g, w, z):
        z = z.astype(np.float64)
        base = w["base"]
        m = self.mech
        if m == "shape":
            y = base + self.tau * z + self.gamma * self._h(g.W @ z)
        elif m == "step":
            y = base + self.tau * z + self.gamma * ((g.W @ z) >= self.kappa - 1e-12)
        elif m == "count":
            y = base + self.tau * z + self.gamma * (g.A @ z) / g.mean_deg
        elif m == "twohop":
            y = base + self.tau * z + self.gamma * (g.W @ z) + self.gamma2 * self._f2(g, z)
        elif m == "hetero":
            ld = np.log(g.deg)
            tau_i = self.tau * (1 + 0.5 * (ld - ld.mean()) / (ld.std() or 1.0))
            y = base + tau_i * z + self.gamma * (g.W @ z)
        elif m == "prop":
            x = base + self.tau * z
            y = x.copy()
            for _ in range(60):
                y = x + self.rho * (g.W @ y)
        else:
            raise ValueError(m)
        return y + w["eps"]

    def gate(self, g, w):
        n = g.n
        return float(np.mean(self.Y(g, w, np.ones(n)) - self.Y(g, w, np.zeros(n))))

    def dm_target(self, g, w):
        return self.gate(g, w)
