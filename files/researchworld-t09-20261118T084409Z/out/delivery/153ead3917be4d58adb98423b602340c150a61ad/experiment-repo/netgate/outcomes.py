"""Fixed potential outcomes Y_i(z) with continuous interference knobs.

    Y_i(z) = alpha_i + beta_i z_i + gamma_i [ (1-w2) H(g1_i) + w2 H(g2_i) ],   H(g) = (1-kappa) g + kappa h(g)
with h(0)=0, h(1)=1 (so the GATE is mean(beta_i+gamma_i) whatever kappa, w2 and shape are), g1/g2 the treated
fraction among 1-hop / (walk-weighted) 2-hop neighbours.  Kind 'count' replaces the bracket by c1_i / dbar
(treated-neighbour COUNT, degree-multiplicative).  Observed outcome = Y_i(z) + sigma * eps_i, eps frozen across arms.
"""
from dataclasses import dataclass, field

import numpy as np


def shape_h(g, shape, theta=0.5, steep=12.0):
    if shape == "linear":
        return g
    if shape == "convex":
        return g ** 2
    if shape == "concave":
        return 2 * g - g ** 2
    if shape == "thresh":
        s = lambda x: 1 / (1 + np.exp(-steep * (x - theta)))
        return (s(g) - s(0.0)) / (s(1.0) - s(0.0))
    raise ValueError(shape)


@dataclass(frozen=True)
class OutSpec:
    kind: str = "param"         # 'param' | 'count'
    beta: float = 1.0           # direct effect
    gamma: float = 1.0          # indirect effect (strength)
    kappa: float = 0.0          # curvature mix: 0 = linear in g
    shape: str = "convex"
    theta: float = 0.5
    w2: float = 0.0             # weight of 2-hop exposure
    sigma: float = 0.0          # idiosyncratic noise sd (redrawn per replicate)
    sigma_alpha: float = 0.0    # frozen baseline heterogeneity sd (redrawn with the replicate)
    het_beta: float = 0.0       # direct effect varies with standardised log degree
    het_gamma: float = 0.0      # indirect effect varies with standardised log degree

    def H(self, g):
        return (1 - self.kappa) * g + self.kappa * shape_h(g, self.shape, self.theta)


def freeze(spec, ctx, rng):
    """Draw the replicate's frozen heterogeneity."""
    n = ctx.n
    ld = np.log(ctx.deg)
    zd = (ld - ld.mean()) / (ld.std() + 1e-12)
    return dict(
        alpha=spec.sigma_alpha * rng.standard_normal(n),
        beta=spec.beta * (1 + spec.het_beta * zd),
        gamma=spec.gamma * (1 + spec.het_gamma * zd),
    )


def potential(spec, fz, ctx, state):
    """Noise-free potential outcomes at exposure `state` (dict of z, g1, g2, c1)."""
    if spec.kind == "param":
        e = (1 - spec.w2) * spec.H(state["g1"]) + (spec.w2 * spec.H(state["g2"]) if spec.w2 else 0.0)
    elif spec.kind == "count":
        e = state["c1"] / ctx.dbar
    else:
        raise ValueError(spec.kind)
    return fz["alpha"] + fz["beta"] * state["z"] + fz["gamma"] * e


def truth(spec, fz, ctx):
    return float(np.mean(potential(spec, fz, ctx, ctx.corner(1)) - potential(spec, fz, ctx, ctx.corner(0))))


def oracle_exposure(spec, ctx, state):
    """The true (known-shape) exposure feature used by REG-O."""
    if spec.kind == "param":
        return (1 - spec.w2) * spec.H(state["g1"]) + (spec.w2 * spec.H(state["g2"]) if spec.w2 else 0.0)
    return state["c1"] / ctx.dbar
