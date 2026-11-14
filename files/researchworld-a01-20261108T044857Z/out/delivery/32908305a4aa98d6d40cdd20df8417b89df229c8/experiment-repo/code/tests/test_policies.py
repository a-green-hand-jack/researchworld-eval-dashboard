import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from mti import scorerules as sr, policies as pol

def test_policy_vectors_match_solver_costs():
    rng = np.random.default_rng(0)
    for _ in range(600):
        n = int(rng.integers(2, 8)); M = int(rng.integers(3, 9)); X = rng.uniform(0, 10, (M, n)); i = int(rng.integers(M))
        cap = X[i] + rng.uniform(0, 6, n) * (rng.random(n) < .8)
        for rule in ["mean", "median", "min"]:
            v = sr.RULES[rule][0](X); tau = np.delete(v, i).max()
            if v[i] > tau: continue
            L = sr.RULES[rule][1](X[i], tau, cap, 1e-3); y = pol.Y[rule](X[i], tau, cap, 1e-3)
            if np.isinf(L): assert y is None
            else:
                assert y is not None and abs((y - X[i]).sum() - L) < 1e-7
                assert sr.RULES[rule][0](y) >= tau + 1e-3 - 1e-9 and (y <= np.maximum(cap, X[i]) + 1e-12).all() and (y >= X[i]).all()
