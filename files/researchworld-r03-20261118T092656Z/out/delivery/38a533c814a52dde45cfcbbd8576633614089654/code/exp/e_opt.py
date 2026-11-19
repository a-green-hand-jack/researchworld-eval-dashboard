"""Greedy vs optimum on the fitted models, restricted-eigenvalue gamma estimate, selection stability across history resamples.
python exp/e_opt.py SETTING REP -> results/SETTING/opt_rep{REP}.csv, stability_rep{REP}.csv  (dense settings; uses the saved fold fits)"""
import sys, os, glob, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
import bselect as SEL, fa as FA, theory as TH

setting, rep = sys.argv[1], int(sys.argv[2]); d = f"results/{setting}"
fits = [np.load(f) for f in sorted(glob.glob(f"{d}/fit_rep{rep}_fold*.npz"))]
rng = np.random.default_rng(rep)
KS = [1, 2, 3, 4, 6, 8, 12]
rows = []


def lam_min(C, S):
    return np.linalg.eigvalsh(C[np.ix_(S, S)])[0]


def worst_subset(C, k, n_start=20):
    N = C.shape[0]; best = 9.0
    for _ in range(n_start):
        S = list(rng.choice(N, k, replace=False)); v = lam_min(C, S); imp = True
        while imp:
            imp = False
            for pos in range(k):
                for j in range(N):
                    if j in S: continue
                    T = S.copy(); T[pos] = j; w = lam_min(C, T)
                    if w < v - 1e-12: S, v, imp = T, w, True
        best = min(best, v)
    return best


for fi, z in enumerate(fits):
    Lam, psi = z['Lam'], z['psi']; N = len(psi); par = dict(Lam=Lam, psi=psi)
    if Lam.shape[1] == 0: continue
    C = Lam @ Lam.T + np.diag(psi)
    order = SEL.greedy_design(par, np.arange(N), max(KS), 'A_all')
    ordc = SEL.greedy_design(par, np.arange(N), max(KS), 'A_comp')
    for k in KS:
        if k >= N: continue
        g = SEL.f_value(par, order[:k])
        if k <= 3 or (N <= 30 and k <= 4):
            _, opt = SEL.brute_force_opt(par, list(range(N)), k); how = 'exhaustive'
        else:
            _, opt = SEL.local_search_opt(par, list(range(N)), k, n_start=6, rng=rng, init=order[:k]); how = 'local_search'
        opt = max(opt, g)
        gam = np.linalg.eigvalsh(C[np.ix_(order[:k], order[:k])])[0] if k > 3 else None
        gam_min = min(lam_min(C, list(S)) for S in itertools.combinations(range(N), k)) if (k <= 3 or (N <= 30 and k <= 4)) else worst_subset(C, k, 6)
        # complement-error objective (no guarantee): greedy vs swap search on the exact error
        eg = TH.bayes_error(Lam, psi, ordc[:k])
        S = list(ordc[:k]); v = eg; imp = True
        while imp:
            imp = False
            for pos in range(k):
                for j in range(N):
                    if j in S: continue
                    T = S.copy(); T[pos] = j; w = TH.bayes_error(Lam, psi, T)
                    if w < v - 1e-12: S, v, imp = T, w, True
        rows.append(dict(setting=setting, rep=rep, fold=fi, k=k, r=Lam.shape[1], f_greedy=g, f_opt=opt, ratio=g / opt, ref=how,
                         gamma_min_est=gam_min, bound=1 - np.exp(-gam_min), err_comp_greedy=eg, err_comp_swap=v, err_ratio=eg / v))
pd.DataFrame(rows).to_csv(f"{d}/opt_rep{rep}.csv", index=False)
# stability of the greedy sets across the fold histories (each is a ~80% history resample)
st = []
for name in ('A_all', 'A_comp'):
    ords = []
    for z in fits:
        Lam, psi = z['Lam'], z['psi']
        if Lam.shape[1] == 0: continue
        cols = z['cols']; o = SEL.greedy_design(dict(Lam=Lam, psi=psi), np.arange(len(psi)), 12, name); ords.append(cols[o])
    for k in (3, 8, 12):
        J = [len(set(a[:k]) & set(b[:k])) / len(set(a[:k]) | set(b[:k])) for a, b in itertools.combinations(ords, 2)]
        st.append(dict(setting=setting, rep=rep, criterion=name, k=k, mean_jaccard=float(np.mean(J)), n_pairs=len(J)))
pd.DataFrame(st).to_csv(f"{d}/stability_rep{rep}.csv", index=False)
print(pd.DataFrame(rows).groupby('k')[['ratio', 'gamma_min_est', 'bound', 'err_ratio']].agg(['min', 'mean']).round(3)); print(pd.DataFrame(st))
