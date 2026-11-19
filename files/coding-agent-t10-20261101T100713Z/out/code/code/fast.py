"""Closed-form, loop-light versions of classical / PPI++ / cross-fitted linear AIPW for the mean (no covariates),
used for the studentized-bootstrap experiment.  `tests/check_fast.py` verifies them against ppi_py / methods.py."""
import numpy as np


def classical(Y, F, Fu, perm=None):
    return Y.mean(), Y.std(ddof=1) / np.sqrt(len(Y))


def ppi_pp(Y, F, Fu, perm=None, ddof=1):  # ddof=0 reproduces ppi_py exactly
    n, N = len(Y), len(Fu)
    th1 = F.mean() * 0 + (Y - F).mean() + Fu.mean()                 # lambda = 1 point estimate
    g, gh = Y - th1, F - th1
    cov = np.mean((g - g.mean()) * (gh - gh.mean()))
    varF = np.var(np.r_[F, Fu], ddof=1)
    lam = np.clip(cov / ((1 + n / N) * varF), 0, 1)
    th = (Y - lam * F).mean() + lam * Fu.mean()
    se = np.sqrt((lam * Fu).var(ddof=ddof) / N + (Y - lam * F).var(ddof=ddof) / n)
    return th, se


def aipw_lin(Y, F, Fu, perm, K=5):
    """Cross-fitted AIPW with g = a + b F; labeled points use out-of-fold g, unlabeled use the fold-ensemble."""
    n, N = len(Y), len(Fu)
    folds = perm % K
    gL = np.empty(n); A = np.empty(K); B = np.empty(K)
    for k in range(K):
        te = folds == k; tr = ~te
        x, y = F[tr], Y[tr]
        xm, ym = x.mean(), y.mean()
        sxx = ((x - xm) ** 2).sum()
        b = ((x - xm) * (y - ym)).sum() / sxx if sxx > 1e-300 and len(y) > 2 else 0.0
        a = ym - b * xm
        gL[te] = a + b * F[te]; A[k], B[k] = a, b
    a_, b_ = A.mean(), B.mean()
    gU_mean, gU_var = a_ + b_ * Fu.mean(), b_ ** 2 * Fu.var(ddof=1)
    a = (Y - gL) / n + gL / (n + N)
    th = a.sum() + N * gU_mean / (n + N)
    var = n * a.var(ddof=1) + N * gU_var / (n + N) ** 2
    return th, np.sqrt(var)


def boot_t_interval(fn, Y, F, Fu, rng, B=399, alpha=0.05, K=5):
    """Studentized (bootstrap-t) interval; labeled and unlabeled samples are resampled independently."""
    n, N = len(Y), len(Fu)
    th, se = fn(Y, F, Fu, rng.permutation(n))
    t = np.empty(B)
    for b in range(B):
        i = rng.integers(0, n, n); j = rng.integers(0, N, N)
        tb, sb = fn(Y[i], F[i], Fu[j], rng.permutation(n))
        t[b] = (tb - th) / max(sb, 1e-12)
    lo_q, hi_q = np.quantile(t, [alpha / 2, 1 - alpha / 2])
    return th - hi_q * se, th - lo_q * se, th, se
