"""Data-only diagnostics and intervals pre-registered in PREREG.md (D1 extrapolation validation, D2 family spread,
D3 curvature bound) plus bootstrap comparators.  Everything uses only (graph, z, y)."""
import numpy as np

from . import estimators as E


def _fit_pred(f, ctx, spec, st, y, fit, test):
    Phi = f(st, ctx, spec)
    beta, *_ = np.linalg.lstsq(Phi[fit], y[fit], rcond=None)
    return y[test] - Phi[test] @ beta


def d1(ctx, spec, st, y, feat="REG-L", qhi=0.8, qlo=0.2):
    f = E.FEATURES[feat]
    g = st["g1"]
    phat = st["z"].mean()
    hi, lo = np.quantile(g, qhi), np.quantile(g, qlo)
    up = g > hi
    low = g < lo
    out = dict(d1=np.nan, d1_e1=np.nan, d1_e0=np.nan)
    e1 = e0 = np.nan
    if up.sum() > 20 and (~up).sum() > 50:
        r = _fit_pred(f, ctx, spec, st, y, ~up, up)
        gap = g[up].mean() - g[~up].mean()
        e1 = r.mean() / gap * (1 - phat) if gap > 1e-9 else np.nan
    if low.sum() > 20 and (~low).sum() > 50:
        r = _fit_pred(f, ctx, spec, st, y, ~low, low)
        gap = g[~low].mean() - g[low].mean()
        e0 = r.mean() / gap * phat if gap > 1e-9 else np.nan
    out["d1_e1"], out["d1_e0"] = float(e1), float(e0)
    out["d1"] = float(abs(np.nan_to_num(e0) - np.nan_to_num(e1)))
    return out


def d3(ctx, spec, st, y, S):
    """Curvature bound from REG-Q: B = M_hat ((1-p)^2+p^2)/2, M_hat = 2|c2| + 4 se(c2)."""
    f = E.FEATURES["REG-Q"]
    Phi = f(st, ctx, spec)
    beta, *_ = np.linalg.lstsq(Phi, y, rcond=None)
    e = y - Phi @ beta
    s = Phi * e[:, None]
    if S is not None:
        meat = s.T @ (S @ s)
    else:
        meat = s.T @ s
    bread = np.linalg.pinv(Phi.T @ Phi)
    V = bread @ meat @ bread
    c2, se2 = beta[3], np.sqrt(max(V[3, 3], 0))
    M = 2 * abs(c2) + 4 * se2
    p = st["z"].mean()
    return dict(d3_c2=float(c2), d3_se2=float(se2), d3_B=float(M * ((1 - p) ** 2 + p ** 2) / 2))


def d4(ctx, spec, st, y, tau_L, q=0.25):
    """Degree transport (PREREG addendum): fit y ~ 1 + z + g + g^2 + g^3 on the units of degree <= q-quantile only, read the corner contrast
    b_z + h(1) - h(0) off the fitted curve (assumption: the same h at every degree); score = |tau_D4 - tau_REG-L|."""
    g, z = st["g1"], st["z"]
    R = ctx.deg <= np.quantile(ctx.deg, q)
    out = dict(d4=np.nan, d4_tau=np.nan, d4_gmax=np.nan, d4_nref=int(R.sum()))
    if R.sum() < 50:
        return out
    Phi = np.c_[np.ones(R.sum()), z[R], g[R], g[R] ** 2, g[R] ** 3]
    b, *_ = np.linalg.lstsq(Phi, y[R], rcond=None)
    tau = b[1] + b[2] + b[3] + b[4]
    out.update(d4_tau=float(tau), d4=float(abs(tau - tau_L)), d4_gmax=float(np.quantile(g[R], 0.99)))
    return out


def spread(ctx, spec, st, y, names=("REG-L", "REG-Q", "REG-G")):
    v = [E.reg_estimate(nm, ctx, spec, st, y)[0] for nm in names]
    return dict(d2=float((max(v) - min(v)) / 2))


def boot_pairs(ctx, spec, st, y, B=200, rng=None, feat="REG-L"):
    """Unit-pairs bootstrap (resample (z_i, g_i, y_i) rows, refit, predict corners); ignores network dependence."""
    f = E.FEATURES[feat]
    Phi = f(st, ctx, spec)
    D = (f(ctx.corner(1), ctx, spec) - f(ctx.corner(0), ctx, spec)).mean(0)
    n = len(y)
    est = np.empty(B)
    for b in range(B):
        i = rng.integers(0, n, n)
        est[b] = D @ np.linalg.lstsq(Phi[i], y[i], rcond=None)[0]
    return np.quantile(est, [0.025, 0.975])


def boot_blocks(ctx, spec, st, y, labels, B=200, rng=None, feat="REG-L"):
    """Cluster block bootstrap (resample Louvain blocks of units with replacement)."""
    f = E.FEATURES[feat]
    Phi = f(st, ctx, spec)
    D = (f(ctx.corner(1), ctx, spec) - f(ctx.corner(0), ctx, spec)).mean(0)
    K = labels.max() + 1
    idx = [np.where(labels == k)[0] for k in range(K)]
    est = np.empty(B)
    for b in range(B):
        ks = rng.integers(0, K, K)
        i = np.concatenate([idx[k] for k in ks])
        est[b] = D @ np.linalg.lstsq(Phi[i], y[i], rcond=None)[0]
    return np.quantile(est, [0.025, 0.975])
