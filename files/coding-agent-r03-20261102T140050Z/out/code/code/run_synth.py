"""Synthetic experiments that check the theory (all numbers are produced here; seeds fixed).
Usage: python run_synth.py  -> writes /work/out/synth/*.csv"""
import sys, os, json, itertools, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bsel import select as sel
from bsel.fa import fit_fa, predict_fa

OUT = '/work/out/synth'; os.makedirs(OUT, exist_ok=True)


def make_fa(N, r, g=3.0, strengths=None, kappa=0.0, sigma2=1.0, seed=0, hetero_noise=0.0):
    """Loadings rows lambda_j ~ N(0, g*sigma2*diag(w)) * h_j (h_j log-normal leverage with sd kappa, E h^2 = 1);
    noise psi_j = sigma2 * exp(hetero_noise * eps)."""
    rng = np.random.default_rng(seed)
    w = np.ones(r) if strengths is None else np.asarray(strengths, float)
    L = rng.standard_normal((N, r)) * np.sqrt(g * sigma2 * w)
    if kappa > 0:
        h = np.exp(kappa * rng.standard_normal(N)); h /= np.sqrt(np.mean(h ** 2)); L = L * h[:, None]
    psi = sigma2 * np.exp(hetero_noise * rng.standard_normal(N)) if hetero_noise > 0 else np.full(N, sigma2)
    return L, psi


def bayes_err_vec(L, psi, S, C=None):
    """Exact expected squared error of the Bayes predictor for each target j in T = C\\S: psi_j + l_j' A^-1 l_j."""
    N, r = L.shape
    C = np.arange(N) if C is None else np.asarray(C)
    T = np.setdiff1d(C, S)
    if len(S) == 0: return T, psi[T] + (L[T] ** 2).sum(1)
    A = np.eye(r) + (L[S] / psi[S, None]).T @ L[S]
    return T, psi[T] + np.einsum('jk,kl,jl->j', L[T], np.linalg.inv(A), L[T])


def bayes_err(L, psi, S): return float(bayes_err_vec(L, psi, np.asarray(S, int))[1].mean())


def mc_err(L, psi, S, n=20000, rng=None):
    """Monte-Carlo MSE of the Bayes predictor on T, averaged over targets."""
    rng = rng or np.random.default_rng(0)
    N, r = L.shape; S = np.asarray(S, int); T = np.setdiff1d(np.arange(N), S)
    F = rng.standard_normal((n, r)); Z = F @ L.T + rng.standard_normal((n, N)) * np.sqrt(psi)
    A = np.eye(r) + (L[S] / psi[S, None]).T @ L[S]
    M = np.linalg.solve(A, (L[S] / psi[S, None]).T)           # (r,k)
    Zh = (Z[:, S] @ M.T) @ L[T].T
    return float(np.mean((Zh - Z[:, T]) ** 2))


def cov_of(L, psi): return L @ L.T + np.diag(psi)


def exp1_formula_check():
    """E1: closed-form Bayes error vs Monte Carlo, for random and greedy S."""
    rows = []
    N, r = 60, 3
    L, psi = make_fa(N, r, g=2.0, strengths=[1, .6, .3], kappa=0.6, seed=1)
    cov = cov_of(L, psi); rng = np.random.default_rng(5)
    order = sel.greedy_var(cov, 30)
    for k in (1, 2, 3, 5, 8, 12, 20, 30):
        Sg = np.array(order[:k]); rows.append(dict(sel='greedy', k=k, formula=bayes_err(L, psi, Sg), mc=mc_err(L, psi, Sg, 40000, rng)))
        fr, mr = [], []
        for d in range(40):
            S = rng.permutation(N)[:k]; fr.append(bayes_err(L, psi, S)); mr.append(mc_err(L, psi, S, 3000, rng))
        rows.append(dict(sel='random', k=k, formula=np.mean(fr), mc=np.mean(mr), mc_se=np.std(mr) / np.sqrt(len(mr))))
        rows[-1]['formula_sd'] = np.std(fr)
    pd.DataFrame(rows).to_csv(f'{OUT}/e1_formula_check.csv', index=False)
    print('E1 done')


def exp2_k_scaling():
    """E2: excess error over the noise floor vs k for random S (iid Gaussian loadings): exact expectation by simulation
    of the closed form, vs. (a) Jensen lower bound sum_i g_i/(1+k g_i), (b) large-SNR limit r/(k-r-1)."""
    rows = []
    N = 400
    for r, g in itertools.product((1, 2, 4, 8, 16), (1.0, 10.0)):
        L, psi = make_fa(N, r, g=g, seed=10 + r)
        Gev = np.linalg.eigvalsh(L.T @ L / N)             # empirical g_i (sigma2 = 1)
        rng = np.random.default_rng(r)
        covm = cov_of(L, psi); og = sel.greedy_var(covm, 120)
        for k in sorted(set([1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 120])):
            if k > 120: continue
            ex = [bayes_err(L, psi, rng.permutation(N)[:k]) - 1.0 for _ in range(300)]
            exg = bayes_err(L, psi, np.array(og[:k])) - 1.0
            rows.append(dict(r=r, g=g, k=k, excess_random=np.mean(ex), excess_random_se=np.std(ex) / np.sqrt(300), excess_greedy=exg,
                             jensen=float(np.sum(Gev / (1 + k * Gev))), invwishart=(r / (k - r - 1) if k > r + 1 else np.nan)))
    pd.DataFrame(rows).to_csv(f'{OUT}/e2_k_scaling.csv', index=False)
    print('E2 done')


def swap_search(cov, S, iters=3):
    S = list(S); best = sel.objective(cov, S)
    for _ in range(iters):
        improved = False
        for a in range(len(S)):
            for c in range(len(cov)):
                if c in S: continue
                T = S.copy(); T[a] = c; v = sel.objective(cov, T)
                if v < best - 1e-12: best, S, improved = v, T, True
        if not improved: break
    return S, best


def exp3_greedy_vs_opt():
    """E3: greedy vs exhaustive optimum (small N) / swap local search (N=60) vs random; objective = sum_j Var(z_j|z_S)."""
    rows = []
    t0 = time.time()
    for rep in range(30):
        for (N, r, kappa, g) in [(12, 2, 0.0, 1.0), (12, 2, 0.8, 1.0), (12, 4, 0.8, 0.5), (12, 1, 0.8, 1.0)]:
            L, psi = make_fa(N, r, g=g, kappa=kappa, seed=1000 + rep, hetero_noise=0.5)
            cov = cov_of(L, psi); d = np.sqrt(np.diag(cov)); corr = cov / np.outer(d, d)
            lam_min = float(np.linalg.eigvalsh(corr)[0])
            go = sel.greedy_var(corr, 8); rng = np.random.default_rng(rep)
            for k in (2, 3, 4, 6):
                opt = sel.objective(corr, sel.exhaustive_best(corr, k)); gr = sel.objective(corr, go[:k])
                rd = np.mean([sel.objective(corr, rng.permutation(N)[:k]) for _ in range(100)])
                tot = np.trace(corr); lam_ = np.sort(np.linalg.eigvalsh(corr))[::-1]; tail = float(lam_[k:].sum())
                # variance-reduction objective V = tr - F; Das-Kempe-type guarantee V_greedy >= (1-exp(-lam_min)) V_opt
                rows.append(dict(N=N, r=r, kappa=kappa, g=g, rep=rep, k=k, F_opt=opt, F_greedy=gr, F_random=rd, tot=tot, tail=tail, lam_min=lam_min,
                                 V_ratio=(tot - gr) / (tot - opt), V_ratio_random=(tot - rd) / (tot - opt), bound=1 - np.exp(-lam_min)))
    pd.DataFrame(rows).to_csv(f'{OUT}/e3_greedy_vs_opt.csv', index=False)
    rows = []
    for rep in range(20):
        for kappa in (0.0, 0.5, 1.0):
            N, r = 60, 4
            L, psi = make_fa(N, r, g=1.0, kappa=kappa, seed=2000 + rep, hetero_noise=0.5)
            corr = cov_of(L, psi); d = np.sqrt(np.diag(corr)); corr = corr / np.outer(d, d)
            go = sel.greedy_var(corr, 12); rng = np.random.default_rng(rep)
            for k in (4, 8, 12):
                S, v = swap_search(corr, go[:k])
                rd = np.mean([sel.objective(corr, rng.permutation(N)[:k]) for _ in range(100)])
                rows.append(dict(N=N, r=r, kappa=kappa, rep=rep, k=k, F_greedy=sel.objective(corr, go[:k]), F_swap=v, F_random=rd, tot=np.trace(corr),
                                 F_pivot=sel.objective(corr, sel.greedy_pivot(corr, k)), F_mi=sel.objective(corr, sel.greedy_mi(corr, k)),
                                 F_central=sel.objective(corr, sel.central(corr, k))))
    pd.DataFrame(rows).to_csv(f'{OUT}/e3b_greedy_vs_swap.csv', index=False)
    print('E3 done', time.time() - t0)


def exp4_finite_M():
    """E4: finite training set. (a) unstructured OLS on the k selected benchmarks vs the Bayes-oracle:
    predicted inflation 1 + k/(M-k-1) (Gaussian design, known means); (b) FA fitted by EM on M rows."""
    rows = []
    N, r = 80, 4
    L, psi = make_fa(N, r, g=2.0, kappa=0.5, seed=3)
    cov = cov_of(L, psi)
    rng = np.random.default_rng(11)
    for M in (20, 40, 80, 160, 640):
        for k in (3, 6, 12, 18):
            if M <= k + 2: continue
            res = []
            for rep in range(60 if M < 400 else 20):
                S = rng.permutation(N)[:k]; T = np.setdiff1d(np.arange(N), S)
                F = rng.standard_normal((M, r)); Z = F @ L.T + rng.standard_normal((M, N)) * np.sqrt(psi)
                Zt = (rng.standard_normal((400, r)) @ L.T + rng.standard_normal((400, N)) * np.sqrt(psi))
                B = np.linalg.lstsq(Z[:, S], Z[:, T], rcond=None)[0]       # OLS, no intercept (means known = 0)
                e_ols = np.mean((Zt[:, S] @ B - Zt[:, T]) ** 2)
                e_or = bayes_err(L, psi, S)
                res.append((e_ols, e_or))
            res = np.array(res)
            rows.append(dict(M=M, k=k, ols=res[:, 0].mean(), ols_se=res[:, 0].std() / np.sqrt(len(res)), oracle=res[:, 1].mean(),
                             predicted_inflation=1 + k / (M - k - 1), measured_inflation=res[:, 0].mean() / res[:, 1].mean()))
    pd.DataFrame(rows).to_csv(f'{OUT}/e4a_ols_inflation.csv', index=False)
    # (b) EM-fitted factor model + fold-in, vs oracle, vs OLS
    rows = []
    for M in (20, 40, 80, 160, 640):
        for k in (3, 6, 12):
            for rep in range(12):
                S = rng.permutation(N)[:k]; T = np.setdiff1d(np.arange(N), S)
                Z = rng.standard_normal((M, r)) @ L.T + rng.standard_normal((M, N)) * np.sqrt(psi)
                Zt = rng.standard_normal((400, r)) @ L.T + rng.standard_normal((400, N)) * np.sqrt(psi)
                mu = Z.mean(0); sd = Z.std(0); Zs = (Z - mu) / sd
                par = fit_fa(Zs, r, n_iter=200, tol=1e-4)
                P = np.array([predict_fa(par, S, ((Zt[i] - mu) / sd)[S]) for i in range(len(Zt))]) * sd + mu
                e_fa = np.mean((P[:, T] - Zt[:, T]) ** 2)
                B = np.linalg.lstsq(Z[:, S] - mu[S], Z[:, T] - mu[T], rcond=None)[0] if M > k + 2 else None
                e_ols = np.mean(((Zt[:, S] - mu[S]) @ B + mu[T] - Zt[:, T]) ** 2) if B is not None else np.nan
                rows.append(dict(M=M, k=k, rep=rep, fa=e_fa, ols=e_ols, oracle=bayes_err(L, psi, S)))
    pd.DataFrame(rows).to_csv(f'{OUT}/e4b_fa_vs_ols.csv', index=False)
    print('E4 done')


def exp5_gain_vs_conditions():
    """E5: relative gain of greedy over random selection as a function of leverage heterogeneity, rank, noise (oracle covariance)."""
    rows = []
    for r, g, kappa, N in itertools.product((1, 2, 4, 8), (0.3, 1.0, 3.0), (0.0, 0.5, 1.0, 1.5), (100,)):
        for rep in range(5):
            L, psi = make_fa(N, r, g=g, kappa=kappa, seed=5000 + rep, hetero_noise=0.5)
            cov = cov_of(L, psi); d = np.sqrt(np.diag(cov)); corr = cov / np.outer(d, d)
            go = sel.greedy_var(corr, 24); rng = np.random.default_rng(rep)
            for k in (2, 4, 8, 16, 24):
                fr = np.mean([sel.objective(corr, rng.permutation(N)[:k]) for _ in range(60)]) / N
                rows.append(dict(r=r, g=g, kappa=kappa, rep=rep, k=k, F_random=fr, F_greedy=sel.objective(corr, go[:k]) / N))
    pd.DataFrame(rows).to_csv(f'{OUT}/e5_gain_conditions.csv', index=False)
    print('E5 done')


def exp6_k_star():
    """E6: smallest k with simulated random-selection excess error <= eps*sigma^2, versus the necessary/sufficient bounds of Prop. 2."""
    rows = []
    N = 600
    for r, g in itertools.product((1, 2, 4, 8), (1.0, 10.0)):
        L, psi = make_fa(N, r, g=g, seed=50 + r); rng = np.random.default_rng(r)
        Sets = [rng.permutation(N) for _ in range(200)]
        ex = {}
        for k in range(1, 130):
            ex[k] = np.mean([bayes_err(L, psi, S[:k]) - 1.0 for S in Sets])
        og = sel.greedy_var(cov_of(L, psi), 129); exg = {k: bayes_err(L, psi, np.array(og[:k])) - 1.0 for k in range(1, 130)}
        for eps in (0.5, 0.2, 0.1):
            ks = [k for k in ex if ex[k] <= eps]; kg = [k for k in exg if exg[k] <= eps]
            rows.append(dict(r=r, g=g, eps=eps, k_star=(min(ks) if ks else np.nan), k_star_greedy=(min(kg) if kg else np.nan), lower=r / eps - 1 / g, upper=r * (1 + 1 / eps) + 1))
    pd.DataFrame(rows).to_csv(f'{OUT}/e6_k_star.csv', index=False)
    print('E6 done')


if __name__ == '__main__':
    which = sys.argv[1:] or ['1', '2', '3', '4', '5', '6']
    for w in which: {'1': exp1_formula_check, '2': exp2_k_scaling, '3': exp3_greedy_vs_opt, '4': exp4_finite_M, '5': exp5_gain_vs_conditions, '6': exp6_k_star}[w]()
