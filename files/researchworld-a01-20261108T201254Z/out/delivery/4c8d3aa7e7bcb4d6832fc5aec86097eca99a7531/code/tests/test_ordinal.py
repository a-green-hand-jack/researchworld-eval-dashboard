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
            cost = {"L1": (y - X[i]).sum(), "K": (y > X[i]).sum(), "Linf": (y - X[i]).max()}[objective]
            best = min(best, cost)
    return best

def test_rules_vs_bruteforce():
    for rule in ["borda", "condorcet", "plurality"]:
        for obj in ["L1", "K", "Linf"]:
            for _ in range(60):
                M = int(rng.integers(3, 6)); n = int(rng.integers(2, 5))
                X = rng.integers(0, 8, (M, n)).astype(float); i = int(rng.integers(0, M))
                c = X[i] + rng.integers(0, 8, n)
                got = od.MIN_INV[rule](X, i, c, EPS, obj) if obj != "Linf" else od.linf_ordinal(rule, X, i, c, EPS); want = brute(rule, X, i, c, obj)
                assert (np.isinf(got) and np.isinf(want)) or np.isclose(got, want), (rule, obj, X, i, c, got, want)


def test_timeout_is_censored_not_infeasible():
    """A solver time-out must be reported as NaN / 'censored' (with a valid lower bound), never as INF (= proven infeasible)."""
    from mti import data as dt
    X, names, tasks, meta = dt.load("ollb"); mr = (-X.mean(axis=1)).argsort(kind="stable"); i = mr[2000]
    old = od.TIME_LIMIT; od.TIME_LIMIT = 0.02
    try:
        info = {}; v = od.borda_min_investment(X, i, np.full(X.shape[1], 100.0), EPS, "L1", info=info)
    finally: od.TIME_LIMIT = old
    assert np.isnan(v) and info["status"] == "censored", (v, info)
    info2 = {}; v2 = od.borda_min_investment(X, mr[3], np.full(X.shape[1], 100.0), EPS, "L1", info=info2)
    assert info2["status"] == "opt" and np.isfinite(v2) and abs(info2["lb"] - v2) < 1e-6
    info3 = {}; v3 = od.borda_min_investment(X, mr[3], X[mr[3]], EPS, "L1", info=info3)     # no headroom: proven infeasible
    assert np.isinf(v3) and info3["status"] == "infeasible"
