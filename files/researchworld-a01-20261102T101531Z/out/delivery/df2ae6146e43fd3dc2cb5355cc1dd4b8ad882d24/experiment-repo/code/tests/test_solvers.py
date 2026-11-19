import sys, numpy as np
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lbattack import rules as R, solvers as V

def run(seed=0, trials=300):
    rng = np.random.default_rng(seed)
    bad = 0; tot = 0
    for _ in range(trials):
        m = int(rng.integers(3, 9)); n = int(rng.integers(2, 8))
        base = rng.normal(50, 15, size=(m, 1)); S = np.clip(base + rng.normal(0, 12, (m, n)), 0, 100).round(0)
        t = int(rng.integers(m)); delta = float(rng.choice([5, 15, 40, 100]))
        for rule in R.RULES:
            if rule == "median" and n % 2 == 0:
                pass
            a = V.min_k(S, t, rule, delta); b = V._enum_min_k(S, t, rule, delta)
            tot += 1
            if a != b:
                bad += 1; print("MISMATCH", rule, a, b, n, m, delta)
    print("checked", tot, "mismatches", bad)
    return bad

def run_l1(seed=1, trials=200):
    """l1 cost vs. brute-force LP/grid: boost inf-cost must make t first and
    cost-eps must not."""
    rng = np.random.default_rng(seed); bad = 0
    for _ in range(trials):
        m = int(rng.integers(3, 9)); n = int(rng.choice([3, 5, 7]))
        S = np.clip(rng.normal(50, 15, (m, 1)) + rng.normal(0, 12, (m, n)), 0, 99)
        t = int(rng.integers(m))
        for rule in ["mean", "geo", "median", "min"]:
            c = V.l1_cost(S, t, rule)
            if c == 0 or c == V.INF: continue
            # random search for a cheaper feasible allocation must fail
            for _ in range(200):
                x = rng.dirichlet(np.ones(n)) * c * 0.995
                S2 = S.copy(); S2[t] = np.minimum(S2[t] + x, 100)
                if R.is_first(S2, t, rule): bad += 1; print("CHEAPER", rule); break
            # constructive upper bound: verify via greedy: a feasible allocation at cost c(1+1e-6)
            S2 = S.copy(); s = S[t]; cc = V._threshold(S, t, rule)
            if rule == "mean": S2[t] = s + (c * 1.000001) / n
            elif rule == "min": S2[t] = np.maximum(s, cc + 1e-6)
            elif rule == "median":
                need = (n + 1) // 2; idx = np.argsort(np.maximum(cc - s, 0))[:need]; S2[t, idx] = np.maximum(s[idx], cc + 1e-6)
            elif rule == "geo":
                S2[t] = np.maximum(s, 0); 
                lo_, hi_ = s.min(), 100.
                for _ in range(100):
                    L = (lo_ + hi_) / 2
                    if np.log(np.maximum(s, L) + 1).sum() >= n * np.log(cc + 1): hi_ = L
                    else: lo_ = L
                S2[t] = np.maximum(s, hi_ + 1e-6)
            if not R.is_first(S2, t, rule): bad += 1; print("INFEASIBLE", rule, c)
    print("l1 mismatches", bad)
    return bad

def run_milp_vs_enum(seed=3, trials=400):
    rng = np.random.default_rng(seed); bad = 0
    for _ in range(trials):
        m = int(rng.integers(3, 30)); n = int(rng.integers(2, 9))
        S = np.clip(rng.normal(50, 15, (m, 1)) + rng.normal(0, 12, (m, n)), 0, 100).round(0)
        t = int(rng.integers(m)); d = float(rng.choice([5, 15, 40, 100]))
        for rule in R.ORDINAL:
            a = V.min_k_ordinal(S, t, rule, d, 100.0, enum_max=0); b = V.min_k_ordinal(S, t, rule, d, 100.0)
            if a != b: bad += 1; print("MILP!=ENUM", rule, a, b)
    print("milp-vs-enum mismatches", bad); return bad



def run_new(seed=21, trials=300):
    """pmean / trim / copeland vs brute force; closed forms (enum_max=0) vs enumeration;
    trim greedy gap statistics (greedy is an upper bound)."""
    rng = np.random.default_rng(seed); bad = 0; greedy_gap = []; tot = 0
    rules = R.CARDINAL_POWER + ["trim", "copeland"]
    for _ in range(trials):
        m = int(rng.integers(3, 12)); n = int(rng.integers(3, 10))
        S = np.clip(rng.normal(50, 15, (m, 1)) + rng.normal(0, 12, (m, n)), 0, 100).round(0)
        t = int(rng.integers(m)); d = float(rng.choice([5, 15, 40, 100]))
        for rule in rules:
            ref = V._enum_min_k(S, t, rule, d)
            a = V.min_k(S, t, rule, d); tot += 1
            if a != ref: bad += 1; print("MISMATCH(enum path)", rule, a, ref)
            if rule == "copeland":
                a2 = V.min_k(S, t, rule, d, enum_max=0)
            elif rule == "trim":
                a2 = V.min_k(S, t, rule, d, enum_max=0)
                if a2 != V.INF and ref != V.INF: greedy_gap.append(a2 - ref)
                if (a2 == V.INF) != (ref == V.INF): bad += 1; print("TRIM feasibility mismatch")
                continue
            else:
                a2 = V.min_k(S, t, rule, d, enum_max=0)
            if a2 != ref: bad += 1; print("MISMATCH(closed/milp)", rule, a2, ref)
    print("new-rule checks", tot, "mismatches", bad, "| trim greedy excess over exact: mean %.3f max %d (n=%d)" % (np.mean(greedy_gap), max(greedy_gap), len(greedy_gap)))
    return bad

def run_gmin(seed=5, trials=150):
    """g_min vs. a generic NLP solver (SLSQP) and vs. feasibility of the returned bound."""
    from scipy.optimize import minimize
    rng = np.random.default_rng(seed); bad = 0; tot = 0
    for _ in range(trials):
        m = int(rng.integers(3, 8)); n = int(rng.choice([3, 5, 7]))
        S = np.clip(rng.normal(50, 15, (m, 1)) + rng.normal(0, 12, (m, n)), 0, 99)
        t = int(rng.integers(m)); u = rng.uniform(5, 60, n); w = rng.choice([1.0, 1 / rng.uniform(5, 60)], n)
        for rule in ["mean", "geo", "pmean:0.5", "pmean:-1", "min", "median"]:
            g = V.g_min(S, t, rule, u, w); tot += 1
            c = V._threshold(S, t, rule)
            if g == 0 or g == V.INF or np.isnan(g): continue
            # NLP reference (convex for these rules except median/min which are checked constructively)
            f = lambda x: R.scores((S[t] + x)[None, :], rule)[0] - c
            best = np.inf
            for _ in range(8):
                x0 = rng.uniform(0, 1, n) * u
                r = minimize(lambda x: (w * x).sum(), x0, constraints=[{"type": "ineq", "fun": f}], bounds=[(0, ui) for ui in u], method="SLSQP", options={"maxiter": 300})
                if r.success and f(r.x) > -1e-6: best = min(best, r.fun)
            if rule in ("mean", "geo", "pmean:0.5", "pmean:-1") and best < g - 1e-4 * max(1, g):
                bad += 1; print("GMIN WORSE THAN NLP", rule, g, best)
            if g > best + 1e-3 * max(1, best) and rule in ("mean", "geo", "pmean:0.5", "pmean:-1") and best < np.inf:
                bad += 1; print("GMIN ABOVE NLP", rule, g, best)
    print("g_min checks", tot, "bad", bad); return bad


def run_gmin_bruteforce(seed=6, trials=400):
    """g_min of the median (odd n) and min vs. enumeration of the tasks raised to the threshold, and the returned plan re-checked with the reference rule."""
    import itertools
    rng = np.random.default_rng(seed); bad = 0; tot = 0
    for _ in range(trials):
        m = int(rng.integers(3, 9)); n = int(rng.choice([3, 5, 7, 9]))
        S = np.clip(rng.normal(50, 15, (m, 1)) + rng.normal(0, 12, (m, n)), 0, 99).round(int(rng.choice([0, 1, 3])))
        t = int(rng.integers(m)); u = rng.uniform(1, 60, n) if rng.random() < 0.7 else np.full(n, 100.0); w = rng.choice([1.0, 1 / rng.uniform(5, 60)], n)
        for rule in ["median", "min"]:
            g = V.g_min(S, t, rule, u, w); c = V._threshold(S, t, rule); s = S[t]; tot += 1
            if rule == "min":
                x = np.maximum(c - s, 0.0); ref = float((w * x).sum()) if np.all(x <= u + 1e-12) else np.inf
            else:
                need = (n + 1) // 2; best = np.inf
                for k in range(n + 1):
                    for T in itertools.combinations(range(n), k):
                        x = np.zeros(n); x[list(T)] = np.maximum(c - s[list(T)], 0.0)
                        if np.any(x > u + 1e-12): continue
                        if np.sum(s + x >= c - 1e-9) >= need: best = min(best, (w * x).sum())
                ref = 0.0 if R.scores(S[t][None, :], rule)[0] > c else best
            if not (np.isclose(g, ref, rtol=1e-9, atol=1e-9) or (np.isinf(g) and np.isinf(ref))): bad += 1; print("GMIN-BF MISMATCH", rule, n, g, ref)
    print("g_min brute-force checks", tot, "bad", bad); return bad


def run_median_even(seed=5, trials=400):
    """median, n even (closed form via the two middle order statistics) vs brute force, closed-form path forced."""
    rng = np.random.default_rng(seed); bad = 0
    for i in range(trials):
        m = int(rng.integers(3, 12)); n = int(rng.choice([4, 6, 8, 10])); S = np.clip(rng.normal(50, 15, (m, 1)) + rng.normal(0, 12, (m, n)), 0, 100).round(0)
        t = int(rng.integers(m)); d = float(rng.choice([5, 15, 40, 100, np.inf])); hi = 100.0 if i % 2 else np.minimum(100, S.max(0) + 1)
        a = V.min_k(S, t, "median", d, hi, enum_max=0); b = V._enum_min_k(S, t, "median", d, hi)
        if a != b: bad += 1; print("MEDIAN-EVEN MISMATCH", n, a, b)
        if np.isfinite(a) and a > 0:
            k, T = V.min_k(S, t, "median", d, hi, enum_max=0, return_set=True); S2 = S.copy(); S2[t, T] = V._boost(S[t], d, hi)[T]
            if not R.is_first(S2, t, "median"): bad += 1; print("INVALID SET")
    print("median-even mismatches", bad); return bad


if __name__ == "__main__":
    b = run() + run_l1() + run_milp_vs_enum() + run_new() + run_gmin() + run_gmin_bruteforce() + run_median_even()
    sys.exit(1 if b else 0)
