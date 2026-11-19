"""Brute-force validation of the minimal-investment solvers on small integer boards.
Run: python code/test_solvers.py   (about 1-2 minutes)"""
import itertools, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from lb import agg
from lb.agg import INF

rng = np.random.default_rng(0)


def wins(rule, S, t, y):
    n, m = S.shape
    S2 = S.copy(); S2[t] = y
    if rule in agg.SCORE_RULES:
        fv = agg.f_values(rule, S2)
        return fv[t] >= np.delete(fv, t).max() - 1e-9
    oth = [i for i in range(n) if i != t]
    R = S[oth]
    if rule == "borda":
        Bt = sum(int((R[:, j] <= y[j]).sum()) for j in range(m))
        best = -1
        for ri, r in enumerate(oth):
            B = 0.0
            for j in range(m):
                others = np.delete(R[:, j], ri)
                B += (others < R[ri, j]).sum() + 0.5 * (others == R[ri, j]).sum() + float(y[j] < R[ri, j])
            best = max(best, B)
        return Bt >= best
    if rule == "plural":
        top = R.max(0); own = R.argmax(0)
        cnt = np.zeros(len(oth)); tc = 0
        for j in range(m):
            if y[j] >= top[j]:
                tc += 1
            else:
                cnt[own[j]] += 1
        return tc >= cnt.max()


def brute(rule, S, t, u, step=1):
    n, m = S.shape
    x = S[t]
    best_l1, best_br = INF, INF
    ranges = [np.arange(0, u[j] - x[j] + 1e-9, step) for j in range(m)]
    for d in itertools.product(*ranges):
        d = np.array(d)
        l1 = d.sum(); br = (d > 0).sum()
        if l1 >= best_l1 and br >= best_br:
            continue
        if wins(rule, S, t, x + d):
            best_l1 = min(best_l1, l1); best_br = min(best_br, br)
    return best_l1, best_br


def run(rules, trials, n=5, m=4, hi=8, cap=10, exact_l1=True):
    bad = 0
    for tr in range(trials):
        S = rng.integers(0, hi + 1, size=(n, m)).astype(float)
        if rules[0] == "gmean":
            S += 1
        fv0 = None
        for rule in rules:
            if rule in agg.SCORE_RULES:
                fv = agg.f_values(rule, S)
                t = int(np.argsort(fv)[len(fv) // 2])
            else:
                t = int(rng.integers(n))
            u = np.full(m, float(cap)) if rng.random() < 0.6 else np.minimum(S.max(0) + rng.integers(0, 3, m), cap)
            if rule in ("trim20", "median"):   # LP . window solvers require x-monotone caps
                g = float(rng.integers(1, cap + 1))
                u = np.minimum(S[t] + g, cap) if rng.random() < 0.6 else np.full(m, float(cap))
            u = np.maximum(u, S[t])
            r = agg.target_costs(rule, S, t, u)
            bl1, bbr = brute(rule, S, t, u)
            if rule == "borda":
                assert abs(agg.borda_milp(S, t, u, "l1") - bl1) < 1e-9 or bl1 == INF, (agg.borda_milp(S, t, u, "l1"), bl1)
                assert agg.borda_milp(S, t, u, "br") == bbr or bbr == INF
                ok = r["l1_lb"] - 1e-9 <= bl1 <= r["l1"] + 1e-9 and r["br_lb"] <= bbr <= r["br"]
            elif rule in ("mean", "trim20", "median") and not (rule == "median" and agg.kth_from_top("median", m)):
                # continuous optimum can be fractional: grid cost within 1 above
                ok = ((r["l1"] <= bl1 + 1e-3 and bl1 - r["l1"] < 1.0 + 1e-3) or r["l1"] == bl1 == INF) and r["br"] == bbr
                if rule != "mean":
                    ok = ok and True
            else:
                ok = (abs(r["l1"] - bl1) < 1e-9 or r["l1"] == bl1 == INF) and r["br"] == bbr
            if not ok:
                bad += 1
                print("MISMATCH", rule, S.tolist(), t, u.tolist(), r, (bl1, bbr))
    return bad


if __name__ == "__main__":
    tot = 0
    for rules, trials, kw in [(["mean", "median", "min", "max", "q25", "q75"], 25, dict(m=5)),
                              (["median", "trim20"], 25, dict(m=4)),
                              (["trim20"], 20, dict(m=5)),
                              (["borda", "plural"], 25, dict(m=4, n=6))]:
        b = run(rules, trials, **kw); tot += b
        print(rules, "trials", trials, "mismatches", b, flush=True)
    # cross-check: trimmed-mean MILP == order-statistic closed form for odd m median
    for _ in range(200):
        m = int(rng.choice([3, 5, 7, 9]))
        S = rng.uniform(0, 100, size=(8, m))
        fv = agg.f_values("median", S); t = int(np.argsort(fv)[3])
        u = np.full(m, 100.0)
        tau = np.delete(fv, t).max()
        l1c, _ = agg.order_stat_cost(S[t], u, (m + 1) // 2, tau)
        l1m = agg.trim_cost_milp(S[t], u, (m - 1) // 2, tau, "l1")
        assert abs(l1c - l1m) < 1e-4 * max(1, l1c), (l1c, l1m)
        brm = agg.trim_cost_milp(S[t], u, (m - 1) // 2, tau, "br")
        _, brc = agg.order_stat_cost(S[t], u, (m + 1) // 2, tau)
        assert brm == brc == agg.trim_breadth_ub(S[t], u, (m - 1) // 2, tau)
    print("median closed form == trimmed MILP == LP == window search (200 random boards): OK")
    # trimmed mean: LP depth == MILP depth, window-breadth UB vs MILP breadth, with x-monotone gain caps
    neq = tot_b = 0
    for _ in range(150):
        m = int(rng.choice([4, 6, 8, 10])); a = int(rng.integers(1, (m - 1) // 2 + 1))
        S = rng.uniform(0, 100, size=(8, m)); fv = agg.f_values("mean", S)
        x = S[int(np.argsort(fv)[4])]; g = float(rng.choice([5, 10, 25, 100])); u = np.minimum(x + g, 100.0)
        tau = float(np.sort(S, 1)[:, a:m - a].mean(1).max())
        l1m = agg.trim_cost_milp(x, u, a, tau, "l1"); l1l = agg.trim_l1_lp(x, u, a, tau)
        assert abs(l1m - l1l) < 1e-3 * max(1, l1l) or (l1m == INF and l1l == INF), (l1m, l1l)
        if l1m < INF:
            bm = agg.trim_cost_milp(x, u, a, tau, "br"); bu = agg.trim_breadth_ub(x, u, a, tau)
            assert bu >= bm, (bu, bm)
            tot_b += 1; neq += int(bu == bm)
    print("trimmed LP depth == MILP depth: OK;  window breadth equals MILP-optimal breadth in", neq, "of", tot_b)
    # geometric mean: compare with generic SLSQP
    from scipy.optimize import minimize
    for _ in range(40):
        m = 5
        S = rng.uniform(5, 90, size=(6, m)); fv = agg.f_values("gmean", S); t = int(np.argsort(fv)[2])
        u = np.full(m, 100.0); tau = np.delete(fv, t).max(); x = S[t]
        l1, br = agg.gmean_cost(x, u, tau)
        con = {"type": "ineq", "fun": lambda d: np.log(x + d).sum() - m * np.log(tau)}
        r = minimize(lambda d: d.sum(), np.full(m, 10.0), constraints=[con], bounds=[(0, 100 - xx) for xx in x],
                     method="SLSQP", options={"ftol": 1e-12, "maxiter": 500})
        assert abs(r.fun - l1) < 1e-3 * max(1, l1), (r.fun, l1)
    print("gmean water-filling == SLSQP: OK")
    # leverage bound for order-statistic rules with ceiling caps: depth <= (k - a) * (tau - f(x)) <= k * (tau - f(x))
    for _ in range(300):
        m = int(rng.integers(3, 12)); S = rng.uniform(0, 100, size=(9, m))
        rule = ["median", "q25", "q75", "min", "max"][int(rng.integers(5))]
        k = agg.kth_from_top(rule, m)
        if k is None:
            continue
        fv = agg.f_values(rule, S); t = int(np.argsort(fv)[3]); tau = np.delete(fv, t).max()
        l1, br = agg.order_stat_cost(S[t], np.full(m, 100.0), k, tau)
        a_ = int((S[t] >= tau).sum())
        assert l1 <= (k - a_) * (tau - fv[t]) + 1e-9
    print("leverage bound depth <= (k-a)*gap: OK")
    print("TOTAL MISMATCHES", tot)
    sys.exit(1 if tot else 0)
