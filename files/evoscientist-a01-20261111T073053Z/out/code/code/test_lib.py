"""Exactness tests: cardinal closed-form solvers vs brute force; ordinal MILPs vs brute force; solution verification."""
import itertools, numpy as np, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
rng = np.random.default_rng(0)

def agg_brute(rule, x):
    if rule == 'mean': return x.mean()
    if rule == 'min': return x.min()
    if rule == 'median': return np.median(x)
    if rule == 'geo': return power_mean(x[None], 0.0)[0]
    if rule == 'harm': return power_mean(x[None], -1.0)[0]

def brute_cardinal(a, S_riv, rule, g, ub, step):
    n = len(a); T = max(agg_brute(rule, r) for r in S_riv)
    best = [np.inf, np.inf]
    grids = [np.arange(0, min(g, ub - aj) + 1e-9, step) for aj in a]
    for d in itertools.product(*grids):
        d = np.array(d)
        if agg_brute(rule, a + d) >= T + 1e-9 - 1e-12 - 1e-9 + 1e-9:   # >= T + eps (eps=1e-9 in test)
            best[0] = min(best[0], (d > 0).sum()); best[1] = min(best[1], d.sum())
    return best

bad = 0
# --- cardinal (integer data, half-integer grid)
for trial in range(120):
    n = rng.integers(3, 6); M = 4
    S = rng.integers(0, 11, size=(M, n)).astype(float); a = S[0]; riv = S[1:]
    g = float(rng.choice([2, 4, 10])); ub = 10.0
    for rule in ['mean', 'min', 'median']:
        lib.UB = ub
        T = lib.cardinal_threshold(riv, rule)
        if rule == 'mean': r = solve_power(a, T, 1.0, g, ub, 0.0)
        elif rule == 'min': r = solve_min(a, T, g, ub, 0.0)
        else:
            ra, rb = median_ranks(n); r = solve_orderpair(a, T, ra, rb, g, ub, 0.0)
        # brute force with threshold >= T (eps ~ 0 -> use equality tolerance)
        n_ = n; best = [np.inf, np.inf]
        grids = [np.arange(0, min(g, ub - aj) + 1e-9, 0.5) for aj in a]
        for d in itertools.product(*grids):
            d = np.array(d)
            if agg_brute(rule, a + d) >= T - 1e-9:
                best[0] = min(best[0], (d > 0).sum()); best[1] = min(best[1], d.sum())
        if not np.isfinite(best[0]):
            ok = (not r['feasible'])
        else:
            ok = r['feasible'] and r['K'] == best[0] and abs(r['L1'] - best[1]) < 1e-6
        if not ok:
            bad += 1; print('CARDINAL MISMATCH', rule, a, riv.tolist(), g, r, best)
print('cardinal tests done, mismatches:', bad)
lib.UB = 100.0

# --- geometric and harmonic: compare against SLSQP and subset enumeration (continuous data)
from scipy.optimize import minimize
bad = 0
for trial in range(40):
    n = 5; S = rng.uniform(5, 60, size=(6, n)); a = S[0]; riv = S[1:]; g = 30.0
    for rule, p in [('geo', 0.0), ('harm', -1.0)]:
        T = lib.cardinal_threshold(riv, rule); r = solve_power(a, T, p, g, 100.0, 1e-6)
        cap = np.minimum(g, 100 - a)
        # K by subset enumeration (boost chosen subset to cap)
        K = None
        for k in range(0, n + 1):
            for sub in itertools.combinations(range(n), k):
                d = np.zeros(n); d[list(sub)] = cap[list(sub)]
                if power_mean((a + d)[None], p)[0] >= T + 1e-6: K = k; break
            if K is not None: break
        # L1 by SLSQP
        f = lambda d: d.sum()
        cons = {'type': 'ineq', 'fun': lambda d: power_mean((a + d)[None], p)[0] - (T + 1e-6)}
        o = minimize(f, np.full(n, 1.0), constraints=[cons], bounds=[(0, c) for c in cap], method='SLSQP', options=dict(ftol=1e-12, maxiter=500))
        okK = (K is None and not r['feasible']) or (r['feasible'] and r['K'] == K)
        okL = (not r['feasible']) or abs(r['L1'] - o.fun) < 1e-3
        if not (okK and okL): bad += 1; print('POWER MISMATCH', rule, r, K, o.fun)
print('power-mean tests done, mismatches:', bad)

# --- ordinal MILP vs brute force over level combinations (tiny instances)
def brute_ordinal(S, t, rule, g, obj):
    opts, riv = lib._levels(S, t, g, 100.0)
    best = None
    for combo in itertools.product(*[range(len(o)) for o in opts]):
        d = np.array([opts[j][c][1] for j, c in enumerate(combo)])
        if lib.is_first(S, t, rule, d):
            val = (int((d > 0).sum()), d.sum())
            key = val[0] if obj == 'K' else val[1]
            if best is None or key < best[0] - 1e-12: best = (key, val)
    return best
bad = 0; cnt = 0
for trial in range(60):
    n = int(rng.integers(3, 6)); M = int(rng.integers(4, 7))
    S = np.round(rng.uniform(0, 100, size=(M, n)), 0)       # integers => some ties
    t = int(rng.integers(0, M)); g = float(rng.choice([10, 30, 100]))
    for rule in ORDINAL:
        for obj in ['K', 'L1']:
            r = solve_ordinal(S, t, rule, g, obj); b = brute_ordinal(S, t, rule, g, obj)
            cnt += 1
            if b is None: ok = (not r['feasible'])
            else:
                key = r['K'] if obj == 'K' else r['L1']
                ok = r['feasible'] and abs(key - b[0]) < 1e-6 and (r.get('already') or lib.is_first(S, t, rule, r['delta']))
            if not ok: bad += 1; print('ORDINAL MISMATCH', rule, obj, S.tolist(), t, g, r, b)
print('ordinal tests done:', cnt, 'mismatches:', bad)
