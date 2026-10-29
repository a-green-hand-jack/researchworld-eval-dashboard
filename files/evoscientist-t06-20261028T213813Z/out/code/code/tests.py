"""Sanity tests for the BT fit and the attack code (run: python tests.py)."""
import numpy as np
from bt import Board, fit, contrast, min_budget, linear_budget, sigmoid, direct_flip_budget


def two_player(w_a, w_b):
    return Board('t', 't', 't', ['A', 'B'], np.array([[1., -1.]]), np.array([[w_a, w_b, 0.]]))


def test_fit_closed_form():
    b = two_player(60, 40)
    th = fit(b.X, b.W)
    assert abs((th[0] - th[1]) - np.log(60 / 40)) < 1e-2, th


def test_flip_two_player_exact():
    # flipping k wins of A to B: reversal iff 60-k < 40+k  -> k=11
    b = two_player(60, 40)
    th = fit(b.X, b.W); q = contrast(2, 0, 1)
    K, cens = min_budget(b, 'flip', q, th)
    assert not cens and K == 11, K
    K, cens = min_budget(b, 'remove', q, th)  # remove k wins of A: 60-k<40 -> k=21
    assert K == 21, K
    K, cens = min_budget(b, 'insert', q, th)  # add k B wins: 60 < 40+k -> k=21
    assert K == 21, K
    assert direct_flip_budget(b, 0, 1, q, th) == 11


def test_indirect_beats_direct():
    # three players; A vs B direct votes are few, but A's wins over C and B's wins over C can be changed
    X = np.array([[1., -1., 0.], [1., 0., -1.], [0., 1., -1.]])
    W = np.array([[6., 4., 0.], [60., 40., 0.], [50., 50., 0.]])
    b = Board('t', 't', 't', list('ABC'), X, W)
    th = fit(b.X, b.W); q = contrast(3, 0, 1)
    assert q @ th > 0
    Kg, c = min_budget(b, 'flip', q, th)
    Kd = direct_flip_budget(b, 0, 1, q, th)
    assert Kg < Kd, (Kg, Kd)


def test_linear_close():
    rng = np.random.default_rng(0)
    n = 6
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    X = np.zeros((len(pairs), n))
    for k, (i, j) in enumerate(pairs):
        X[k, i], X[k, j] = 1, -1
    true = np.linspace(1, -1, n)
    W = np.zeros((len(pairs), 3))
    for k, (i, j) in enumerate(pairs):
        wa = rng.binomial(300, sigmoid(true[i] - true[j]))
        W[k] = [wa, 300 - wa, 0]
    b = Board('t', 't', 't', list(range(n)), X, W)
    th = fit(b.X, b.W)
    order = np.argsort(-th)
    q = contrast(n, order[0], order[1])
    Kex, _ = min_budget(b, 'flip', q, th)
    Kl = linear_budget(b, 'flip', q, th)
    print('exact', Kex, 'linear', Kl)
    assert 0.5 < Kex / Kl < 2.0


if __name__ == '__main__':
    for f in [test_fit_closed_form, test_flip_two_player_exact, test_indirect_beats_direct, test_linear_close]:
        f(); print('ok', f.__name__)
