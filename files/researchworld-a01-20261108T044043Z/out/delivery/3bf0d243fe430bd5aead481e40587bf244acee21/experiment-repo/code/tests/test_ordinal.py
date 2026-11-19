import itertools, numpy as np, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from mti import ordinal as od
rng = np.random.default_rng(1)
EPS = 1.0   # integer data, eps=1 => integer optimum; brute force over integer y

def brute(rule, X, i, c, objective):
    n = X.shape[1]; f = od.FIRST[rule]; best = np.inf
    axes = [np.arange(X[i, t], c[t] + 1) for t in range(n)]
    for y in itertools.product(*axes):
        y = np.array(y, float); Y = X.copy(); Y[i] = y
        if f(Y) == i:
            cost = (y - X[i]).sum() if objective == "L1" else (y > X[i]).sum()
            best = min(best, cost)
    return best

def test_rules_vs_bruteforce():
    for rule in ["borda", "condorcet", "plurality", "copeland"]:
        for obj in ["L1", "K"]:
            for _ in range(60):
                M = int(rng.integers(3, 6)); n = int(rng.integers(2, 5))
                X = rng.integers(0, 8, (M, n)).astype(float); i = int(rng.integers(0, M))
                c = X[i] + rng.integers(0, 8, n)
                got = od.MIN_INV[rule](X, i, c, EPS, obj); want = brute(rule, X, i, c, obj)
                assert (np.isinf(got) and np.isinf(want)) or np.isclose(got, want), (rule, obj, X, i, c, got, want)


def test_grid_is_within_n_eps_of_continuous_infimum():
    """Strict-win levels s+eps: the optimum on the finite grid exceeds the infimum of the continuous problem (eps -> 0) by at most
    eps per raised task, and the number of raised tasks and feasibility do not depend on eps (real-valued scores, slack caps)."""
    r = np.random.default_rng(5); big, small = 1e-2, 1e-4
    for rule in ["borda", "condorcet", "plurality", "copeland"]:
        for _ in range(40):
            M = int(r.integers(3, 7)); n = int(r.integers(2, 5)); X = r.uniform(0, 50, (M, n)); i = int(r.integers(0, M))
            if r.random() < 0.3: X[:, 0] = np.round(X[:, 0])          # some exact ties
            c = np.full(n, 100.0)
            lb, ls = od.MIN_INV[rule](X, i, c, big, "L1"), od.MIN_INV[rule](X, i, c, small, "L1")
            kb, ks = od.MIN_INV[rule](X, i, c, big, "K"), od.MIN_INV[rule](X, i, c, small, "K")
            assert np.isinf(lb) == np.isinf(ls) and kb == ks
            if np.isfinite(lb):      # HiGHS stops at a relative MIP gap of 1e-4, so each optimum is only known to that relative accuracy
                tol = 2e-4 * max(lb, ls) + 1e-9
                assert ls - tol <= lb <= ls + n * big + tol, (rule, X, i, lb, ls)
