"""E1: calibration-set variability of coverage and the pitfalls of single-split evaluation.
 (a) coverage-given-calibration vs exact Beta(n+1-l, l) law for all scores,
 (b) lattice-valued (low-count) compositions: ties break the law; randomised tie-breaking restores it,
 (c) mis-ranking probability of a single-split comparison between two conformal predictors.
Writes results/e1_*.csv"""
import numpy as np, pandas as pd
from scipy import stats
from ccp.geometry import SCORES
from ccp.synth import SynthProblem
from ccp.conformal import beta_params

ALPHA = 0.1
R = 5000
M = 2000000
rows = []
pr = SynthProblem(D=3, family="dirichlet", kappa=100, tau=1.5, seed=1)
rng = np.random.default_rng(0)
_, mu_t, y_t = pr.sample(M, rng)
St = {k: np.sort(f(y_t, mu_t)) for k, f in SCORES.items()}
for n in (20, 50, 100, 500, 2000):
    a, b = beta_params(n, ALPHA)
    k = int(np.ceil((n + 1) * (1 - ALPHA)))
    V = {k_: [] for k_ in SCORES}
    for r in range(R):
        rr = np.random.default_rng([1, n, r])
        _, mu_c, y_c = pr.sample(n, rr)
        for name, f in SCORES.items():
            q = np.sort(f(y_c, mu_c))[k - 1]
            V[name].append(np.searchsorted(St[name], q, side="right") / M)
    for name in SCORES:
        v = np.array(V[name])
        ks = stats.kstest(v, stats.beta(a, b).cdf)
        rows.append(dict(n=n, score=name, mean=v.mean(), sd=v.std(ddof=1), beta_mean=a / (a + b),
                         beta_sd=stats.beta(a, b).std(), ks_stat=ks.statistic, ks_p=ks.pvalue,
                         frac_below_nominal=(v < 1 - ALPHA).mean(), beta_frac_below=stats.beta(a, b).cdf(1 - ALPHA)))
pd.DataFrame(rows).to_csv("/work/results/e1a_beta_law.csv", index=False)
print(pd.DataFrame(rows).groupby("n")[["mean", "sd", "beta_mean", "beta_sd", "ks_stat", "ks_p"]].mean())

# (b) lattice-valued compositions: y = counts / N_ann, predictor takes few distinct values.
rows = []
D = 3
for Nann in (5, 10, 20, 50):
    for n in (100, 1000):
        a, b = beta_params(n, ALPHA)
        k = int(np.ceil((n + 1) * (1 - ALPHA)))
        p0 = np.array([0.5, 0.3, 0.2])
        # test pool (large) -- counts from Dirichlet-multinomial around a constant centre, kappa=20
        def draw(m, rr):
            pdir = rr.dirichlet(20 * p0, size=m)
            return np.array([rr.multinomial(Nann, pp) for pp in pdir]) / Nann
        rr0 = np.random.default_rng(5)
        yt = draw(200000, rr0)
        yhat = np.broadcast_to(p0, yt.shape)
        # scores restricted to the ones defined at zeros
        for name in ("euclid", "tv", "hellinger", "chi2"):
            f = SCORES[name]
            st = f(yt, yhat)
            ut = rr0.uniform(size=len(st))
            order = np.lexsort((ut, st))
            st_s, ut_s = st[order], ut[order]
            V_plain, V_rand = [], []
            for r in range(1000):
                rr = np.random.default_rng([2, Nann, n, r])
                yc = draw(n, rr)
                sc = f(yc, np.broadcast_to(p0, yc.shape))
                uc = rr.uniform(size=n)
                o = np.lexsort((uc, sc))
                sk, uk = sc[o][k - 1], uc[o][k - 1]
                V_plain.append(np.mean(st <= sk))
                V_rand.append(np.mean((st < sk) | ((st == sk) & (ut <= uk))))
            for lab, v in (("plain", V_plain), ("randomised", V_rand)):
                v = np.array(v)
                rows.append(dict(N_ann=Nann, n=n, score=name, variant=lab, mean=v.mean(), sd=v.std(ddof=1),
                                 beta_mean=a / (a + b), beta_sd=stats.beta(a, b).std(),
                                 ks_stat=stats.kstest(v, stats.beta(a, b).cdf).statistic,
                                 n_distinct_scores=len(np.unique(st))))
pd.DataFrame(rows).to_csv("/work/results/e1b_ties.csv", index=False)
print(pd.DataFrame(rows).query("score=='euclid' and n==1000"))

# (c) mis-ranking probability of single-split evaluation, from the exact Beta + Binomial law.
rng = np.random.default_rng(3)
rows = []
for n in (100, 500, 2000):
    for m in (500, 2000, 10000):
        for a_hi in (0.10, 0.09, 0.08, 0.05):
            # A targets 1-0.10 ; B targets 1-a_hi? we compare nominal 0.90 (A) with nominal 1-a_hi' (B) where B is MORE conservative
            if a_hi == 0.10:
                continue
            aA, bA = beta_params(n, 0.10)
            aB, bB = beta_params(n, a_hi)
            R_ = 200000
            # independent calibration sets for A and B (e.g. different seeds / different data splits)
            VA = rng.beta(aA, bA, R_); VB = rng.beta(aB, bB, R_)
            covA = rng.binomial(m, VA) / m; covB = rng.binomial(m, VB) / m
            # same calibration set: V_B >= V_A exactly (order statistics), only test noise remains
            U = np.sort(rng.uniform(size=(R_ // 10, n)), axis=1)
            kA = int(np.ceil((n + 1) * 0.9)); kB = int(np.ceil((n + 1) * (1 - a_hi)))
            VA2, VB2 = U[:, kA - 1], U[:, min(kB, n) - 1]
            covA2 = rng.binomial(m, VA2) / m
            covB2 = rng.binomial(m, VB2) / m
            rows.append(dict(n=n, m=m, nominal_gap=(1 - a_hi) - 0.9, p_misrank_indep=np.mean(covA >= covB),
                             p_misrank_paired=np.mean(covA2 >= covB2)))
pd.DataFrame(rows).to_csv("/work/results/e1c_misrank.csv", index=False)
print(pd.DataFrame(rows).pivot_table(index=["n", "m"], columns="nominal_gap", values=["p_misrank_indep", "p_misrank_paired"]).round(3))
