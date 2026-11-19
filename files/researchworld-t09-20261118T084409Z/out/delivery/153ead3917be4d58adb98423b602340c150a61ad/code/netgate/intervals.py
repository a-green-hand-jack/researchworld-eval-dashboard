"""Standard errors for the regression estimator D'beta_hat (feature map Phi, OLS) beyond the pre-registered sandwich.

All use only (graph, z, y).  Returned as dict name -> se.
  iid        OLS, residual variance without degrees-of-freedom correction
  hc2, hc3   leverage-corrected heteroskedasticity-robust (diagonal meat; no network dependence)
  sand2      pre-registered network sandwich (closed 2-hop dependence pattern), as in estimators.sandwich_var
  sand2hc    the same with residuals divided by (1 - h_ii) (leverage-corrected)
  crve       cluster-robust (CR1) sandwich over clusters (blocks for SBM, Louvain otherwise)
  rerand     assignment resampling: z* ~ Bernoulli(p_hat), y* = Phi(z*) beta_hat + e (residuals stay with their unit)
  rerandG    the same with the generating surface = REG-G fit (flexible), the estimator still REG-L
"""
import numpy as np

from . import estimators as E


def _bread(Phi):
    return np.linalg.pinv(Phi.T @ Phi)


def analytic(Phi, y, D, S, labels=None):
    n, k = Phi.shape
    B = _bread(Phi)
    beta = B @ (Phi.T @ y)
    e = y - Phi @ beta
    h = np.einsum("ij,jk,ik->i", Phi, B, Phi)
    h = np.minimum(h, 0.999)
    s = Phi * e[:, None]
    a = B @ D

    def quad(meat):
        return float(np.sqrt(max(a @ meat @ a, 0.0)))

    out = {"iid": float(np.sqrt(max(e.var() * (D @ B @ D), 0.0)))}
    out["hc2"] = quad(s.T @ (s / (1 - h)[:, None]))
    out["hc3"] = quad(s.T @ (s / ((1 - h) ** 2)[:, None]))
    if S is not None:
        out["sand2"] = quad(s.T @ (S @ s))
        s3 = Phi * (e / (1 - h))[:, None]
        out["sand2hc"] = quad(s3.T @ (S @ s3))
    if labels is not None:
        K = int(labels.max()) + 1
        G = np.zeros((K, k))
        np.add.at(G, labels, s)
        c = K / max(K - 1, 1) * (n - 1) / max(n - k, 1)
        out["crve"] = quad(c * G.T @ G)
    return out


def rerand(ctx, spec, st, y, p_hat, rng, feat="REG-L", gen="REG-L", B=100):
    f, fg = E.FEATURES[feat], E.FEATURES[gen]
    Phi_g = fg(st, ctx, spec)
    bg, *_ = np.linalg.lstsq(Phi_g, y, rcond=None)
    e = y - Phi_g @ bg
    D = (f(ctx.corner(1), ctx, spec) - f(ctx.corner(0), ctx, spec)).mean(0)
    est = np.empty(B)
    for b in range(B):
        z = (rng.random(ctx.n) < p_hat).astype(float)
        s2 = ctx.state(z)
        ys = fg(s2, ctx, spec) @ bg + e
        P = f(s2, ctx, spec)
        est[b] = D @ np.linalg.solve(P.T @ P, P.T @ ys)
    return float(est.std(ddof=1))


def all_se(ctx, spec, st, y, S, labels, rng, B=100):
    Phi = E.FEATURES["REG-L"](st, ctx, spec)
    D = (E.FEATURES["REG-L"](ctx.corner(1), ctx, spec) - E.FEATURES["REG-L"](ctx.corner(0), ctx, spec)).mean(0)
    out = analytic(Phi, y, D, S, labels)
    p_hat = float(st["z"].mean())
    out["rerand"] = rerand(ctx, spec, st, y, p_hat, rng, gen="REG-L", B=B)
    out["rerandG"] = rerand(ctx, spec, st, y, p_hat, rng, gen="REG-G", B=B)
    return out
