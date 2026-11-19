"""Frontier check: breadth-constrained MILPs against subset enumeration with the unconstrained solver (boosts masked outside the subset)."""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from lbprice import solvers as SV
rng = np.random.default_rng(11); bad = 0; n = 0
for trial in range(60):
    N, m = int(rng.integers(4, 8)), int(rng.integers(3, 6))
    S = np.round(rng.uniform(30, 90, (N, m)), 1); t = int(rng.integers(N)); B = float(rng.choice([8, 20, 100]))
    for rule in ["mean", "zmean", "median", "min", "plurality", "borda", "copeland"]:
        kw = dict(sigma=S.std(0)) if rule == "zmean" else {}
        fr = SV.frontier(rule, S, t, B, **kw)
        for k, cost, depth, feas in fr:
            best = np.inf
            for sub in itertools.combinations(range(m), k):
                Bm = np.zeros(m); Bm[list(sub)] = B
                p = SV.price(rule, S, t, Bm, objective="depth", **kw)
                if p["feasible"]: best = min(best, p["depth"])
            n += 1
            if not ((np.isinf(best) and not feas) or (feas and abs(depth - best) < 1e-5 * max(1, best))):
                bad += 1; print("MISMATCH", rule, trial, k, depth, best)
print("frontier checks", n, "mismatches", bad)
