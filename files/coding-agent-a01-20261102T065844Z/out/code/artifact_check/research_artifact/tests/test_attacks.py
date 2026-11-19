import itertools
import numpy as np
import pytest
from scipy.optimize import linprog, minimize
from src.attacks import (RULES, aggregate, min_support, min_mass_one,
                         support_witness, all_subsets, thresholds)

@pytest.mark.parametrize("d", [3, 4, 5, 6, 7])
def test_support_against_exhaustive(d):
    rng = np.random.default_rng(721+d)
    x = rng.integers(0, 11, (65, d))/10
    u = x + rng.choice([0., .25, .5, 1.], (65, d))*(1-x)
    tau = rng.choice([0., .25, .5, .75, 1., 1.00001], 65)
    masks = all_subsets(d)
    y = np.where(masks[None], u[:, None], x[:, None])
    for rule in RULES:
        feasible = aggregate(y, rule) >= tau[:, None]-1e-12
        brute = masks.sum(axis=1)[np.argmax(feasible, axis=1)]
        brute[~feasible.any(axis=1)] = d+1
        actual = min_support(x, u, tau, rule)
        np.testing.assert_array_equal(actual, brute)
        for i in range(len(x)):
            w = support_witness(x[i], u[i], tau[i], rule)
            assert (w is None) == (brute[i] > d)

def median_lp(x, u, tau):
    """Independent oracle: enumerate all orderings and solve a linear program."""
    d = len(x)
    best = np.inf
    for perm in itertools.permutations(range(d)):
        a, b = [], []
        for l, h in zip(perm[:-1], perm[1:]):
            row = np.zeros(d); row[l] = 1; row[h] = -1
            a.append(row); b.append(0.)
        row = np.zeros(d)
        if d % 2:
            row[perm[d//2]] = -1
        else:
            row[perm[d//2-1]] = -.5; row[perm[d//2]] = -.5
        a.append(row); b.append(-tau)
        r = linprog(np.ones(d), A_ub=a, b_ub=b, bounds=list(zip(x, u)), method="highs")
        if r.success:
            best = min(best, (r.fun-x.sum())/d)
    return best

@pytest.mark.parametrize("d", [3, 4, 6])
def test_mass_median_against_lp(d):
    rng = np.random.default_rng(80+d)
    for _ in range(5):
        x = rng.uniform(0, .7, d)
        u = x + rng.uniform(.1, 1., d)*(1-x)
        tau = float(rng.uniform(.2, .9))
        actual = min_mass_one(x, u, tau, "median")
        expected = median_lp(x, u, tau)
        assert np.isclose(actual, expected, atol=1e-9) or (np.isinf(actual) and np.isinf(expected))

def test_geometric_mass_against_convex_solver():
    rng = np.random.default_rng(921)
    for _ in range(20):
        x = rng.uniform(.02, .5, 6)
        u = rng.uniform(.65, 1., 6)
        tau = .6
        exact = min_mass_one(x, u, tau, "geometric")
        r = minimize(lambda y: y.sum(), (x+u)/2, jac=lambda y: np.ones(6),
                     method="SLSQP", bounds=list(zip(x, u)),
                     constraints=[{"type": "ineq", "fun": lambda y: np.log(y).sum()-6*np.log(tau),
                                   "jac": lambda y: 1/y}], options={"ftol": 1e-11, "maxiter": 300})
        assert r.success
        assert abs(exact-(r.fun-x.sum())/6) < 1e-7

def test_competitor_threshold_and_counterexamples():
    x = np.array([[.59, .59, .59], [0., .1, .61], [.6, .6, .6]])
    tau = np.full(3, .6)
    np.testing.assert_array_equal(min_support(x, np.ones_like(x), tau, "mean")[:2], [1, 2])
    np.testing.assert_array_equal(min_support(x, np.ones_like(x), tau, "median")[:2], [2, 1])
    for rule in RULES:
        s = aggregate(x, rule)
        np.testing.assert_allclose(thresholds(x, rule), [np.delete(s, i).max() for i in range(3)])

def test_weighted_mean_against_brute():
    rng = np.random.default_rng(29)
    x = rng.uniform(0, 1, (20, 6)); u = x+.3*(1-x); tau = rng.uniform(.3, .9, 20)
    w = np.array([1, 2, 3, 4, 5, 6])
    masks = all_subsets(6)
    ok = aggregate(np.where(masks[None], u[:, None], x[:, None]), "mean", weights=w) >= tau[:, None]-1e-12
    k = masks.sum(axis=1)[ok.argmax(axis=1)]; k[~ok.any(axis=1)] = 7
    np.testing.assert_array_equal(min_support(x, u, tau, "mean", weights=w), k)

def test_ceiling_reverses_order_on_identical_leaderboard():
    x = np.array([[.59, .59, .59], [.6, .6, .6], [.604, 0, 0],
                  [0, .604, 0], [0, 0, .604]])
    for margin in [0., 1e-6]:
        for ceiling, expected in [(np.ones_like(x), (1, 2)),
                                  (np.broadcast_to(x.max(axis=0), x.shape), (3, 2))]:
            actual = tuple(min_support(x, ceiling, thresholds(x, r, margin), r)[0]
                           for r in ['mean', 'median'])
            assert actual == expected

def test_mixed_cost_simultaneous_minima():
    rng=np.random.default_rng(2028)
    for _ in range(12):
        x=rng.uniform(.05,.65,5);u=x+rng.uniform(.2,1.,5)*(1-x);tau=.6
        for rule in ['mean','median']:
            k=min_support(x[None],u[None],np.array([tau]),rule)[0]
            c=min_mass_one(x,u,tau,rule)
            if not np.isfinite(c):continue
            for lam in [.1,.5,.9]:
                best=np.inf
                for mask in all_subsets(5):
                    restricted=np.where(mask,u,x)
                    cm=min_mass_one(x,restricted,tau,rule)
                    best=min(best,lam*mask.sum()/5+(1-lam)*cm)
                assert abs(best-(lam*k/5+(1-lam)*c))<1e-10
