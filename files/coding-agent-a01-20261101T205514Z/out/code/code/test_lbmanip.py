"""Brute-force verification of the exact solvers in lbmanip on tiny random instances.

Semantics used by the brute force: the target gets an infinitesimal bonus EPS on every task (the
epsilon -> 0 limit used by the solvers), and may be raised by any amount up to the cap.
Two regimes: continuous scores (no ties; depth and breadth checked) and integer scores with many
ties (depth checked; breadth is only compared when ties cannot matter).
"""
import itertools, sys
import numpy as np
from scipy.optimize import linprog
import lbmanip as L

EPS = 1e-7


def first_eps(rule, S, t, d_full):
    S2 = np.array(S, float); S2[t] = S2[t] + d_full + EPS
    return L.is_first(rule, S2, t, tol=0.0)


def brute_breadth(rule, S, t, u):
    m = S.shape[1]
    for k in range(m + 1):
        for sub in itertools.combinations(range(m), k):
            d = np.zeros(m); d[list(sub)] = u[list(sub)]
            if first_eps(rule, S, t, d): return k
    return np.inf


def brute_depth(rule, S, t, u, cands):
    best = np.inf
    for combo in itertools.product(*cands):
        c = sum(combo)
        if c < best and first_eps(rule, S, t, np.array(combo)): best = c
    return best


def depth_candidates(rule, S, t, u, ties):
    N, m = S.shape
    cands = []
    for j in range(m):
        base = {0.0, float(u[j])}
        if rule in ('borda', 'copeland', 'plurality'):
            base |= {S[i, j] - S[t, j] for i in range(N) if i != t and 0 <= S[i, j] - S[t, j] <= u[j]}
        else:  # threshold-type aggregates: tau - s_tj where tau is a score of some model (or an aggregate)
            base |= {x - S[t, j] for x in S.reshape(-1) if 0 <= x - S[t, j] <= u[j]}
            if ties:
                base |= set(float(a) for a in range(int(u[j]) + 1))
        cands.append(sorted(base))
    return cands


def run(n_trials, seed, ties):
    rng = np.random.default_rng(seed)
    bad = 0
    stats = {r: 0 for r in L.ALL_RULES}
    for trial in range(n_trials):
        N = int(rng.integers(3, 7)); m = int(rng.integers(2, 5))
        if ties:
            S = rng.integers(1, 10, size=(N, m)).astype(float); u = rng.integers(0, 6, size=m).astype(float)
        else:
            S = np.round(rng.uniform(1, 10, size=(N, m)), 3); u = np.round(rng.uniform(0, 6, size=m), 3)
        t = int(rng.integers(0, N))
        for rule in L.ALL_RULES:
            res = L.min_investment(rule, S, t, u)
            msgs = []
            # ---- feasibility / plan validity
            if np.isfinite(res['depth']) and not res['already']:
                if not L.verify_plan(rule, S, t, res['delta']):
                    msgs.append('plan does not make target first')
                if (res['delta'] > u + 1e-9).any(): msgs.append('plan exceeds cap')
            # ---- depth
            if rule in ('geo', 'harm'):
                if np.isfinite(res['depth']):
                    cands = [sorted(set(np.arange(0, u[j] + 1e-9, 0.25)) | {float(u[j])}) for j in range(m)]
                    bd = brute_depth(rule, S, t, u, cands) if m <= 3 else None
                    if bd is not None and not (bd >= res['depth'] - 1e-6 and bd - res['depth'] <= 0.25 * m + 1e-6):
                        msgs.append(f'concave-mean depth {res["depth"]} vs grid {bd}')
                else:
                    if first_eps(rule, S, t, u): msgs.append('declared infeasible but feasible')
            elif rule == 'mean' and not ties:
                tau, _ = L._tau('mean', S, t)
                if not res['already'] and np.isfinite(res['depth']):
                    lp = linprog(np.ones(m), A_ub=[-np.ones(m) / m], b_ub=[-(tau - S[t].mean())], bounds=[(0, x) for x in u])
                    if abs(lp.fun - res['depth']) > 1e-7: msgs.append(f'mean depth {res["depth"]} vs LP {lp.fun}')
                elif not np.isfinite(res['depth']) and first_eps(rule, S, t, u):
                    msgs.append('declared infeasible but feasible')
            else:
                bd = brute_depth(rule, S, t, u, depth_candidates(rule, S, t, u, ties))
                if not ((np.isinf(bd) and np.isinf(res['depth'])) or abs(bd - res['depth']) < 1e-5):
                    msgs.append(f'depth {res["depth"]} vs brute {bd}')
            # ---- breadth
            if not ties:
                bb = brute_breadth(rule, S, t, u)
                if not ((np.isinf(bb) and np.isinf(res['breadth'])) or bb == res['breadth']):
                    msgs.append(f'breadth {res["breadth"]} vs brute {bb}')
            stats[rule] += 1
            if msgs:
                bad += 1
                print('MISMATCH', rule, 'ties' if ties else 'cont', 'trial', trial, msgs)
                print(S.tolist(), t, u.tolist())
    print('ties' if ties else 'continuous', 'trials', n_trials, 'mismatches', bad, stats)
    return bad


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    bad = run(n, 0, False) + run(n, 1, True)
    sys.exit(1 if bad else 0)
