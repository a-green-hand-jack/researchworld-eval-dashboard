"""Reporting estimators for the score of a configuration picked by argmax on a finite question set.

Input everywhere: S, an (n, K) 0/1 matrix of per-question scores of the K candidate configurations that the search
visited, all evaluated on the same n search questions. The tuned configuration is c* = argmax_c mean(S[:, c]).

Each estimator returns (point_estimate, lo, hi) for a two-sided interval at level 1-alpha for mu_{c*}
(true accuracy of the *selected* configuration on fresh questions), plus c*.
"""
import numpy as np
from scipy.special import log_ndtr
from scipy.optimize import brentq
from scipy.stats import norm


def argmax_rand(m, rng):
    mx = m.max(); idx = np.flatnonzero(m >= mx - 1e-12)
    return int(idx[0] if len(idx) == 1 else rng.choice(idx))


def wilson(k, n, alpha):
    z = norm.ppf(1 - alpha / 2); p = k / n
    d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def naive(S, rng, alpha=0.1, c=None):
    n, K = S.shape; m = S.mean(0); c = argmax_rand(m, rng) if c is None else c
    lo, hi = wilson(S[:, c].sum(), n, alpha)
    return m[c], lo, hi, c


def holdout(S, rng, alpha=0.1, frac_sel=0.5):
    """Split questions: select on the first part, report (with Wilson interval) on the held-out part."""
    n, K = S.shape; ns = int(round(n * frac_sel))
    A, B = S[:ns], S[ns:]
    c = argmax_rand(A.mean(0), rng)
    lo, hi = wilson(B[:, c].sum(), len(B), alpha)
    return B[:, c].mean(), lo, hi, c


def boot_optimism(S, rng, alpha=0.1, B=200, c=None):
    """Efron-style optimism correction replicating the selection step inside each bootstrap resample.
    point = naive - E_b[ mean_b(c_b) - mean_orig(c_b) ]. Interval: naive-centred, half-width from the bootstrap
    distribution of (mean_b(c_b)-mean_orig(c_b)) plus sampling sd of the selected config (percentile of optimism-corrected pivot)."""
    n, K = S.shape; m = S.mean(0); c = argmax_rand(m, rng) if c is None else c
    idx = rng.randint(0, n, size=(B, n))
    # bootstrap means via counts matrix
    cnt = np.zeros((B, n), dtype=np.float32)
    for b in range(B):
        cnt[b] = np.bincount(idx[b], minlength=n)
    mb = cnt @ S / n  # (B,K)
    cb = np.argmax(mb, 1)
    opt = mb[np.arange(B), cb] - m[cb]
    est = m[c] - opt.mean()
    # pivot: bootstrap analogue of (hat mu_{c*} - mu_{c*}) = (mb[c_b] - m[c_b]) - opt-corrected; use percentiles of (opt - mean opt) spread
    # plus binomial noise of the selected config
    se = np.sqrt(max(m[c] * (1 - m[c]), 1e-4) / n)
    dev = opt - opt.mean()
    tot = dev + rng.randn(B) * se
    lo = est + np.quantile(-tot, alpha / 2); hi = est + np.quantile(-tot, 1 - alpha / 2)
    return est, lo, hi, c


def maxT(S, rng, alpha=0.1, B=300, c=None):
    """Simultaneous (max-|T|) bootstrap band over all K visited configs; valid for ANY selection rule among them.
    Interval for mu_{c*}: m[c*] +- q, q = (1-alpha) quantile of max_c |mean_b(c)-mean(c)|."""
    n, K = S.shape; m = S.mean(0); c = argmax_rand(m, rng) if c is None else c
    idx = rng.randint(0, n, size=(B, n))
    cnt = np.zeros((B, n), dtype=np.float32)
    for b in range(B):
        cnt[b] = np.bincount(idx[b], minlength=n)
    mb = cnt @ S / n
    q = np.quantile(np.abs(mb - m).max(1), 1 - alpha)
    return m[c], m[c] - q, m[c] + q, c


def _tn_cdf(t, mu, sig, vm, vp):
    """P(T<=t | T in [vm,vp]), T~N(mu,sig^2); log-space stable."""
    a, b, x = (vm - mu) / sig, (vp - mu) / sig, (t - mu) / sig
    la, lb, lx = log_ndtr(a), log_ndtr(b), log_ndtr(x)
    if np.isinf(vp):
        # use survival forms for stability
        sa, sx = log_ndtr(-a), log_ndtr(-x)
        # P(T<=t|T>=vm) = 1 - S(x)/S(a)
        return 1.0 - np.exp(sx - sa) if x > a else 0.0
    num = np.exp(lx - lb) - np.exp(la - lb) if x > a else 0.0
    den = 1.0 - np.exp(la - lb)
    return float(np.clip(num / den, 0, 1)) if den > 0 else 0.5


def conditional(S, rng, alpha=0.1, cap=6.0, ridge=1e-6, c=None):
    """Polyhedral (Lee et al. 2016) conditional-on-selection inference for the winner of a Gaussian argmax.
    Gaussian approx: mean vector y ~ N(mu, Sigma), Sigma = sample covariance / n (plug-in).
    Condition on {y_c* >= y_c for all c}; interval for mu_{c*} by inverting the truncated-normal pivot;
    point = median-unbiased estimate (pivot = 1/2)."""
    n, K = S.shape; y = S.mean(0); c = argmax_rand(y, rng) if c is None else c
    if K == 1:
        lo, hi = wilson(S[:, 0].sum(), n, alpha); return y[0], lo, hi, 0
    Sig = np.cov(S, rowvar=False, ddof=1).reshape(K, K) / n + ridge * np.eye(K) / n
    sig2 = Sig[c, c]; sig = np.sqrt(sig2)
    cvec = Sig[:, c] / sig2
    t = y[c]; z = y - cvec * t
    others = np.arange(K) != c
    # constraint j: y_j - y_c <= 0 ; a_j'y = (z_j - z_c) + (cvec_j - 1) t <= 0   (cvec_c = 1)
    aj_c = cvec[others] - 1.0
    rhs = -(z[others] - z[c])
    vm, vp = -np.inf, np.inf
    neg = aj_c < -1e-12; pos = aj_c > 1e-12
    if neg.any(): vm = np.max(rhs[neg] / aj_c[neg])
    if pos.any(): vp = np.min(rhs[pos] / aj_c[pos])
    vm = min(vm, t); vp = max(vp, t)
    f = lambda mu: _tn_cdf(t, mu, sig, vm, vp)
    lo_b, hi_b = t - cap * sig, t + cap * sig
    # cdf decreasing in mu. upper limit: f(mu)=alpha/2 ; lower limit: f(mu)=1-alpha/2 ; median: 1/2
    def solve(target):
        fl, fh = f(lo_b) - target, f(hi_b) - target
        if fl <= 0: return lo_b
        if fh >= 0: return hi_b
        return brentq(lambda m_: f(m_) - target, lo_b, hi_b, xtol=1e-5)
    hi = solve(alpha / 2); lo = solve(1 - alpha / 2); med = solve(0.5)
    return med, lo, hi, c


def ladder(S, rng, alpha=0.1, eta=None, order=None):
    """Ladder (Blum & Hardt 2015) adapted to accuracy: scan candidates in random order, keep the best *reported*
    score, update only if the candidate's empirical accuracy beats it by more than eta; report rounded value.
    Returns (reported, nan, nan, config at last update)."""
    n, K = S.shape; eta = eta if eta is not None else n ** (-1 / 3)
    m = S.mean(0); order = rng.permutation(K) if order is None else order
    rep, cur = 0.0, int(order[0])
    first = True
    for c in order:
        if first or m[c] > rep + eta:
            rep = np.round(m[c] / eta) * eta; cur = int(c); first = False
    return min(rep, 1.0), np.nan, np.nan, cur


METHODS = {
    "naive": naive,
    "holdout50": lambda S, r, a: holdout(S, r, a, 0.5),
    "holdout75": lambda S, r, a: holdout(S, r, a, 0.75),
    "boot_opt": boot_optimism,
    "maxT": maxT,
    "cond": conditional,
    "ladder_n13": lambda S, r, a: ladder(S, r, a, None),
    "ladder_n12": lambda S, r, a: ladder(S, r, a, 0.5 / np.sqrt(S.shape[0])),
}
