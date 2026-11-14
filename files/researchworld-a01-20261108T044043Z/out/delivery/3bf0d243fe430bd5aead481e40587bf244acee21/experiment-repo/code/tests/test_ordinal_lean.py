"""The memory-lean Borda/Condorcet MILPs equal the dense ones (random boards, then OLLB targets beyond rank 50)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import mti.ordinal as od, mti.ordinal_lean as ol


def same(a, b): return (np.isnan(a) and np.isnan(b)) or a == b or abs(a - b) <= 2e-4 * max(abs(a), abs(b)) + 1e-9


def test_random_boards():
    rng = np.random.default_rng(1)
    for _ in range(25):
        M, n = rng.integers(8, 40), rng.integers(3, 7)
        X = np.round(rng.uniform(0, 60, (M, n)), 1)
        i = rng.integers(0, M); cap = np.minimum(X[i] + rng.uniform(0, 40, n), 100)
        for obj in ("L1", "K"):
            assert same(od.borda_min_investment(X, i, cap, 1e-3, obj), ol.borda_min_investment(X, i, cap, 1e-3, obj))
            assert same(od.condorcet_min_investment(X, i, cap, 1e-3, obj), ol.condorcet_min_investment(X, i, cap, 1e-3, obj))


def test_ollb():
    import mti.data as dt
    from scipy.stats import rankdata
    X, *_ = dt.load("ollb"); rk = rankdata(-X.mean(1), method="min"); o = np.argsort(rk, kind="stable")
    for pos in (60, 120, 250):
        i = o[pos]
        for sc in ("ceil", "emp99"):
            cap = dt.make_cap(sc, X, i)
            for obj in ("L1", "K"):
                assert same(od.borda_min_investment(X, i, cap, 1e-3, obj), ol.borda_min_investment(X, i, cap, 1e-3, obj)), (pos, sc, obj)
                assert same(od.condorcet_min_investment(X, i, cap, 1e-3, obj), ol.condorcet_min_investment(X, i, cap, 1e-3, obj)), (pos, sc, obj)


if __name__ == "__main__":
    test_random_boards(); print("random ok"); test_ollb(); print("ollb ok")
