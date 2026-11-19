"""Theory checks on the factor model with KNOWN parameters (Bayes-optimal inference).

Model: z = W f + e, f~N(0,I_r), e~N(0,diag(psi)).  Given observed set S, the posterior covariance of f is
  Sigma_S = (I + sum_{j in S} w_j w_j'/psi_j)^-1  and the expected squared error on target j not in S is  psi_j + w_j' Sigma_S w_j.
(A) random S, iid N(0,(lam/r) I) loadings, homoscedastic psi, c = lam/(r psi):
      Jensen lower bound   E tr Sigma_S >= r/(1+k c)
      Wishart upper bound  E tr Sigma_S <= r/(c (k-r-1))   (k>r+1)
    => relative excess error over the noise floor, e(k) = (MSE-psi)/psi ~ c*tr Sigma_S lies in [rc/(1+kc), r/(k-r-1)] ; to get e<=eps need k >= r+1+r/eps.
(B) greedy (conditional-variance / D-optimal) vs brute-force optimum for small N.
usage: python theory_check.py <out dir>
"""
import sys, os, itertools
import numpy as np, pandas as pd
import lib

def bayes_err(W, psi, S):
    N, r = W.shape
    S = list(S)
    Sig = np.linalg.inv(np.eye(r) + (W[S] / psi[S, None]).T @ W[S])
    T = [j for j in range(N) if j not in set(S)]
    return float(np.mean(psi[T] + np.einsum('ja,ab,jb->j', W[T], Sig, W[T])))

def exp_A(out, n_mc=2000, N=400):
    rng = np.random.default_rng(1)
    rows = []
    for r in [1, 3, 8]:
        for snr in [0.5, 2.0, 8.0]:          # lam/psi, total loading variance per benchmark over noise variance
            lam, psi = snr, 1.0
            c = lam / (r * psi)
            for k in [r + 2, r + 4, 2 * r + 2, 4 * r, 8 * r, 16 * r]:
                if k > N // 4:
                    continue
                e = []
                for _ in range(n_mc // 10):
                    W = rng.normal(size=(N, r)) * np.sqrt(lam / r)
                    for _ in range(10):
                        S = rng.choice(N, k, replace=False)
                        e.append(bayes_err(W, np.full(N, psi), S))
                emp = (np.mean(e) - psi) / psi
                lo = r * c / (1 + k * c)
                hi = r / (k - r - 1) if k > r + 1 else np.nan
                rows.append(dict(r=r, snr=snr, k=k, excess_mc=emp, lower=lo, upper=hi))
    df = pd.DataFrame(rows)
    df['within'] = (df.excess_mc >= df.lower * 0.97) & (df.excess_mc <= df.upper * 1.03)
    df.to_csv(os.path.join(out, 'theory_A_random.csv'), index=False)
    print(df.round(4).to_string()); print('fraction within bounds', df.within.mean())

def exp_B(out, N=16, n_inst=40):
    rng = np.random.default_rng(2)
    rows = []
    for kind in ['iid', 'hetero', 'cluster']:
        for inst in range(n_inst):
            r = 3
            if kind == 'cluster':
                C = rng.normal(size=(4, r)); W = C[rng.integers(0, 4, N)] * .9 + .15 * rng.normal(size=(N, r))
            else:
                W = rng.normal(size=(N, r)) * 0.9
                if kind == 'hetero':
                    W *= np.exp(0.8 * rng.normal(size=(N, 1)))
            psi = np.full(N, 0.3)
            C = W @ W.T + np.diag(psi)
            for k in [2, 3, 4, 5]:
                best = min(bayes_err(W, psi, S) for S in itertools.combinations(range(N), k))
                worst = max(bayes_err(W, psi, S) for S in itertools.combinations(range(N), k))
                g = bayes_err(W, psi, lib.greedy_cond_var(C, k)[:k])
                d = bayes_err(W, psi, lib.greedy_dopt(W, psi, k)[:k])
                rnd = np.mean([bayes_err(W, psi, rng.choice(N, k, replace=False)) for _ in range(200)])
                # fraction of the random->optimal gap closed
                rows.append(dict(kind=kind, inst=inst, k=k, best=best, greedy_cv=g, greedy_dopt=d, random=rnd, worst=worst,
                                 closed_cv=(rnd - g) / (rnd - best), closed_dopt=(rnd - d) / (rnd - best)))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out, 'theory_B_greedy.csv'), index=False)
    print(df.groupby(['kind', 'k'])[['closed_cv', 'closed_dopt']].agg(['mean', 'min']).round(3).to_string())

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    exp_A(out); exp_B(out)
