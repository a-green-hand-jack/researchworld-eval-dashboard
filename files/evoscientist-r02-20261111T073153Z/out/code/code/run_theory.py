"""Theory checks. Usage: python run_theory.py
 A. exact finite-sample coverage law Beta(n+1-l, l) (continuous scores) and tie effect (discrete scores);
    evaluation-noise of a single-run coverage estimate.
 B. K=2 closed-form conditional coverage of the Euclidean score vs. pivotal Aitchison score.
 C. zero-replacement asymptotics of the Aitchison quantile: q/log(1/eps) -> sqrt(g_(k)/K), g(z)=z(K-z).
Writes results/theory_{beta,beta_eval,k2,k2_formula,zero}.csv"""
import os
import numpy as np, pandas as pd
from scipy import stats
from scipy.special import expit, logit
from scipy.optimize import brentq
from compconf import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
ALPHA = 0.1


# ------------------------------------------------------------------ A
def exp_beta(R=20000, nref=4000000):
    rng = np.random.default_rng(1)
    K, d = 3, 5
    rows, erows = [], []
    for dgp, sname in [("ln", "l2"), ("ln", "ait"), ("mult", "l1")]:
        W = make_world(rng, K)
        sc = Score(sname, K, eps=0.025 if dgp == "mult" else 1e-3)
        def draw(n):
            if dgp == "mult":  # vectorised multinomial (same law as gen_data, faster)
                X = rng.normal(size=(n, W.shape[0])); m = softmax(X @ W, axis=1)
                Y = rng.multinomial(20, m) * 0.05
            else:
                X, Y, m = gen_data(rng, W, n, dgp, K)
            return sc.paired(Y, m)  # oracle predictor f = m(x)
        ref = np.sort(draw(nref))
        for n in [10, 20, 50, 100, 500, 2000]:
            l = int(np.floor((n + 1) * ALPHA))
            k = int(np.ceil((n + 1) * (1 - ALPHA)))
            covs = np.empty(R)
            S = np.concatenate([draw(n * (R // 10)) for _ in range(10)]).reshape(R, n)
            q = np.partition(S, k - 1, axis=1)[:, k - 1]
            covs = np.searchsorted(ref, q, side="right") / nref
            a, b = n + 1 - l, l
            ks = stats.kstest(covs, stats.beta(a, b).cdf)
            rows.append(dict(dgp=dgp, score=sname, n=n, R=R, mean_emp=covs.mean(), mean_beta=a / (a + b),
                             sd_emp=covs.std(), sd_beta=stats.beta(a, b).std(), ks_stat=ks.statistic,
                             ks_p=ks.pvalue, min_cov=covs.min(), q05_emp=np.quantile(covs, .05),
                             q05_beta=stats.beta(a, b).ppf(.05)))
            if dgp == "ln" and sname == "l2":
                np.save(os.path.join(OUT, f"beta_covs_{n}.npy"), covs[:5000])
                # single-run evaluation noise: test coverage hat with n_test points
                for nt in [100, 1000, 10000]:
                    hat = rng.binomial(nt, covs) / nt
                    bb = stats.betabinom(nt, a, b)
                    tol = 0.02
                    p_out_th = bb.cdf(np.ceil((1 - ALPHA - tol) * nt) - 1) + bb.sf(np.floor((1 - ALPHA + tol) * nt))
                    erows.append(dict(n_cal=n, n_test=nt, sd_emp=hat.std(), sd_theory=bb.std() / nt,
                                      p_outside_tol_emp=np.mean(np.abs(hat - (1 - ALPHA)) > tol + 1e-12),
                                      p_outside_tol_theory=p_out_th))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "theory_beta.csv"), index=False)
    pd.DataFrame(erows).to_csv(os.path.join(OUT, "theory_beta_eval.csv"), index=False)


# ------------------------------------------------------------------ B
def cond_cov_formula(f, r, tau):
    u = logit(f)
    hi = np.where(f + r >= 1, np.inf, logit(np.minimum(f + r, 1 - 1e-300)))
    lo = np.where(f - r <= 0, -np.inf, logit(np.maximum(f - r, 1e-300)))
    return stats.norm.cdf((hi - u) / tau) - stats.norm.cdf((lo - u) / tau)


def exp_k2(tau=1.0, usd=1.5, ncal=2000, R=40, nt=200000, nb=25):
    """Y1 = expit(u + tau*e), u = logit f1 ~ N(0, usd^2). Oracle predictor f1 = expit(u)."""
    rng = np.random.default_rng(2)
    # population threshold for the Euclidean score in y1 units (r = q/sqrt2)
    ug = np.linspace(-8, 8, 4001)
    pu = stats.norm.pdf(ug, 0, usd); pu /= pu.sum()
    def marg(r):
        return (cond_cov_formula(expit(ug), r, tau) * pu).sum()
    r_pop = brentq(lambda r: marg(r) - (1 - ALPHA), 1e-4, 0.999)
    fg = np.linspace(0.005, 0.995, 199)
    pd.DataFrame(dict(f=fg, cov_l2_formula=cond_cov_formula(fg, r_pop, tau), r_pop=r_pop, tau=tau)).to_csv(
        os.path.join(OUT, "theory_k2_formula.csv"), index=False)
    # worst-case gap of the formula as function of tau (usd fixed)
    gaps = []
    for t in [0.25, 0.5, 1.0, 1.5, 2.0]:
        def mg(r): return (cond_cov_formula(expit(ug), r, t) * pu).sum()
        rp = brentq(lambda r: mg(r) - (1 - ALPHA), 1e-4, 0.999)
        c = cond_cov_formula(expit(ug), rp, t)
        m = pu > 1e-4 * pu.max()
        gaps.append(dict(tau=t, r_pop=rp, min_cov=c[m].min(), max_cov=c[m].max(),
                         f_at_min=expit(ug[m][c[m].argmin()])))
    pd.DataFrame(gaps).to_csv(os.path.join(OUT, "theory_k2_gaps.csv"), index=False)
    # Monte Carlo: split conformal with 4 scores, binned conditional coverage
    scs = {s: Score(s, 2, eps=1e-3) for s in ["l2", "hell", "kl", "ait"]}
    def draw(n):
        u = rng.normal(0, usd, n)
        y1 = expit(u + tau * rng.normal(size=n))
        f1 = expit(u)
        return np.stack([f1, 1 - f1], 1), np.stack([y1, 1 - y1], 1)
    edges = np.linspace(0, 1, nb + 1)
    acc = {s: np.zeros(nb) for s in scs}; cnt = np.zeros(nb)
    for r in range(R):
        Fc, Yc = draw(ncal)
        Ft, Yt = draw(nt)
        b = np.clip(np.digitize(Ft[:, 0], edges) - 1, 0, nb - 1)
        cnt += np.bincount(b, minlength=nb)
        for s, sc in scs.items():
            q = conf_quantile(sc.paired(Yc, Fc), ALPHA)
            cov = sc.paired(Yt, Ft) <= q
            acc[s] += np.bincount(b, weights=cov, minlength=nb)
    mid = 0.5 * (edges[1:] + edges[:-1])
    df = pd.DataFrame({"f_mid": mid, "n": cnt, **{f"cov_{s}": acc[s] / np.maximum(cnt, 1) for s in scs}})
    df.to_csv(os.path.join(OUT, "theory_k2.csv"), index=False)


# ------------------------------------------------------------------ C
def exp_zero(R=200, n_cal=200):
    rng = np.random.default_rng(3)
    rows = []
    epss = [10.0 ** (-j) for j in range(2, 11)]
    for K in [3, 5, 10]:
        for N in [20, 100]:
            for rep in range(R):
                W = make_world(rng, K)
                X, Y, m = gen_data(rng, W, n_cal, "mult", K, N=N)
                F = m
                z = (Y <= 0).sum(1)
                g = z * (K - z)
                k = int(np.ceil((n_cal + 1) * (1 - ALPHA)))
                gk = np.sort(g)[k - 1]
                pred_slope = np.sqrt(gk / K)
                for e in epss:
                    sc = Score("ait", K, eps=e)
                    q = conf_quantile(sc.paired(Y, F), ALPHA)
                    rows.append(dict(K=K, N=N, rep=rep, eps=e, q=q, L=np.log(1 / e), pred_slope=pred_slope,
                                     zero_frac=(z > 0).mean()))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "theory_zero.csv"), index=False)


if __name__ == "__main__":
    exp_beta()
    exp_k2()
    exp_zero()
    print("done")
