"""Exact solvers for the price of first place under each rule.

price(rule, S, t, B, ...) returns the cheapest plan delta (m-vector, points, 0 <= delta_j <= min(B, ceil_j - S[t,j]))
making target t strictly first (margin eps_agg in the aggregate for aggregate rules; strictly more than every rival
for the rank rules; a boost passes a rival on a task only if it exceeds the rival's score by eps_task).
objective='depth': minimise the cost sum_j (kappa_j delta_j)^gamma; objective='breadth': minimise the number of
tasks touched (ties by cost).  Every returned plan is re-checked with rules.is_first on the modified score matrix.
"""
import time, itertools
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import csr_matrix, lil_matrix, hstack, vstack, coo_matrix
from . import rules as R

EPS_TASK = 1e-6   # points a boost must exceed a rival's score by to pass it
EPS_AGG = 1e-6    # margin (aggregate units) required to be strictly first under aggregate rules
INF = float("inf")


def _phi(d, kappa, gamma):
    return (kappa * d) ** gamma


def _plan(S, t, rule, delta, *, ceil, kappa, gamma, rivals, eps_agg, extra=None, status="optimal", gap=0.0, rkw=None, t0=None):
    delta = np.clip(np.asarray(delta, float), 0, None)
    delta[delta < 1e-9] = 0.0
    if rule == "copeland":   # fast exact re-check from the cached board scores (tests compare with the full recomputation)
        C = R.copeland_after_boost(S, t, S[t] + delta, R.copeland_cached(S))
        ok = bool(C[t] > C[rivals].max())
    else:
        S2 = S.copy()
        S2[t] = S2[t] + delta
        ok = bool(R.is_first(S2, t, rule, rivals, eps_agg=eps_agg, **(rkw or {})))
    p = dict(rule=rule, feasible=True, status=status, delta=delta, depth=float(delta.sum()),
             breadth=int((delta > 0).sum()), cost=float(_phi(delta, kappa, gamma).sum()), verified=ok, mip_gap=gap,
             seconds=(time.time() - t0) if t0 else None)
    if extra: p.update(extra)
    return p


def _infeasible(rule, m, status="infeasible", t0=None, gap=None):
    return dict(rule=rule, feasible=False, status=status, delta=np.zeros(m), depth=INF, breadth=m + 1, cost=INF,
                verified=True, mip_gap=gap, seconds=(time.time() - t0) if t0 else None)


def _zero(S, t, rule, m, **kw):
    return _plan(S, t, rule, np.zeros(m), status="already_first", **kw)


# ----------------------------------------------------------------------------------------------- mean family
def _fill(w, kappa, gamma, caps, G):
    """min sum (kappa d)^gamma s.t. sum w d >= G, 0<=d<=caps (w>0 on the allowed set). Returns delta or None."""
    w = np.asarray(w, float)
    if np.sum(w * caps) < G - 1e-9:
        return None
    if gamma == 1:
        d = np.zeros(len(w))
        order = np.argsort(-(w / kappa), kind="stable")
        rem = G
        for j in order:
            if rem <= 1e-12: break
            if w[j] <= 0: continue
            x = min(caps[j], rem / w[j]); d[j] = x; rem -= w[j] * x
        return d
    lo, hi = 0.0, 1.0
    f = lambda lam: np.minimum(caps, (lam * w / (gamma * kappa ** gamma)) ** (1.0 / (gamma - 1)))
    while np.sum(w * f(hi)) < G: hi *= 2
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if np.sum(w * f(mid)) < G: lo = mid
        else: hi = mid
    return f(hi)


def solve_mean(S, t, B, *, rule, wts, ceil, kappa, gamma, rivals, objective, eps_agg, rkw, t0, kmax=None):
    m = S.shape[1]
    A = R.scores(S, rule, **rkw)
    V = A[rivals].max()
    wt = np.asarray(wts, float)
    G = (V + eps_agg) - A[t]
    G_raw = G
    kw = dict(ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, eps_agg=eps_agg, rkw=rkw, t0=t0)
    if G <= 0:
        return _zero(S, t, rule, m, **kw)
    caps = np.minimum(B, ceil - S[t])
    if kmax is not None and kmax < m:   # at most kmax tasks touched (linear cost): small MILP
        assert gamma == 1, "breadth-constrained depth is implemented for linear cost only"
        if kmax <= 0: return _infeasible(rule, m, t0=t0)
        c = np.concatenate([kappa, np.zeros(m)])
        A = csr_matrix(np.vstack([np.concatenate([wt, np.zeros(m)]), np.hstack([np.eye(m), -np.diag(caps)]),
                                  np.concatenate([np.zeros(m), np.ones(m)])]))
        lb = np.concatenate([[G], np.full(m, -np.inf), [-np.inf]]); ub = np.concatenate([[np.inf], np.zeros(m), [kmax]])
        res = _run_milp(c, A, lb, ub, np.concatenate([np.zeros(m), np.ones(m)]), np.zeros(2 * m), np.concatenate([np.maximum(caps, 0), np.ones(m)]), 60.0)
        if res.x is None: return _infeasible(rule, m, status=_status(res, t0), t0=t0)
        return _plan(S, t, rule, res.x[:m], status=_status(res, t0), gap=_gap(res), **kw)
    if objective == "breadth":
        order = np.argsort(-(wt * caps), kind="stable")
        cum = np.cumsum(wt[order] * caps[order])
        if cum[-1] < G - 1e-9: return _infeasible(rule, m, t0=t0)
        k = int(np.searchsorted(cum, G - 1e-9) + 1)
        sel = np.zeros(m, bool); sel[order[:k]] = True
        c2 = np.where(sel, caps, 0.0)
        d = _fill(np.where(sel, wt, 0.0), kappa, gamma, c2, G)
    else:
        d = _fill(wt, kappa, gamma, caps, G)
        if d is None: return _infeasible(rule, m, t0=t0)
    return _plan(S, t, rule, d, **kw)


# ----------------------------------------------------------------------------------------------- quantile rules
def solve_quantile(S, t, B, *, r, ceil, kappa, gamma, rivals, objective, eps_agg, t0, kmax=None):
    """r-th largest score (r=1 max, r=m min, r=(m+1)/2 odd median)."""
    N, m = S.shape
    rkw = dict(r=r)
    A = R.scores(S, "quantile", r=r)
    V = A[rivals].max() + eps_agg
    kw = dict(ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, eps_agg=eps_agg, rkw=dict(r=r), t0=t0)
    rule = "quantile"
    s = S[t]
    a = int((s >= V - 1e-12).sum())
    need = r - a
    if need <= 0: return _zero(S, t, rule, m, **kw)
    caps = np.minimum(B, ceil - s)
    d = V - s
    cand = np.where((s < V - 1e-12) & (d <= caps + 1e-12))[0]
    if len(cand) < need or (kmax is not None and need > kmax): return _infeasible(rule, m, t0=t0)
    cost = _phi(d[cand], kappa[cand], gamma)
    pick = cand[np.argsort(cost, kind="stable")[:need]]
    delta = np.zeros(m); delta[pick] = d[pick]
    return _plan(S, t, rule, delta, **kw)


def solve_median_even(S, t, B, *, ceil, kappa, gamma, rivals, objective, eps_agg, t0, exact_dp_limit=12):
    """Median of an even number of tasks = mean of the two middle scores.  Enumerate the break-points of the
    piecewise-linear cost over the upper threshold p (q = 2V - p) and solve each by dynamic programming."""
    N, m = S.shape
    assert m % 2 == 0 and m <= exact_dp_limit
    a = m // 2
    A = R.scores(S, "median")
    V = A[rivals].max() + eps_agg
    kw = dict(ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, eps_agg=eps_agg, rkw={}, t0=t0)
    s = S[t]
    if A[t] >= V - 1e-12: return _zero(S, t, "median", m, **kw)
    caps = np.minimum(B, ceil - s)
    cands = {V}
    for j in range(m):
        for x in (s[j], s[j] + caps[j], 2 * V - s[j], 2 * V - s[j] - caps[j]):
            if V - 1e-12 <= x <= 100 + 1e-9: cands.add(float(x))
    BIG = 1e7

    def solve_at(p):
        """Cheapest plan with the upper middle score >= p and the lower one >= q = 2V - p (DP over the two counts)."""
        q = 2 * V - p
        # per task options: (class, cost, delta): class 2 => >= p ; 1 => >= q only; 0 => neither
        dp = {(0, 0): (0.0, np.zeros(m))}
        for j in range(m):
            opts = []
            cls0 = 2 if s[j] >= p - 1e-12 else (1 if s[j] >= q - 1e-12 else 0)
            opts.append((cls0, 0.0, 0.0, 0))
            if p - s[j] <= caps[j] + 1e-12 and s[j] < p - 1e-12:
                dd = p - s[j]; opts.append((2, float(_phi(dd, kappa[j], gamma)), dd, 1))
            if cls0 == 0 and q - s[j] <= caps[j] + 1e-12:
                dd = q - s[j]; opts.append((1, float(_phi(dd, kappa[j], gamma)), dd, 1))
            nd = {}
            for (np_, nq_), (sc, vec) in dp.items():
                for cls, c, dd, touched in opts:
                    np2 = min(a, np_ + (cls == 2)); nq2 = min(a + 1, nq_ + (cls >= 1))
                    val = sc + (touched * BIG if objective == "breadth" else 0.0) + c
                    if (np2, nq2) not in nd or val < nd[(np2, nq2)][0]:
                        v2 = vec.copy(); v2[j] = dd; nd[(np2, nq2)] = (val, v2)
            dp = nd
        return dp.get((a, a + 1))

    best = (INF, INF, None)
    cs = sorted(cands)
    if gamma != 1:
        # convex cost: the optimum over p is not at a break-point; refine on a grid between break-points, then by golden section
        # (certified only up to the tolerance below; the plan itself is always re-verified)
        grid = sorted({float(x) for lo, hi in zip(cs[:-1], cs[1:]) for x in np.linspace(lo, hi, 25)} | set(cs))
        vals = [(solve_at(x) or (INF, None))[0] for x in grid]
        for i in np.argsort(vals)[:3]:
            lo, hi = grid[max(i - 1, 0)], grid[min(i + 1, len(grid) - 1)]
            for _ in range(40):
                m1, m2 = lo + (hi - lo) / 2.618, hi - (hi - lo) / 2.618
                f1, f2 = (solve_at(m1) or (INF, None))[0], (solve_at(m2) or (INF, None))[0]
                if f1 < f2: hi = m2
                else: lo = m1
            cs = cs + [0.5 * (lo + hi)]
    for p in sorted(set(cs)):
        r = solve_at(p)
        if r is not None and r[0] < best[0]: best = (r[0], 0, r[1])
    if best[2] is None: return _infeasible("median", m, t0=t0)
    return _plan(S, t, "median", best[2], **kw)


# ----------------------------------------------------------------------------------------------- MILP helpers
def _run_milp(c, A, lb, ub, integrality, bounds_lo, bounds_hi, time_limit):
    res = milp(c, constraints=LinearConstraint(A, lb, ub) if A is not None else None, integrality=integrality,
               bounds=Bounds(bounds_lo, bounds_hi), options=dict(time_limit=time_limit, mip_rel_gap=1e-9, disp=False))
    return res


def _gap(res):
    g = getattr(res, "mip_gap", None)
    return float(g) if g is not None else None


def _status(res, t0):
    if res.status == 0: return "optimal"
    if res.status == 1: return "time_limit"
    return "infeasible" if res.status == 2 else "failed"


# ----------------------------------------------------------------------------------------------- plurality
def solve_plurality(S, t, B, *, ceil, kappa, gamma, rivals, objective, eps_agg, eps_task, time_limit, t0, kmax=None):
    N, m = S.shape
    kw = dict(ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, eps_agg=eps_agg, rkw={}, t0=t0)
    if R.is_first(S, t, "plurality", rivals): return _zero(S, t, "plurality", m, **kw)
    others = np.delete(np.arange(N), t)
    top_oth = S[others].max(axis=0)                       # best rival score on each task
    caps = np.minimum(B, ceil - S[t])
    wins_all = R.plurality_scores(S)
    t_wins = (S[t] > top_oth)
    d = top_oth - S[t] + eps_task
    cand = np.where((~t_wins) & (d <= caps + 1e-12))[0]
    mc = len(cand)
    # rival i's strict wins: tasks where s_ij > every other model's score incl. t
    best_all = S.max(axis=0)
    uniq = (S == best_all).sum(axis=0) == 1
    win_owner = np.where(uniq, S.argmax(axis=0), -1)
    wins_t0 = float(t_wins.sum())
    rows, lbs = [], []
    # constraint per rival i: wins_t0 + sum x_j - (w_i - sum_{j in W_i} x_j) >= 1
    for i in np.array(rivals):
        wi = float((win_owner == i).sum())
        coef = np.array([1.0 + (win_owner[j] == i) for j in cand]) if mc else np.zeros(0)
        rows.append(coef); lbs.append(1.0 + wi - wins_t0)
    if mc == 0: return _infeasible("plurality", m, t0=t0)
    # keep the binding set small: only rivals with at least as many wins as could matter, plus a generic rival with 0 wins
    A = np.array(rows)
    # remove duplicate rows (many rivals with 0 wins)
    keyset = {}
    for row, lb in zip(A, lbs):
        key = (tuple(row), lb)
        keyset[key] = (row, lb)
    A = np.array([k[0] for k in keyset.values()]); lbv = np.array([k[1] for k in keyset.values()])
    cost = _phi(d[cand], kappa[cand], gamma)
    if objective == "breadth":
        c = 1.0 + 1e-4 * cost / (cost.max() + 1e-12)
    else:
        c = cost
    ubv = np.full(len(lbv), np.inf)
    if kmax is not None:
        A = np.vstack([A, np.ones((1, mc))]); lbv = np.append(lbv, -np.inf); ubv = np.append(ubv, kmax)
    res = _run_milp(c, A, lbv, ubv, np.ones(mc), np.zeros(mc), np.ones(mc), time_limit)
    st = _status(res, t0)
    if res.x is None: return _infeasible("plurality", m, status=st, t0=t0)
    delta = np.zeros(m); delta[cand[res.x > 0.5]] = d[cand[res.x > 0.5]]
    return _plan(S, t, "plurality", delta, status=st, gap=_gap(res), **kw)


# ----------------------------------------------------------------------------------------------- Borda
def solve_borda(S, t, B, *, ceil, kappa, gamma, rivals, objective, eps_agg, eps_task, time_limit, t0, max_iter=40, kmax=None):
    """Level MILP (one multiple-choice group per task); rival constraints are added lazily until the plan is first."""
    N, m = S.shape
    kw = dict(ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, eps_agg=eps_agg, rkw={}, t0=t0)
    if R.is_first(S, t, "borda", rivals): return _zero(S, t, "borda", m, **kw)
    caps = np.minimum(B, ceil - S[t])
    others = np.delete(np.arange(N), t)
    A0 = R.borda_scores(S)
    # levels per task
    lev_task, lev_d, lev_du, lev_v = [], [], [], []
    for j in range(m):
        col = S[others, j]
        vs = np.unique(col[(col >= S[t, j] - 1e-12) & (col - S[t, j] + eps_task <= caps[j] + 1e-12)])
        if len(vs) == 0: continue
        srt = np.sort(col)
        u0 = np.searchsorted(srt, S[t, j], side="left") + 0.5 * (np.searchsorted(srt, S[t, j], side="right") - np.searchsorted(srt, S[t, j], side="left"))
        for v in vs:
            L = v + eps_task
            lev_task.append(j); lev_d.append(L - S[t, j]); lev_v.append(v)
            lev_du.append(np.searchsorted(srt, L, side="left") - u0)   # others strictly below L (L is never an existing score)
    nL = len(lev_task)
    if nL == 0: return _infeasible("borda", m, t0=t0)
    lev_task = np.array(lev_task); lev_d = np.array(lev_d); lev_du = np.array(lev_du, float); lev_v = np.array(lev_v)
    cost = _phi(lev_d, kappa[lev_task], gamma)
    c = (1.0 + 1e-4 * cost / (cost.max() + 1e-12)) if objective == "breadth" else cost
    # multiple-choice rows
    G = coo_matrix((np.ones(nL), (lev_task, np.arange(nL))), shape=(m, nL)).tocsr()
    rowsR, lbR = [], []
    active = list(np.array(rivals)[np.argsort(-A0[rivals])[:3]])
    seen = set(active)
    t_pair = None
    best = None
    for it in range(max_iter):
        rows, lbs = [], []
        for i in active:
            # coefficient of level l in rival i's constraint: du_l + reduction of i
            si = S[i, lev_task]; st_ = S[t, lev_task]
            wgt = np.where(si > st_ + 1e-12, 1.0, np.where(np.abs(si - st_) <= 1e-12, 0.5, 0.0))
            red = wgt * (si <= lev_v + 1e-12)
            rows.append(lev_du + red); lbs.append(0.5 - (A0[t] - A0[i]))
        Aub = np.vstack(rows)
        Afull = vstack([G, csr_matrix(Aub)] + ([csr_matrix(np.ones((1, nL)))] if kmax is not None else [])).tocsr()
        lb = np.concatenate([np.zeros(m), lbs] + ([[-np.inf]] if kmax is not None else []))
        ub = np.concatenate([np.ones(m), np.full(len(lbs), np.inf)] + ([[kmax]] if kmax is not None else []))
        res = _run_milp(c, Afull, lb, ub, np.ones(nL), np.zeros(nL), np.ones(nL), time_limit)
        st = _status(res, t0)
        if res.x is None:
            return _infeasible("borda", m, status=st, t0=t0)
        delta = np.zeros(m)
        ch = res.x > 0.5
        delta[lev_task[ch]] = lev_d[ch]
        S2 = S.copy(); S2[t] += delta
        A2 = R.borda_scores(S2)
        viol = [i for i in rivals if A2[i] >= A2[t] - 1e-9 and i not in seen]
        if not viol:
            return _plan(S, t, "borda", delta, status=st, gap=_gap(res), **kw)
        viol = sorted(viol, key=lambda i: -A2[i])[:8]
        active += viol; seen.update(viol)
    return _plan(S, t, "borda", delta, status="lazy_iter_limit", gap=None, **kw)


# ----------------------------------------------------------------------------------------------- Copeland
def solve_copeland(S, t, B, *, ceil, kappa, gamma, rivals, objective, eps_agg, eps_task, time_limit, t0, kmax=None):
    """MILP: continuous boosts delta_j, binary y_ij (t passes rival i on task j), pair-outcome binaries W_i, T_i.
    The pair outcomes are only lower-bounded by the boosts, so the model cannot overstate t's Copeland score."""
    N, m = S.shape
    kw = dict(ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, eps_agg=eps_agg, rkw={}, t0=t0)
    C0 = R.copeland_cached(S)
    if C0[t] > C0[rivals].max(): return _zero(S, t, "copeland", m, **kw)
    caps = np.minimum(B, ceil - S[t])
    others = np.delete(np.arange(N), t)
    win = (S[t][None, :] > S[others]).sum(1); los = (S[t][None, :] < S[others]).sum(1)
    D0 = (win - los).astype(float)                       # D_i0 for rivals in `others` order
    pos = {int(i): k for k, i in enumerate(others)}
    beaten = D0 > 0
    U0 = np.where(~beaten)[0]                            # indices into `others` not yet beaten
    nU = len(U0)
    # base_r: Copeland score of rival r among all models except t
    out_rt = np.where(D0 > 0, 0.0, np.where(D0 == 0, 0.5, 1.0))     # what r earns against t now
    base = C0[others] - out_rt
    C_beat0 = float(beaten.sum())
    # variables: delta (m) | y (pairs) | W (nU) | T (nU) | u (m, breadth)
    pairs = []
    for ui, k in enumerate(U0):
        i = others[k]
        for j in range(m):
            if S[i, j] >= S[t, j] - 1e-12 and S[i, j] - S[t, j] + eps_task <= caps[j] + 1e-12:
                pairs.append((ui, j, S[i, j] - S[t, j] + eps_task, 2.0 if S[i, j] > S[t, j] + 1e-12 else 1.0))
    nP = len(pairs)
    nv = m + nP + 2 * nU + m
    iy, iW, iT, iu = m, m + nP, m + nP + nU, m + nP + 2 * nU
    rows_i, rows_j, vals, lbs, ubs = [], [], [], [], []
    r = 0
    def add(coefs, lb, ub):
        nonlocal r
        for j_, v_ in coefs: rows_i.append(r); rows_j.append(j_); vals.append(v_)
        lbs.append(lb); ubs.append(ub); r += 1
    for p, (ui, j, d, a) in enumerate(pairs):
        add([(j, 1.0), (iy + p, -d)], 0.0, np.inf)               # delta_j >= d y
    by_u = [[] for _ in range(nU)]
    for p, (ui, j, d, a) in enumerate(pairs): by_u[ui].append((iy + p, a))
    for ui in range(nU):
        Dk = D0[U0[ui]]
        add(by_u[ui] + [(iW + ui, -(1.0 - Dk)), (iT + ui, Dk)], 0.0, np.inf)   # sum a y >= (1-D0) W + (-D0) T
        add([(iW + ui, 1.0), (iT + ui, 1.0)], -np.inf, 1.0)
    tot = [(iW + ui, 1.0) for ui in range(nU)] + [(iT + ui, 0.5) for ui in range(nU)]
    Rset = [int(i) for i in rivals]
    if nU or True:
        # rivals already beaten (not in U0): single constraint with the largest base
        rb = [pos[i] for i in Rset if beaten[pos[i]]]
        if rb:
            add(tot, base[rb].max() + 0.5 - C_beat0, np.inf)
        for i in Rset:
            k = pos[i]
            if not beaten[k]:
                ui = int(np.where(U0 == k)[0][0])
                add(tot + [(iW + ui, 1.0), (iT + ui, 0.5)], base[k] + 1.0 + 0.5 - C_beat0, np.inf)
    for j in range(m):
        add([(iu + j, caps[j] if caps[j] > 0 else 1.0), (j, -1.0)], 0.0, np.inf)   # u_j * cap >= delta_j
    if kmax is not None: add([(iu + j, 1.0) for j in range(m)], -np.inf, kmax)
    A = csr_matrix((vals, (rows_i, rows_j)), shape=(r, nv))
    cvec = np.zeros(nv)
    if gamma == 1:
        cc = kappa.copy()
    else:
        cc = kappa ** gamma * np.maximum(caps, 1e-9) ** (gamma - 1)      # chord (upper) approximation, flagged in output
    if objective == "breadth":
        cvec[iu:iu + m] = 1.0; cvec[:m] = 1e-4 * cc / (cc.max() * max(caps.max(), 1e-9) + 1e-12)
    else:
        cvec[:m] = cc
    integ = np.zeros(nv); integ[iy:] = 1
    lo = np.zeros(nv); hi = np.concatenate([caps, np.ones(nv - m)])
    res = _run_milp(cvec, A, np.array(lbs), np.array(ubs), integ, lo, hi, time_limit)
    st = _status(res, t0)
    if res.x is None: return _infeasible("copeland", m, status=st, t0=t0)
    delta = res.x[:m].copy()
    # tidy: boosts are only needed up to the highest passed rival; recompute from y
    need = np.zeros(m)
    for p, (ui, j, d, a) in enumerate(pairs):
        if res.x[iy + p] > 0.5: need[j] = max(need[j], d)
    delta = need
    return _plan(S, t, "copeland", delta, status=st, gap=_gap(res), **kw)


# ----------------------------------------------------------------------------------------------- dispatch
def price(rule, S, t, B, *, ceil=100.0, kappa=None, gamma=1, rivals=None, objective="depth", eps_agg=EPS_AGG,
          eps_task=EPS_TASK, sigma=None, r=None, w=None, time_limit=120.0, kmax=None):
    """Cheapest plan making t first.  rule in rules.RULES or 'quantile' (with r) or 'gmean' (not implemented)."""
    t0 = time.time()
    S = np.asarray(S, float)
    N, m = S.shape
    ceil = np.broadcast_to(np.asarray(ceil, float), (m,)).copy()
    kappa = np.ones(m) if kappa is None else np.broadcast_to(np.asarray(kappa, float), (m,)).copy()
    rivals = np.delete(np.arange(N), t) if rivals is None else np.array([i for i in rivals if i != t])
    if rule == "mean":
        wts = np.ones(m) / m if w is None else np.asarray(w, float) / np.sum(w)
        return solve_mean(S, t, B, rule="mean", wts=wts, ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective=objective,
                          eps_agg=eps_agg, rkw=dict(w=w) if w is not None else {}, t0=t0, kmax=kmax)
    if rule == "zmean":
        sg = S.std(axis=0) if sigma is None else np.asarray(sigma, float)
        return solve_mean(S, t, B, rule="zmean", wts=1.0 / (m * sg), ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective=objective,
                          eps_agg=eps_agg, rkw=dict(sigma=sg), t0=t0, kmax=kmax)
    if rule == "min":
        return _relabel(solve_quantile(S, t, B, r=m, ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective=objective, eps_agg=eps_agg, t0=t0, kmax=kmax), "min")
    if rule == "quantile":
        return solve_quantile(S, t, B, r=r, ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective=objective, eps_agg=eps_agg, t0=t0, kmax=kmax)
    if rule == "median":
        if m % 2 == 1:
            return _relabel(solve_quantile(S, t, B, r=(m + 1) // 2, ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective=objective, eps_agg=eps_agg, t0=t0, kmax=kmax), "median")
        if kmax is not None and kmax < m:   # even m: enumerate task subsets (m <= 12), boosts only on the subset
            best = None
            for k in range(0, kmax + 1):
                for sub in itertools.combinations(range(m), k):
                    Bm = np.zeros(m); Bm[list(sub)] = np.broadcast_to(np.asarray(B, float), (m,))[list(sub)]
                    p = solve_median_even(S, t, Bm, ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective="depth", eps_agg=eps_agg, t0=t0)
                    if p["feasible"] and (best is None or p["cost"] < best["cost"] - 1e-12): best = p
            return best if best is not None else _infeasible("median", m, t0=t0)
        return solve_median_even(S, t, B, ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective=objective, eps_agg=eps_agg, t0=t0)
    if rule == "plurality":
        return solve_plurality(S, t, B, ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective=objective, eps_agg=eps_agg, eps_task=eps_task, time_limit=time_limit, t0=t0, kmax=kmax)
    if rule == "borda":
        return solve_borda(S, t, B, ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective=objective, eps_agg=eps_agg, eps_task=eps_task, time_limit=time_limit, t0=t0, kmax=kmax)
    if rule == "copeland":
        return solve_copeland(S, t, B, ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective=objective, eps_agg=eps_agg, eps_task=eps_task, time_limit=time_limit, t0=t0, kmax=kmax)
    raise ValueError(rule)


def _relabel(p, rule):
    p["rule"] = rule
    return p


def frontier(rule, S, t, B, *, kmax_cap=None, **kw):
    """Breadth-depth frontier: list of (k, cost, depth, feasible) for k = 0..m, cost = least cost of a plan touching at most k tasks."""
    m = S.shape[1]
    pk = price(rule, S, t, B, objective="breadth", **kw)
    if not pk["feasible"]: return [(k, np.inf, np.inf, False) for k in range(m + 1)]
    pinf = price(rule, S, t, B, objective="depth", **kw)
    out = []
    kmin = pk["breadth"]
    for k in range(m + 1):
        if k < kmin: out.append((k, np.inf, np.inf, False)); continue
        if k >= m or (out and out[-1][3] and out[-1][1] <= pinf["cost"] + 1e-9):
            out.append((k, pinf["cost"], pinf["depth"], True)); continue
        p = price(rule, S, t, B, objective="depth", kmax=k, **kw)
        out.append((k, p["cost"], p["depth"], p["feasible"]))
    return out
