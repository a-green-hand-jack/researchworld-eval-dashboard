"""Search algorithms, reporting methods and Monte-Carlo harness for the 'winner's curse of prompt tuning' study.

World: a matrix Y[N, K] in {0,1} of per-item correctness of K candidate configurations on a population of N items.
A 'benchmark' S is a random subset of n items. A search algorithm sees only Y[S, :] (through evaluation calls) and returns a config.
Truth for the selected config = mean of Y[P \\ S, config] (fresh items; real data) or the exact accuracy (synthetic).
"""
import numpy as np
from scipy import stats, special, optimize

# factor structure of the real grid (6 groups x 4 instructions x 3 cues = 72); used by coordinate ascent / mipro-like
FACTORS = (6, 4, 3)
def cfg_levels(c):
    g, r = divmod(c, 12); i, k = divmod(r, 3); return (g, i, k)
def levels_cfg(l):
    return l[0] * 12 + l[1] * 3 + l[2]

# ---------------------------------------------------------------- search algorithms (operate on Ys = Y[S,:] restricted to pool)
# each returns (chosen config index, reported score on full S)
def _argmax(v, rng):
    return int(np.argmax(v + 1e-9 * rng.random(len(v))))

def random_search(Ys, rng, B, pool=None):
    pool = np.arange(Ys.shape[1]) if pool is None else pool
    cand = rng.choice(pool, size=min(B, len(pool)), replace=False)
    m = Ys[:, cand].mean(0)
    j = _argmax(m, rng)
    return int(cand[j]), float(m[j])

def successive_halving(Ys, rng, B, pool=None, eta=3, min_n=25):
    pool = np.arange(Ys.shape[1]) if pool is None else pool
    cand = rng.choice(pool, size=min(B, len(pool)), replace=False)
    n = Ys.shape[0]
    order = rng.permutation(n)
    nrung = max(1, int(np.ceil(np.log(len(cand)) / np.log(eta))) + 1)
    sizes = [max(min_n, int(round(n / eta ** (nrung - 1 - r)))) for r in range(nrung)]
    sizes[-1] = n
    for r in range(nrung):
        idx = order[:min(sizes[r], n)]
        m = Ys[np.ix_(idx, cand)].mean(0)
        if r == nrung - 1 or len(cand) == 1:
            break
        keep = max(1, int(np.ceil(len(cand) / eta)))
        top = np.argsort(-(m + 1e-9 * rng.random(len(m))))[:keep]
        cand = cand[top]
    # final decision on the last rung evaluated on all of S
    m = Ys[:, cand].mean(0)
    j = _argmax(m, rng)
    return int(cand[j]), float(m[j])

def coordinate_ascent(Ys, rng, B=None, pool=None, passes=2):
    """Greedy factor-wise ascent from a random start (full-S evaluations). Path dependent / adaptive."""
    lev = [int(rng.integers(f)) for f in FACTORS]
    cache = {}
    def ev(l):
        c = levels_cfg(l)
        if c not in cache: cache[c] = float(Ys[:, c].mean())
        return cache[c]
    best = ev(lev)
    for _ in range(passes):
        changed = False
        for f in rng.permutation(len(FACTORS)):
            vals = []
            for v in range(FACTORS[f]):
                l2 = list(lev); l2[f] = v; vals.append(ev(l2))
            vals = np.array(vals); v = _argmax(vals, rng)
            if vals[v] > best + 1e-12:
                lev[f] = v; best = vals[v]; changed = True
        if not changed: break
    c = levels_cfg(lev)
    return c, float(Ys[:, c].mean())

def mipro_like(Ys, rng, B, pool=None, mb=50, finalists=3, explore=0.3):
    """Surrogate-guided search in the spirit of MIPRO: B trials on random minibatches, additive per-factor-level
    surrogate for proposal, then full-S evaluation of the top finalists."""
    n = Ys.shape[0]; mb = min(mb, n)
    sums = {}; cnts = {}
    lvl_sum = [np.zeros(f) for f in FACTORS]; lvl_cnt = [np.zeros(f) for f in FACTORS]
    for t in range(B):
        lev = []
        for f, F in enumerate(FACTORS):
            if t < 2 or rng.random() < explore or lvl_cnt[f].sum() == 0:
                lev.append(int(rng.integers(F)))
            else:
                mean = (lvl_sum[f] + 0.0) / np.maximum(lvl_cnt[f], 1)
                mean[lvl_cnt[f] == 0] = mean.max()  # optimism for untried levels
                p = np.exp((mean - mean.max()) / 0.03); p /= p.sum()
                lev.append(int(rng.choice(F, p=p)))
        c = levels_cfg(lev)
        idx = rng.choice(n, size=mb, replace=False)
        s = float(Ys[idx, c].mean())
        sums[c] = sums.get(c, 0.0) + s; cnts[c] = cnts.get(c, 0) + 1
        for f in range(len(FACTORS)):
            lvl_sum[f][lev[f]] += s; lvl_cnt[f][lev[f]] += 1
    cs = np.array(list(sums.keys())); avg = np.array([sums[c] / cnts[c] for c in cs])
    top = cs[np.argsort(-(avg + 1e-9 * rng.random(len(avg))))[:finalists]]
    m = Ys[:, top].mean(0)
    j = _argmax(m, rng)
    return int(top[j]), float(m[j])

ALGOS = {"rs": random_search, "sh": successive_halving, "ca": coordinate_ascent, "mipro": mipro_like}

# ---------------------------------------------------------------- confidence intervals
def wald(p, n, z=1.959964):
    se = np.sqrt(max(p * (1 - p), 1e-12) / n); return p - z * se, p + z * se
def wilson(k, n, z=1.959964):
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h

# ---------------------------------------------------------------- conditional (winner) inference, polyhedral lemma
def _tn_cdf(y, mu, sig, lo, hi):
    """CDF at y of N(mu,sig^2) truncated to [lo,hi] (scipy's truncnorm is tail-stable)."""
    a, b = (lo - mu) / sig, (hi - mu) / sig
    if b - a < 1e-12: return 0.5
    return float(stats.truncnorm.cdf((y - mu) / sig, a, b))

def winner_conditional(Yc, Sigma, win, alpha=0.05, span=60.0):
    """Conditional-on-selection inference for mu[win] given Y ~ N(mu, Sigma) and selection event {Y[win] >= Y[c] for all c}.
    Returns (median-unbiased estimate, lo, hi). Sigma is the covariance of the vector Yc (already divided by n)."""
    K = len(Yc); sig2 = Sigma[win, win]; sig = np.sqrt(sig2)
    cvec = Sigma[:, win] / sig2
    y = Yc[win]; Z = Yc - cvec * y
    lo, hi = -np.inf, np.inf
    for c in range(K):
        if c == win: continue
        a = np.zeros(K); a[c] = 1; a[win] = -1          # a'Y <= 0
        al = a @ cvec; az = a @ Z
        if abs(al) < 1e-14: continue
        bound = -az / al
        if al > 0: hi = min(hi, bound)
        else: lo = max(lo, bound)
    lo = min(lo, y); hi = max(hi, y)
    def F(mu): return _tn_cdf(y, mu, sig, lo, hi)
    def root(target):
        g = lambda mu: F(mu) - target
        L, U = y - span * sig, y + span * sig
        gl, gu = g(L), g(U)
        if gl < 0: return -np.inf   # F decreasing in mu: F(L) is largest
        if gu > 0: return np.inf
        return optimize.brentq(g, L, U, xtol=1e-9)
    return root(0.5), root(1 - alpha / 2), root(alpha / 2)   # F decreasing: F=1-a/2 -> lower end

# ---------------------------------------------------------------- Monte-Carlo harness
def draw_split(N, n, rng):
    perm = rng.permutation(N); return perm[:n], perm[n:]
