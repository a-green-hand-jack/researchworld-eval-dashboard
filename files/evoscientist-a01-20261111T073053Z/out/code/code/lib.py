"""Core library: aggregation rules and minimum-investment solvers.

Notation. S is an (M x n) score matrix (models x tasks, higher = better, scale 0..UB=100).
A target model t has scores a = S[t].  An *investment* is a boost vector delta >= 0 with
  a_j + delta_j <= UB   (ceiling)      and      delta_j <= g   (per-task gain cap).
breadth K = #{j: delta_j > 0};  magnitude L1 = sum_j delta_j.
The target is "first" under rule A iff A(a + delta) > A(s_r) for every rival r (strict).
Rivals are held fixed for cardinal rules; for ordinal rules (Borda / Copeland / plurality) the
rivals' aggregate scores change with the target's scores, which the MILPs model exactly.
"""
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, csr_matrix

UB = 100.0
EPS = 1e-6      # strictness margin on the aggregate (score points) for cardinal rules
EPSO = 1e-3     # margin (score points) by which the target must pass a rival on a task (ordinal rules)
PLM = 5e-5      # strict-margin for plurality credits (> solver feasibility tol 1e-6, < smallest credit gap 1/(M(M-1)))
SHIFT = 1.0     # geometric / harmonic means are computed on (score + SHIFT) - SHIFT (scores can be 0)

CARDINAL = ['mean', 'geo', 'harm', 'min', 'median']
ORDINAL = ['borda', 'copeland', 'plurality']
RULES = CARDINAL + ORDINAL
RULE_LABEL = {'mean': 'Mean', 'geo': 'Geometric mean', 'harm': 'Harmonic mean', 'min': 'Minimum',
              'median': 'Median', 'borda': 'Borda (mean win rate)', 'copeland': 'Copeland (pairwise majority)',
              'plurality': 'Plurality (#task wins)'}
PMEAN = {'mean': 1.0, 'geo': 0.0, 'harm': -1.0}

# ---------------------------------------------------------------------------------------------
# aggregation (scores for every model)
# ---------------------------------------------------------------------------------------------
def power_mean(S, p):
    S = np.asarray(S, float)
    if p == 1: return S.mean(axis=-1)
    X = S + SHIFT
    if p == 0: return np.exp(np.log(X).mean(axis=-1)) - SHIFT
    return (np.mean(X ** p, axis=-1)) ** (1.0 / p) - SHIFT

def pair_ranks(n):
    """descending ranks (ra, rb) whose average defines the median"""
    return (n + 1) // 2, (n + 2) // 2   # odd n: equal; even n: n/2, n/2+1  -> check below

def median_ranks(n):
    return (n // 2, n // 2 + 1) if n % 2 == 0 else ((n + 1) // 2, (n + 1) // 2)

def pairwise_wins(S):
    """W[a,b] = (#tasks a beats b) + 0.5 (#ties); diagonal 0.  S: (M x n)."""
    M, n = S.shape
    W = np.zeros((M, M))
    for j in range(n):
        c = S[:, j]
        W += (c[:, None] > c[None, :]) + 0.5 * (c[:, None] == c[None, :])
    np.fill_diagonal(W, 0.0)
    return W

def borda_scores(S):
    """sum over tasks of #models beaten (ties 0.5)  == sum of pairwise wins."""
    return pairwise_wins(S).sum(axis=1)

def copeland_scores(S, W=None):
    M, n = S.shape
    W = pairwise_wins(S) if W is None else W
    out = np.where(W > n / 2, 1.0, np.where(W == n / 2, 0.5, 0.0))
    np.fill_diagonal(out, 0.0)
    return out.sum(axis=1)

def plurality_credit(S):
    """credit[m,j] = 1/#tied if m is (jointly) best on task j else 0."""
    mx = S.max(axis=0, keepdims=True)
    top = (S == mx).astype(float)
    return top / top.sum(axis=0, keepdims=True)

def rule_scores(S, rule):
    S = np.asarray(S, float)
    if rule in PMEAN: return power_mean(S, PMEAN[rule])
    if rule == 'min': return S.min(axis=1)
    if rule == 'median': return np.median(S, axis=1)
    if rule == 'borda': return borda_scores(S)
    if rule == 'copeland': return copeland_scores(S)
    if rule == 'plurality': return plurality_credit(S).sum(axis=1)
    raise ValueError(rule)

# ---------------------------------------------------------------------------------------------
# cardinal rules: exact solvers
# ---------------------------------------------------------------------------------------------
def _phi(x, p):
    x = x + SHIFT
    return np.log(x) if p == 0 else x ** p / p

def _cap(a, g, ub=UB):
    return np.minimum(g, ub - a).clip(min=0.0)

def solve_power(a, T, p, g, ub=UB, eps=EPS):
    """Minimum breadth K and magnitude L1 such that M_p(a+delta) >= T+eps, p<=1 (mean: p=1).
    Separable & monotone => K by greedy on gains (exact); L1 by water-filling (exact for p<1) / linear (p=1)."""
    a = np.asarray(a, float); n = len(a); c = _cap(a, g, ub)
    if p == 1:
        need = n * (T + eps - a.mean())
        if need <= 0: return dict(feasible=True, K=0, L1=0.0)
        gains = np.sort(c)[::-1]; cs = np.cumsum(gains)
        if cs[-1] < need - 1e-12: return dict(feasible=False, K=np.nan, L1=np.nan)
        return dict(feasible=True, K=int(np.searchsorted(cs, need - 1e-12) + 1), L1=float(need))
    # p < 1: work in phi-space
    target = n * _phi(np.array(T + eps), p)
    base = _phi(a, p).sum()
    if base >= target: return dict(feasible=True, K=0, L1=0.0)
    full = _phi(a + c, p)
    if full.sum() < target - 1e-12: return dict(feasible=False, K=np.nan, L1=np.nan)
    gains = np.sort(full - _phi(a, p))[::-1]; cs = np.cumsum(gains)
    K = int(np.searchsorted(cs, target - base - 1e-12) + 1)
    lo, hi = a.min(), ub
    for _ in range(200):                       # bisection on water level lam
        lam = 0.5 * (lo + hi)
        d = np.clip(lam - a, 0, c)
        if _phi(a + d, p).sum() >= target: hi = lam
        else: lo = lam
    d = np.clip(hi - a, 0, c)
    return dict(feasible=True, K=K, L1=float(d.sum()))

def solve_min(a, T, g, ub=UB, eps=EPS):
    a = np.asarray(a, float); c = _cap(a, g, ub); lvl = T + eps
    need = a < lvl - 1e-12
    if not need.any(): return dict(feasible=True, K=0, L1=0.0)
    if np.any(a[need] + c[need] < lvl - 1e-12): return dict(feasible=False, K=np.nan, L1=np.nan)
    return dict(feasible=True, K=int(need.sum()), L1=float((lvl - a[need]).sum()))

def solve_orderpair(a, T, ra, rb, g, ub=UB, eps=EPS):
    """Aggregate = (x_(ra) + x_(rb))/2, x_(r) = r-th largest score (ra<=rb).  ra=rb: r-th order statistic (median for odd n).
    Exact.  Membership: by an exchange argument only the top-rb tasks (by current score) are ever touched.  Within that set
    ra tasks end at level u and rb-ra at level v, u+v = 2(T+eps), u >= v.
      * L1: the ra tasks with the highest current score take level u (exchange argument); cost is convex piecewise-linear in v.
      * K : which ra tasks take level u is an assignment problem with 0/1 penalties (solved greedily per v).
    Both are minimised over the breakpoints of the piecewise-constant and piecewise-linear objectives."""
    a = np.asarray(a, float); n = len(a)
    order = np.argsort(-a, kind='stable'); s = a[order][:rb]
    cap = np.minimum(s + _cap(s, g, ub), ub)       # max reachable level per task in the touched set
    Tp = T + eps; tol = 1e-12
    if ra == rb:
        if cap.min() < Tp - tol: return dict(feasible=False, K=np.nan, L1=np.nan)
        m = s < Tp - tol
        return dict(feasible=True, K=int(m.sum()), L1=float((Tp - s[m]).sum()))
    cands = {Tp}
    for x in list(s) + list(cap):
        cands.add(x); cands.add(2 * Tp - x)
    bestK, bestL = None, None
    for v in cands:
        u = 2 * Tp - v
        if v > Tp + tol or v < -1e-9 or u > ub + tol: continue
        if cap.min() < v - tol or (cap >= u - tol).sum() < ra: continue
        # L1 (top-ra by score at level u; feasible iff those have cap >= u)
        if cap[:ra].min() >= u - tol:
            L = np.maximum(u - s[:ra], 0).sum() + np.maximum(v - s[ra:], 0).sum()
            bestL = L if bestL is None else min(bestL, L)
        # K
        cv = (s < v - tol).astype(int); cu = (s < u - tol).astype(int)
        elig = np.where(cap >= u - tol)[0]
        pen = np.sort((cu - cv)[elig])
        K = int(cv.sum() + pen[:ra].sum())
        bestK = K if bestK is None else min(bestK, K)
    if bestK is None: return dict(feasible=False, K=np.nan, L1=np.nan)
    # L1 may be infeasible for the top-ra assignment only if no candidate satisfied it; then fall back (cannot happen when K feasible)
    if bestL is None: return dict(feasible=False, K=np.nan, L1=np.nan)
    return dict(feasible=True, K=bestK, L1=float(bestL))

def os_threshold(S_riv, r):
    """r-th largest per rival"""
    return np.sort(S_riv, axis=1)[:, ::-1][:, r - 1]

def cardinal_threshold(S_riv, rule):
    n = S_riv.shape[1]
    if rule in PMEAN: return power_mean(S_riv, PMEAN[rule]).max()
    if rule == 'min': return S_riv.min(axis=1).max()
    if rule == 'median': return np.median(S_riv, axis=1).max()
    raise ValueError(rule)

def solve_cardinal(a, S_riv, rule, g, ub=UB, eps=EPS, T=None):
    a = np.asarray(a, float); n = len(a)
    T = cardinal_threshold(S_riv, rule) if T is None else T
    if rule in PMEAN: return solve_power(a, T, PMEAN[rule], g, ub, eps)
    if rule == 'min': return solve_min(a, T, g, ub, eps)
    if rule == 'median':
        ra, rb = median_ranks(n); return solve_orderpair(a, T, ra, rb, g, ub, eps)
    raise ValueError(rule)

def solve_orderstat(a, S_riv, r, g, ub=UB, eps=EPS):
    """rule = r-th largest score (r=1 max ... r=n min)"""
    T = os_threshold(S_riv, r).max()
    return solve_orderpair(a, T, r, r, g, ub, eps)

# ---------------------------------------------------------------------------------------------
# ordinal rules: exact MILPs  (levels formulation)
# ---------------------------------------------------------------------------------------------
def _levels(S, t, g, ub=UB):
    """per task j: list of (level_value, cost) options for the target, option 0 = no change."""
    M, n = S.shape; a = S[t]; riv = np.delete(S, t, axis=0)
    opts = []
    for j in range(n):
        lv = [(a[j], 0.0)]
        cand = np.unique(riv[:, j][riv[:, j] >= a[j] - 1e-12])
        for v in cand:
            val = v + EPSO
            if val - a[j] <= g + 1e-12 and val <= ub + 1e-12 and val > a[j]:
                lv.append((val, val - a[j]))
        opts.append(lv)
    return opts, riv

def _solve(c, A_ub, b_ub, A_eq, b_eq, integrality, lb, ubv, time_limit):
    cons = []
    if A_ub is not None: cons.append(LinearConstraint(csr_matrix(A_ub), -np.inf, b_ub))
    if A_eq is not None: cons.append(LinearConstraint(csr_matrix(A_eq), b_eq, b_eq))
    res = milp(c, constraints=cons, integrality=integrality, bounds=Bounds(lb, ubv),
               options=dict(time_limit=time_limit, mip_rel_gap=1e-9, presolve=True))
    return res

def solve_ordinal(S, t, rule, g, objective='K', ub=UB, time_limit=60.0):
    """Exact minimum investment (objective 'K' = breadth, 'L1' = magnitude) for target row t of S to be strictly
    first under an ordinal rule.  Returns dict(status, feasible, K, L1, optimal)."""
    S = np.asarray(S, float); M, n = S.shape
    sc0 = rule_scores(S, rule)
    # already first?
    others = np.delete(sc0, t)
    if sc0[t] > others.max() + 1e-9: return dict(feasible=True, K=0, L1=0.0, optimal=True, already=True)
    opts, riv = _levels(S, t, g, ub)
    nv = [len(o) for o in opts]; off = np.concatenate([[0], np.cumsum(nv)]); NV = int(off[-1])
    cost = np.array([c for o in opts for (_, c) in o]); Kv = np.array([0.0 if k == 0 else 1.0 for o in opts for k in range(len(o))])
    lvvals = [np.array([v for (v, _) in o]) for o in opts]
    # vic[r, var] = 1 / 0.5 / 0 : does target at that level beat rival r on that task
    def vic_cols(j, rows=None):
        R = riv[:, j] if rows is None else riv[rows, j]
        L = lvvals[j]
        return (L[None, :] > R[:, None]).astype(float) + 0.5 * (L[None, :] == R[:, None])
    # ----- build constraint system
    nextra = 0; rows_ub = []; b_ub = []; extra_int = []
    Rn = M - 1
    if rule == 'borda':
        w = np.zeros(NV)                                        # target's Borda contribution per variable
        for j in range(n): w[off[j]:off[j + 1]] = vic_cols(j).sum(axis=0)
        B_all = borda_scores(S); Bt0 = B_all[t]; Br = np.delete(B_all, t)
        keep = np.where(Br >= Bt0 - 1e-9)[0]
        V = np.zeros((len(keep), NV))
        for j in range(n): V[:, off[j]:off[j + 1]] = vic_cols(j, keep)
        # target_B >= Br_r - (sum of vic of r over chosen) ... : Borda(r) after = Br_r - (vic_r(final) - vic_r(initial))
        v0 = np.array([((S[t] > riv[k]) + 0.5 * (S[t] == riv[k])).sum() for k in range(Rn)])
        # Borda(t) = sum_j w_j z ;  Borda(r') = Br[k] + v0[k] - sum_j vic z
        A = np.zeros((len(keep), NV)); bb = np.zeros(len(keep))
        for i, k in enumerate(keep):
            A[i] = -(w) - V[i]                                  # -(Bt) - vic  <=  -(Br+v0) - 0.5
            bb[i] = -(Br[k] + v0[k]) - 0.5
        A_ub = A; b_ub = bb; nextra = 0; ex_lb = []; ex_ub = []
    elif rule == 'copeland':
        Wm = np.zeros((Rn, NV))
        for j in range(n): Wm[:, off[j]:off[j + 1]] = vic_cols(j)
        Wr = pairwise_wins(riv)                                 # rivals vs rivals
        outr = np.where(Wr > n / 2, 1.0, np.where(Wr == n / 2, 0.5, 0.0)); np.fill_diagonal(outr, 0)
        F = outr.sum(axis=1)                                    # rival Copeland excluding target
        ct0 = np.where(pairwise_wins(S)[t] > n / 2, 1.0, np.where(pairwise_wins(S)[t] == n / 2, 0.5, 0.0))
        ct0[t] = 0; cop_t0 = ct0.sum()
        keep = np.where(F + 1 >= cop_t0 - 1e-9)[0]
        # vars: z (NV), y1_r (Rn), y2_r (Rn)
        tot = NV + 2 * Rn; rows = []; bb = []
        half = n / 2.0
        for r in range(Rn):                                     # y1: W_r >= half*y1 ; y2: W_r >= (half+.5)*y2 ; y2<=y1
            row = np.zeros(tot); row[:NV] = -Wm[r]; row[NV + r] = half; rows.append(row); bb.append(0.0)
            row = np.zeros(tot); row[:NV] = -Wm[r]; row[NV + Rn + r] = half + 0.5; rows.append(row); bb.append(0.0)
            row = np.zeros(tot); row[NV + Rn + r] = 1; row[NV + r] = -1; rows.append(row); bb.append(0.0)
        # target Copeland = 0.5 sum(y1+y2) ; rival k: F_k + 1 - o_k ; need Cop_t >= F_k + 1 - o_k + 0.5
        for k in keep:
            row = np.zeros(tot); row[NV:NV + Rn] = -0.5; row[NV + Rn:] = -0.5
            row[NV + k] += -0.5; row[NV + Rn + k] += -0.5
            rows.append(row); bb.append(-(F[k] + 1 + 0.5))
        A_ub = np.array(rows); b_ub = np.array(bb)
        cost = np.concatenate([cost, np.zeros(2 * Rn)]); Kv = np.concatenate([Kv, np.zeros(2 * Rn)])
        nextra = 2 * Rn
    elif rule == 'plurality':
        cred = plurality_credit(S); mx = S.max(axis=0)
        # option 1 per task: become strictly best (level = best rival + EPSO) -> only meaningful variable per task
        # reuse level variables but only the top level (>= best rival) matters; collapse in-between levels is harmless:
        # a level below best rival changes no credit, so it is dominated (cost>0, no benefit). keep all, credit via level.
        # credit for target at level L on task j: 1 if L > max rival score; initial credit if unchanged.
        riv_max = riv.max(axis=0)
        ct = np.zeros(NV)                                       # target credit per variable
        for j in range(n):
            L = lvvals[j]
            ct[off[j]:off[j + 1]] = np.where(L > riv_max[j], 1.0, np.where(np.arange(len(L)) == 0, cred[t, j], 0.0))
        # rival credit per variable: initial credit unless target strictly best at that level
        cr = np.zeros((Rn, NV)); rc = np.delete(cred, t, axis=0)
        for j in range(n):
            L = lvvals[j]; blk = np.arange(off[j], off[j + 1])
            took = (L > riv_max[j])
            for kk in range(len(L)):
                cr[:, blk[kk]] = 0.0 if took[kk] else rc[:, j]
        keep = np.where(rc.sum(axis=1) > 0)[0]
        A = []; bb = []
        for k in keep:
            A.append(-ct + cr[k]); bb.append(-PLM)              # ct.z > cr_k.z
        if len(keep) == 0 or True:
            A.append(-ct); bb.append(-PLM)                      # target credit > 0
        A_ub = np.array(A); b_ub = np.array(bb)
        nextra = 0
    else:
        raise ValueError(rule)
    tot = NV + nextra
    # one level per task
    A_eq = np.zeros((n, tot)); 
    for j in range(n): A_eq[j, off[j]:off[j + 1]] = 1.0
    b_eq = np.ones(n)
    if A_ub.shape[1] < tot:
        A_ub = np.hstack([A_ub, np.zeros((A_ub.shape[0], tot - A_ub.shape[1]))])
    integrality = np.ones(tot); lb = np.zeros(tot); ubv = np.ones(tot)
    if objective == 'K': c = Kv + 1e-5 * cost / 100.0
    else: c = cost + 1e-4 * Kv
    res = _solve(c, A_ub, b_ub, A_eq, b_eq, integrality, lb, ubv, time_limit)
    if res.status == 0 and res.x is not None:
        z = np.round(res.x[:NV])
        return dict(feasible=True, K=int((z * Kv[:NV]).sum()), L1=float((z * cost[:NV]).sum()), optimal=True, already=False,
                    delta=_delta(z, off, opts, n))
    if res.status == 2:  # infeasible
        return dict(feasible=False, K=np.nan, L1=np.nan, optimal=True, already=False)
    # time limit
    if res.x is not None:
        z = np.round(res.x[:NV])
        return dict(feasible=True, K=int((z * Kv[:NV]).sum()), L1=float((z * cost[:NV]).sum()), optimal=False, already=False,
                    delta=_delta(z, off, opts, n))
    return dict(feasible=None, K=np.nan, L1=np.nan, optimal=False, already=False)

def _delta(z, off, opts, n):
    d = np.zeros(n)
    for j in range(n):
        k = int(np.argmax(z[off[j]:off[j + 1]])); d[j] = opts[j][k][1]
    return d

def is_first(S, t, rule, delta):
    """apply boost delta to row t and check strict first place under `rule`."""
    S2 = np.array(S, float); S2[t] = S2[t] + delta
    sc = rule_scores(S2, rule)
    return bool(sc[t] > np.delete(sc, t).max() + 1e-12)
