"""Synthetic check of the Gaussian-factor-model theory. x = L z + e (z~N(0,I_r), e~N(0,psi_j)), unit-variance columns.
Prediction of benchmark j from set S with known parameters: E err^2 = psi_j + l_j^T P_S l_j, P_S=(I+L_S^T Psi_S^-1 L_S)^-1
(Bayes-optimal, any selection fixed in advance).  For iid isotropic loadings and k>>r:  mean MSE ~ psi (1 + r/k).
usage: theory_synth.py OUT.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0]); from bench import *
rows = []
for (r, rho, M, N) in [(2, 0.6, 150, 100), (5, 0.6, 150, 100), (5, 0.8, 150, 100), (5, 0.6, 600, 100), (10, 0.6, 600, 100)]:
    for rep in range(10):
        rng = np.random.default_rng(rep)
        L = rng.standard_normal((N, r)); L *= np.sqrt(rho) / np.linalg.norm(L, axis=1, keepdims=True) * np.sqrt(rng.uniform(0.6, 1.4, (N, 1)))
        psi = np.maximum(1 - (L ** 2).sum(1), 0.05)
        gen = lambda m: rng.standard_normal((m, r)) @ L.T + rng.standard_normal((m, N)) * np.sqrt(psi)
        Xtr, Xte = gen(M), gen(300)
        fa = FA(r, iters=60, seed=rep, psi_min=0.05).fit(Xtr); ctx = make_ctx(Xtr, fa)
        # oracle sequence for greedy: design from true parameters
        oracle = type("O", (), dict(L=L, psi=psi, r=r))()
        orders = dict(random=sel_random(Xtr, np.random.default_rng(rep)), greedy_est=sel_greedy_bayes(Xtr, None, fa=fa), greedy_true=sel_greedy_bayes(Xtr, None, fa=oracle))
        for n, o in orders.items():
            for k in [1, 2, 3, 5, 8, 12, 16, 24, 32, 48]:
                S = np.array(o[:k]); tgt = np.setdiff1d(np.arange(N), S)
                P = np.linalg.inv(np.eye(r) + (L[S].T / psi[S]) @ L[S])
                theo = np.mean(psi[tgt] + np.einsum("jr,rs,js->j", L[tgt], P, L[tgt]))
                emp_fa = np.mean([(fa.predict(x[S], S)[tgt] - x[tgt]) ** 2 for x in Xte])
                rows.append((r, rho, M, rep, n, k, theo, emp_fa, psi[tgt].mean(), psi.mean() * (1 + r / k)))
pd.DataFrame(rows, columns="r rho M rep sel k theory_oracle emp_fa_est floor approx_psi_1_plus_r_over_k".split()).to_csv(sys.argv[1], index=False)
