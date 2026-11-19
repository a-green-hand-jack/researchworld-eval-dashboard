"""Mean-family solver vs scipy linprog (depth) and subset enumeration (breadth)."""
import itertools, numpy as np
from scipy.optimize import linprog
from lbprice import rules as R, solvers as SV
rng = np.random.default_rng(5); bad = 0; n = 0
for it in range(200):
    N, m = int(rng.integers(5, 9)), int(rng.integers(3, 8)); S = rng.uniform(0, 90, (N, m)); t = int(rng.integers(0, N))
    B = float(rng.uniform(2, 30)); kappa = rng.uniform(0.5, 2, m); rule = ["mean", "zmean"][it % 2]
    p = SV.price(rule, S, t, B, ceil=100.0, kappa=kappa, gamma=1)
    A = R.scores(S, rule); V = np.delete(A, t).max() + SV.EPS_AGG; w = np.ones(m) / m if rule == "mean" else 1 / (m * S.std(axis=0))
    caps = np.minimum(B, 100 - S[t]); G = V - A[t]
    if G <= 0: ok = p["cost"] == 0
    else:
        lp = linprog(kappa, A_ub=[-w], b_ub=[-G], bounds=list(zip(np.zeros(m), caps)))
        ok = (lp.status != 0 and not p["feasible"]) or (lp.status == 0 and p["feasible"] and abs(lp.fun - p["cost"]) < 1e-7 and p["verified"])
        pb = SV.price(rule, S, t, B, ceil=100.0, kappa=kappa, gamma=1, objective="breadth")
        kmin = next((k for k in range(1, m + 1) if any((w[list(c)] * caps[list(c)]).sum() >= G - 1e-9 for c in itertools.combinations(range(m), k))), None)
        ok = ok and ((kmin is None and not pb["feasible"]) or (pb["breadth"] == kmin and pb["verified"]))
    n += 1; bad += (not ok)
    if not ok: print("MISMATCH", it, rule)
# gamma = 2 water-filling vs scipy minimize
from scipy.optimize import minimize
for it in range(30):
    N, m = 6, 5; S = rng.uniform(0, 90, (N, m)); t = int(rng.integers(0, N)); B = 25.0; kappa = rng.uniform(0.5, 2, m)
    p = SV.price("mean", S, t, B, ceil=100.0, kappa=kappa, gamma=2)
    A = S.mean(1); G = np.delete(A, t).max() + SV.EPS_AGG - A[t]
    if G <= 0 or not p["feasible"]: continue
    caps = np.minimum(B, 100 - S[t])
    r = minimize(lambda d: ((kappa * d) ** 2).sum(), x0=caps * 0.5, bounds=list(zip(np.zeros(m), caps)), constraints=[dict(type="ineq", fun=lambda d: d.mean() - G)], method="SLSQP")
    n += 1
    if abs(r.fun - p["cost"]) > 1e-4 * (1 + r.fun): bad += 1; print("gamma2 MISMATCH", r.fun, p["cost"])
print("mean-family checks", n, "mismatches", bad)
