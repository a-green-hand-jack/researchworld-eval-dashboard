"""Checks of the closed forms against direct Gaussian conditioning and brute force. Run: python3 -I tests/test_closed_forms.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np
import fa as FA, bselect as SEL, theory as TH


def instance(rng, N=16, r=4, decay=1.0):
    Lam = rng.standard_normal((N, r)) * (np.arange(1, r + 1) ** -decay)[None, :]
    psi = 0.3 + 0.2 * rng.random(N)
    return dict(mu=np.zeros(N), Lam=Lam, psi=psi)


def test_conditioning():
    rng = np.random.default_rng(0)
    for _ in range(20):
        par = instance(rng); N = 16
        C = par['Lam'] @ par['Lam'].T + np.diag(par['psi'])
        S = rng.choice(N, 4, replace=False); T = np.setdiff1d(np.arange(N), S)
        x = rng.standard_normal((3, N))
        cond = x[:, S] @ np.linalg.solve(C[np.ix_(S, S)], C[np.ix_(S, T)])
        assert np.allclose(cond, FA.predict_fa(par, S, x[:, S])[:, T])
        Cc = C[np.ix_(T, T)] - C[np.ix_(T, S)] @ np.linalg.solve(C[np.ix_(S, S)], C[np.ix_(S, T)])
        assert np.allclose(np.diag(Cc), FA.predicted_mse(par, S, T))        # formula (a)


def test_gain_formula():
    rng = np.random.default_rng(1)
    for _ in range(20):
        par = instance(rng); Lam, psi = par['Lam'], par['psi']; r = 4
        S = list(rng.choice(16, 2, replace=False)); j = int(rng.choice(np.setdiff1d(np.arange(16), S)))
        W = Lam.T @ Lam
        P = np.linalg.inv(np.eye(r) + (Lam[S] / psi[S][:, None]).T @ Lam[S])
        d = SEL.f_value(par, S + [j]) - SEL.f_value(par, S)
        l = Lam[j]
        assert np.isclose(d, l @ P @ W @ P @ l / (psi[j] + l @ P @ l))


def test_tail_bound_and_greedy_ratio():
    rng = np.random.default_rng(2)
    ratios = []
    for a in (0.0, 1.0, 2.0):
        for _ in range(20):
            par = instance(rng, decay=a); Lam, psi = par['Lam'], par['psi']; k = 2
            W = Lam.T @ Lam; tail = np.sort(np.linalg.eigvalsh(W))[::-1][k:].sum()
            for S in (rng.choice(16, k, replace=False), SEL.greedy_design(par, range(16), k)):
                P = np.linalg.inv(np.eye(4) + (Lam[S] / psi[S][:, None]).T @ Lam[S])
                assert np.trace(W @ P) >= tail - 1e-9
            g = SEL.greedy_design(par, range(16), 3); bf, bv = SEL.brute_force_opt(par, range(16), 3)
            ratios.append(SEL.f_value(par, g) / bv)
    assert min(ratios) >= 1 - 1 / np.e
    print('greedy/optimum min', min(ratios), 'mean', np.mean(ratios))


def test_fa_em_recovers():
    """EM estimate of the covariance is as close to the truth as the sample covariance (complete data) and
    within 1.5x of it with 20% of the cells missing (sampling error dominates at M=4000)."""
    rng = np.random.default_rng(3)
    N, r, M = 30, 2, 4000
    L = rng.standard_normal((N, r)) * 0.8; psi = 0.4 + 0.2 * rng.random(N)
    X = rng.standard_normal((M, r)) @ L.T + np.sqrt(psi) * rng.standard_normal((M, N))
    C = L @ L.T + np.diag(psi); ref = np.abs(C - np.cov(X.T)).max()
    for frac, tol in ((1.0, 1.1), (0.8, 1.2)):
        obs = rng.random((M, N)) < frac
        p = FA.fit_fa(np.where(obs, X, np.nan), obs, r, iters=2000, tol=1e-9)
        Ch = p['Lam'] @ p['Lam'].T + np.diag(p['psi'])
        assert np.abs(C - Ch).max() <= tol * ref


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f(); print('ok', n)
