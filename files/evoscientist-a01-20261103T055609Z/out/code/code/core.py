"""Minimum targeted-investment solvers for multi-task leaderboards.

Setting. S is an (n_models x m_tasks) score matrix. Target model i may raise its score on task j by
d_j in [0, room_j] (room_j = ceiling_j - S[i,j]); rivals are static. "Investment" = vector d.
Cost options: L1 (sum d_j, "score points"), L2sq (sum d_j^2, diminishing returns), and tasks touched
(|{j: d_j>0}|). "Rank 1" is *weak* (ties allowed; infimum of cost, tie-break not charged).
"""
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, csr_matrix

INF = float('inf')

# ------------------------------------------------------------------ aggregators
def trimmed_mean(S, t):
    """Mean after dropping t largest and t smallest per row (t=0 mean; t=(m-1)//2 median)."""
    X = np.sort(S, axis=1); m = X.shape[1]
    return X[:, t:m - t].mean(axis=1)

def kth_largest(S, q):
    """q-th largest per row (q=1 max, q=m min)."""
    return -np.sort(-S, axis=1)[:, q - 1]

def wmean(S, w):
    return S @ (w / w.sum())

def median_t(m):
    return (m - 1) // 2

# ------------------------------------------------------------------ helpers
def _room(s, ceil):
    return np.maximum(ceil - s, 0.0)

def _result(cost, d, ok=True):
    return dict(cost=cost, d=d, touched=int((d > 1e-12).sum()) if d is not None else 0, feasible=ok,
                l1=float(d.sum()) if d is not None else INF)

def infeasible(m):
    return dict(cost=INF, d=None, touched=m, feasible=False, l1=INF)

# ------------------------------------------------------------------ order statistics (closed form)
def cost_kth(s, tau, q, ceil, p=1, cw=None):
    """Min cost so that q-th largest score >= tau.  Need >= q tasks with score >= tau.
    p=1: L1 cost; p=2: sum of squares.  Greedy by smallest deficit is exact for both (cost monotone in deficit)."""
    m = len(s)
    deficit = np.maximum(tau - s, 0.0)
    ok_task = (ceil + 1e-15) >= tau                    # can this task reach tau at all?
    have = int((s >= tau).sum())
    need = max(q - have, 0)
    d = np.zeros(m)
    if need > 0:
        cand = np.where((s < tau) & ok_task)[0]
        if len(cand) < need: return infeasible(m)
        wj = np.ones(m) if cw is None else cw
        pick = cand[np.argsort((deficit * wj)[cand] if p == 1 else deficit[cand], kind='stable')[:need]]
        d[pick] = deficit[pick]
    return _result(((d ** p) * (1 if cw is None else cw)).sum(), d)

# ------------------------------------------------------------------ weighted mean (closed form / water filling)
def cost_wmean(s, tau, w, ceil, p=1, cw=None):
    """Min cost so that sum_j w_j s'_j / sum w >= tau, w>=0 (normalised inside).
    p=1: fractional knapsack (largest w first). p=2: minimise sum d^2 with caps -> water filling d_j=min(room_j, lam*w_j)."""
    wn = w / w.sum(); m = len(s)
    need = tau - float(wn @ s)
    if need <= 0: return _result(0.0, np.zeros(m))
    room = _room(s, ceil)
    if float(wn @ room) < need - 1e-12: return infeasible(m)
    d = np.zeros(m)
    if p == 1:
        cwj = np.ones(m) if cw is None else cw
        for j in np.lexsort((-room, -(wn / cwj))):   # best weight-per-cost first; ties -> largest headroom
            if need <= 1e-15: break
            if wn[j] <= 0 or room[j] <= 0: continue
            g = min(room[j], need / wn[j]); d[j] = g; need -= g * wn[j]
        return _result((d * cwj).sum(), d)
    # p == 2 : d_j = min(room_j, lam*wn_j); find lam by bisection
    lo, hi = 0.0, 1.0
    f = lambda lam: float(wn @ np.minimum(room, lam * wn))
    while f(hi) < need: hi *= 2
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if f(mid) < need: lo = mid
        else: hi = mid
    d = np.minimum(room, hi * wn)
    return _result((d ** 2).sum(), d)

# ------------------------------------------------------------------ trimmed mean (exact MILP, L1)
def cost_trimmed_milp(s, tau, t, ceil, kmax=None, time_limit=30, cw=None):
    """Min L1 cost so that trimmed mean (t each side) >= tau, optional cap on #tasks touched.
    Uses  Tm(s') >= tau  <=>  exists B,|B|=t: total(s') - sum_B s' - top_t(s') >= tau*K,  top_t convex (LP form).
    Variables per task j: d_j, v_j, p_j (continuous), b_j, y_j (binary); plus u."""
    m = len(s); K = m - 2 * t
    room = _room(s, ceil)
    base = tau * K - (s.sum())
    if t == 0 and kmax is None:                      # plain mean: closed form
        return cost_wmean(s, tau, np.ones(m), ceil, 1, cw=cw)
    use_y = kmax is not None
    # var layout: d(0:m) v(m:2m) p(2m:3m) b(3m:4m) y(4m:5m) u(5m)
    nv = 5 * m + 1
    iD, iV, iP, iB, iY, iU = 0, m, 2 * m, 3 * m, 4 * m, 5 * m
    c = np.zeros(nv); c[iD:iD + m] = 1.0 if cw is None else cw
    lb = np.zeros(nv); ub = np.full(nv, np.inf)
    ub[iD:iD + m] = room
    ub[iB:iB + m] = 1; ub[iY:iY + m] = 1
    lb[iU] = -np.inf
    ub[iV:iV + m] = np.inf
    ub[iP:iP + m] = np.inf
    integrality = np.zeros(nv); integrality[iB:iB + m] = 1; integrality[iY:iY + m] = 1
    rows = []; lo = []; hi = []
    A = lil_matrix((3 * m + 4, nv)); r = 0
    # (1) total(s') - sum p - t u - sum v >= tau K - S0   ->  sum d - sum p - sum v - t u >= base
    A[r, iD:iD + m] = 1; A[r, iP:iP + m] = -1; A[r, iV:iV + m] = -1; A[r, iU] = -t
    lo.append(base); hi.append(np.inf); r += 1
    cj = s + room                                    # per-task ceiling (upper bound of s'_j)
    for j in range(m):
        # (2) v_j - d_j + u >= s_j
        A[r, iV + j] = 1; A[r, iD + j] = -1; A[r, iU] = 1; lo.append(s[j]); hi.append(np.inf); r += 1
        # (3) p_j - d_j - c_j b_j >= s_j - c_j
        A[r, iP + j] = 1; A[r, iD + j] = -1; A[r, iB + j] = -cj[j]; lo.append(s[j] - cj[j]); hi.append(np.inf); r += 1
        # (4) d_j <= room_j y_j
        if use_y:
            A[r, iD + j] = 1; A[r, iY + j] = -room[j]; lo.append(-np.inf); hi.append(0.0); r += 1
    A[r, iB:iB + m] = 1; lo.append(t); hi.append(t); r += 1
    if use_y:
        A[r, iY:iY + m] = 1; lo.append(0); hi.append(kmax); r += 1
    A = csr_matrix(A[:r])
    res = milp(c, constraints=LinearConstraint(A, np.array(lo), np.array(hi)), integrality=integrality,
               bounds=Bounds(lb, ub), options=dict(time_limit=time_limit, mip_rel_gap=1e-9, presolve=True))
    if res.x is None: return infeasible(m)
    d = np.clip(res.x[iD:iD + m], 0, room); d[d < 1e-10] = 0
    return _result(float((d * (1 if cw is None else cw)).sum()), d)

# ------------------------------------------------------------------ rank-based rules (ILP)
def _levels(S, i, j, ceil_j):
    """Candidate raise levels for target i on task j: distinct rival scores v with s_ij <= v <= ceil."""
    col = S[:, j]; s = col[i]
    v = np.unique(col[(col >= s) & (col <= ceil_j + 1e-15)])
    return v

def _pair_credit(col, i, v):
    """credit target i has over each other model r on this task if its score is (just above) v: 1 if col[r]<=v else 0."""
    return (col <= v + 1e-15).astype(float)

def _base_credit(col, i):
    s = col[i]
    return np.where(col < s, 1.0, np.where(col == s, 0.5, 0.0))

def _solve_levelmodel(S, i, ceil, rule, kmax=None, time_limit=20, rivals=None, max_rounds=30, cw=None):
    """Multiple-choice ILP over (task, level) for rank-based rules, with lazy rival constraints.
    rule in {'borda','condorcet'}.  Weak first place.  Cost = L1 sum of raises.
    Returns dict(cost,d,touched,feasible)."""
    n, m = S.shape
    others = np.array([r for r in range(n) if r != i])
    lev = [_levels(S, i, j, ceil[j]) for j in range(m)]
    # variable list
    var_task, var_val, var_cost = [], [], []
    for j in range(m):
        for v in lev[j]:
            var_task.append(j); var_val.append(v); var_cost.append(v - S[i, j])
    nx = len(var_task)
    var_task = np.array(var_task); var_val = np.array(var_val); var_cost = np.array(var_cost)
    # credit[x, r] = new credit over r  (1 or 0) ;  base credit per task/rival
    base_c = np.stack([_base_credit(S[:, j], i) for j in range(m)], 0)       # m x n
    newc = np.stack([_pair_credit(S[:, var_task[x]], i, var_val[x]) for x in range(nx)], 0)  # nx x n
    gain = newc - base_c[var_task]                                           # nx x n   (>=0 for x with level>=s)
    gain[:, i] = 0
    # x = 0 option per task is "no raise" (implicit: sum_l x_jl <= 1)
    if rule == 'borda':
        Bi0 = sum(base_c[j, others].sum() for j in range(m))
        # rival total Borda points B_r = sum_j sum_q credit(r over q)
        def pair_credit_all(col):
            return (col[:, None] > col[None, :]) * 1.0 + 0.5 * (col[:, None] == col[None, :])
        Br0 = np.zeros(n)
        for j in range(m):
            Pc = pair_credit_all(S[:, j]); np.fill_diagonal(Pc, 0); Br0 += Pc.sum(1)
        Bi0 = Br0[i]
        gtot = gain[:, others].sum(1)                    # total pairwise gain of x
    else:  # condorcet: target must have strictly more task-wins than r  (weak: >=)
        Wi0 = np.zeros(n); Wr0 = np.zeros(n)
        for j in range(m):
            col = S[:, j]; Wi0 += (col[i] > col) * 1.0 - (col[i] < col) * 1.0   # (wins - losses) of i vs r on task j
        # margin_r = #tasks i beats r - #tasks r beats i ; need >= 0 (weak)
        mar0 = Wi0
        # new margin contribution from x: from base (+1/0/-1) to +1 (pass at level v): delta = 1 - base_sign
        base_sign = np.stack([np.where(S[i, j] > S[:, j], 1.0, np.where(S[i, j] < S[:, j], -1.0, 0.0)) for j in range(m)], 0)
        newsign = np.where(newc > 0.5, 1.0, -1.0)         # pass => +1 ; not passed: unchanged handled via gain
        dm = np.where(newc > 0.5, 1.0 - base_sign[var_task], 0.0)   # change in margin vs r from x
        dm[:, i] = 0
    # ILP with lazy rival constraints
    active = set(rivals) if rivals is not None else None
    if active is None:
        if rule == 'borda':
            order = others[np.argsort(-Br0[others])]; active = set(order[:40].tolist())
        else:
            viol = others[mar0[others] < 0]; active = set(viol.tolist())
    nvar = nx + m          # x vars + y vars (touched)
    for rnd in range(max_rounds):
        act = sorted(active)
        rows = []; lo = []; hi = []
        A = lil_matrix((len(act) + m + 2, nvar)); r = 0
        for j in range(m):
            idx = np.where(var_task == j)[0]
            A[r, idx] = 1; lo.append(-np.inf); hi.append(1.0); r += 1
        for rv in act:
            if rule == 'borda':
                # Bi0 + sum gtot x  >= Br0[rv] - sum gain[x,rv] x     (weak first)
                coef = gtot + gain[:, rv]
                A[r, :nx] = coef; lo.append(Br0[rv] - Bi0); hi.append(np.inf)
            else:
                A[r, :nx] = dm[:, rv]; lo.append(-mar0[rv]); hi.append(np.inf)
            r += 1
        if kmax is not None:
            for x in range(nx): pass
            # y_j >= sum_l x_jl  and sum y <= kmax
            A2 = lil_matrix((m + 1, nvar))
            for j in range(m):
                idx = np.where(var_task == j)[0]
                A2[j, idx] = 1; A2[j, nx + j] = -1
            A2[m, nx:] = 1
            cons = [LinearConstraint(csr_matrix(A[:r]), np.array(lo), np.array(hi)),
                    LinearConstraint(csr_matrix(A2), np.r_[np.full(m, -np.inf), -np.inf], np.r_[np.zeros(m), kmax])]
        else:
            cons = [LinearConstraint(csr_matrix(A[:r]), np.array(lo), np.array(hi))]
        c = np.r_[var_cost * (1 if cw is None else cw[var_task]), np.zeros(m)]
        integrality = np.r_[np.ones(nx), np.ones(m)]
        ub = np.ones(nvar)
        res = milp(c, constraints=cons, integrality=integrality, bounds=Bounds(np.zeros(nvar), ub),
                   options=dict(time_limit=time_limit, mip_rel_gap=1e-9))
        if res.x is None: return infeasible(m)
        last_opt = (res.status == 0)
        x = np.round(res.x[:nx]).astype(int)
        d = np.zeros(m)
        for k in np.where(x == 1)[0]: d[var_task[k]] = var_cost[k] + 1e-9   # +eps: strict lead on the task (infimum semantics)
        # check all rivals
        if rule == 'borda':
            tot = Bi0 + gtot[x == 1].sum()
            Brn = Br0 - gain[x == 1].sum(0)
            bad = [rv for rv in others if tot < Brn[rv] - 1e-9]
        else:
            mar = mar0 + dm[x == 1].sum(0)
            bad = [rv for rv in others if mar[rv] < -1e-9]
        if not bad:
            out = _result(float((d * (1 if cw is None else cw)).sum()), d); out['opt'] = bool(last_opt)
            return out
        active |= set(bad[:50])
    return infeasible(m)

def cost_borda(S, i, ceil, **kw): return _solve_levelmodel(S, i, ceil, 'borda', **kw)
def cost_condorcet(S, i, ceil, **kw): return _solve_levelmodel(S, i, ceil, 'condorcet', **kw)

def cost_plurality(S, i, ceil, time_limit=30, unit=False, cw=None):
    """Weak first place in #task-wins (ties on a task: nobody gets the win unless strictly above all).
    Target wins task j after raising to (just above) max over rivals; cost = deficit to that max.
    Choose set W of tasks to win (binary w_j); constraint for each rival r with wins>0."""
    n, m = S.shape
    rival_max = np.array([np.max(np.delete(S[:, j], i)) for j in range(m)])
    deficit = np.maximum(rival_max - S[i, j] if False else rival_max - S[i], 0.0)
    room = _room(S[i], ceil)
    can = (S[i] + room + 1e-15) >= rival_max
    # task winner under baseline (strict max, ties => no win; use sup-semantics: tie counted as win for weak-first? keep strict)
    mx = S.max(0)
    win0 = np.zeros((n, m), dtype=bool)
    for j in range(m):
        w = np.where(S[:, j] == mx[j])[0]
        if len(w) == 1: win0[w[0], j] = True
    ti = win0[i].astype(int)
    Wr0 = win0.sum(1)
    # binary w_j (raise to win task j) only meaningful when ti[j]==0 and can[j]
    idx = [j for j in range(m) if ti[j] == 0 and can[j]]
    if not idx: 
        ok = ti.sum() >= np.max(np.delete(Wr0, i)); return _result(0.0, np.zeros(m)) if ok else infeasible(m)
    nvar = len(idx)
    c = np.array([1.0 if unit else deficit[j] * (1 if cw is None else cw[j]) for j in idx])
    rivals = [r for r in range(n) if r != i and Wr0[r] > 0]
    A = np.zeros((len(rivals), nvar)); lo = np.zeros(len(rivals))
    for a, r in enumerate(rivals):
        # wins_i' = ti.sum() + sum w ; wins_r' = Wr0[r] - sum_{j in W, r holds j} 1 ; need wins_i' >= wins_r'
        for b, j in enumerate(idx):
            A[a, b] = 1 + (1 if win0[r, j] else 0)
        lo[a] = Wr0[r] - ti.sum()
    if len(rivals) == 0: return _result(0.0, np.zeros(m))
    res = milp(c, constraints=LinearConstraint(A, lo, np.full(len(rivals), np.inf)), integrality=np.ones(nvar),
               bounds=Bounds(0, 1), options=dict(time_limit=time_limit))
    if res.x is None: return infeasible(m)
    d = np.zeros(m)
    for b, j in enumerate(idx):
        if res.x[b] > 0.5: d[j] = deficit[j] + 1e-9
    return _result(float((d * (1 if cw is None else cw)).sum()), d)

# ------------------------------------------------------------------ rule registry & utilities
def apply_investment(s, d, eps=1e-9):
    out = s + d + eps * (d > 0)
    return out

def first_place_scalar(S, i, d, aggfun):
    """Check: after applying d to row i, is i weakly first under scalar aggregator aggfun(S)->vector? (strict w/ eps)"""
    S2 = S.copy(); S2[i] = apply_investment(S[i], d)
    a = aggfun(S2)
    return a[i] >= np.max(np.delete(a, i)) - 1e-12

def borda_scores(S):
    n, m = S.shape; B = np.zeros(n)
    for j in range(m):
        col = S[:, j]
        P = (col[:, None] > col[None, :]) * 1.0 + 0.5 * (col[:, None] == col[None, :])
        np.fill_diagonal(P, 0); B += P.sum(1)
    return B

def condorcet_margin_min(S, i):
    n, m = S.shape
    mar = ((S[i][None, :] > S).sum(1) - (S[i][None, :] < S).sum(1)).astype(float)
    mar = np.delete(mar, i)
    return mar.min()

def plurality_counts(S):
    n, m = S.shape; mx = S.max(0); W = np.zeros(n)
    for j in range(m):
        w = np.where(S[:, j] == mx[j])[0]
        if len(w) == 1: W[w[0]] += 1
    return W

# ------------------------------------------------------------------ power means p<=0 (concave): floor lifting (L1 cost)
def power_mean(S, p):
    if p == 0:
        with np.errstate(divide='ignore'):
            return np.exp(np.mean(np.log(np.maximum(S, 0)), axis=1)) * (S.min(axis=1) > 0)
    return np.mean(np.maximum(S, 1e-300) ** p, axis=1) ** (1.0 / p) * (S.min(axis=1) > 0 if p < 0 else 1)

def cost_powermean_floor(s, tau, p, ceil, cw=None):
    """Min cost sum_j cw_j d_j s.t. power mean M_p (p<=0, equal weights) >= tau (concave => convex program).
    KKT: s'_j = clip((mu/cw_j)^(1/(1-p)), s_j, ceil_j); bisection on mu.  cw=None => floor lifting (L1)."""
    m = len(s); w = np.ones(m) if cw is None else cw
    Mp = lambda x: power_mean(x[None, :], p)[0]
    if Mp(s) >= tau: return _result(0.0, np.zeros(m))
    if Mp(np.maximum(s, ceil)) < tau - 1e-15: return infeasible(m)
    sp = lambda mu: np.clip((mu / w) ** (1.0 / (1.0 - p)), s, np.maximum(ceil, s))
    lo, hi = 0.0, 1.0
    while Mp(sp(hi)) < tau: hi *= 2
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if Mp(sp(mid)) < tau: lo = mid
        else: hi = mid
    d = np.maximum(sp(hi) - s, 0.0)
    return _result(float((d * w).sum()), d)
