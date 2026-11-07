"""Sanity tests: fit vs scipy, linear influence vs exact refit, greedy vs brute force."""
import itertools, sys
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, ".")
from btlib import Board, influence, min_edits_to_flip, apply_edits, sig, LAM


def rand_board(P, rng, n=60, home=False):
    i, j = np.triu_indices(P, 1)
    W = rng.integers(0, n, len(i)); L = rng.integers(0, n, len(i)); T = rng.integers(0, 5, len(i))
    return Board(P, i, j, W, L, T)


def test_fit():
    rng = np.random.default_rng(0)
    B = rand_board(6, rng)
    beta = B.fit()
    X, (w, n) = B.X(), B.wn()
    f = lambda b: -(w * np.log(sig(X @ b)) + (n - w) * np.log(sig(-(X @ b)))).sum() + 0.5 * LAM * b @ b
    r = minimize(f, np.zeros(6), method="BFGS", options=dict(gtol=1e-10))
    r.x -= r.x.mean()
    assert np.abs(r.x - beta).max() < 1e-4, (r.x, beta)


def test_home():
    rng = np.random.default_rng(1)
    P = 5; i, j = np.triu_indices(P, 1)
    ii = np.concatenate([i, j]); jj = np.concatenate([j, i]); h = np.ones(len(ii))
    B = Board(P, ii, jj, rng.integers(10, 50, len(ii)), rng.integers(10, 50, len(ii)), np.zeros(len(ii)), home=h)
    beta = B.fit(); X, (w, n) = B.X(), B.wn()
    assert np.abs(X.T @ (w - n * sig(X @ beta))).max() < 1e-3  # score equations (home col included)


def test_influence_vs_exact():
    rng = np.random.default_rng(2)
    B = rand_board(6, rng, n=400)
    beta = B.fit(); a, b = np.argsort(-beta)[:2]
    c = np.zeros(6); c[a], c[b] = 1, -1
    for name, eff, av in influence(B, beta, c, ("remove", "flip", "inject")):
        for cell in range(0, B.n_cells, 4):
            if av[cell] < 1: continue
            B2 = B.copy(); apply_edits(B2, [(cell, name, 1)])
            b2 = B2.fit(beta); exact = (b2[a] - b2[b]) - (beta[a] - beta[b])
            assert abs(exact - eff[cell]) < 0.15 * abs(eff[cell]) + 2e-4, (name, cell, exact, eff[cell])


def test_greedy_vs_brute():
    """Tiny board: brute-force the minimum number of removals flipping the top pair."""
    rng = np.random.default_rng(3)
    P = 3; i, j = np.triu_indices(P, 1)
    for trial in range(6):
        B = Board(P, i, j, rng.integers(2, 9, 3), rng.integers(2, 9, 3), np.zeros(3))
        beta = B.fit(); a, b = np.argsort(-beta)[:2]
        r = min_edits_to_flip(B, a, b, ("remove",))
        best = None
        for k in range(0, 14):
            found = False
            for rw in itertools.product(range(0, k + 1), repeat=6):
                if sum(rw) != k: continue
                if any(rw[c] > B.W[c] or rw[c + 3] > B.L[c] for c in range(3)): continue
                B2 = B.copy()
                apply_edits(B2, [(c, "rW", rw[c]) for c in range(3)] + [(c, "rL", rw[c + 3]) for c in range(3)])
                b2 = B2.fit()
                if b2[a] - b2[b] < -1e-9: found = True; break
            if found: best = k; break
        print("greedy", r["k"], "brute", best)
        assert r["k"] is not None and best is not None and r["k"] >= best and r["k"] <= best + max(1, int(0.25 * best))


if __name__ == "__main__":
    for f in (test_fit, test_home, test_influence_vs_exact, test_greedy_vs_brute):
        f(); print(f.__name__, "ok")
