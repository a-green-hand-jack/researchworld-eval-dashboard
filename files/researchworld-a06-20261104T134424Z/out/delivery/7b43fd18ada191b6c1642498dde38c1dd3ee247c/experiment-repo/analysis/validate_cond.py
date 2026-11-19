"""Validation of the conditional (median-unbiased / equal-tailed) and hybrid winner intervals of lib.py. usage: validate_cond.py OUT_DIR
(1) closed form K=2 independent (truncation point = the loser's score) vs cond_cdf, with an independent mpmath evaluation;
(2) probability-integral-transform check: with known Sigma and theta, draw X ~ N(theta, Sigma), keep the draws whose argmax is k, compute
    u = cond_cdf(theta_k, X_k | selected): u must be Uniform(0,1) (KS test) -- this exercises winner_truncation + cond_cdf for K = 2, 4, 16;
(3) coverage of cond_ci / hybrid_ci with known theta, Sigma known (exact Gaussian) and the width/lead relationship;
(4) the reference-cell pool (tau=.01, rho=.5, K=16, n=200): exact Gaussian X ~ N(theta, Sigma_pool/n) vs Bernoulli tuning draws with Sigma estimated
    from the tuning items (what the paper's method does), to locate the source of the wide intervals / heavy-tailed median.
(5) agreement with an independent Python port of the authors' public replication code of Andrews, Kitagawa & McCloskey (Inference on Winners; Harvard Dataverse
    doi:10.7910/DVN/9GAYB5, JobStart Replication Files/Empirical Application/empirical.m, cvl_fn/cvu_fn/cvl_hyb_fn/cvu_hyb_fn.m), with the Monte-Carlo trandn quantiles
    replaced by exact truncated-normal quantiles (scipy), on random covariance matrices; (6) coverage and point-estimate accuracy of the hybrid median."""
import sys, os, numpy as np, pandas as pd, mpmath as mp, warnings; warnings.filterwarnings("ignore")
from scipy.stats import norm, kstest
from lib import winner_truncation, cond_cdf, cond_ci, hybrid_ci, hybrid_median, est_conditional, est_hybrid
from scipy.stats import truncnorm
from synth import make_pool
out = sys.argv[1]; os.makedirs(out, exist_ok=True); rng = np.random.default_rng(0); rows = []

# (1) closed form K=2 independent: u = (Phi(.) ...) ; mpmath reference at 50 digits
mp.mp.dps = 50; worst = 0.0
for _ in range(2000):
    th = rng.normal(0, .02); sg = abs(rng.normal(.03, .01)) + .01; xj = th + rng.normal(0, .05); x = xj + abs(rng.normal(0, .05)) + 1e-4
    Sig = np.diag([sg ** 2, sg ** 2]); p = np.array([x, xj]); Vm, Vp, sk = winner_truncation(p, Sig, 0)
    ref = (mp.ncdf(-(xj - th) / sg) - mp.ncdf(-(x - th) / sg)) / mp.ncdf(-(xj - th) / sg)
    worst = max(worst, abs(float(ref) - cond_cdf(th, x, sk, Vm, Vp)))
    assert abs(Vm - xj) < 1e-9 and Vp == np.inf
rows.append(dict(check="K=2 independent closed form vs mpmath", stat="max |cdf diff| over 2000 draws", value=worst))

# (2) PIT / (3) coverage, known Sigma
def pool_cov(K, tau, rho, n, m=.3, seed=1, Kp=128, N=20000):
    Y = make_pool(Kp, N, m=m, tau=tau, rho=rho, seed=seed)[:K]; return Y.mean(1), np.cov(Y.astype(float)) / n
def pit_cov(th, Sig, R=20000, beta=.005, Bc=2000):
    K = len(th); L = np.linalg.cholesky(Sig + 1e-14 * np.eye(K)); sd = np.sqrt(np.diag(Sig)); Rm = Sig / np.outer(sd, sd)
    w, V = np.linalg.eigh(Rm); Lc = V * np.sqrt(np.clip(w, 0, None)); cb = float(np.quantile(np.abs(rng.standard_normal((Bc, K)) @ Lc.T).max(1), 1 - beta))
    us, cov_c, cov_h, wid_c, wid_h, lead = [], [], [], [], [], []
    for _ in range(R):
        x = th + L @ rng.standard_normal(K); k = int(np.argmax(x)); Vm, Vp, sk = winner_truncation(x, Sig, k)
        us.append(cond_cdf(th[k], x[k], sk, Vm, Vp)); lead.append((x[k] - Vm) / sk)
        if len(us) <= 1500:
            e, lo, hi = cond_ci(x[k], sk, Vm, Vp); cov_c.append(lo <= th[k] <= hi); wid_c.append(hi - lo)
            lo, hi = hybrid_ci(x[k], sk, Vm, Vp, cb); cov_h.append(lo <= th[k] <= hi); wid_h.append(hi - lo)
    return np.array(us), np.array(cov_c), np.array(cov_h), np.array(wid_c), np.array(wid_h), np.array(lead)
for K, tau, rho, n in [(2, 0.0, 0.5, 200), (4, 0.01, 0.5, 200), (16, 0.01, 0.5, 200), (16, 0.0, 0.5, 200), (16, 0.03, 0.5, 500), (16, 0.05, 0.5, 1000)]:
    th, Sig = pool_cov(K, tau, rho, n); us, cc, ch, wc, wh, lead = pit_cov(th, Sig, R=6000)
    rows.append(dict(check=f"PIT/coverage known Sigma K={K} tau={tau} rho={rho} n={n}", stat="KS p-value of PIT vs U(0,1)", value=kstest(us, "uniform").pvalue))
    for nm, v in (("cond coverage", cc.mean()), ("hybrid coverage", ch.mean()), ("cond median width", np.median(wc)), ("cond mean width", wc.mean()), ("hybrid mean width", wh.mean()),
                  ("median standardised lead (x_k - V-)/se_k", np.median(lead)), ("share lead < 0.5", (lead < .5).mean())):
        rows.append(dict(check=f"PIT/coverage known Sigma K={K} tau={tau} rho={rho} n={n}", stat=nm, value=float(v)))
# (4) reference cell: exact Gaussian vs Bernoulli draws with estimated Sigma
K, n, tau, rho = 16, 200, .01, .5; Y = make_pool(128, 20000, m=.3, tau=tau, rho=rho, seed=1); Ysub = Y[:K]; th = Ysub.mean(1); Sig0 = np.cov(Ysub.astype(float)) / n
Lc = np.linalg.cholesky(Sig0); res = {"gauss_known_Sigma": [], "bernoulli_est_Sigma": []}
for r in range(1500):
    x = th + Lc @ rng.standard_normal(K); k = int(np.argmax(x)); Vm, Vp, sk = winner_truncation(x, Sig0, k); e, lo, hi = cond_ci(x[k], sk, Vm, Vp)
    res["gauss_known_Sigma"].append((e - th[k], lo <= th[k] <= hi, hi - lo, (x[k] - Vm) / sk))
    T = rng.integers(0, Y.shape[1], n); S = Ysub[:, T]; r2 = est_conditional("argmax", S, rng); kk = r2["k"]
    res["bernoulli_est_Sigma"].append((r2["est"] - th[kk], r2["lo"] <= th[kk] <= r2["hi"], r2["hi"] - r2["lo"], np.nan))
for k_, v in res.items():
    a = np.array(v, float); rows += [dict(check=f"reference cell K=16 n=200 tau=.01 rho=.5 ({k_})", stat=s, value=float(f(a[:, i])))
                                      for s, i, f in (("cond median - truth: mean", 0, np.mean), ("cond median - truth: median", 0, np.median), ("coverage", 1, np.mean), ("mean width", 2, np.mean), ("median width", 2, np.median))]

# (5) port of the AKM replication code (empirical.m): truncation points, conditional CI/median, hybrid CI/median, exact quantiles instead of Monte Carlo
def akm_V(X, Sg, ind):
    M = X[ind]; Z = X - (Sg[ind, :] / Sg[ind, ind]) * M; Zm, Zp = [], []
    for j in range(len(X)):
        if Sg[j, ind] < Sg[ind, ind]: Zm.append(Sg[ind, ind] * Z[j] / (Sg[ind, ind] - Sg[j, ind]))
        if Sg[j, ind] > Sg[ind, ind]: Zp.append(Sg[ind, ind] * Z[j] / (Sg[ind, ind] - Sg[j, ind]))
    return (max(Zm) if Zm else -np.inf), (min(Zp) if Zp else np.inf)
def tq(q, mean, var, a, b): sd = np.sqrt(var); return mean + sd * truncnorm.ppf(q, (a - mean) / sd, (b - mean) / sd)
def akm_cond(M, var, Vm, Vp, level):     # cvl_fn / cvu_fn roots: CI_u: M = lower level/2 quantile; CI_l: M = upper quantile; level=1 -> median
    from scipy.optimize import brentq
    L, U = M - 40 * np.sqrt(var), M + 40 * np.sqrt(var)
    f = lambda th, q: tq(q, th, var, Vm, Vp) - M
    return brentq(lambda t: f(t, 1 - level / 2), L, U, xtol=1e-10), brentq(lambda t: f(t, level / 2), L, U, xtol=1e-10)   # (CI_l, CI_u)
def akm_hyb_set(M, var, Vm, Vp, gamma, cbs, ngrid=4001):   # cvl_hyb_fn / cvu_hyb_fn acceptance logic on a fine grid of theta
    ok = []
    for th in np.linspace(M - cbs, M + cbs, ngrid):
        if Vm <= th + cbs and Vp >= th - cbs:
            a, b = max(Vm, th - cbs), min(Vp, th + cbs)
            if b > a:
                cl, cu = tq(gamma / 2, th, var, a, b), tq(1 - gamma / 2, th, var, a, b)
                if cl <= M <= cu: ok.append(th)
    return min(ok), max(ok)
def akm_hyb_med(M, var, Vm, Vp, cbs, ngrid=4001):   # cvl_hyb_fn at gamma = 1: root of (median of the restricted truncated normal) - M
    th = np.linspace(M - cbs, M + cbs, ngrid); g = np.full(ngrid, np.nan)
    for i, t in enumerate(th):
        if Vm <= t + cbs and Vp >= t - cbs:
            a, b = max(Vm, t - cbs), min(Vp, t + cbs)
            if b > a: g[i] = tq(.5, t, var, a, b) - M
    ok = np.flatnonzero(~np.isnan(g)); th, g = th[ok], g[ok]; ix = np.flatnonzero(g[:-1] * g[1:] <= 0)
    if len(ix) == 0: return th[np.argmin(np.abs(g))]
    i = ix[0]; return th[i] + g[i] / (g[i] - g[i + 1]) * (th[i + 1] - th[i])
mx = dict(Vm=0, Vp=0, cond_lo=0, cond_hi=0, cond_med=0, hyb_lo=0, hyb_hi=0, hyb_med=0); n5 = 0; nskip = 0
for it in range(400):
    K = int(rng.integers(2, 17)); A = rng.normal(size=(K, K)); Sg = (A @ A.T / K + .3 * np.eye(K)) * 1e-3; th0 = rng.normal(0, .02, K); X = th0 + np.linalg.cholesky(Sg) @ rng.standard_normal(K); k = int(np.argmax(X))
    Vm, Vp, sk = winner_truncation(X, Sg, k); Vm_a, Vp_a = akm_V(X, Sg, k); M = X[k]; var = Sg[k, k]
    if np.isfinite(Vm): mx["Vm"] = max(mx["Vm"], abs(Vm - Vm_a))
    if np.isfinite(Vp): mx["Vp"] = max(mx["Vp"], abs(Vp - Vp_a))
    if (np.isinf(Vm) != np.isinf(Vm_a)) or (np.isinf(Vp) != np.isinf(Vp_a)): mx["Vm"] = np.inf
    e, lo, hi = cond_ci(M, sk, Vm, Vp)
    try: al, au = akm_cond(M, var, Vm, Vp, .05); am, _ = akm_cond(M, var, Vm, Vp, 1.0)
    except ValueError: nskip += 1; continue          # scipy truncnorm.ppf saturates for extreme truncation points
    mx["cond_lo"] = max(mx["cond_lo"], abs(lo - al) / sk); mx["cond_hi"] = max(mx["cond_hi"], abs(hi - au) / sk); mx["cond_med"] = max(mx["cond_med"], abs(e - am) / sk)
    sdv = np.sqrt(np.diag(Sg)); Rm = Sg / np.outer(sdv, sdv); w, V = np.linalg.eigh(Rm); Lc = V * np.sqrt(np.clip(w, 0, None))
    cb = float(np.quantile(np.abs(rng.standard_normal((200000, K)) @ Lc.T).max(1), 1 - .005)); beta = .005; gam = 1 - (1 - .05) / (1 - beta)
    hl, hh = hybrid_ci(M, sk, Vm, Vp, cb); gl, gh = akm_hyb_set(M, var, Vm, Vp, gam, cb * sk); hm = hybrid_median(M, sk, Vm, Vp, cb); gm = akm_hyb_med(M, var, Vm, Vp, cb * sk)
    step = 2 * cb * sk / 160
    mx["hyb_lo"] = max(mx["hyb_lo"], abs(hl - gl) / step); mx["hyb_hi"] = max(mx["hyb_hi"], abs(hh - gh) / step); mx["hyb_med"] = max(mx["hyb_med"], abs(hm - gm) / step)
    n5 += 1
rows.append(dict(check="AKM replication-code port vs lib.py (400 random Sigma, K=2..16)", stat="instances compared / skipped (port quantile not computable)", value=f"{n5}/{nskip}"))
rows += [dict(check="AKM replication-code port vs lib.py (400 random Sigma, K=2..16)", stat=k_ + (" (units of se)" if k_.startswith("cond") else (" (units of grid step)" if k_.startswith("hyb") else " (abs)")), value=float(v)) for k_, v in mx.items()]
# (6) hybrid median in the reference cell with known Sigma
th, Sig = pool_cov(16, .01, .5, 200); L = np.linalg.cholesky(Sig); sd = np.sqrt(np.diag(Sig)); w, V = np.linalg.eigh(Sig / np.outer(sd, sd)); Lc = V * np.sqrt(np.clip(w, 0, None))
cb = float(np.quantile(np.abs(rng.standard_normal((4000, 16)) @ Lc.T).max(1), .995)); err_h, err_c, cov_h = [], [], []
for _ in range(1500):
    x = th + L @ rng.standard_normal(16); k = int(np.argmax(x)); Vm, Vp, sk = winner_truncation(x, Sig, k)
    err_h.append(hybrid_median(x[k], sk, Vm, Vp, cb) - th[k]); err_c.append(cond_ci(x[k], sk, Vm, Vp)[0] - th[k]); err_n = x[k] - th[k]
    lo, hi = hybrid_ci(x[k], sk, Vm, Vp, cb); cov_h.append(lo <= th[k] <= hi)
for nm, e in (("hybrid median", err_h), ("conditional median", err_c)):
    e = np.array(e); rows += [dict(check="reference cell, known Sigma: point estimates minus true score", stat=f"{nm}: mean", value=e.mean()), dict(check="reference cell, known Sigma: point estimates minus true score", stat=f"{nm}: median abs err", value=np.median(np.abs(e))),
                              dict(check="reference cell, known Sigma: point estimates minus true score", stat=f"{nm}: rmse", value=np.sqrt((e ** 2).mean()))]
rows.append(dict(check="reference cell, known Sigma: hybrid CI", stat="coverage", value=float(np.mean(cov_h))))
pd.DataFrame(rows).to_csv(os.path.join(out, "validation_cond_hybrid.csv"), index=False); print(pd.DataFrame(rows).to_string())
