"""Monte-Carlo harness: one trial = draw benchmark S, run search, produce reports from several reporting methods."""
import numpy as np
from sel import *

def fresh_acc(Y, fresh, c):
    return float(Y[fresh, c].mean())

def replay_bootstrap(Ys, algo, kw, rng, nboot=100):
    """Efron-style optimism of the *whole search procedure*, re-running the search on bootstrap resamples of S."""
    n = Ys.shape[0]; opt = np.empty(nboot); oob = np.empty(nboot)
    for b in range(nboot):
        idx = rng.integers(n, size=n)
        cb, rb = algo(Ys[idx], rng, **kw)
        opt[b] = rb - Ys[:, cb].mean()
        mask = np.ones(n, bool); mask[idx] = False
        oob[b] = Ys[mask, cb].mean() if mask.any() else np.nan
    return opt, oob

def trial(Y, n, algo_name, kw, rng, truth_acc=None, nboot=100, folds=5, rho_hold=0.3, wr=False):
    """Y: [N,K] population matrix.  truth_acc: exact per-config accuracy (synthetic) or None (use fresh items P\\S)."""
    N, K = Y.shape
    S, fresh = (rng.integers(N, size=n), None) if wr else draw_split(N, n, rng)
    if wr and truth_acc is None: truth_acc = Y.mean(0)
    Ys = Y[S]
    algo = ALGOS[algo_name]
    tr = (lambda c: float(truth_acc[c])) if truth_acc is not None else (lambda c: fresh_acc(Y, fresh, c))
    out = {}
    # --- naive
    c, R = algo(Ys, rng, **kw)
    lo, hi = wald(R, n)
    t0 = tr(c)
    out["naive"] = (R, lo, hi, t0)
    # --- replay-bootstrap optimism correction (generic, any search algorithm)
    opt, oob = replay_bootstrap(Ys, algo, kw, rng, nboot)
    pt = R - opt.mean()
    se = np.sqrt(max(pt * (1 - pt), 1e-6) / n)
    out["boot_opt"] = (pt, pt - 1.959964 * se, pt + 1.959964 * se, t0)
    p632 = 0.368 * R + 0.632 * np.nanmean(oob)
    out["boot_632"] = (p632, p632 - 1.959964 * se, p632 + 1.959964 * se, t0)
    # --- hold-out split: search on (1-rho) of S, report on the rest
    perm = rng.permutation(n); nh = int(round(rho_hold * n)); H = perm[:nh]; T = perm[nh:]
    ch, _ = algo(Ys[T], rng, **kw)
    kh = int(Ys[H, ch].sum()); ph = kh / nh; l, h = wilson(kh, nh)
    out["holdout"] = (ph, l, h, tr(ch))
    # --- K-fold cross-fitting: procedure-level estimate (target: the deployed config's fresh accuracy, and the mean fold-config accuracy)
    fperm = rng.permutation(n); fsz = np.array_split(fperm, folds)
    ksum = 0; tfold = []
    for f in range(folds):
        te = fsz[f]; trn = np.concatenate([fsz[g] for g in range(folds) if g != f])
        cf, _ = algo(Ys[trn], rng, **kw)
        ksum += Ys[te, cf].sum(); tfold.append(tr(cf))
    pcf = ksum / n; l, h = wald(pcf, n)
    out["crossfit"] = (pcf, l, h, t0)
    out["crossfit_tfold"] = (pcf, l, h, float(np.mean(tfold)))
    return out


# ------------------------------------------------------------------ methods that need B fully evaluated candidates (random/grid search)
def eb_shrink(Ys_c, win):
    """Empirical-Bayes (normal-normal) winner's-curse shrinkage of the winner toward the grand mean of the evaluated configs.
    Noise covariance of the B accuracies is estimated from the paired item-level data, so shared-item noise is not
    mistaken for between-config signal."""
    n, B = Ys_c.shape; p = Ys_c.mean(0)
    if B < 3: return float(p[win]), float(p[win]), float(p[win])
    Sig = np.cov(Ys_c.T, ddof=1) / n
    P = np.eye(B) - 1.0 / B
    PSP = P @ Sig @ P
    sig2_c = float(np.trace(PSP) / (B - 1))            # E[var_c(Y)] = tau^2 + sig2_c
    tau2 = max(float(p.var(ddof=1)) - sig2_c, 0.0)
    k = tau2 / (tau2 + sig2_c) if (tau2 + sig2_c) > 0 else 0.0
    m = float(p.mean())
    est = m + k * (p[win] - m)
    s_m2 = float(Ys_c.mean(1).var(ddof=1) / n)           # sampling variance of the grand mean (shared item noise)
    sd = np.sqrt(max(k * sig2_c + s_m2, 1e-12))
    return est, est - 1.959964 * sd, est + 1.959964 * sd

def simultaneous_ci(Ys_c, win, rng, nb=500, alpha=0.05):
    """Max-t bootstrap simultaneous band over the B evaluated configs (Chernozhukov et al. style); returns CI for the winner."""
    n, B = Ys_c.shape; p = Ys_c.mean(0)
    se = np.sqrt(np.maximum(p * (1 - p), 1e-6) / n)
    mx = np.empty(nb)
    for b in range(nb):
        idx = rng.integers(n, size=n)
        pb = Ys_c[idx].mean(0)
        mx[b] = np.max(np.abs(pb - p) / se)
    q = np.quantile(mx, 1 - alpha)
    return p[win], p[win] - q * se[win], p[win] + q * se[win], q

def conditional_ci(Ys_c, win, alpha=0.05):
    n, B = Ys_c.shape; p = Ys_c.mean(0)
    Sigma = np.cov(Ys_c.T, ddof=1) / n + 1e-10 * np.eye(B)
    try:
        return winner_conditional(p, Sigma, win, alpha)
    except Exception:
        return (np.nan, np.nan, np.nan)

def ladder_search(Ys, cand, eta):
    """Ladder (Blum & Hardt 2015) run over the candidate sequence: the 'leaderboard' only moves if the sample accuracy
    beats the current best by more than eta; reported value is the rounded best. Returns (config position, reported)."""
    best = -1.0; pos = 0; first = True
    for j in range(len(cand)):
        r = float(Ys[:, j].mean())
        if first or r > best + eta:
            best = round(r / eta) * eta; pos = j; first = False
    return pos, best

def thresholdout_search(Ys, cand, rng, T, sigma):
    """Thresholdout (Dwork et al. 2015): half of S is 'train', half 'holdout'; each candidate query is answered by the
    train accuracy unless it disagrees with the holdout by more than a noisy threshold, in which case the noisy holdout
    accuracy is returned.  The analyst picks the highest answered value and reports it."""
    n = Ys.shape[0]; perm = rng.permutation(n); tr, ho = perm[:n // 2], perm[n // 2:]
    ans = np.empty(len(cand))
    for j in range(len(cand)):
        rt, rh = Ys[tr, j].mean(), Ys[ho, j].mean()
        if abs(rt - rh) > T + rng.laplace(0, 2 * sigma):
            ans[j] = rh + rng.laplace(0, sigma)
        else:
            ans[j] = rt
    j = int(np.argmax(ans + 1e-9 * rng.random(len(cand))))
    return j, float(ans[j])

_EM = {}
def emax_table(B):
    if B not in _EM: _EM[B] = float(np.random.default_rng(99).standard_normal((40000, B)).max(1).mean()) if B > 1 else 0.0
    return _EM[B]

def trial_rs_extras(Y, n, B, rng, truth_acc=None, nboot=100, wr=False):
    N, K = Y.shape
    S, fresh = (rng.integers(N, size=n), None) if wr else draw_split(N, n, rng)
    if wr and truth_acc is None: truth_acc = Y.mean(0)
    Ys = Y[S]
    cand = rng.choice(K, size=min(B, K), replace=False)
    Yc = Ys[:, cand]
    tr = (lambda c: float(truth_acc[c])) if truth_acc is not None else (lambda c: float(Y[fresh, c].mean()))
    p = Yc.mean(0); win = int(np.argmax(p + 1e-9 * rng.random(len(p)))); t0 = tr(int(cand[win])); R = float(p[win])
    out = {}
    lo, hi = wald(R, n); out["naive"] = (R, lo, hi, t0)
    e = eb_shrink(Yc, win); out["eb"] = (e[0], e[1], e[2], t0)
    # worst-case analytic correction: subtract sigma_spec * E[max of B std normals] (eq. 1 with tau = 0), interval = naive width
    Bc = len(cand)
    if Bc >= 3:
        Sg = np.cov(Yc.T, ddof=1) / n; Pm = np.eye(Bc) - 1.0 / Bc
        sg = float(np.sqrt(np.trace(Pm @ Sg @ Pm) / (Bc - 1)))
        pt = R - sg * emax_table(Bc)
        out["worstcase"] = (pt, pt - 1.959964 * np.sqrt(R * (1 - R) / n), pt + 1.959964 * np.sqrt(R * (1 - R) / n), t0)
    s = simultaneous_ci(Yc, win, rng); out["simult"] = (s[0], s[1], s[2], t0)
    m, l, h = conditional_ci(Yc, win); out["cond"] = (m, l, h, t0)
    out["cond_naive_pt"] = (R, l, h, t0)      # CI from the conditional procedure, centred reporting at the raw estimate
    eta = 1.0 / np.sqrt(n)
    j, rep = ladder_search(Yc, cand, eta)
    out["ladder"] = (rep, rep - 1.96 * np.sqrt(0.25 / n), rep + 1.96 * np.sqrt(0.25 / n), tr(int(cand[j])))
    se_d = np.sqrt(2 * 0.25 / (n / 2))
    for nm, tm, sm in (("thresholdout", 1.0, 0.5), ("thresholdout_lo", 1.0, 0.1), ("thresholdout_hi", 2.0, 0.25)):
        j, rep = thresholdout_search(Yc, cand, rng, T=tm * se_d, sigma=sm * se_d)
        out[nm] = (rep, rep - 1.96 * np.sqrt(0.25 / (n / 2)), rep + 1.96 * np.sqrt(0.25 / (n / 2)), tr(int(cand[j])))
    return out


# ------------------------------------------------------------------ decisions about comparisons
def trial_compare(Y, n, rng, algoA, kwA, algoB=None, kwB=None, poolB=None, truth_acc=None, nboot=100, rho_hold=0.3, wr=False, delta=0.0):
    """System A is tuned on S.  System B is either an untuned default (algoB None: a config drawn uniformly from poolB or all configs)
    or tuned by algoB.  We report, for three reporting methods, the claimed gap and a one-sided z-test decision for 'A > B'.
    truth = mu(theta_A) - mu(theta_B) on fresh items (or exact accuracies)."""
    N, K = Y.shape
    S, fresh = (rng.integers(N, size=n), None) if wr else draw_split(N, n, rng)
    if wr and truth_acc is None: truth_acc = Y.mean(0)
    tr = (lambda c: float(truth_acc[c])) if truth_acc is not None else (lambda c: float(Y[fresh, c].mean()))
    Ys = Y[S]
    fa, fb = ALGOS[algoA], (ALGOS[algoB] if algoB else None)
    pool_b = np.arange(K) if poolB is None else poolB
    def run(Ysub):
        ca, _ = fa(Ysub, rng, **kwA)
        cb = int(rng.choice(pool_b)) if fb is None else fb(Ysub, rng, **kwB)[0]
        return ca, cb
    def stat(Ysub, ca, cb):
        d = Ysub[:, ca].astype(float) - Ysub[:, cb]
        return d.mean(), d.std(ddof=1) / np.sqrt(len(d)) + 1e-9
    out = {}
    ca, cb = run(Ys)
    g, se = stat(Ys, ca, cb); G = tr(ca) - tr(cb)
    out["naive"] = (g, se, G)
    # replay-bootstrap optimism, applied to the gap
    opts = []
    for b in range(nboot):
        idx = rng.integers(n, size=n); Yb = Ys[idx]
        cab, cbb = run(Yb)
        gb = (Yb[:, cab].astype(float) - Yb[:, cbb]).mean(); go = (Ys[:, cab].astype(float) - Ys[:, cbb]).mean()
        opts.append(gb - go)
    out["boot_opt"] = (g - float(np.mean(opts)), se, G)
    # hold-out: both systems tuned on (1-rho) of S, compared on the rest
    perm = rng.permutation(n); nh = int(round(rho_hold * n)); H, T = perm[:nh], perm[nh:]
    ca2, cb2 = run(Ys[T])
    gh, seh = stat(Ys[H], ca2, cb2)
    out["holdout"] = (gh, seh, tr(ca2) - tr(cb2))
    return out


def trial_naive(Y, n, algo_name, kw, rng, truth_acc=None, wr=False):
    """Cheap version: only the status-quo report (used for dense sweeps of n and the search budget)."""
    N, K = Y.shape
    S, fresh = (rng.integers(N, size=n), None) if wr else draw_split(N, n, rng)
    if wr and truth_acc is None: truth_acc = Y.mean(0)
    Ys = Y[S]
    c, R = ALGOS[algo_name](Ys, rng, **kw)
    t0 = float(truth_acc[c]) if truth_acc is not None else float(Y[fresh, c].mean())
    lo, hi = wald(R, n)
    # also: accuracy of the *average* config on the same S (what an untuned default would report) and its truth
    return {"naive": (R, lo, hi, t0), "mean_cfg": (float(Ys.mean()), np.nan, np.nan, float(truth_acc.mean()) if truth_acc is not None else float(Y[fresh].mean()))}
