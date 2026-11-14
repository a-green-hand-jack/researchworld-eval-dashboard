"""Shared helpers: rep loop, summary statistics, theory (asymptotic variances)."""
import numpy as np
import pandas as pd
from scipy.stats import norm
from methods import Z95, run_all, spline_basis

METHOD_ORDER = ["classical", "classical_t", "ppi", "ppi++", "ppi++_own", "ppi++_own_t", "strat_ppi5", "spline3", "spline4", "spline4_t", "spline6", "cf_iso"]


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def summarize(theta, se, truth, ref="ppi++"):
    """theta, se: dict method -> arrays over reps.  Returns list of row dicts."""
    rows = []
    w_ref = 2 * Z95 * se[ref]
    for m in theta:
        t, s = theta[m], se[m]
        ok = np.isfinite(t) & np.isfinite(s)
        hit = (np.abs(t - truth) <= Z95 * s)[ok]
        w = 2 * Z95 * s[ok]
        lo, hi = wilson(hit.sum(), ok.sum())
        ratio = (w / w_ref[ok])
        rows.append(dict(method=m, reps=int(ok.sum()), cover=hit.mean(), cover_lo=lo, cover_hi=hi,
                         width=w.mean(), width_se=w.std(ddof=1) / np.sqrt(ok.sum()),
                         ratio_vs_ppipp=ratio.mean(), ratio_se=ratio.std(ddof=1) / np.sqrt(ok.sum()),
                         rmse=np.sqrt(np.mean((t[ok] - truth) ** 2)), bias=np.mean(t[ok] - truth)))
    return rows


def run_reps(draw, truth, R, seed, names=None):
    """draw(rng) -> (Y_L, F_L, F_U).  Returns dict of arrays."""
    rng = np.random.default_rng(seed)
    th, se = {}, {}
    for _ in range(R):
        Y, FL, FU = draw(rng)
        res = run_all(Y, FL, FU, rng, names)
        for m, (t, s) in res.items():
            th.setdefault(m, []).append(float(np.squeeze(t)))
            se.setdefault(m, []).append(float(np.squeeze(s)))
    return {m: np.array(v) for m, v in th.items()}, {m: np.array(v) for m, v in se.items()}


# ---------------------------------------------------------------- theory
def cv_variance(varY, c, SL, SU, n, N, lam):
    """Asymptotic variance of mean(Y) - lam'(mean_L H - mean_U H):
    [Var Y - 2 lam'c + lam' SL lam]/n + lam' SU lam / N."""
    lam = np.atleast_1d(lam)
    return (varY - 2 * lam @ c + lam @ SL @ lam) / n + lam @ SU @ lam / N


def asym_variances(g, EV, f, n, N, k_spline=(3, 4, 6)):
    """Asymptotic variances for all methods, from population moments.
    g, EV, f: arrays over a (large) sample/quadrature approximating the population (equal weights).
    g = E[Y|f] evaluated at each f; EV = Var(Y|f) at each f.
    Returns dict of variances."""
    varg = g.var()
    varY = varg + EV.mean()
    out = {"classical": varY / n}
    f = np.asarray(f, float)
    # linear controls
    c1 = np.array([np.mean((g - g.mean()) * (f - f.mean()))])
    S1 = np.array([[f.var()]])
    out["ppi"] = cv_variance(varY, c1, S1, S1, n, N, np.array([1.0]))
    lam_opt = np.linalg.solve(S1 + (n / N) * S1, c1)
    out["ppi++_own"] = cv_variance(varY, c1, S1, S1, n, N, lam_opt)
    lam_clip = np.clip(lam_opt, 0, 1)
    out["ppi++"] = cv_variance(varY, c1, S1, S1, n, N, lam_clip)
    # efficient bound / oracle recalibration h = c* g
    out["efficient"] = EV.mean() / n + varg / (n + N)
    out["cf_iso"] = out["efficient"]  # asymptotically equivalent (if g monotone)
    for k in k_spline:
        H, _ = spline_basis(f, f[:0], k)
        H = H - H.mean(0)
        S = (H.T @ H / len(H)).reshape(H.shape[1], H.shape[1])  # population (ddof=0) moments
        c = (H * (g - g.mean())[:, None]).mean(0)
        lam = np.linalg.solve(S + (n / N) * S, c)
        out[f"spline{k}"] = cv_variance(varY, c, S, S, n, N, lam)
    return out


def theory_ratio(vars_, ref="ppi++"):
    return {m: np.sqrt(v / vars_[ref]) for m, v in vars_.items()}
