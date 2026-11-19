"""Core library: search procedures over a correctness matrix Y[K_pool, N] (bool), and reporting estimators.
Population = the N pool questions (distribution of a fresh question = uniform over pool columns);
the tuning set T is n i.i.d. draws from the pool, so the true score of config k is exactly mu_k = Y[k].mean().
All procedures only see Y[:, T]."""
import numpy as np
from scipy import stats

# ---------------------------------------------------------------- search procedures
# each takes S (K x n bool/float: correctness of the K candidate configs on the tuning questions, in a random order),
# an rng, and optional grid structure; returns (k_selected, reported_score_on_tuning_set).
def _argmax_random_ties(v, rng):
    m = v.max(); c = np.flatnonzero(v >= m - 1e-12)
    return int(c[0] if len(c) == 1 else rng.choice(c))

def proc_argmax(S, rng, **kw):
    """Evaluate all K candidates on the whole tuning set; pick best (grid / random search with full evaluation)."""
    a = S.mean(1); k = _argmax_random_ties(a, rng)
    return k, a[k]

def proc_sh(S, rng, **kw):
    """Successive halving (best-arm identification): R=ceil(log2 K) rounds, equal split of the n questions into rounds
    (disjoint blocks), keep the top half by cumulative score; final report = survivor's score on ALL n tuning questions."""
    K, n = S.shape
    R = max(1, int(np.ceil(np.log2(K)))) if K > 1 else 1
    alive = np.arange(K); edges = np.linspace(0, n, R + 1).astype(int)
    cum = np.zeros(K); cnt = 0
    for r in range(R):
        blk = S[alive][:, edges[r]:edges[r + 1]]
        cum_r = blk.sum(1)
        if r == 0: c = cum_r
        else: c = cum_r  # score on the fresh block of this round only (standard SH with budget split)
        keep = max(1, int(np.ceil(len(alive) / 2)))
        order = np.argsort(-(c + 1e-9 * rng.random(len(alive))))
        alive = alive[order[:keep]]
        if len(alive) == 1: break
    k = int(alive[0]); return k, S[k].mean()

def proc_greedy(S, rng, grid=None, **kw):
    """Coordinate ascent over a factorial grid (dims = tuple of level counts); candidates are the K=prod(dims) configs
    in C order. Start random; for each factor in turn pick the best level given the others (full-T score); repeat to convergence."""
    dims = grid; K, n = S.shape
    a = S.mean(1); idx = np.array([rng.integers(d) for d in dims])
    def flat(ix): return int(np.ravel_multi_index(tuple(ix), dims))
    cur = a[flat(idx)]; changed = True; it = 0
    while changed and it < 10:
        changed = False; it += 1
        for f in rng.permutation(len(dims)):
            vals = []
            for l in range(dims[f]):
                j = idx.copy(); j[f] = l; vals.append(a[flat(j)])
            vals = np.array(vals); l = _argmax_random_ties(vals, rng)
            if vals[l] > cur + 1e-12: idx[f] = l; cur = vals[l]; changed = True
    k = flat(idx); return k, a[k]

def proc_sr(S, rng, **kw):
    """Successive Rejects (Audibert-Bubeck 2010; fixed-budget best-arm identification), budget B = n*K/4 item-evaluations, arms
    pulled on nested prefixes of the tuning questions (pull = evaluate config on the next unused question). Report = winner's
    mean over the pulls the algorithm collected for it (the last phase's n_{K-1} questions)."""
    K, n = S.shape
    if K == 1: return 0, S[0].mean()
    B = n * K / 4.0; lbar = 0.5 + sum(1.0 / i for i in range(2, K + 1)); alive = list(range(K)); prev = 0
    for ph in range(1, K):
        nk = int(np.ceil((B - K) / (lbar * (K + 1 - ph)))); nk = min(max(nk, 1), n)
        m = S[alive][:, :nk].mean(1)
        worst = _argmax_random_ties(-m, rng); alive.pop(worst); prev = nk
    k = alive[0]; return k, S[k, :prev].mean()

PROCS = {"sr": proc_sr, "argmax": proc_argmax, "sh": proc_sh, "greedy": proc_greedy}

# ---------------------------------------------------------------- one replication helpers
def draw_T(N, n, rng): return rng.integers(0, N, n)

def wilson(p, n, alpha=0.05):
    z = stats.norm.ppf(1 - alpha / 2); d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h

def _pair(S, k, Sb, cols=None):
    """baseline's score and paired sd of (pick - baseline) on the report columns -> se of the difference."""
    if Sb is None: return dict()
    x = S[k] if cols is None else S[k][cols]; b = Sb if cols is None else Sb[cols]
    d = x.astype(float) - b; n = len(d)
    return dict(base=float(b.mean()), dse=float(d.std(ddof=1) / np.sqrt(n)) + 1e-12)

# ---------------------------------------------------------------- reporting estimators
def est_naive(proc, S, rng, Sb=None, **kw):
    k, a = PROCS[proc](S, rng, **kw); n = S.shape[1]
    lo, hi = wilson(a, n); return dict(k=k, est=a, lo=lo, hi=hi, z=1.645, **_pair(S, k, Sb))

def est_split(proc, S, rng, Sb=None, frac_search=0.5, S_clean=None, **kw):
    """Select on a random fraction, report on the rest (fresh data for the report). S_clean: outcomes without demo leakage for the report part."""
    K, n = S.shape; ns = int(round(n * frac_search))
    k, _ = PROCS[proc](S[:, :ns], rng, **kw); y = (S if S_clean is None else S_clean)[k, ns:]; a = y.mean()
    lo, hi = wilson(a, n - ns); return dict(k=k, est=a, lo=lo, hi=hi, z=1.645, **_pair(S, k, Sb, np.arange(ns, n)))

def est_crossfit(proc, S, rng, Sb=None, folds=5, **kw):
    """k-fold: run whole procedure on k-1 folds, score its pick on the held-out fold; mean over folds estimates the
    procedure's out-of-sample performance (estimand = procedure run on (1-1/k) n, not a specific final config).
    The reported config k is the full-T procedure output. CI: normal on fold-level accuracies pooled (binomial on n)."""
    K, n = S.shape; f = np.array_split(np.arange(n), folds); sc = []
    for i in range(folds):
        tr = np.concatenate([f[j] for j in range(folds) if j != i])
        kk, _ = PROCS[proc](S[:, tr], rng, **kw); sc.append(S[kk, f[i]].sum())
    a = sum(sc) / n; k, _ = PROCS[proc](S, rng, **kw)
    lo, hi = wilson(a, n); return dict(k=k, est=a, lo=lo, hi=hi, z=1.645, **_pair(S, k, Sb))

def est_boot_optimism(proc, S, rng, Sb=None, B=100, **kw):
    """Procedure-agnostic bootstrap correction (Harrell optimism). For b in 1..B: resample the n tuning questions with
    replacement, run the procedure on the resample, optimism_b = score(pick, resample) - score(pick, original T).
    corrected = naive - mean optimism. Also returns the OOB-based estimate (score of pick on questions not in the resample)."""
    K, n = S.shape; k, a = PROCS[proc](S, rng, **kw); opt = []; oob_num = 0.0; oob_den = 0
    oobs = []
    for b in range(B):
        ix = rng.integers(0, n, n); Sboot = S[:, ix]
        kb, ab = PROCS[proc](Sboot, rng, **kw)
        opt.append(ab - S[kb].mean())
        m = np.ones(n, bool); m[ix] = False
        if m.any(): oobs.append(S[kb, m].mean())
    est = a - np.mean(opt); oob = float(np.mean(oobs))
    se = np.sqrt(a * (1 - a) / n)
    return dict(k=k, est=est, lo=est - 1.96 * se, hi=est + 1.96 * se, naive=a, oob=oob, est632=0.368 * a + 0.632 * oob, opt=float(np.mean(opt)), z=1.645, **_pair(S, k, Sb))

def sim_crit(S, rng, B=500, alpha=0.05):
    """Simultaneous critical value c: (1-alpha)-quantile of max_k |phat*_k - phat_k| / se_k over bootstrap resamples of T
    (Gaussian-max / bootstrap-of-maxima, Chernozhukov-Chetverikov-Kato). Valid for ANY data-dependent selection among
    the K candidates (post-selection / PoSI-type guarantee). se_k from the plug-in binomial; configs with se=0 excluded."""
    K, n = S.shape; p = S.mean(1); se = np.sqrt(np.maximum(p * (1 - p), 1e-4) / n)
    mx = np.empty(B)
    for b in range(B):
        ix = rng.integers(0, n, n); pb = S[:, ix].mean(1)
        mx[b] = np.max(np.abs(pb - p) / se)
    return np.quantile(mx, 1 - alpha), se, p

def est_simultaneous(proc, S, rng, Sb=None, B=300, **kw):
    k, a = PROCS[proc](S, rng, **kw); c, se, p = sim_crit(S, rng, B)
    return dict(k=k, est=a, lo=a - c * se[k], hi=a + c * se[k], crit=c, z=c, **_pair(S, k, Sb))

def winner_truncation(p, Sig, k):
    """Polyhedral lemma for the event {argmax(theta_hat) = k}, theta_hat ~ N(theta, Sig): writing theta_hat = z + c*theta_hat_k with
    c = Sig[:, k]/Sig[k, k] and z independent of theta_hat_k, the event is Vm <= theta_hat_k <= Vp. Returns (Vm, Vp, sk)."""
    K = len(p); sk = np.sqrt(Sig[k, k]); c = Sig[:, k] / Sig[k, k]; z = p - c * p[k]; js = np.array([j for j in range(K) if j != k])
    aj = c[js] - 1.0; bj = -z[js]      # constraint (c_j - 1) x <= -z_j  (theta_hat_j <= theta_hat_k)
    lo_b = [b / a for a, b in zip(aj, bj) if a < -1e-12]; hi_b = [b / a for a, b in zip(aj, bj) if a > 1e-12]
    return (max(lo_b) if lo_b else -np.inf), (min(hi_b) if hi_b else np.inf), sk

def cond_cdf(theta, x, sk, Vm, Vp):
    """P(theta_hat_k <= x | selected, theta_k = theta): truncated-normal cdf on [Vm, Vp] (survival-function form in the upper tail for stability)."""
    from scipy.stats import norm
    a, b, u = (Vm - theta) / sk, (Vp - theta) / sk, (x - theta) / sk
    if a > 0:
        la, lu, lb = norm.logsf(a), norm.logsf(u), norm.logsf(b)
        num = -np.expm1(lu - la); den = -np.expm1(lb - la)
        return float(np.clip(num / den, 0, 1)) if den > 0 else (1.0 if u >= (a + b) / 2 else 0.0)
    num = norm.cdf(u) - norm.cdf(a); den = norm.cdf(b) - norm.cdf(a)
    return float(np.clip(num / den, 0, 1)) if den > 0 else 0.5

def cond_ci(x, sk, Vm, Vp, alpha=0.05):
    """Conditionally median-unbiased estimate and equal-tailed (1-alpha) CI by inverting cond_cdf (decreasing in theta); root bracket x +- 80 sk
    (limits are NOT clipped to [0, 1])."""
    from scipy.optimize import brentq
    def solve(q):
        f = lambda t: cond_cdf(t, x, sk, Vm, Vp) - q
        L, U = x - 80 * sk, x + 80 * sk
        try: return brentq(f, L, U, xtol=1e-7)
        except ValueError: return L if f(L) < 0 else U
    return solve(0.5), solve(1 - alpha / 2), solve(alpha / 2)

def _hyb_cdf(t, x, sk, Vm, Vp, cb):
    """P(theta_hat_k <= x | selected, |theta_hat_k - t| <= cb sk, theta_k = t): truncated-normal cdf on [max(Vm, t - cb sk), min(Vp, t + cb sk)];
    None if x lies outside that set or the set has no mass (t is then not a candidate value)."""
    from scipy.stats import norm
    a = max(Vm, t - cb * sk); b = min(Vp, t + cb * sk)
    if a >= b: return None
    a_, b_, u = (a - t) / sk, (b - t) / sk, (x - t) / sk
    if u < a_ or u > b_: return None
    den = norm.cdf(b_) - norm.cdf(a_)
    if den <= 1e-14: return None
    return (norm.cdf(u) - norm.cdf(a_)) / den

def hybrid_ci(x, sk, Vm, Vp, cb, alpha=0.05, beta=0.005, grid=161):
    """Hybrid CI (see est_hybrid) from the truncation set [Vm, Vp] and the projection half-width cb*sk: the values t in the projection interval
    x +- cb sk (grid of `grid` points) not rejected by the conditional test at level (alpha-beta)/(1-beta) on the restricted set."""
    a1 = (alpha - beta) / (2 * (1 - beta)); keep = []
    for t in np.linspace(x - cb * sk, x + cb * sk, grid):
        F = _hyb_cdf(t, x, sk, Vm, Vp, cb)
        if F is not None and a1 <= F <= 1 - a1: keep.append(t)
    return (min(keep), max(keep)) if keep else (x - cb * sk, x + cb * sk)

def hybrid_median(x, sk, Vm, Vp, cb, grid=161):
    """Hybrid median-unbiased estimate (AKM's hybrid estimator at gamma = 1): the t in x +- cb sk with restricted conditional cdf = 1/2
    (linear interpolation on the grid; the end of the interval if the cdf never crosses 1/2)."""
    ts = np.linspace(x - cb * sk, x + cb * sk, grid); F = np.array([np.nan if (f := _hyb_cdf(t, x, sk, Vm, Vp, cb)) is None else f for t in ts])
    ok = np.flatnonzero(~np.isnan(F))
    if len(ok) == 0: return x
    ts, F = ts[ok], F[ok]; d = F - 0.5; ix = np.flatnonzero(d[:-1] * d[1:] <= 0)
    if len(ix) == 0: return float(ts[np.argmin(np.abs(d))])
    i = ix[0]; w = d[i] / (d[i] - d[i + 1]) if d[i] != d[i + 1] else 0.0
    return float(ts[i] + w * (ts[i + 1] - ts[i]))

def est_conditional(proc, S, rng, Sb=None, alpha=0.05, **kw):
    """Exact conditional-on-selection inference for the winner of a full-evaluation argmax (polyhedral lemma, Lee et al. 2016;
    'inference on winners', Andrews-Kitagawa-McCloskey 2024 for the same event) under the Gaussian approximation
    theta_hat ~ N(theta, Sigma/n), Sigma = sample covariance of the K configs' 0/1 outcomes over the n tuning questions, divided by n.
    Returns the conditionally median-unbiased point estimate and the equal-tailed conditional CI. Only defined for proc == 'argmax'
    (selection event is a polyhedron). Scores are dithered by U(-.5, .5)/n to break lattice ties (selection stays the argmax)."""
    assert proc == "argmax"
    K, n = S.shape; p = S.mean(1) + (rng.random(K) - 0.5) / n; k = int(np.argmax(p))
    if K == 1:
        lo, hi = wilson(p[0], n); return dict(k=0, est=p[0], lo=lo, hi=hi, naive=p[0], z=1.645, **_pair(S, 0, Sb))
    Sig = np.cov(S.astype(float)) / n; Vm, Vp, sk = winner_truncation(p, Sig, k); x = p[k]
    est, lo, hi = cond_ci(x, sk, Vm, Vp, alpha)
    return dict(k=k, est=est, lo=lo, hi=hi, naive=x, z=1.645, **_pair(S, k, Sb))

def est_ladder(proc, S, rng, Sb=None, c=1.0, **kw):
    """Ladder-type thresholded reporting (Blum & Hardt 2015) applied to a sequential search: candidates are submitted in random
    order; the reported best-so-far score only changes when a candidate beats it by more than eta = c/sqrt(n), and is rounded to
    the eta grid. Selected config = last one that moved the ladder; report = ladder value. Only defined for proc == 'argmax'."""
    assert proc == "argmax"
    K, n = S.shape; eta = c / np.sqrt(n); a = S.mean(1); best = -np.inf; k = None
    for j in rng.permutation(K):
        if k is None:
            best = np.round(a[j] / eta) * eta; k = int(j)
        elif a[j] > best + eta:
            best = np.round(a[j] / eta) * eta; k = int(j)
    lo, hi = wilson(min(max(best, 0), 1), n)
    return dict(k=k, est=best, lo=lo, hi=hi, naive=a[k], z=1.645, **_pair(S, k, Sb))

def est_hybrid(proc, S, rng, Sb=None, alpha=0.05, beta=0.005, grid=161, Bc=1000, **kw):
    """Hybrid conditional / projection inference for the winner of a full-evaluation argmax (Andrews-Kitagawa-McCloskey 2024, 'Inference on
    Winners', hybrid estimator and CI), Gaussian approximation as in est_conditional (same dithered scores, one draw). The winner's score is covered by
    theta_hat_k +- c_beta*se_k (c_beta: 1-beta quantile of max_j |Z_j|, Z ~ N(0, corr) from the estimated correlation matrix, Bc draws; the
    least-favourable/projection part); the conditional test given selection is then run on the truncation set additionally restricted to
    |theta_hat_k - theta0| <= c_beta*se_k at level (alpha-beta)/(1-beta). beta = .005. CI = values theta0 not rejected, found by inversion on a grid of 161
    points inside the projection interval (not clipped to [0, 1]). Point estimate = hybrid median-unbiased estimate (conditional median on the restricted
    set; always inside theta_hat_k +- c_beta*se_k); the unrestricted conditional median is returned as `cond_est`."""
    assert proc == "argmax"
    K, n = S.shape
    if K == 1: return est_conditional(proc, S, rng, Sb=Sb, alpha=alpha)
    p = S.mean(1) + (rng.random(K) - 0.5) / n; k = int(np.argmax(p)); x = p[k]
    Sig = np.cov(S.astype(float)) / n; Vm, Vp, sk = winner_truncation(p, Sig, k)
    sd = np.sqrt(np.clip(np.diag(Sig), 1e-12, None)); R = Sig / np.outer(sd, sd)
    w, V = np.linalg.eigh(R); L = V * np.sqrt(np.clip(w, 0, None))
    cb = float(np.quantile(np.abs(rng.standard_normal((Bc, K)) @ L.T).max(1), 1 - beta))
    lo, hi = hybrid_ci(x, sk, Vm, Vp, cb, alpha, beta, grid); est = hybrid_median(x, sk, Vm, Vp, cb, grid)
    return dict(k=k, est=est, lo=lo, hi=hi, naive=x, z=1.645, crit=cb, cond_est=cond_ci(x, sk, Vm, Vp, alpha)[0], **_pair(S, k, Sb))

ESTIMATORS = {"hybrid": est_hybrid, "ladder": est_ladder, "cond": est_conditional, "naive": est_naive, "split": est_split, "crossfit": est_crossfit, "boot_opt": est_boot_optimism, "simul": est_simultaneous}

def theory_gap_gauss(K, s, tau):
    """Gap approx for independent Gaussian-noise argmax: E[eps_sel] = s^2/sqrt(s^2+tau^2) * E[max of K std normals];
    s = sampling sd of each tuning-set score, tau = sd of true means across configs."""
    from scipy.stats import norm
    # E[max of K iid N(0,1)] by numerical integration
    x = np.linspace(-8, 8, 20001); F = norm.cdf(x); f = norm.pdf(x)
    EM = np.trapezoid(x * K * F ** (K - 1) * f, x)
    return s * s / np.sqrt(s * s + tau * tau) * EM
