"""lbmanip: minimal targeted investment needed for a target model to rank first on a
multi-task leaderboard, under different aggregation rules.

Setting.  S is an (N models x m tasks) score matrix (higher is better); t is the target row.
An *investment plan* is a vector delta in R^m_{>=0} with delta_j <= u_j (cap).  After the plan the
target's scores are s_t + delta; the other rows are unchanged ("no reaction, no spillover").
Depth  = min sum_j delta_j        (score points, L1)
Breadth = min #{j : delta_j > 0}  (tasks touched, L0), where each touched task may be raised by
          up to its cap u_j.
"First" means strictly first under the rule's aggregate.  All costs are infimum costs (epsilon -> 0):
to *pass* a rival in a task the target must reach that rival's score (ties are broken for the
target by an infinitesimal extra amount).

Rules
  target-only ("cardinal") rules: aggregate f(s_i) of a model's own scores:
     mean (optionally weighted), power means with p<1 (p=0 geometric, p=-1 harmonic, p=-inf min),
     median (lower median for even m), max.
  relational ("ordinal") rules: Borda (= mean rank / HELM mean win rate), Copeland, plurality.
"""
from __future__ import annotations
import numpy as np
from scipy import sparse
from scipy.optimize import milp, LinearConstraint, Bounds

EPS = 1e-12
FLOOR = 1e-3   # floor used inside geometric / harmonic means only
INF = float('inf')


# ----------------------------------------------------------------------------------------------
# Baseline aggregates
# ----------------------------------------------------------------------------------------------
def pmean(S, p, w=None):
    """Power mean along axis 1 (p=0 geometric; p=-inf min; p=+inf max)."""
    S = np.asarray(S, float)
    if np.isinf(p):
        return S.min(1) if p < 0 else S.max(1)
    w = np.full(S.shape[1], 1.0 / S.shape[1]) if w is None else np.asarray(w, float) / np.sum(w)
    S = np.maximum(S, FLOOR)   # scores of exactly 0 would zero out geometric/harmonic means
    if p == 0:
        return np.exp((np.log(S) * w).sum(1))
    return ((S ** p) * w).sum(1) ** (1.0 / p)


def median_low(S):
    S = np.sort(np.asarray(S, float), axis=1)
    m = S.shape[1]
    return S[:, (m + 1) // 2 - 1]  # ceil(m/2)-th smallest (1-indexed)


def pairwise_points(S):
    """P[i, j, l] doubled points of model i vs model l in task j: 2 win, 1 tie, 0 loss (diag 0)."""
    S = np.asarray(S, float)
    N = S.shape[0]
    gt = (S[:, None, :] > S[None, :, :]).astype(np.int8)  # [i, l, j]
    eq = (S[:, None, :] == S[None, :, :]).astype(np.int8)
    P = 2 * gt + eq
    P[np.arange(N), np.arange(N), :] = 0
    return P  # [i, l, j]


def borda_scores(S):
    """Doubled Borda points: sum over tasks and other models of 2*win + tie."""
    S = np.asarray(S, float)
    N, m = S.shape
    out = np.zeros(N)
    for j in range(m):
        col = S[:, j]
        srt = np.sort(col)
        less = np.searchsorted(srt, col, 'left')
        leq = np.searchsorted(srt, col, 'right')
        eq = leq - less - 1  # ties excluding self
        out += 2 * less + eq
    return out


def copeland_scores(S):
    S = np.asarray(S, float)
    N, m = S.shape
    wins = np.zeros((N, N))
    for j in range(m):
        c = S[:, j]
        wins += (c[:, None] > c[None, :]) + 0.5 * (c[:, None] == c[None, :])
    np.fill_diagonal(wins, m / 2)  # neutral
    O = np.where(wins > m / 2 + 1e-9, 1.0, np.where(np.abs(wins - m / 2) <= 1e-9, 0.5, 0.0))
    np.fill_diagonal(O, 0)
    return O.sum(1)


def plurality_scores(S):
    S = np.asarray(S, float)
    top = S == S.max(0, keepdims=True)
    return (top / top.sum(0, keepdims=True)).sum(1)


CARDINAL = {
    'mean': lambda S, w=None: pmean(S, 1, w),
    'geo': lambda S, w=None: pmean(S, 0),
    'harm': lambda S, w=None: pmean(S, -1),
    'min': lambda S, w=None: S.min(1),
    'median': lambda S, w=None: median_low(S),
    'max': lambda S, w=None: S.max(1),
}
ORDINAL = {'borda': borda_scores, 'copeland': copeland_scores, 'plurality': plurality_scores}
ALL_RULES = list(CARDINAL) + list(ORDINAL)


def aggregate(rule, S, w=None):
    if rule in CARDINAL:
        return CARDINAL[rule](np.asarray(S, float), w)
    return ORDINAL[rule](np.asarray(S, float))


def rank_of(vals, t, tol=1e-12):
    """Competition rank of t (1 = strictly best; ties share the pessimistic rank)."""
    return 1 + int((np.delete(vals, t) >= vals[t] - tol).sum())


def is_first(rule, S, t, w=None, tol=1e-12):
    v = aggregate(rule, S, w)
    return bool(v[t] > np.delete(v, t).max() + tol)


# ----------------------------------------------------------------------------------------------
# Caps
# ----------------------------------------------------------------------------------------------
def make_caps(S, t, mode='frontier', delta=None, ceiling=1.0):
    """u_j = max gain allowed in task j."""
    S = np.asarray(S, float)
    s = S[t]
    if mode == 'frontier':
        c = S.max(0)
    elif mode == 'ceiling':
        c = np.full(S.shape[1], ceiling)
    elif mode == 'delta':
        c = s + delta
        c = np.minimum(c, ceiling)
    else:
        raise ValueError(mode)
    return np.maximum(c - s, 0.0)


# ----------------------------------------------------------------------------------------------
# Cardinal rules: exact solvers (depth and breadth)
# Each returns dict(cost=..., k=..., delta=...) or cost=inf if infeasible.
# ----------------------------------------------------------------------------------------------
def _tau(rule, S, t, w=None):
    v = aggregate(rule, S, w)
    return np.delete(v, t).max(), v[t]


def solve_cardinal(rule, S, t, u, w=None):
    S = np.asarray(S, float)
    s = S[t]
    m = len(s)
    tau, ft = _tau(rule, S, t, w)
    if ft > tau + 1e-12:
        return dict(cost=0.0, k=0, delta=np.zeros(m), tau=tau, already=True)
    out = dict(tau=tau, already=False)
    if rule == 'mean':
        ww = np.full(m, 1.0 / m) if w is None else np.asarray(w, float) / np.sum(w)
        D = tau - (ww * s).sum()
        if (ww * u).sum() < D - 1e-12:
            return dict(cost=INF, k=INF, delta=None, **out)
        order = np.argsort(-ww, kind='stable')  # most value per unit first
        delta = np.zeros(m); rem = D
        for j in order:
            if rem <= 0: break
            g = min(u[j], rem / ww[j]); delta[j] = g; rem -= g * ww[j]
        # breadth: largest value-gains first
        gains = np.sort(ww * u)[::-1]
        k = 0 if D <= 1e-12 else int(np.searchsorted(np.cumsum(gains), D - 1e-9, 'left') + 1)
        return dict(cost=float(delta.sum()), k=k, delta=delta, **out)
    if rule in ('geo', 'harm', 'min'):
        p = {'geo': 0, 'harm': -1, 'min': -np.inf}[rule]
        if rule != 'min':
            s = np.maximum(s, FLOOR)
        top = s + u
        if pmean(top[None], p)[0] < tau - 1e-12:
            return dict(cost=INF, k=INF, delta=None, **out)
        if rule == 'min':
            delta = np.maximum(tau - s, 0.0)
        else:  # water-filling: find the lowest common level L with M_p(clip(L, s, s+u)) = tau
            lo, hi = s.min(), top.max()
            for _ in range(200):
                mid = 0.5 * (lo + hi)
                if pmean(np.clip(mid, s, top)[None], p)[0] >= tau: hi = mid
                else: lo = mid
            delta = np.clip(hi, s, top) - s
        # breadth: choose tasks with the largest increase of the separable potential phi
        if rule == 'min':
            need = int((s <= tau + 1e-12).sum())
            k = need  # every task at/below tau must be touched (feasible since top > tau)
        else:
            phi = (lambda x: np.log(x)) if rule == 'geo' else (lambda x: -1.0 / x)
            inc = np.sort(phi(top) - phi(s))[::-1]
            tgt = phi(np.array([tau]))[0] * m - phi(s).sum()
            k = int(np.searchsorted(np.cumsum(inc), tgt - 1e-9, 'left') + 1)
        return dict(cost=float(delta.sum()), k=k, delta=delta, **out)
    if rule == 'median':
        need_total = m // 2 + 1  # values strictly above tau
        above = int((s > tau + 1e-12).sum())
        need = need_total - above
        feas = (s + u >= tau - 1e-12) & ~(s > tau + 1e-12)
        cands = np.where(feas)[0]
        if len(cands) < need:
            return dict(cost=INF, k=INF, delta=None, **out)
        cost_j = np.maximum(tau - s[cands], 0.0)
        pick = cands[np.argsort(cost_j, kind='stable')[:need]]
        delta = np.zeros(m); delta[pick] = np.maximum(tau - s[pick], 0.0)
        return dict(cost=float(delta.sum()), k=need, delta=delta, **out)
    if rule == 'max':
        feas = s + u >= tau - 1e-12
        if not feas.any():
            return dict(cost=INF, k=INF, delta=None, **out)
        j = np.argmin(np.where(feas, tau - s, INF))
        delta = np.zeros(m); delta[j] = max(tau - s[j], 0.0)
        return dict(cost=float(delta[j]), k=1, delta=delta, **out)
    raise ValueError(rule)


# ----------------------------------------------------------------------------------------------
# Ordinal rules: MILP formulations (depth) and breadth MILP
# ----------------------------------------------------------------------------------------------
def _task_levels(S, t, u):
    """For every task j: the rivals not strictly below the target ("open" rivals) grouped by score.
    Returns per task: vals (ascending distinct thresholds >= s_tj and feasible under cap),
    and for each rival i the level index k(i,j) (or -1 if already strictly beaten, -2 if beyond cap)."""
    N, m = S.shape
    levels = []
    kidx = -np.ones((N, m), dtype=int)
    for j in range(m):
        col = S[:, j]
        sj = col[t]
        capj = sj + u[j]
        mask = (col >= sj - 0.0)
        mask[t] = False
        idx = np.where(mask)[0]
        vals = np.unique(col[idx])
        vals = vals[vals <= capj + 1e-12]
        for i in idx:
            pos = np.searchsorted(vals, col[i] - 1e-15)
            if pos < len(vals) and abs(vals[pos] - col[i]) < 1e-12:
                kidx[i, j] = pos
            else:
                kidx[i, j] = -2  # beyond cap: cannot be passed
        levels.append(vals)
    return levels, kidx


def _milp(c, A_rows, lb, ub, integrality, bounds_lo, bounds_hi, time_limit=120):
    A = sparse.csr_matrix(A_rows)
    res = milp(c, constraints=LinearConstraint(A, lb, ub), integrality=integrality,
               bounds=Bounds(bounds_lo, bounds_hi), options=dict(time_limit=time_limit, mip_rel_gap=1e-9))
    return res


class _Model:
    """Sparse constraint builder."""
    def __init__(self):
        self.rows, self.cols, self.vals = [], [], []
        self.lb, self.ub = [], []
        self.nr = 0
    def add(self, coefs: dict, lb, ub):
        for c, v in coefs.items():
            self.rows.append(self.nr); self.cols.append(c); self.vals.append(v)
        self.lb.append(lb); self.ub.append(ub); self.nr += 1
    def matrix(self, nc):
        return sparse.csr_matrix((self.vals, (self.rows, self.cols)), shape=(self.nr, nc))


def solve_ordinal(rule, S, t, u, time_limit=120, objective='depth', prune=True):
    """Exact (MILP) minimal investment for Borda / Copeland / plurality.
    objective='depth': min sum delta (levels cost their score increments)
    objective='breadth': min number of tasks touched; each touched task raised by its full cap u_j."""
    S = np.asarray(S, float)
    N, m = S.shape
    if is_first(rule, S, t):
        return dict(cost=0.0, k=0, already=True)
    if rule == 'plurality':
        return _plurality(S, t, u, objective)
    levels, kidx = _task_levels(S, t, u)
    base = aggregate(rule, S)
    nxt = 0
    if objective == 'depth':
        zid = []  # variable index of z[j][k]
        cost = []
        for j in range(m):
            ids = []
            prev = S[t, j]
            for v in levels[j]:
                ids.append(nxt); cost.append(v - prev); prev = v; nxt += 1
            zid.append(ids)
        nz = nxt
    else:  # breadth: one binary per task meaning "raise to cap"
        x0 = 0
        nz = m
        nxt = m
        cost = [1.0] * m
    cons = _Model()
    ub_extra = []

    def win_terms(i, j):
        """(const, var) for win'_{ij} in {0,1}: either a constant or a variable index."""
        if S[i, j] < S[t, j]:
            return 1, None
        k = kidx[i, j]
        if k == -2:
            return 0, None
        if objective == 'depth':
            return 0, zid[j][k]
        # breadth: raising task j to full cap passes rivals with score <= cap; ties are free
        if S[i, j] == S[t, j]:
            return 1, None
        if S[i, j] <= S[t, j] + u[j] + 1e-12:
            return 0, j
        return 0, None

    if objective == 'depth':
        for j in range(m):
            for k in range(1, len(zid[j])):
                cons.add({zid[j][k]: 1.0, zid[j][k - 1]: -1.0}, -np.inf, 0.0)  # nested
    # per-rival win structure
    cwin = np.zeros(N)           # constant wins of t over rival i
    wvars = [dict() for _ in range(N)]  # var -> multiplicity (0/1)
    for i in range(N):
        if i == t: continue
        for j in range(m):
            c, v = win_terms(i, j)
            cwin[i] += c
            if v is not None:
                wvars[i][v] = wvars[i].get(v, 0) + 1
    Wvar = nxt; nxt += 1   # total wins of t = sum_i,j win'_ij
    Wc = cwin.sum()
    row = {Wvar: 1.0}
    tot = {}
    for i in range(N):
        for v, mult in wvars[i].items():
            tot[v] = tot.get(v, 0) + mult
    for v, mult in tot.items():
        row[v] = row.get(v, 0) - mult
    cons.add(row, Wc, Wc)  # Wvar - sum mult*z = Wc

    integrality = None
    if rule == 'borda':
        # per-rival points of rival l against t at baseline (doubled)
        pts_vs_t = np.array([(2 * (S[l] > S[t]) + (S[l] == S[t])).sum() for l in range(N)])
        Bl = base
        Bt0 = base[t]
        for l in range(N):
            if l == t: continue
            if prune and Bl[l] < Bt0 - 1e-9:
                continue  # rival below target can never overtake (its points only fall)
            # 2W + 2*sum_j win'_lj >= 1 + B_l - P_l + 2m
            row = {Wvar: 2.0}
            for v, mult in wvars[l].items():
                row[v] = row.get(v, 0) + 2.0 * mult
            rhs = 1 + Bl[l] - pts_vs_t[l] + 2 * m - 2 * cwin[l]
            cons.add(row, rhs, np.inf)
        nvar = nxt
    elif rule == 'copeland':
        # rival-rival Copeland points (excluding t)
        wins = np.zeros((N, N))
        for j in range(m):
            c = S[:, j]
            wins += (c[:, None] > c[None, :]) + 0.5 * (c[:, None] == c[None, :])
        O = np.where(wins > m / 2 + 1e-9, 1.0, np.where(np.abs(wins - m / 2) <= 1e-9, 0.5, 0.0))
        np.fill_diagonal(O, 0)
        Cm = O.sum(1) - O[:, t]  # points vs other rivals only
        Ct0 = base[t]
        a_id, b_id = {}, {}
        ceil_h, floor_h1 = int(np.ceil(m / 2)), m // 2 + 1
        for i in range(N):
            if i == t: continue
            a_id[i] = nxt; nxt += 1
            b_id[i] = nxt; nxt += 1
            # c_i = cwin[i] + sum wvars  >= ceil(m/2)*a_i ; >= (floor(m/2)+1)*b_i
            for var, thr in ((a_id[i], ceil_h), (b_id[i], floor_h1)):
                row = {var: -float(thr)}
                for v, mult in wvars[i].items():
                    row[v] = row.get(v, 0) + mult
                cons.add(row, -cwin[i], np.inf)
        A_sum = {}
        for i in a_id:
            A_sum[a_id[i]] = 1.0; A_sum[b_id[i]] = 1.0
        for l in a_id:
            # A + a_l + b_l >= 2*Cm_l + 3
            if prune and Cm[l] + 1 < Ct0 - 1e-9:
                continue
            row = dict(A_sum)
            row[a_id[l]] = row[a_id[l]] + 1.0
            row[b_id[l]] = row[b_id[l]] + 1.0
            cons.add(row, 2 * Cm[l] + 3, np.inf)
        nvar = nxt
    else:
        raise ValueError(rule)
    c = np.zeros(nvar)
    c[:nz] = cost
    lo = np.zeros(nvar); hi = np.ones(nvar)
    hi[Wvar] = N * m + 1
    integ = np.ones(nvar)
    A = cons.matrix(nvar)
    res = milp(c, constraints=LinearConstraint(A, np.array(cons.lb, float), np.array(cons.ub, float)),
               integrality=integ, bounds=Bounds(lo, hi),
               options=dict(time_limit=time_limit, mip_rel_gap=1e-9))
    if res.status == 2 or res.x is None:
        return dict(cost=INF, k=INF, already=False, status=res.status)
    z = np.round(res.x[:nz]).astype(int)
    if objective == 'depth':
        delta = np.zeros(m)
        for j in range(m):
            ks = [k for k, i in enumerate(zid[j]) if z[i] == 1]
            if ks:
                delta[j] = levels[j][max(ks)] - S[t, j]
        return dict(cost=float(delta.sum()), k=int((delta > 0).sum()), delta=delta, already=False,
                    status=res.status, optimal=(res.status == 0))
    delta = z * u
    return dict(cost=float(delta.sum()), k=int(z.sum()), delta=delta, already=False, status=res.status,
                optimal=(res.status == 0))


def _plurality(S, t, u, objective):
    N, m = S.shape
    top = S.max(0)
    rival_top = np.delete(S, t, axis=0).max(0)
    gap = np.maximum(rival_top - S[t], 0.0)            # cost to become strictly top in j
    feas = gap <= u + 1e-12
    # share of rival i in task j if the target does not take the task
    istop = (S == top)
    share = istop / istop.sum(0, keepdims=True)
    share[t] = 0
    free = gap <= 1e-15
    x_fixed_hi = np.where(feas, 1.0, 0.0)
    lo = np.where(free, 1.0, 0.0)
    # F_t' = sum_j x_j ; F_i' = sum_j (1-x_j) share_ij ;   F_t' >= F_i' + margin
    margin = 1e-3   # genuine score differences are multiples of >= 1/lcm(tie sizes) >> margin
    rows, lb = [], []
    for i in range(N):
        if i == t: continue
        # sum_j x_j (1 - share_ij) >= sum_j share_ij  + margin   - ... derive:
        # sum x_j >= sum share_ij - sum x_j share_ij + margin  <=> sum x_j (1+share_ij) >= sum share_ij + margin
        rows.append(1.0 + share[i]); lb.append(share[i].sum() + margin)
    scale = 1e3     # keep the strictness margin far above the solver's 1e-6 feasibility tolerance
    A = scale * np.array(rows)
    lb = [scale * v for v in lb]
    c = gap.copy() if objective == 'depth' else np.where(gap > 0, 1.0, 0.0)
    if objective == 'breadth':
        c = np.where(free, 0.0, 1.0)
    res = milp(c, constraints=LinearConstraint(A, np.array(lb), np.full(len(lb), np.inf)),
               integrality=np.ones(m), bounds=Bounds(lo, x_fixed_hi),
               options=dict(time_limit=60, mip_rel_gap=1e-9))
    if res.x is None or res.status == 2:
        return dict(cost=INF, k=INF, already=False)
    x = np.round(res.x)
    delta = x * gap if objective == 'depth' else x * np.maximum(gap, 0)
    if objective == 'breadth':
        delta = x * np.where(free, 0.0, u)
    return dict(cost=float(delta.sum()), k=int((delta > 0).sum()), delta=delta, already=False)


# ----------------------------------------------------------------------------------------------
# Unified front-end
# ----------------------------------------------------------------------------------------------
def min_investment(rule, S, t, u, w=None, time_limit=120):
    """Returns dict(depth=..., breadth=..., depth_delta=...). Infinite if the cap makes it impossible."""
    S = np.asarray(S, float)
    if rule in CARDINAL:
        r = solve_cardinal(rule, S, t, u, w)
        return dict(depth=r['cost'], breadth=r['k'], delta=r.get('delta'), already=r.get('already', False))
    rd = solve_ordinal(rule, S, t, u, time_limit, 'depth')
    if rd.get('already'):
        return dict(depth=0.0, breadth=0, delta=np.zeros(S.shape[1]), already=True)
    if not np.isfinite(rd['cost']):
        return dict(depth=INF, breadth=INF, delta=None, already=False)
    rb = solve_ordinal(rule, S, t, u, time_limit, 'breadth')
    return dict(depth=rd['cost'], breadth=rb['k'], delta=rd['delta'], already=False,
                optimal=rd.get('optimal', True) and rb.get('optimal', True))


def verify_plan(rule, S, t, delta, eps=1e-7, w=None):
    """Apply delta (+eps on every raised task, to break ties) and check the target is strictly first."""
    S2 = np.array(S, float, copy=True)
    d = np.asarray(delta, float)
    S2[t] = S2[t] + d + eps   # infinitesimal bonus everywhere = the epsilon->0 limit semantics
    return is_first(rule, S2, t, w, tol=0.0)
