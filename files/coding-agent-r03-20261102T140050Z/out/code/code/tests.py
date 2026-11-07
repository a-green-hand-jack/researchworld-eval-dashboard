"""Sanity tests (run: python tests.py). Checks the closed forms used in the paper against direct linear algebra."""
import numpy as np, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bsel import select as sel
from bsel.fa import fit_fa, predict_fa, expected_mse, model_cov
from run_synth import make_fa, bayes_err, cov_of

rng = np.random.default_rng(0)
# 1. Prop 1: psi_j + l_j' (I + L_S' Psi^-1 L_S)^-1 l_j == Sigma_jj - Sigma_jS Sigma_SS^-1 Sigma_Sj
L, psi = make_fa(30, 3, g=1.5, kappa=0.5, seed=1, hetero_noise=0.4); cov = cov_of(L, psi)
S = np.array([3, 7, 11, 20]); T = np.setdiff1d(np.arange(30), S)
direct = np.diag(cov)[T] - np.einsum('ij,ji->i', cov[np.ix_(T, S)], np.linalg.solve(cov[np.ix_(S, S)], cov[np.ix_(S, T)]))
assert np.allclose(direct.mean(), bayes_err(L, psi, S)), 'Prop 1 identity'
# 2. fold-in prediction equals Gaussian conditional mean
par = dict(mu=np.zeros(30), L=L, psi=psi); z = rng.standard_normal(30)
pred = predict_fa(par, S, z[S]); cond = cov[:, S] @ np.linalg.solve(cov[np.ix_(S, S)], z[S])
assert np.allclose(pred[T], cond[T]), 'fold-in == conditional mean (on targets)'
assert np.isclose(expected_mse(par, S), direct.mean()), 'expected_mse'
# 3. greedy objective monotone, objective(greedy) <= objective(random) on average, tail bound holds
C = cov / np.sqrt(np.outer(np.diag(cov), np.diag(cov)))
order = sel.greedy_var(C, 10); vals = [sel.objective(C, order[:k]) for k in range(1, 11)]
assert all(a >= b - 1e-12 for a, b in zip(vals, vals[1:])), 'monotone'
lam = np.sort(np.linalg.eigvalsh(C))[::-1]
assert all(v >= lam[k:].sum() - 1e-9 for k, v in zip(range(1, 11), vals)), 'tail bound (Prop 3)'
rnd = np.mean([sel.objective(C, rng.permutation(30)[:5]) for _ in range(200)]); assert vals[4] < rnd, 'greedy beats random'
# 4. exhaustive optimum <= greedy, and ratio is high
Cs = C[:10, :10]; assert sel.objective(Cs, sel.exhaustive_best(Cs, 3)) <= sel.objective(Cs, sel.greedy_var(Cs, 3)) + 1e-12
# 5. EM FA recovers covariance roughly with complete data
Z = rng.standard_normal((4000, 3)) @ L[:12].T + rng.standard_normal((4000, 12)) * np.sqrt(psi[:12])
p = fit_fa((Z - Z.mean(0)) / Z.std(0), 3, n_iter=300); print('FA cov rel. error', np.linalg.norm(model_cov(p) - np.corrcoef(Z.T)) / np.linalg.norm(np.corrcoef(Z.T)))
print('all tests passed')
