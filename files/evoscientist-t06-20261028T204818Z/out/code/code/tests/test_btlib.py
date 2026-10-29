"""Unit tests for btlib (run: python -m pytest code/tests -q)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import btlib as bt  # noqa: E402


def synth(m=6, N=600, seed=0, tie_rate=0.2, home=False):
    rng = np.random.default_rng(seed)
    th = np.linspace(1.0, -1.0, m)
    a = rng.integers(0, m, N)
    b = (a + rng.integers(1, m, N)) % m
    h = rng.integers(0, 2, N) if home else np.zeros(N)
    p = bt.sigmoid(th[a] - th[b] + 0.3 * h)
    u = rng.random(N)
    y = np.where(u < p, 1.0, 0.0)
    tie = rng.random(N) < tie_rate
    y[tie] = 0.5
    names = [f"p{k}" for k in range(m)]
    return bt.build_table([names[k] for k in a], [names[k] for k in b], y, h=h, use_home=home, players=names)


def test_counts_and_fit_gradient():
    tt = synth(home=True)
    assert tt.N == 600
    f = bt.fit_bt(tt, lam=0.01)
    assert f.converged
    g = tt.design().T @ (tt.n * (tt.y - f.p)) - 0.01 * f.theta
    assert np.max(np.abs(g)) < 1e-6


def test_fit_matches_unaggregated_logistic():
    # direct optimisation on expanded data with scipy must give the same estimate
    from scipy.optimize import minimize
    tt = synth(m=4, N=200, seed=3)
    f = bt.fit_bt(tt, lam=0.01)
    X, y, n = tt.design(), tt.y, tt.n

    def nll(t):
        eta = X @ t
        return -np.sum(n * (y * -np.logaddexp(0, -eta) + (1 - y) * -np.logaddexp(0, eta))) + 0.005 * t @ t
    r = minimize(nll, np.zeros(X.shape[1]), method="BFGS", options={"gtol": 1e-10})
    assert np.allclose(r.x, f.theta, atol=1e-5)


def test_influence_predicts_single_drop():
    tt = synth(N=2000, seed=1)
    f = bt.fit_bt(tt)
    i, j = 0, 1
    eff, src, dst, cap = bt.candidate_moves(tt, f, tt.n, i, j, "drop")
    gap0 = f.theta[i] - f.theta[j]
    for t in np.where(tt.n > 0)[0][:12]:
        n2 = tt.n.copy(); n2[t] -= 1
        f2 = bt.fit_bt(tt, n2, theta0=f.theta)
        actual = (f2.theta[i] - f2.theta[j]) - gap0
        assert abs(actual - eff[t]) < 0.05 * abs(eff[t]) + 1e-6


def test_flip_and_add_effects_sign():
    tt = bt.build_table(*_names_from(synth(N=1500, seed=2)), all_pairs=True)
    f = bt.fit_bt(tt)
    for kind in ("flip", "add"):
        eff, src, dst, cap = bt.candidate_moves(tt, f, tt.n, 0, 1, kind)
        k = np.argmin(eff)
        n2 = tt.n.copy()
        if src[k] >= 0:
            n2[src[k]] -= 1
        n2[dst[k]] += 1
        f2 = bt.fit_bt(tt, n2, theta0=f.theta)
        actual = (f2.theta[0] - f2.theta[1]) - (f.theta[0] - f.theta[1])
        assert actual < 0 and abs(actual - eff[k]) < 0.1 * abs(eff[k])


def _names_from(tt):
    a, b, y = [], [], []
    for t in np.where(tt.n > 0)[0]:
        c = int(tt.n[t])
        a += [tt.players[tt.a[t]]] * c; b += [tt.players[tt.b[t]]] * c; y += [tt.y[t]] * c
    return a, b, y


def test_greedy_verified_and_close_to_exact():
    tt = synth(m=5, N=120, seed=5)
    f = bt.fit_bt(tt)
    r = bt.ranking(f.theta, tt.m)
    for pos in range(3):
        i, j = r[pos], r[pos + 1]
        res = bt.min_perturbation(tt, i, j, "drop", fit0=f)
        assert res["k"] is not None
        n2 = bt._apply(tt.n, res["moves"])
        f2 = bt.fit_bt(tt, n2)
        assert f2.theta[j] > f2.theta[i]            # verified flip
        assert abs(tt.N - n2.sum() - res["k"]) < 1e-9
        ex = bt.exact_min_drop(tt, i, j, kmax=min(2, res["k"]), fit0=f)
        if ex is not None:
            assert ex <= res["k"]
        if res["k"] <= 2:
            assert ex is not None and ex == res["k"], (ex, res["k"])


def test_random_drop_counts():
    tt = synth()
    rng = np.random.default_rng(0)
    n2 = bt.random_drop_counts(rng, tt.n, 50)
    assert n2.sum() == tt.N - 50 and (n2 >= 0).all()
    n3 = bt.random_flip_counts(rng, tt, tt.n, 50)
    assert n3.sum() == tt.N
