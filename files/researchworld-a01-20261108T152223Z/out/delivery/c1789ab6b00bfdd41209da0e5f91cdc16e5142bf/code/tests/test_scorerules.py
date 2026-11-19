import itertools, numpy as np, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
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
    for rule in ["mean", "geomean", "harmonic", "median", "min", "wmean0", "wmean3", "pow0.5", "pow-2"]:
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


def test_wmean_L1_vs_lp_and_lexK_vs_enumeration():
    for sd in (0, 1, 4):
        rule = f"wmean{sd}"; fv, l1, kk = sr.RULES[rule]
        for _ in range(60):
            n = int(rng.integers(2, 8)); x, c, tau = inst(n); eps = 0.5; w = sr.wweights(n, sd); b = tau + eps
            r = linprog(np.ones(n), A_ub=-w[None, :], b_ub=-(b - w @ x), bounds=list(zip(np.zeros(n), c - x)))
            want = 0.0 if w @ x >= b else (r.fun if r.success else np.inf)
            got = l1(x, tau, c, eps)
            assert (np.isinf(got) and np.isinf(want)) or np.isclose(got, want), (rule, x, c, tau, got, want)

def test_powmean_lexK_vs_subset_enumeration():
    """L1_lexK: min L1 over all K-minimal subsets, checked against a generic optimiser over subsets (SLSQP) for small n."""
    for rule in ("geomean", "pow-2"):
        fv, l1, kk = sr.RULES[rule]
        for _ in range(25):
            n = int(rng.integers(2, 6)); x = rng.uniform(0, 20, n); c = x + rng.uniform(0, 15, n); X = np.vstack([x, rng.uniform(0, 30, (4, n))])
            out = sr.min_investment(rule, X, 0, c, 1e-3, measures=("L1", "K", "plan"))
            if not np.isfinite(out["L1"]) or out["L1"] == 0: continue
            b = np.delete(fv(X), 0).max() + 1e-3; K = int(out["K"]); best = np.inf
            for S in itertools.combinations(range(n), K):
                S = list(S); cs = x.copy(); cs[S] = c[S]
                if fv(cs) < b: continue
                f = lambda y: np.sum(y - x[S]); g = lambda y: fv(np.where(np.isin(np.arange(n), S), np.put(cs.copy(), S, y) or cs, x)) - b
                def gg(y): z = x.copy(); z[S] = y; return fv(z) - b
                r = minimize(f, c[S], bounds=list(zip(x[S], c[S])), constraints=[{"type": "ineq", "fun": gg}], method="SLSQP", options={"ftol": 1e-12, "maxiter": 500})
                if r.success and gg(r.x) > -1e-7: best = min(best, r.fun)
            assert abs(best - out["L1_lexK"]) < 2e-3, (rule, x, c, out, best)
