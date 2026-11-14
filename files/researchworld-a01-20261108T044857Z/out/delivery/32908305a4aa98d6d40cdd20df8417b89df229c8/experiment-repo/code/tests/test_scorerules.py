import itertools, numpy as np, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from scipy.optimize import linprog, minimize
from mti import scorerules as sr

rng = np.random.default_rng(0)

def brute_K(fv, x, c, b):
    n = len(x)
    for k in range(n + 1):
        for S in itertools.combinations(range(n), k):
            y = x.copy(); y[list(S)] = c[list(S)]
            if fv(y) >= b - 1e-12: return k
    return np.inf

def brute_L1_grid(fv, x, c, b, step):
    n = len(x); axes = [np.arange(x[t], c[t] + 1e-9, step) for t in range(n)]
    best = np.inf
    for y in itertools.product(*axes):
        y = np.array(y)
        if fv(y) >= b - 1e-12: best = min(best, (y - x).sum())
    return best

def inst(n, hi=6):
    x = rng.integers(0, hi, n).astype(float); c = x + rng.integers(0, 5, n)
    tau = float(rng.integers(2, hi + 2)); return x, c, tau

def test_K_all_rules():
    for rule in ["mean", "geomean", "harmonic", "median", "min"]:
        fv, l1, kk = sr.RULES[rule]
        for _ in range(150):
            n = int(rng.integers(2, 8)); x, c, tau = inst(n); eps = 1.0
            assert kk(x, tau, c, eps) == brute_K(fv, x, c, tau + eps), (rule, x, c, tau)

def test_L1_grid_median_min():
    for rule, step in [("median", 0.5), ("min", 0.5)]:
        fv, l1, kk = sr.RULES[rule]
        for _ in range(120):
            n = int(rng.integers(2, 6)); x, c, tau = inst(n); eps = 1.0
            got = l1(x, tau, c, eps); want = brute_L1_grid(fv, x, c, tau + eps, step)
            assert np.isclose(got, want), (rule, x, c, tau, got, want)

def test_L1_mean_lp():
    for _ in range(100):
        n = int(rng.integers(2, 8)); x, c, tau = inst(n); eps = 0.7
        r = linprog(np.ones(n), A_ub=[-np.ones(n)], b_ub=[-(n * (tau + eps))], bounds=list(zip(x, c)))
        want = (r.fun - x.sum()) if r.success else np.inf
        want = max(want, 0) if np.isfinite(want) else want
        assert np.isclose(sr.mean_L1(x, tau, c, eps), want), (x, c, tau)

def test_L1_powmean_convex():
    for p in [0.0, -1.0]:
        for _ in range(40):
            n = int(rng.integers(2, 6)); x, c, tau = inst(n); eps = 0.5
            fv = lambda Y: sr.powmean_v(Y, p)
            got = sr.powmean_L1(x, tau, c, eps, p=p)
            if fv(x) >= tau + eps: assert got == 0; continue
            if fv(c) < tau + eps: assert got == np.inf; continue
            cons = {"type": "ineq", "fun": lambda y: fv(y) - (tau + eps)}
            best = np.inf
            for st in [c.copy(), (x + c) / 2, np.maximum(x, tau + eps)]:
                st = np.clip(st, x, c)
                r = minimize(lambda y: (y - x).sum(), st, bounds=list(zip(x, c)), constraints=[cons], method="SLSQP", options={"ftol": 1e-12, "maxiter": 500})
                if r.success and fv(r.x) >= tau + eps - 1e-6: best = min(best, r.fun + x.sum() - x.sum())
            assert got <= best + 1e-4 and got >= best - 1e-3, (p, x, c, tau, got, best)

def test_median_even_lp():
    for _ in range(150):
        n = int(rng.choice([2, 4, 6])); x, c, tau = inst(n); eps = 0.6; b = tau + eps; h = n // 2
        # independent LP over assignments (A of size h, extra e)
        best = np.inf
        for A in itertools.combinations(range(n), h):
            for e in range(n):
                if e in A: continue
                # vars: y(n), a, bb ; min sum y ; y_t>=a (A), y_e>=bb, a+bb>=2b, a>=bb
                N = n + 2; cost = np.r_[np.ones(n), 0, 0]
                Aub, bub = [], []
                for t in A: r = np.zeros(N); r[N - 2] = 1; r[t] = -1; Aub.append(r); bub.append(0)
                r = np.zeros(N); r[N - 1] = 1; r[e] = -1; Aub.append(r); bub.append(0)
                r = np.zeros(N); r[N - 2] = -1; r[N - 1] = -1; Aub.append(r); bub.append(-2 * b)
                r = np.zeros(N); r[N - 1] = 1; r[N - 2] = -1; Aub.append(r); bub.append(0)
                res = linprog(cost, A_ub=Aub, b_ub=bub, bounds=list(zip(x, c)) + [(-50, 50)] * 2)
                if res.success: best = min(best, res.fun - x.sum())
        got = sr.median_L1(x, tau, c, eps)
        if np.median(x) >= b: best = 0
        assert np.isclose(got, best, atol=1e-6) or (np.isinf(got) and np.isinf(best)), (x, c, tau, got, best)

def test_trimmed_milp_vs_grid():
    for _ in range(25):
        n = 5; t = 1; x, c, tau = inst(n, 5); eps = 1.0
        fv = lambda Y: sr.trimmed_v(Y, t)
        got = sr.trimmed_L1_milp(x, tau, c, eps, t)
        want = brute_L1_grid(fv, x, c, tau + eps, 0.5)
        assert np.isclose(got, want, atol=1e-4) or (np.isinf(got) and np.isinf(want)) or got <= want + 1e-6, (x, c, tau, got, want)

def test_trimmed_lp_vs_milp_and_K():
    import itertools
    for _ in range(25):
        n = 5; t = 1; x, c, tau = inst(n, 5); eps = 1.0
        a = sr.trimmed_L1_lp(x, tau, c, eps, t); b = sr.trimmed_L1_milp(x, tau, c, eps, t)
        assert (np.isinf(a) and np.isinf(b)) or np.isclose(a, b, atol=1e-5), (x, c, tau, a, b)
        fv = lambda Y: sr.trimmed_v(Y, t)
        assert sr.trimmed_K_enum(x, tau, c, eps, t) == brute_K(fv, x, c, tau + eps)

def test_L2_vs_slsqp():
    for rule in ["mean", "min", "median"]:
        for _ in range(40):
            n = int(rng.choice([3, 5])); x, c, tau = inst(n); eps = 0.5
            fv = sr.RULES[rule][0]; got = sr.L2_RULES[rule](x, tau, c, eps)
            if fv(x) >= tau + eps: assert got == 0; continue
            if fv(c) < tau + eps: assert got == np.inf; continue
            best = np.inf
            if rule == "median":   # enumerate which m tasks, convex QP via SLSQP per subset
                m = (n + 1) // 2
                for S in itertools.combinations(range(n), m):
                    y = x.copy()
                    for t in S: y[t] = max(x[t], tau + eps)
                    if (y[list(S)] <= c[list(S)] + 1e-12).all() and fv(y) >= tau + eps - 1e-12: best = min(best, ((y - x) ** 2).sum())
            else:
                cons = {"type": "ineq", "fun": lambda y: fv(y) - (tau + eps)} if rule == "mean" else None
                if rule == "min": best = ((np.maximum(x, tau + eps) - x) ** 2).sum()
                else:
                    r = minimize(lambda y: ((y - x) ** 2).sum(), np.clip(x + 1, x, c), bounds=list(zip(x, c)), constraints=[cons], method="SLSQP", options={"ftol": 1e-13, "maxiter": 500})
                    best = r.fun
            assert abs(got - best) < 1e-4 * max(1, best), (rule, x, c, tau, got, best)


def test_weighted_mean_vs_lp():
    from scipy.optimize import linprog, milp, LinearConstraint, Bounds
    from mti import weighted as wt
    rng = np.random.default_rng(5)
    for _ in range(80):
        M, n = 4, int(rng.integers(2, 7)); X = rng.uniform(0, 80, (M, n)); i = int(rng.integers(M))
        c = np.minimum(X[i] + rng.uniform(0, 40, n), 100); w = rng.dirichlet(np.ones(n))
        V = X @ w; tau = np.delete(V, i).max(); L1, K = wt.weighted_min_investment(X, i, c, w, 1e-3)
        if V[i] > tau: assert (L1, K) == (0.0, 0); continue
        r = linprog(np.ones(n), A_ub=-w[None, :], b_ub=[-(tau + 1e-3 - V[i])], bounds=list(zip(np.zeros(n), c - X[i])), method="highs")
        if r.status != 0: assert np.isinf(L1); continue
        assert np.isclose(L1, r.fun, atol=1e-8)
        # K by MILP: y_t - x_t <= h_t r_t
        h = c - X[i]; A1 = np.hstack([w[None, :], np.zeros((1, n))]); A2 = np.hstack([np.eye(n), -np.diag(h)])
        m = milp(np.r_[np.zeros(n), np.ones(n)], constraints=[LinearConstraint(A1, tau + 1e-3 - V[i], np.inf), LinearConstraint(A2, -np.inf, 0)],
                 integrality=np.r_[np.zeros(n), np.ones(n)], bounds=Bounds(np.zeros(2 * n), np.r_[h, np.ones(n)]))
        assert K == round(m.fun)
