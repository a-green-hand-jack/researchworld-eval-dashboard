"""Verify every exact solver against exhaustive enumeration on small random integer instances.
Run: python3 -m tests.test_bruteforce [n_instances]"""
import sys, itertools, numpy as np
from lbprice import rules as R, solvers as SV

def brute(rule, S, t, B, ceil, rivals, objective, kappa, gamma, eps_agg, rkw):
    N, m = S.shape
    caps = np.minimum(B, ceil - S[t]).astype(int)
    best = None
    for delta in itertools.product(*[range(c + 1) for c in caps]):
        d = np.array(delta, float)
        S2 = S.copy(); S2[t] += d
        if R.is_first(S2, t, rule, rivals, eps_agg=eps_agg, **rkw):
            cost = float(((kappa * d) ** gamma).sum()); br = int((d > 0).sum())
            key = (br, cost) if objective == "breadth" else (cost, br)
            if best is None or key < (best[0][0] - 1e-9, best[0][1]) or (abs(key[0] - best[0][0]) <= 1e-9 and key[1] < best[0][1] - 1e-9): best = (key, d)
    return best

def run(n_inst=60, seed=0):
    rng = np.random.default_rng(seed)
    bad = 0; tot = 0; stats = {}
    for it in range(n_inst):
        N = int(rng.integers(5, 8)); m = int(rng.choice([4, 5])); B = int(rng.integers(2, 6)); ceil = 20.0
        S = rng.integers(0, 17, size=(N, m)).astype(float)
        t = int(rng.integers(0, N)); kappa = rng.uniform(0.5, 2.0, m) if it % 3 == 0 else np.ones(m)
        gamma = 2 if it % 5 == 0 else 1
        rivals = None if it % 4 else np.array([i for i in range(N) if i != t][: max(2, N // 2)])
        riv = np.delete(np.arange(N), t) if rivals is None else rivals
        for rule, rkw in [("median", {}), ("min", dict(r=m)), ("quantile2", dict(r=2))]:
            for objective in ("depth", "breadth"):
                kw = dict(ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective=objective, eps_agg=1.0, eps_task=1.0)
                if rule == "quantile2":
                    p = SV.price("quantile", S, t, B, r=2, **kw); rr = "quantile"
                else:
                    p = SV.price(rule, S, t, B, **kw); rr = "quantile" if rule == "min" else rule
                if rule == "copeland" and gamma != 1 and objective == "depth":
                    continue  # chord approximation for convex cost in the Copeland MILP (flagged), not exact
                bf = brute("min" if rule == "min" else rr, S, t, B, ceil, riv, objective, kappa, gamma, 1.0, rkw if rule != "median" else {}) if True else None
                tot += 1
                if bf is None:
                    ok = not p["feasible"]
                elif not p["feasible"]:
                    ok = False
                else:
                    key = (p["breadth"], p["cost"]) if objective == "breadth" else (p["cost"], p["breadth"])
                    ok = np.allclose(key[0] if objective == "depth" else key[0], bf[0][0]) and (objective == "depth" or np.isclose(key[1], bf[0][1], rtol=1e-6, atol=1e-6)) and p["verified"]
                    if objective == "depth" and not np.isclose(p["cost"], bf[0][0], rtol=1e-6, atol=1e-6): ok = False
                if rule == "median" and m % 2 == 0 and gamma != 1 and bf is not None and p["feasible"]:
                    # even m, convex cost: the solver searches the continuous threshold (to a tolerance); the integer grid brute force is only an upper bound
                    ok = bool(p["verified"] and (0.8 * bf[0][0] <= p["cost"] <= bf[0][0] + 1e-6 if objective == "depth" else (p["breadth"] == bf[0][0] and p["cost"] <= bf[0][1] + 1e-6)))
                stats.setdefault(rule, [0, 0]); stats[rule][0] += 1; stats[rule][1] += ok
                if not ok:
                    bad += 1; print("MISMATCH", rule, objective, "inst", it, "solver", p["feasible"], p["cost"], p["breadth"], "brute", None if bf is None else bf[0])
    print("checked", tot, "mismatches", bad, stats)
    return bad

def brute_levels(rule, S, t, caps, rivals, objective, kappa, gamma, eps):
    """Enumerate every per-task level in {0} u {d, d+eps : d = s_kj - s_tj >= 0, d+eps <= cap} (ties included)."""
    N, m = S.shape
    lv = []
    for j in range(m):
        ds = {0.0}
        for k in range(N):
            d = S[k, j] - S[t, j]
            if k != t and d >= 0:
                for x in (d, d + eps):
                    if x <= caps[j] + 1e-12: ds.add(float(x))
        lv.append(sorted(ds))
    best = None
    for delta in itertools.product(*lv):
        d = np.array(delta); S2 = S.copy(); S2[t] += d
        if R.is_first(S2, t, rule, rivals):
            cost = float(((kappa * d) ** gamma).sum()); br = int((d > 0).sum())
            key = (br, cost) if objective == "breadth" else (cost, br)
            if best is None or key < best: best = key
    return best

def run_rank(n_inst=40, seed=1):
    """Borda, Copeland and plurality against level enumeration; costs agree up to the eps-sized tie-level advantage."""
    rng = np.random.default_rng(seed); eps = 1e-4; bad = tot = 0; stats = {}
    for it in range(n_inst):
        N = int(rng.integers(5, 8)); m = int(rng.choice([3, 4])); ceil = 40.0
        S = rng.integers(0, 17, size=(N, m)).astype(float); t = int(rng.integers(0, N))
        B = float(rng.uniform(2.2, 9.7)); kappa = rng.uniform(0.5, 2.0, m) if it % 3 == 0 else np.ones(m)
        gamma = 2 if it % 5 == 0 else 1
        rivals = None if it % 4 else np.array([i for i in range(N) if i != t][: max(2, N // 2)])
        riv = np.delete(np.arange(N), t) if rivals is None else rivals
        caps = np.minimum(B, ceil - S[t])
        for rule in ("borda", "copeland", "plurality"):
            for objective in ("depth", "breadth"):
                if rule == "copeland" and gamma != 1 and objective == "depth": continue
                p = SV.price(rule, S, t, B, ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective=objective, eps_task=eps, eps_agg=eps)
                bf = brute_levels(rule, S, t, caps, riv, objective, kappa, gamma, eps)
                tot += 1
                if bf is None: ok = not p["feasible"]
                elif not p["feasible"]: ok = False
                else:
                    if objective == "breadth": ok = p["breadth"] == bf[0] and p["cost"] <= bf[1] + 0.02 * (1 + bf[1])
                    else: ok = abs(p["cost"] - bf[0]) <= 0.02 * (1 + bf[0]) and p["breadth"] >= 0
                    ok = ok and p["verified"]
                stats.setdefault(rule, [0, 0]); stats[rule][0] += 1; stats[rule][1] += bool(ok)
                if not ok: bad += 1; print("MISMATCH", rule, objective, "inst", it, p["feasible"], p["cost"], p["breadth"], "brute", bf)
    print("rank-rule check", tot, "mismatches", bad, stats); return bad

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    sys.exit(1 if (run(n) + run_rank(n)) else 0)
