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


# ---- adversarial real-valued check, independent of the solvers' level enumeration (reviewer issue experiment-repo#6)
D0 = 1e-9      # brute-force witness: "just above s" is s + D0, far below every gap of the test data (multiples of 4e-4)

def brute_strict(rule, X, i, c, rng, extra=3):
    """Per task the candidate positions are x, every rival score s > x (tie), s + D0 (strictly above s), c, plus random points in
    [x, c]; all combinations. Returns (min L1 infimum, min K, feasible) over combinations that make the target strictly first."""
    n = X.shape[1]; f = od.FIRST[rule]; best_l1 = np.inf; best_k = np.inf; axes = []
    for t in range(n):
        s = X[:, t][np.arange(len(X)) != i]
        pts = [X[i, t], c[t]] + [v for v in s if X[i, t] <= v <= c[t]] + [v + D0 for v in s if X[i, t] <= v + D0 <= c[t]]
        pts += list(rng.uniform(X[i, t], c[t], extra)) if c[t] > X[i, t] else []
        axes.append(np.unique(np.array(pts)))
    for y in itertools.product(*axes):
        y = np.array(y); Y = X.copy(); Y[i] = y
        if f(Y) == i:
            best_l1 = min(best_l1, (y - X[i]).sum()); best_k = min(best_k, int((y > X[i]).sum()))
    return best_l1, best_k

def test_strict_model_fractional_ties_and_cap_boundary():
    rng2 = np.random.default_rng(7); EP = 1e-3; checked = 0
    for rule in ["borda", "condorcet", "plurality", "copeland"]:
        for _ in range(80):
            M = int(rng2.integers(3, 6)); n = int(rng2.integers(2, 4))
            X = rng2.integers(0, 6, (M, n)) * 4e-4          # ties and gaps smaller than eps
            i = int(rng2.integers(0, M))
            c = X[i] + rng2.integers(0, 6, n) * 3e-4 + rng2.choice([0, 1e-4, 5e-5], n)   # caps off the grid, inside gaps
            l1, k = brute_strict(rule, X, i, c, rng2)
            got1 = od.MIN_INV[rule](X, i, c, EP, "L1"); gotk = od.MIN_INV[rule](X, i, c, EP, "K")
            assert np.isinf(got1) == np.isinf(l1) and np.isinf(gotk) == np.isinf(k), (rule, X, i, c, got1, l1, gotk, k)
            if np.isfinite(l1):
                n = X.shape[1]
                assert gotk == k, (rule, X, i, c, gotk, k)
                assert l1 - 1e-7 <= got1 <= l1 + n * EP + 1e-7, (rule, X, i, c, got1, l1, n)   # witness within n*eps of the infimum
                # Linf: smallest uniform raise (infimum) must make the target first at d = got + tol and not below it by more than tol
                li = od.linf_ordinal(rule, X, i, c)
                Y = X.copy(); Y[i] = np.minimum(X[i] + li + 1e-5, np.maximum(c, X[i])); assert od.FIRST[rule](Y) == i or li == 0
                checked += 1
    assert checked > 50

def test_reviewer_example():
    X = np.repeat(np.array([[0.], [.0005], [.0003]]), 6, axis=1); cap = np.full(6, .0007)
    for rule in od.MIN_INV:
        r = od.min_investment_ordinal(rule, X, 0, cap)
        assert all(np.isfinite(v) for v in r.values()), (rule, r)


def test_plurality_fractional_credits_large_M():
    """reviewer example (experiment-repo#6): 401 models, credits 1/200 and 1/201; the lead of the only useful raise is 2.5e-5."""
    a = 200; X = np.zeros((2 * a + 1, 4)); X[1:a, 0] = 1; X[a:, 1] = 1; X[0, 2] = 1; X[a, 3] = 1
    cap = np.array([1., 0., 1., 0.]); Y = X.copy(); Y[0] = cap
    assert od.plurality_first(X) != 0 and od.plurality_first(Y) == 0
    r = od.min_investment_ordinal("plurality", X, 0, cap)
    assert np.isclose(r["L1"], 1.0) and r["K"] == 1 and np.isclose(r["Linf"], 1.0, atol=1e-5), r


def test_plurality_fine_lattice_is_never_falsely_infeasible():
    """reviewer cases (experiment-repo#6): lcm of the tie-group sizes beyond what a float MILP resolves; the target is initially tied
    and any raise above the tie wins. The cap raise wins, so the solver must return the one-task witness, not infeasible or a crash."""
    for sizes in ([101, 103, 107, 109, 113], [11, 13, 17, 19, 23, 29, 31, 37]):
        X = np.zeros((max(sizes), len(sizes)))
        for t, p in enumerate(sizes): X[:p, t] = 1
        cap = np.full(len(sizes), 2.)
        r = od.min_investment_ordinal("plurality", X, 0, cap)
        assert np.isclose(r["L1"], 1e-3) and r["K"] == 1 and r["Linf"] < 1e-5, (sizes, r)


def test_plurality_cut_loop_equals_lattice():
    """the relaxation + exact check + no-good cuts path gives the same L1 and K as the integer-lattice path"""
    rng3 = np.random.default_rng(11); old = od.PLURALITY_LATTICE_MAX; n_done = 0
    for _ in range(150):
        M = int(rng3.integers(3, 30)); n = int(rng3.integers(2, 7))
        X = rng3.integers(0, 4, (M, n)).astype(float); i = int(rng3.integers(0, M)); c = X[i] + rng3.integers(0, 3, n)
        got = {}
        for lim in (old, 0):
            od.PLURALITY_LATTICE_MAX = lim
            try: got[lim] = (od.plurality_min_investment(X, i, c, 1.0, "L1"), od.plurality_min_investment(X, i, c, 1.0, "K"))
            finally: od.PLURALITY_LATTICE_MAX = old
        assert all((np.isnan(a) and np.isnan(b)) or a == b or np.isclose(a, b) for a, b in zip(got[old], got[0])), (X, i, c, got)
        n_done += 1
    assert n_done == 150
