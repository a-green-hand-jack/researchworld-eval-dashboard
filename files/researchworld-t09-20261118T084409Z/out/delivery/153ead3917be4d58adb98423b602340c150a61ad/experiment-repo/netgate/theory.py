"""Quantities computed from the design and graph, independent of the replicates' own assignments:
  - exact finite-d projection bias of an OLS regression estimator (design-weighted OLS projection of the
    noise-free response, Monte Carlo over the design only);
  - corner leverage L = D' Sigma^{-1} D (Var_iid = sigma^2 L / n)."""
import numpy as np

from .estimators import FEATURES
from .outcomes import potential


def projection(names, ctx, spec, fz, design, rng, M=40, fctx=None):
    """fctx: the graph the regression features are built from (the observed graph) when it differs from the true one."""
    fc = fctx if fctx is not None else ctx
    out = {}
    c1, c0 = ctx.corner(1), ctx.corner(0)
    f1, f0 = fc.corner(1), fc.corner(0)
    tau = float(np.mean(potential(spec, fz, ctx, c1) - potential(spec, fz, ctx, c0)))
    acc = {nm: [0, 0] for nm in names}
    fz0 = dict(fz, alpha=np.zeros(ctx.n))
    for _ in range(M):
        z = design.draw(ctx.n, rng)
        st = ctx.state(z)
        sf = fc.state(z)
        f = potential(spec, fz0, ctx, st)
        for nm in names:
            Phi = FEATURES[nm](sf, fc, spec)
            a = acc[nm]
            a[0] = a[0] + Phi.T @ Phi / ctx.n
            a[1] = a[1] + Phi.T @ f / ctx.n
    for nm in names:
        Mm, v = acc[nm][0] / M, acc[nm][1] / M
        D = (FEATURES[nm](f1, fc, spec) - FEATURES[nm](f0, fc, spec)).mean(0)
        beta = np.linalg.lstsq(Mm, v, rcond=None)[0]
        L = float(D @ np.linalg.lstsq(Mm, D, rcond=None)[0])
        out[nm] = dict(bias_pred=float(D @ beta) - tau, L=L)
    return out
