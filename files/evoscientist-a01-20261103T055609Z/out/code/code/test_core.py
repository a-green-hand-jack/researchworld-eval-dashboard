"""Verification of the solvers in core.py against independent brute-force oracles on small random instances."""
import itertools, sys, numpy as np
from scipy.optimize import linprog
import core as C

rng = np.random.default_rng(0)
EPS = 1e-7

def rival_tau(S, i, f):
    a = f(S); return np.max(np.delete(a, i))

def check_feasible_scalar(S, i, res, f, ceil, tol=1e-6):
    if not res['feasible']: return True
    d = res['d']; assert (d >= -1e-12).all() and (S[i] + d <= ceil + 1e-9).all()
    S2 = S.copy(); S2[i] = S[i] + d; a = f(S2)
    return a[i] >= np.max(np.delete(a, i)) - tol

# ---- oracle 1: trimmed mean via LP over all permutations
def trimmed_oracle(s, tau, t, ceil):
    m = len(s); K = m - 2 * t; best = np.inf
    for perm in itertools.permutations(range(m)):
        # variables x_j = s'_j (j in 0..m-1), sorted order perm: x[perm[0]]<=...<=x[perm[-1]]
        A = []; b = []
        for a in range(m - 1):
            row = np.zeros(m); row[perm[a]] = 1; row[perm[a + 1]] = -1; A.append(row); b.append(0)
        row = np.zeros(m); row[list(perm[t:m - t])] = -1.0 / K; A.append(row); b.append(-tau)
        res = linprog(np.ones(m), A_ub=np.array(A), b_ub=b, bounds=[(s[j], ceil[j]) for j in range(m)], method='highs')
        if res.status == 0: best = min(best, res.fun - s.sum())
    return best

def test_trimmed():
    bad = 0
    for trial in range(40):
        m = int(rng.choice([4, 5, 6])); t = int(rng.integers(0, (m - 1) // 2 + 1)) if m > 2 else 0
        t = min(t, (m - 1) // 2)
        s = rng.random(m); ceil = np.ones(m)
        tau = float(np.sort(s)[t:m - t].mean() + rng.random() * 0.4)
        r = C.cost_trimmed_milp(s, tau, t, ceil)
        o = trimmed_oracle(s, tau, t, ceil)
        if not (np.isinf(o) and not r['feasible']) and abs(r['cost'] - o) > 1e-6:
            bad += 1; print('trimmed mismatch', m, t, r['cost'], o)
        if r['feasible']:
            assert C.trimmed_mean(( s + r['d'])[None, :], t)[0] >= tau - 1e-6
    print('trimmed MILP vs permutation-LP oracle: mismatches', bad)
    return bad

# ---- oracle 2: kth-largest by brute-force subsets
def kth_oracle(s, tau, q, ceil, p):
    m = len(s); best = np.inf
    for sub in itertools.combinations(range(m), q):
        if all(ceil[j] >= tau - 1e-15 for j in sub):
            best = min(best, sum(max(tau - s[j], 0) ** p for j in sub))
    return best

def test_kth():
    bad = 0
    for trial in range(200):
        m = int(rng.integers(3, 9)); q = int(rng.integers(1, m + 1)); p = int(rng.choice([1, 2]))
        s = rng.random(m); ceil = np.where(rng.random(m) < 0.3, s + rng.random(m) * 0.3, 1.0)
        tau = float(rng.random())
        r = C.cost_kth(s, tau, q, ceil, p); o = kth_oracle(s, tau, q, ceil, p)
        if (np.isinf(o) != (not r['feasible'])) or (r['feasible'] and abs(r['cost'] - o) > 1e-9):
            bad += 1; print('kth mismatch', r['cost'], o)
    print('kth-largest greedy vs subset oracle: mismatches', bad); return bad

def test_wmean():
    bad = 0
    for trial in range(100):
        m = int(rng.integers(2, 8)); s = rng.random(m); w = rng.random(m) + 0.01; ceil = np.where(rng.random(m) < .3, s + .2 * rng.random(m), 1.0)
        tau = float((w / w.sum()) @ s + rng.random() * 0.3)
        for p in (1, 2):
            r = C.cost_wmean(s, tau, w, ceil, p)
            wn = w / w.sum()
            if p == 1:
                res = linprog(np.ones(m), A_ub=[-wn], b_ub=[-(tau - wn @ s)], bounds=[(0, ceil[j] - s[j]) for j in range(m)], method='highs')
                o = res.fun if res.status == 0 else np.inf
            else:
                from scipy.optimize import minimize
                if wn @ (ceil - s) < tau - wn @ s - 1e-12: o = np.inf
                else:
                    res = minimize(lambda d: (d ** 2).sum(), np.zeros(m), jac=lambda d: 2 * d, bounds=[(0, ceil[j] - s[j]) for j in range(m)],
                                   constraints=[{'type': 'ineq', 'fun': lambda d: wn @ (s + d) - tau}], method='SLSQP', options=dict(ftol=1e-14, maxiter=500))
                    o = res.fun if wn @ (s + res.x) >= tau - 1e-7 else np.inf
            if np.isinf(o) != (not r['feasible']) or (r['feasible'] and abs(r['cost'] - o) > 1e-5):
                bad += 1; print('wmean mismatch p', p, r['cost'], o)
    print('weighted mean vs LP/SLSQP oracle: mismatches', bad); return bad

# ---- rank-based oracles: enumerate all level combinations (small n, m)
def levels_all(S, i, j, ceil):
    col = S[:, j]; s = col[i]
    return np.unique(col[(col >= s) & (col <= ceil[j] + 1e-15)])

def rank_oracle(S, i, ceil, rule):
    n, m = S.shape
    opts = [list(levels_all(S, i, j, ceil)) for j in range(m)]
    opts = [[None] + o for o in opts]   # None = no raise (strictly)
    best = np.inf
    for combo in itertools.product(*opts):
        S2 = S.copy(); d = np.zeros(m)
        for j, v in enumerate(combo):
            if v is not None:
                S2[i, j] = v + 1e-9; d[j] = v - S[i, j]
        if rule == 'borda':
            B = C.borda_scores(S2); ok = B[i] >= np.max(np.delete(B, i)) - 1e-12
        elif rule == 'condorcet':
            ok = C.condorcet_margin_min(S2, i) >= 0
        else:
            W = C.plurality_counts(S2); ok = W[i] >= np.max(np.delete(W, i))
        if ok: best = min(best, d.sum())
    return best

def test_rank(rule, fn, ntr=60):
    bad = 0
    for trial in range(ntr):
        n = int(rng.integers(3, 6)); m = int(rng.integers(2, 6))
        S = np.round(rng.random((n, m)), 2); ceil = np.ones(m) if rng.random() < .5 else S.max(0)
        i = int(rng.integers(0, n))
        r = fn(S, i, ceil); o = rank_oracle(S, i, ceil, rule)
        if np.isinf(o) != (not r['feasible']) or (r['feasible'] and abs(r['cost'] - o) > 1e-6):
            bad += 1; print(rule, 'mismatch', n, m, r['cost'], o)
    print(f'{rule} ILP vs enumeration oracle: mismatches', bad); return bad

if __name__ == '__main__':
    tot = 0
    tot += test_kth(); tot += test_wmean(); tot += test_trimmed()
    tot += test_rank('borda', C.cost_borda); tot += test_rank('condorcet', C.cost_condorcet)
    tot += test_rank('plurality', C.cost_plurality)
    print("TOTAL MISMATCHES", tot)

# ---------- additional tests: power-mean floor lifting, and kmax (touched-task cap) variants
def test_power():
    from scipy.optimize import minimize
    bad = 0
    for trial in range(60):
        m = int(rng.integers(2, 7)); s = rng.random(m) * 0.9 + 0.02; ceil = np.where(rng.random(m) < .3, s + .3 * rng.random(m), 1.0)
        for p in (0, -1):
            tau = float(C.power_mean(s[None], p)[0] + rng.random() * 0.2)
            r = C.cost_powermean_floor(s, tau, p, ceil)
            f = lambda d: C.power_mean((s + d)[None], p)[0]
            best = np.inf
            for st in range(5):
                x0 = rng.random(m) * (ceil - s)
                res = minimize(lambda d: d.sum(), x0, jac=lambda d: np.ones(m), bounds=[(0, ceil[j] - s[j]) for j in range(m)],
                               constraints=[{'type': 'ineq', 'fun': lambda d: f(d) - tau}], method='SLSQP', options=dict(ftol=1e-13, maxiter=300))
                if res.success and f(res.x) >= tau - 1e-7: best = min(best, res.fun)
            if np.isinf(best) and not r['feasible']: continue
            if np.isinf(best) or not r['feasible'] or abs(best - r['cost']) > 1e-4:
                bad += 1; print('power mismatch', p, r['cost'], best)
    print('power-mean floor-lifting vs SLSQP: mismatches', bad); return bad

def kmax_oracle(S, i, ceil, rule, kmax):
    n, m = S.shape
    opts = [[None] + list(levels_all(S, i, j, ceil)) for j in range(m)]
    best = np.inf
    for combo in itertools.product(*opts):
        if sum(v is not None for v in combo) > kmax: continue
        S2 = S.copy(); d = np.zeros(m)
        for j, v in enumerate(combo):
            if v is not None: S2[i, j] = v + 1e-9; d[j] = v - S[i, j]
        if rule == 'borda': B = C.borda_scores(S2); ok = B[i] >= np.max(np.delete(B, i)) - 1e-12
        elif rule == 'condorcet': ok = C.condorcet_margin_min(S2, i) >= 0
        else: W = C.plurality_counts(S2); ok = W[i] >= np.max(np.delete(W, i))
        if ok: best = min(best, d.sum())
    return best

def test_kmax():
    bad = 0
    for trial in range(60):
        n = int(rng.integers(3, 6)); m = int(rng.integers(2, 6)); S = np.round(rng.random((n, m)), 2); ceil = np.ones(m); i = int(rng.integers(0, n)); k = int(rng.integers(1, m + 1))
        for rule, fn in (('borda', C.cost_borda), ('condorcet', C.cost_condorcet)):
            r = fn(S, i, ceil, kmax=k); o = kmax_oracle(S, i, ceil, rule, k)
            if np.isinf(o) != (not r['feasible']) or (r['feasible'] and abs(r['cost'] - o) > 1e-6): bad += 1; print(rule, 'kmax mismatch', r['cost'], o)
    # trimmed with kmax vs oracle: brute force subsets of touched tasks, LP via permutations
    for trial in range(25):
        m = int(rng.choice([4, 5])); t = int(rng.integers(0, (m - 1) // 2 + 1)); s = rng.random(m); ceil = np.ones(m); k = int(rng.integers(1, m + 1))
        tau = float(np.sort(s)[t:m - t].mean() + rng.random() * 0.3)
        r = C.cost_trimmed_milp(s, tau, t, ceil, kmax=k)
        best = np.inf
        for sub in itertools.combinations(range(m), k):
            c2 = np.array([ceil[j] if j in sub else s[j] for j in range(m)])
            o = trimmed_oracle_ub(s, tau, t, c2); best = min(best, o)
        if np.isinf(best) != (not r['feasible']) or (r['feasible'] and abs(best - r['cost']) > 1e-6): bad += 1; print('trim kmax mismatch', r['cost'], best)
    print('kmax variants vs oracle: mismatches', bad); return bad

def trimmed_oracle_ub(s, tau, t, ceil):
    return trimmed_oracle(s, tau, t, ceil)

if __name__ == '__main__':
    tot2 = test_power() + test_kmax(); print('TOTAL2', tot2)

# ---------- weighted-cost (item-count) variants
def test_weighted():
    from scipy.optimize import minimize
    bad = 0
    for trial in range(120):
        m = int(rng.integers(3, 8)); s = rng.random(m) * 0.9 + 0.02; ceil = np.where(rng.random(m) < .3, s + .3 * rng.random(m), 1.0); cw = rng.random(m) * 10 + 0.5
        # kth
        q = int(rng.integers(1, m + 1)); tau = float(rng.random())
        r = C.cost_kth(s, tau, q, ceil, 1, cw=cw); best = np.inf
        for sub in itertools.combinations(range(m), q):
            if all(ceil[j] >= tau for j in sub): best = min(best, sum(max(tau - s[j], 0) * cw[j] for j in sub))
        if np.isinf(best) != (not r['feasible']) or (r['feasible'] and abs(best - r['cost']) > 1e-9): bad += 1; print('w-kth', r['cost'], best)
        # mean
        tau = float(s.mean() + rng.random() * .3); wn = np.ones(m) / m
        r = C.cost_wmean(s, tau, np.ones(m), ceil, 1, cw=cw)
        res = linprog(cw, A_ub=[-wn], b_ub=[-(tau - wn @ s)], bounds=[(0, ceil[j] - s[j]) for j in range(m)], method='highs')
        o = res.fun if res.status == 0 else np.inf
        if np.isinf(o) != (not r['feasible']) or (r['feasible'] and abs(o - r['cost']) > 1e-7): bad += 1; print('w-mean', r['cost'], o)
        # trimmed
        t = int(rng.integers(0, (m - 1) // 2 + 1))
        if m <= 6:
            tau = float(np.sort(s)[t:m - t].mean() + rng.random() * .2); r = C.cost_trimmed_milp(s, tau, t, ceil, cw=cw)
            best = np.inf
            for perm in itertools.permutations(range(m)):
                A = []; b = []
                for a in range(m - 1):
                    row = np.zeros(m); row[perm[a]] = 1; row[perm[a + 1]] = -1; A.append(row); b.append(0)
                row = np.zeros(m); row[list(perm[t:m - t])] = -1.0 / (m - 2 * t); A.append(row); b.append(-tau)
                rr = linprog(cw, A_ub=np.array(A), b_ub=b, bounds=[(s[j], ceil[j]) for j in range(m)], method='highs')
                if rr.status == 0: best = min(best, rr.fun - cw @ s)
            if np.isinf(best) != (not r['feasible']) or (r['feasible'] and abs(best - r['cost']) > 1e-5): bad += 1; print('w-trim', r['cost'], best)
        # power means
        for p in (0, -1):
            tau = float(C.power_mean(s[None], p)[0] + rng.random() * 0.2); r = C.cost_powermean_floor(s, tau, p, ceil, cw=cw)
            f = lambda d: C.power_mean((s + d)[None], p)[0]; best = np.inf
            for st in range(5):
                x0 = rng.random(m) * (ceil - s)
                res = minimize(lambda d: cw @ d, x0, jac=lambda d: cw, bounds=[(0, ceil[j] - s[j]) for j in range(m)],
                               constraints=[{'type': 'ineq', 'fun': lambda d: f(d) - tau}], method='SLSQP', options=dict(ftol=1e-13, maxiter=300))
                if res.success and f(res.x) >= tau - 1e-7: best = min(best, res.fun)
            if np.isinf(best) and not r['feasible']: continue
            if not r['feasible']: bad += 1; print('w-pow infeasible', p); continue
            feas = f(r['d']) >= tau - 1e-9 and (r['d'] >= 0).all() and (r['d'] <= ceil - s + 1e-12).all()
            # SLSQP may fail on badly-scaled cases: require own feasibility and cost <= oracle (when oracle found one)
            if not feas or (not np.isinf(best) and r['cost'] > best + 1e-6 * max(1, best)) or (not np.isinf(best) and abs(best - r['cost']) > 1e-4 * max(1, best)):
                bad += 1; print('w-pow', p, r['cost'], best)
    # ranks with weights: enumeration
    for rule, fn in (('borda', C.cost_borda), ('condorcet', C.cost_condorcet), ('plurality', C.cost_plurality)):
        for trial in range(40):
            n = int(rng.integers(3, 6)); m = int(rng.integers(2, 5)); S = np.round(rng.random((n, m)), 2); ceil = np.ones(m); i = int(rng.integers(0, n)); cw = rng.random(m) * 5 + .5
            r = fn(S, i, ceil, cw=cw)
            opts = [[None] + list(levels_all(S, i, j, ceil)) for j in range(m)]; best = np.inf
            for combo in itertools.product(*opts):
                S2 = S.copy(); dd = np.zeros(m)
                for j, v in enumerate(combo):
                    if v is not None: S2[i, j] = v + 1e-9; dd[j] = v - S[i, j]
                if rule == 'borda': B = C.borda_scores(S2); ok = B[i] >= np.max(np.delete(B, i)) - 1e-12
                elif rule == 'condorcet': ok = C.condorcet_margin_min(S2, i) >= 0
                else: W = C.plurality_counts(S2); ok = W[i] >= np.max(np.delete(W, i))
                if ok: best = min(best, cw @ dd)
            if np.isinf(best) != (not r['feasible']) or (r['feasible'] and abs(best - r['cost']) > 1e-6): bad += 1; print('w-' + rule, r['cost'], best)
    print('weighted-cost variants vs oracles: mismatches', bad); return bad

if __name__ == '__main__':
    t3 = test_weighted(); print('TOTAL3', t3); sys.exit(1 if t3 else 0)
