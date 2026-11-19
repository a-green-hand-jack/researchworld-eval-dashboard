"""E8: history-size (M) and missingness sweeps on real matrices.
Held-out test models are fixed per repetition; history = random subsample of M other models (family-excluded if groups are given),
optionally with a fraction of history cells hidden completely at random. Reports for each (M, mask) cell: the likelihood-selected rank,
the BBP count rank_eff(M) = #{rho_ref_i > sqrt(N/M)} with rho_ref estimated on the largest history (de-biased reference spectrum),
measured error(k) of greedyAcomp+FA, random+FA (mean over draws), and the finite-M forecast (from the cell's own fit).
python exp/e8_sweep.py SETTING OUT --Ms 30,60,125,500 --masks 0 --reps 5 [--ntest 300]"""
import sys, os, argparse, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
import fa as FA, bselect as SEL, theory as TH
from settings import mteb_setting, llm_setting

ap = argparse.ArgumentParser(); ap.add_argument('setting'); ap.add_argument('out')
ap.add_argument('--Ms', default='30,60,125,500'); ap.add_argument('--masks', default='0'); ap.add_argument('--reps', type=int, default=5)
ap.add_argument('--first', type=int, default=0); ap.add_argument('--ntest', type=int, default=300)
ap.add_argument('--ks', default='1,2,3,5,8,12,20'); ap.add_argument('--n_random', type=int, default=50)
a = ap.parse_args()
s = llm_setting(a.setting) if a.setting in ('OLMB40', 'HELMMMLU', 'HELMLITE', 'OLMB6', 'LIVEBENCH') else mteb_setting(a.setting)
X, obs = s['X'], s['obs']
keep = obs.all(1)                                   # OLMB40 is 99.98% dense: the 5 incomplete models are dropped here
assert keep.mean() > 0.99, 'dense matrices only'
X = X[keep]; G = np.asarray(s.get('groups', np.arange(len(s['X']))))[keep]; Mtot, N = X.shape
Ms = [int(x) for x in a.Ms.split(',')]; masks = [float(x) for x in a.masks.split(',')]; KS = [int(k) for k in a.ks.split(',') if int(k) < N - 3]
ranks = [r for r in (0, 1, 2, 3, 4, 6, 8, 12, 16, 24) if r < N // 2 + 1]
rows = []; os.makedirs(a.out, exist_ok=True)


def fit(Xh, oh, seed):
    mu = np.nanmean(np.where(oh, Xh, np.nan), 0); sd = np.nanstd(np.where(oh, Xh, np.nan), 0, ddof=1)
    Xs = np.where(oh, (Xh - mu) / sd, 0.0)
    r, sc = FA.cv_select_rank(Xs, oh, ranks, seed=seed)
    return FA.fit_fa(Xs, oh, r, seed=seed), r, mu, sd


for rep in range(a.first, a.first + a.reps):
    rng = np.random.default_rng([rep, 8, sum(map(ord, a.setting))])
    te = rng.choice(Mtot, min(a.ntest, Mtot // 4), replace=False)
    pool = np.setdiff1d(np.where(~np.isin(G, G[te]))[0], te)                 # no test family in the history
    pool = rng.permutation(pool)
    Mmax = min(max(Ms), len(pool))
    # reference spectrum on the largest history
    ref, r_ref, mu_r, sd_r = fit(X[pool[:Mmax]], np.ones((Mmax, N), bool), rep)
    for M in Ms:
        if M > len(pool): continue
        hist = pool[:M]
        for mk in masks:
            t0 = time.time()
            oh = rng.random((M, N)) >= mk
            oh[np.where(oh.sum(1) == 0)[0], 0] = True
            par, r_cv, mu, sd = fit(X[hist], oh, rep)
            Xt = (X[te] - mu) / sd
            rho_ref = TH.debias_spikes(ref['Lam'], ref['psi'], Mmax)[2]
            rank_eff = int((rho_ref > np.sqrt(N / M)).sum())
            order = SEL.greedy_design(par, np.arange(N), max(KS), 'A_comp')
            for k in KS:
                S = order[:k]; T = np.setdiff1d(np.arange(N), S)
                meas = float(((FA.predict_fa(par, S, Xt[:, S])[:, T] - Xt[:, T]) ** 2).mean())
                rm = []
                for _ in range(a.n_random):
                    Sr = rng.choice(N, k, replace=False); Tr = np.setdiff1d(np.arange(N), Sr)
                    rm.append(((FA.predict_fa(par, Sr, Xt[:, Sr])[:, Tr] - Xt[:, Tr]) ** 2).mean())
                m0 = float((Xt[:, T] ** 2).mean())
                rows.append(dict(setting=a.setting, rep=rep, M=M, mask=mk, k=k, r_cv=r_cv, r_ref=r_ref, rank_eff=rank_eff, N=N,
                                 thr=float(np.sqrt(N / M)), measured=meas, random=float(np.mean(rm)), mean_pred=m0,
                                 naive=TH.bayes_error(par['Lam'], par['psi'], S),
                                 fm=TH.forecast_finite_m(par['Lam'], par['psi'], M * (1 - mk), S),
                                 fm_noinfl=TH.forecast_finite_m(par['Lam'], par['psi'], M * (1 - mk), S, inflate=False),
                                 floor=TH.tail_floor(par['Lam'], par['psi'], S)))
            print(a.setting, rep, M, mk, 'r_cv', r_cv, 'rank_eff', rank_eff, round(time.time() - t0), flush=True)
    pd.DataFrame(rows).to_parquet(f"{a.out}/sweep_{a.setting}_{a.first}.parquet")
