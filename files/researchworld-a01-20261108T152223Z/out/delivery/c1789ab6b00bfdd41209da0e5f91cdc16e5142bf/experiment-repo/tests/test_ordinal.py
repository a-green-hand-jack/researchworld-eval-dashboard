import itertools, numpy as np, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
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


def test_plan_coordinates_and_lexicographic():
    """K_at_L1 >= K; L1_lexK between min L1 and the L1 of any K-minimal plan; checked by brute force for L1_lexK."""
    for rule in ["borda", "copeland", "plurality"]:
        for _ in range(40):
            M = int(rng.integers(3, 6)); n = int(rng.integers(2, 5))
            X = rng.integers(0, 8, (M, n)).astype(float); i = int(rng.integers(0, M)); c = X[i] + rng.integers(0, 8, n)
            out = od.min_investment_ordinal(rule, X, i, c, EPS, measures=("L1", "K", "L1_lexK"))
            if not np.isfinite(out["L1"]): assert not np.isfinite(out["K"]); continue
            assert out["K_at_L1"] >= out["K"] - 1e-9 and out["L1_lexK"] >= out["L1"] - 1e-9
            f = od.FIRST[rule]; best = np.inf
            for y in itertools.product(*[np.arange(X[i, t], c[t] + 1) for t in range(n)]):
                y = np.array(y, float); Y = X.copy(); Y[i] = y
                if f(Y) == i and (y > X[i]).sum() == out["K"]: best = min(best, (y - X[i]).sum())
            assert np.isclose(best, out["L1_lexK"]) or out["K"] == 0, (rule, X, i, c, out, best)
