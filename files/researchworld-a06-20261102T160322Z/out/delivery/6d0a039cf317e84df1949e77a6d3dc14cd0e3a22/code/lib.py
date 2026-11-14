"""Core library: search procedures, reporting methods M0-M5, theory. Operates on binary outcome matrices Y (K candidates x n items).
All randomness through an explicit numpy Generator."""
import functools
import numpy as np
from scipy import stats, optimize, special

# ---------------------------------------------------------------- candidate spaces
LEVELS = {1: (1,), 2: (2,), 5: (5,), 10: (5, 2), 20: (5, 4), 24: (4, 2, 3), 50: (5, 5, 2), 100: (5, 5, 4), 200: (5, 5, 4, 2)}

def coords(levels):
    """index -> factor-level coordinates (mixed radix), shape (K, F)"""
    K = int(np.prod(levels)); idx = np.arange(K); out = []
    for L in reversed(levels):
        out.append(idx % L); idx = idx // L
    return np.stack(out[::-1], 1)

@functools.lru_cache(maxsize=None)
def neighbors(levels):
    """list of arrays: neighbors[c] = configs differing from c in exactly one factor"""
    co = coords(levels); K = len(co); nb = []
    for c in range(K):
        d = (co != co[c]).sum(1)
        nb.append(np.where(d == 1)[0])
    return nb

# ---------------------------------------------------------------- search procedures
def argmax_tb(v, rng):
    """argmax with uniformly random tie-breaking"""
    m = v.max(); w = np.flatnonzero(v >= m - 1e-12)
    return int(w[0] if len(w) == 1 else rng.choice(w))

def p_exhaustive(Y, rng, **kw):
    """evaluate all K candidates on all of D, take the best (random search with K draws / grid search)"""
    return argmax_tb(Y.mean(1), rng), Y.shape[0]

def p_halving(Y, rng, **kw):
    """successive halving: R=ceil(log2 K) rounds, each round scores survivors on a new slice of D (cumulative); keep top half"""
    K, n = Y.shape; R = max(1, int(np.ceil(np.log2(K)))) if K > 1 else 1
    perm = rng.permutation(n); sl = np.array_split(perm, R)
    alive = np.arange(K); cum = np.zeros(K); cnt = 0; evals = 0
    for r in range(R):
        cum[alive] += Y[np.ix_(alive, sl[r])].sum(1); cnt += len(sl[r]); evals += len(alive)
        if len(alive) == 1: break
        s = cum[alive] / cnt + 1e-9 * rng.random(len(alive))
        keep = max(1, len(alive) // 2); alive = alive[np.argsort(-s)[:keep]]
    s = cum[alive] / cnt + 1e-9 * rng.random(len(alive))
    return int(alive[np.argmax(s)]), evals  # evals = candidate-slice evaluations

def p_greedy(Y, rng, levels=None, nb=None, max_steps=50, **kw):
    """coordinate/greedy edit search over the factorial space: start at a random config, move to the best one-factor
    neighbour while it strictly improves the score on D (the same D is reused at every step: adaptive)."""
    K = Y.shape[0]; m = Y.mean(1)
    c = int(rng.integers(K)); seen = {c}
    for _ in range(max_steps):
        cand = nb[c]
        if len(cand) == 0: break
        seen.update(cand.tolist())
        b = cand[argmax_tb(m[cand], rng)]
        if m[b] > m[c] + 1e-12: c = int(b)
        else: break
    return c, len(seen)

PROC = {"exhaustive": p_exhaustive, "halving": p_halving, "greedy": p_greedy}

# ---------------------------------------------------------------- intervals
def wilson(k, n, level=0.95):
    z = stats.norm.ppf(0.5 + level / 2); p = k / n
    d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d

# ---------------------------------------------------------------- M4: selection-aware inference
def mult_boot_q(Y, rng, B=500, level=0.95, beta=None):
    """Gaussian multiplier bootstrap critical values for max_c |(phat_c - p_c)|/se_c (two-sided, `level`) and for
    max_c (phat_c - p_c)/se_c (one-sided, 1-beta) (Chernozhukov-Chetverikov-Kato). Returns (q2, q1, phat, se)."""
    K, n = Y.shape; p = Y.mean(1); R = Y - p[:, None]; se = np.sqrt(np.maximum((R ** 2).mean(1), 1e-12))
    xi = rng.standard_normal((B, n)); T = (xi @ R.T) / np.sqrt(n) / se[None]
    q2 = float(np.quantile(np.abs(T).max(1), level))
    q1 = float(np.quantile(T.max(1), 1 - beta)) if beta else None
    return q2, q1, p, se / np.sqrt(n)

def cond_ci(Y, chat, alpha=0.05, hybrid_beta=None, q_first=None, rng=None):
    """Conditional / hybrid interval for the selected candidate. Scores are integers/n, so exact ties with the winner occur
    and the Gaussian selection event degenerates (V_lo = Z). Tie handling: the other candidates' means are lowered by an
    independent U(0, 1/n) (the winner keeps its value), i.e. the winner wins its ties; this is a pragmatic continuity fix."""
    K, n = Y.shape; X = Y.mean(1)
    if K == 1:
        se = max(np.sqrt(X[0] * (1 - X[0]) / n), 1e-9); return X[0] - 1.96 * se, X[0] + 1.96 * se, X[0]
    if rng is not None:
        j = rng.random(K) / n; j[chat] = 0.0; X = X - j
    return cond_ci_gauss(X, np.atleast_2d(np.cov(Y)) / n, chat, alpha, hybrid_beta, q_first)

def cond_ci_gauss(X, S, chat, alpha=0.05, hybrid_beta=None, q_first=None):
    """Conditional (Lee et al. 2016 / Andrews-Kitagawa-McCloskey) inference for theta_{chat} given chat = argmax of means,
    Gaussian approximation X ~ N(theta, Sigma), Sigma = Cov(Y rows)/n. Optional hybrid truncation with first-stage critical value.
    Returns (lo, hi, median_unbiased)."""
    K = len(X)
    sz2 = max(S[chat, chat], 1e-12); sz = np.sqrt(sz2); Z = X[chat]
    cvec = S[:, chat] / sz2; W = X - cvec * Z
    others = np.arange(K) != chat
    a = (np.where(np.arange(K) == chat, 1.0, 0.0)[None] - np.eye(K)[others])  # rows e_chat - e_j
    alpha_j = a @ cvec; aW = a @ W
    lo, hi = -np.inf, np.inf
    pos = alpha_j > 1e-12; neg = alpha_j < -1e-12
    if pos.any(): lo = np.max(-aW[pos] / alpha_j[pos])
    if neg.any(): hi = np.min(-aW[neg] / alpha_j[neg])
    lo = min(lo, Z); hi = max(hi, Z)
    grid = Z + sz * np.sinh(np.linspace(-np.arcsinh(60), np.arcsinh(60), 1601)) * 1.0
    if hybrid_beta is not None:
        a2 = (alpha - hybrid_beta) / (1 - hybrid_beta)
        lo_v = np.maximum(lo, grid - q_first * sz); hi_v = np.minimum(hi, grid + q_first * sz)
    else:
        a2 = alpha; lo_v = np.full_like(grid, lo); hi_v = np.full_like(grid, hi)
    Fv = _trunc_cdf(Z, grid, lo_v, hi_v, sz)
    ok = (Fv >= a2 / 2) & (Fv <= 1 - a2 / 2)
    ib = int(np.argmin(np.abs(Fv - 0.5))); med = grid[ib] if abs(Fv[ib] - 0.5) < 0.05 and 0 < ib < len(grid) - 1 else np.nan
    if not ok.any(): return -np.inf, float(grid[0]), float(med)
    l, h = float(grid[ok].min()), float(grid[ok].max())
    return (-np.inf if ok[0] else l), (np.inf if ok[-1] else h), float(med)

def _trunc_cdf(Z, th, lo, hi, sz):
    """P(Z' <= Z) for Z' ~ N(th, sz^2) truncated to [lo, hi]; vectorised over th (and lo, hi); numerically stable in the tails.
    Returns 1 where Z >= hi, 0 where Z <= lo."""
    a = (lo - th) / sz; b = (hi - th) / sz; z = (Z - th) / sz
    out = np.empty_like(th, dtype=float)
    out[:] = np.nan
    np.seterr(over='ignore', invalid='ignore')
    lowT = b <= 0; upT = (a > 0) & ~lowT; mid = ~lowT & ~upT
    lN = special.log_ndtr
    if lowT.any():
        x = lowT; la, lz, lb = lN(a[x]), lN(np.minimum(z[x], b[x])), lN(b[x])
        out[x] = (np.exp(lz - lb) - np.exp(la - lb)) / (1 - np.exp(la - lb) + 1e-300)
    if upT.any():
        x = upT; qa, qz, qb = lN(-a[x]), lN(-np.maximum(z[x], a[x])), lN(-b[x])
        out[x] = (1 - np.exp(qz - qa)) / (1 - np.exp(qb - qa) + 1e-300)
    if mid.any():
        x = mid; Pa, Pz, Pb = stats.norm.cdf(a[x]), stats.norm.cdf(np.clip(z[x], a[x], b[x])), stats.norm.cdf(b[x])
        out[x] = (Pz - Pa) / np.maximum(Pb - Pa, 1e-300)
    out = np.where(Z >= hi, 1.0, np.where(Z <= lo, 0.0, out))
    return np.clip(out, 0, 1)

def simultaneous_ci(Y, chat, rng, level=0.95, B=500, beta=0.005):
    q2, q1, p, se = mult_boot_q(Y, rng, B=B, level=level, beta=beta)
    return p[chat] - q2 * se[chat], p[chat] + q2 * se[chat], q1

# ---------------------------------------------------------------- M3: bootstrap optimism correction
def boot_opt(Y, proc, rng, B=100, pkw=None):
    """Efron optimism correction and .632 for the whole search procedure. Returns (est_opt_corrected, est_632)."""
    pkw = pkw or {}; K, n = Y.shape; chat, _ = proc(Y, rng, **pkw); R0 = Y[chat].mean()
    opt = []; oob = []
    for _ in range(B):
        idx = rng.integers(0, n, n); Yb = Y[:, idx]
        cb, _ = proc(Yb, rng, **pkw)
        opt.append(Yb[cb].mean() - Y[cb].mean())
        m = np.ones(n, bool); m[idx] = False
        if m.any(): oob.append(Y[cb][m].mean())
    return R0 - float(np.mean(opt)), 0.368 * R0 + 0.632 * float(np.mean(oob)), chat

# ---------------------------------------------------------------- M5: disclosure-based
def eb_shrink(Y, chat):
    """What a reader can compute from a *disclosed* score vector (all K candidate scores on D, and n): normal-normal
    empirical-Bayes posterior mean of the selected candidate's accuracy; moment estimate of tau^2."""
    K, n = Y.shape; p = Y.mean(1)
    if K < 3: return p[chat], np.nan, np.nan
    v = np.mean(p * (1 - p)) / n; mu = p.mean(); t2 = max(p.var(ddof=1) - v, 0.0)
    B = v / (v + t2) if (v + t2) > 0 else 1.0
    est = mu + (1 - B) * (p[chat] - mu); h = 1.96 * np.sqrt((1 - B) * v + B * B * v / K)   # normal-normal posterior sd
    return est, est - h, est + h

def ladder(Y, rng, eta=None):
    """Ladder (Blum & Hardt 2015) applied to the K evaluations in random order: report best-so-far, updated only if a new
    candidate beats it by more than eta; value rounded to a multiple of eta. Returns reported value."""
    K, n = Y.shape; eta = eta or n ** (-1 / 3); p = Y.mean(1)[rng.permutation(K)]
    best = 0.0
    for v in p:
        if v < best + eta: continue
        best = np.round(v / eta) * eta
    return float(best)

# ---------------------------------------------------------------- theory (exhaustive / random search)
def g_max(K):
    """E[max of K iid N(0,1)] (exact quadrature)"""
    if K == 1: return 0.0
    x = np.linspace(-9, 9, 40001); F = stats.norm.cdf(x); pdf = stats.norm.pdf(x)
    return float(np.trapezoid(x * K * F ** (K - 1) * pdf, x))

def theory_gap(n, K, sigma, r, tau):
    """Gaussian-approximation prediction of E[reported - true] for exhaustive search: estimates p_c = theta_c + e_c,
    theta_c ~ iid N(.,tau^2), e_c ~ N(0, sigma^2/n) with pairwise correlation r (common part cancels in the argmax):
    Delta = s^2 g(K) / sqrt(tau^2 + s^2), s^2 = sigma^2 (1-r)/n."""
    s2 = sigma ** 2 * (1 - r) / n
    return s2 * g_max(K) / np.sqrt(tau ** 2 + s2) if (tau ** 2 + s2) > 0 else 0.0
