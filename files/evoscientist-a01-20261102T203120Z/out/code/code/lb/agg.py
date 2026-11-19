"""Minimal-investment solvers for targeted-improvement manipulation of multi-task leaderboards.

Setting
-------
Board S (n models x m tasks, higher is better, units: score points). Target model t with score vector x = S[t].
An *investment* is a vector d >= 0 with y = x + d <= u (u = per-task cap, e.g. 100 or the best score observed
on the task, or x + g for a per-task gain bound g). All other models are frozen (no response).
Target *wins* under rule f if it is ranked first, with ties resolved in favour of the target
(so reported costs are infima of the cost of strictly winning).

Costs:  depth  c1(d) = sum_j d_j   (total score points bought)
        breadth c0(d) = |{j: d_j > 0}| (number of tasks that must be touched)

Rules (score-based): mean, gmean, median, trim20, q25, q75, min, max
Rules (rank-based):  borda (mean rank / Borda count), plural (number of first places)

All solvers return (cost, feasible) via `inf` for infeasible.
"""
import math
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.stats import rankdata

INF = float("inf")
SCORE_RULES = ["mean", "gmean", "median", "trim20", "q25", "q75", "min", "max"]
RANK_RULES = ["borda", "plural"]
ALL_RULES = SCORE_RULES + RANK_RULES
EPS = 1e-9


# ----------------------------------------------------------------------------- rule values
def n_trim(rule, m):
    if rule == "trim20":
        return int(math.floor(0.2 * m))
    if rule == "median":
        return (m - 1) // 2 if m % 2 == 1 else (m - 2) // 2
    raise ValueError(rule)


def kth_from_top(rule, m):
    """Rules that are a single order statistic: value of the k-th largest task."""
    if rule == "max":
        return 1
    if rule == "min":
        return m
    if rule == "median" and m % 2 == 1:
        return (m + 1) // 2
    if rule == "q25":
        return m - math.ceil(0.25 * m) + 1   # ceil(.25 m)-th smallest
    if rule == "q75":
        return m - math.ceil(0.75 * m) + 1   # ceil(.75 m)-th smallest
    return None


def f_values(rule, S):
    """Score-rule value for each row of S (n x m) -> (n,)."""
    S = np.asarray(S, float)
    m = S.shape[1]
    if rule == "mean":
        return S.mean(1)
    if rule == "gmean":
        with np.errstate(divide="ignore"):
            return np.exp(np.log(S).mean(1))
    k = kth_from_top(rule, m)
    if k is not None:
        return -np.sort(-S, axis=1)[:, k - 1]
    a = n_trim(rule, m)
    srt = np.sort(S, axis=1)
    return srt[:, a:m - a].mean(1)


# ----------------------------------------------------------------------------- closed forms
def order_stat_cost(x, u, k, tau):
    """k-th-largest rule. Need >= k tasks with value >= tau. Returns (l1, breadth) (both optimal simultaneously)."""
    x = np.asarray(x, float); u = np.asarray(u, float)
    above = x >= tau - EPS
    need = k - int(above.sum())
    if need <= 0:
        return 0.0, 0
    cand = (~above) & (u >= tau - EPS)
    if cand.sum() < need:
        return INF, INF
    deficits = np.sort((tau - x)[cand])
    return float(deficits[:need].sum()), need


def mean_cost(x, u, tau):
    x = np.asarray(x, float); u = np.asarray(u, float)
    m = len(x)
    B = m * (tau - x.mean())
    if B <= EPS:
        return 0.0, 0
    h = np.sort(u - x)[::-1]
    cs = np.cumsum(h)
    if cs[-1] < B - 1e-9:
        return INF, INF
    return float(B), int(np.searchsorted(cs, B - 1e-9) + 1)


def gmean_cost(x, u, tau):
    """Geometric mean: sum log y >= m log tau.  L1-optimal = water-filling y_j = clip(lam, x_j, u_j)."""
    x = np.asarray(x, float); u = np.asarray(u, float)
    m = len(x)
    if (x <= 0).any():
        raise ValueError("gmean needs positive scores")
    need = m * math.log(tau) - np.log(x).sum()
    if need <= EPS:
        return 0.0, 0
    gain = np.log(u / x)
    gs = np.sort(gain)[::-1]
    cs = np.cumsum(gs)
    if cs[-1] < need - 1e-12:
        return INF, INF
    k = int(np.searchsorted(cs, need - 1e-12) + 1)
    lo, hi = x.min(), u.max()
    for _ in range(200):
        lam = 0.5 * (lo + hi)
        if np.log(np.clip(lam, x, u)).sum() - np.log(x).sum() >= need:
            hi = lam
        else:
            lo = lam
    y = np.clip(hi, x, u)
    return float((y - x).sum()), k


# ----------------------------------------------------------------------------- trimmed mean (MILP)
def trim_cost_milp(x, u, a, tau, obj="l1", scale=None):
    """Exact min cost for the a-trimmed mean (drop a lowest and a highest) via MILP.
    TM(y)*(m-2a) = max_{|B|=a} [ sum_{j notin B} y_j - top_a(y_{notin B}) ]  (exists-B form), top_a via LP dual."""
    x = np.asarray(x, float); u = np.asarray(u, float)
    m = len(x)
    if a == 0:
        l1, br = mean_cost(x, u, tau)
        return (l1 if obj == "l1" else br)
    if obj == "br" and False:
        pass
    srt = np.sort(x)
    if srt[a:m - a].mean() >= tau - 1e-12:
        return 0.0
    sc = scale or max(1.0, float(np.max(u)))
    xs, us, ts = x / sc, u / sc, tau / sc
    U = 1.0 + 1e-9
    # variable layout: y[0:m], w[m:2m], v[2m:3m], s[3m:4m], lam[4m], b[4m+1:5m+1]
    N = 5 * m + 1
    iy, iw, iv, isl, ilam, ib = 0, m, 2 * m, 3 * m, 4 * m, 4 * m + 1
    lb = np.zeros(N); ub = np.zeros(N)
    lb[iy:iy + m] = xs; ub[iy:iy + m] = us
    lb[iw:iw + m] = 0; ub[iw:iw + m] = 1
    lb[iv:iv + m] = 0; ub[iv:iv + m] = U
    lb[isl:isl + m] = 0; ub[isl:isl + m] = U
    lb[ilam] = 0; ub[ilam] = U
    lb[ib:ib + m] = 0; ub[ib:ib + m] = 1
    integrality = np.zeros(N); integrality[iw:iw + m] = 1; integrality[ib:ib + m] = 1
    rows, lo_, hi_ = [], [], []

    def add(coefs, l, h):
        r = np.zeros(N)
        for i, c in coefs:
            r[i] += c
        rows.append(r); lo_.append(l); hi_.append(h)

    add([(iw + j, 1.0) for j in range(m)], a, a)
    for j in range(m):
        add([(iv + j, 1.0), (iy + j, -1.0)], -np.inf, 0.0)               # v <= y
        add([(iv + j, 1.0), (iw + j, U)], -np.inf, U)                     # v <= U(1-w)
        add([(iy + j, 1.0), (ilam, -1.0), (iw + j, -U), (isl + j, -1.0)], -np.inf, 0.0)  # s >= y-lam-Uw
        add([(iy + j, 1.0), (ib + j, -(us[j] - xs[j])), ], -np.inf, xs[j])  # y - x <= (u-x) b
    add([(iv + j, 1.0) for j in range(m)] + [(ilam, -float(a))] + [(isl + j, -1.0) for j in range(m)],
        (m - 2 * a) * ts - 1e-9, np.inf)
    c = np.zeros(N)
    if obj == "l1":
        c[iy:iy + m] = 1.0
    else:
        c[ib:ib + m] = 1.0
    res = milp(c, constraints=LinearConstraint(np.array(rows), lo_, hi_), integrality=integrality,
               bounds=Bounds(lb, ub), options={"mip_rel_gap": 1e-9, "time_limit": 60})
    if res.status != 0 or res.x is None:
        return INF
    y = res.x[iy:iy + m] * sc
    chk = np.sort(y)[a:m - a].mean()
    assert chk >= tau - 1e-4 * sc, (chk, tau)
    if obj == "l1":
        return float((y - x).sum())
    return float(round(res.fun))



def trim_l1_lp(x, u, a, tau):
    """Exact min depth for the a-trimmed mean when caps are x-monotone (u_j nondecreasing in x_j, e.g. a uniform
    ceiling or x_j+g).  Exchange argument: an optimal y can be taken order-preserving w.r.t. x, so TM(y) is the sum of
    the middle coordinates of the sorted vector and the problem is an LP in m variables."""
    from scipy.optimize import linprog
    x = np.asarray(x, float); u = np.asarray(u, float)
    m = len(x)
    if a == 0:
        return mean_cost(x, u, tau)[0]
    order = np.argsort(x, kind="stable")
    xs, us = x[order], u[order]
    assert (np.diff(us) >= -1e-9).all(), "caps must be nondecreasing in x for the LP; use trim_cost_milp"
    if xs[a:m - a].mean() >= tau - 1e-12:
        return 0.0
    # variables y_0..y_{m-1} (sorted); min sum y ; y>=x ; y<=u ; y_k<=y_{k+1} ; sum_{a<=k<m-a} y_k >= (m-2a) tau
    A = np.zeros((m, m)); b = np.zeros(m)
    for k in range(m - 1):
        A[k, k] = 1; A[k, k + 1] = -1
    A[m - 1, a:m - a] = -1.0; b[m - 1] = -(m - 2 * a) * tau
    r = linprog(np.ones(m), A_ub=A, b_ub=b, bounds=list(zip(xs, us)), method="highs")
    if r.status != 0:
        return INF
    return float(r.fun - xs.sum())


def trim_breadth_ub(x, u, a, tau):
    """Upper bound on min breadth for the a-trimmed mean: smallest k such that raising some contiguous window (in
    ascending-x order) of k tasks to its cap reaches tau.  Validated against brute force on small boards."""
    x = np.asarray(x, float); u = np.asarray(u, float)
    m = len(x)
    order = np.argsort(x, kind="stable")
    xs, us = x[order], u[order]
    if np.sort(xs)[a:m - a].mean() >= tau - 1e-12:
        return 0
    for k in range(1, m + 1):
        for s0 in range(0, m - k + 1):
            y = xs.copy(); y[s0:s0 + k] = us[s0:s0 + k]
            if np.sort(y)[a:m - a].mean() >= tau - 1e-9:
                return k
    return INF


# ----------------------------------------------------------------------------- rank-based rules
def borda_prep(S, t):
    """Pre-compute rival Borda totals (excluding t) for target t."""
    n, m = S.shape
    oth = np.array([i for i in range(n) if i != t])
    R = S[oth]
    pts = np.zeros(len(oth))
    for j in range(m):
        pts += rankdata(R[:, j], method="average") - 1.0
    return oth, R, pts


def borda_cost(S, t, u, want_breadth=True, prep=None):
    """Borda / mean-rank rule. Returns dict with l1_lb, l1_ub, k_lb, k_ub.
    Win condition (ties favour target):  B_t0 + G >= B_rr + m - p_r  for all rivals r, where G = total number of
    (rival, task) pairs newly passed and p_r = #tasks where r is passed.  With C_r = B_rr + m - p0_r:
       G >= max_r(B_rr) - B_t0  (necessary, p_r <= m-p0_r)   and   G >= max_r(C_r) - B_t0   (sufficient).
    Min cost to achieve gain >= T computed by exact multiple-choice-knapsack DP (levels = rival scores)."""
    n, m = S.shape
    x = S[t]
    oth, R, pts = prep if prep is not None else borda_prep(S, t)
    p0 = (R <= x[None, :]).sum(1)          # tasks where rival is already passed (ties favour target)
    Cr = pts + (m - p0)
    srt = np.sort(R, axis=0)
    base = np.array([np.searchsorted(srt[:, j], x[j], side="right") for j in range(m)])
    Bt0 = float(base.sum())
    Tub = int(math.ceil(Cr.max() - Bt0 - 1e-9))
    Tlb = int(math.ceil(pts.max() - Bt0 - 1e-9))
    out = {"l1_lb": 0.0, "l1_ub": 0.0, "k_lb": 0, "k_ub": 0}
    if Tub <= 0:
        return out
    Tcap = Tub
    # per-task options
    opts, maxgain = [], np.zeros(m)
    for j in range(m):
        col = srt[:, j]
        lv = np.unique(col[(col > x[j]) & (col <= u[j] + EPS)])
        gains = np.searchsorted(col, lv, side="right") - base[j]
        costs = lv - x[j]
        maxgain[j] = gains.max() if len(gains) else 0
        keep = np.ones(len(lv), bool)
        if len(lv):  # truncate after first option that saturates
            first = np.argmax(gains >= Tcap) if (gains >= Tcap).any() else len(lv) - 1
            keep[first + 1:] = False
        opts.append((costs[keep], np.minimum(gains[keep], Tcap).astype(int)))
    if maxgain.sum() < max(Tlb, 0) - 1e-9:
        return {"l1_lb": INF, "l1_ub": INF, "k_lb": INF, "k_ub": INF}
    dp = np.full(Tcap + 1, INF); dp[0] = 0.0
    for j in range(m):
        new = dp.copy()
        cj, gj = opts[j]
        for c, g in zip(cj, gj):
            # gain g: new[min(T+g, Tcap)] = min(old[T] + c)
            if g >= Tcap:
                new[Tcap] = min(new[Tcap], dp.min() + c)
            else:
                np.minimum(new[g:], dp[:Tcap + 1 - g] + c, out=new[g:])
                new[Tcap] = min(new[Tcap], dp[Tcap + 1 - g:].min() + c)
        dp = new
    # dp[T] = min cost to get gain exactly/saturating... convert to "at least T"
    atleast = np.minimum.accumulate(dp[::-1])[::-1]
    out["l1_ub"] = float(atleast[Tub])
    out["l1_lb"] = float(atleast[max(Tlb, 0)])
    mg = np.sort(maxgain)[::-1]; cs = np.cumsum(mg)
    out["k_ub"] = int(np.searchsorted(cs, Tub - 1e-9) + 1) if cs[-1] >= Tub else INF
    out["k_lb"] = int(np.searchsorted(cs, max(Tlb, 0) - 1e-9) + 1) if cs[-1] >= max(Tlb, 0) else INF
    return out



def borda_milp(S, t, u, obj="l1"):
    """Exact Borda (mean-rank) minimal investment via MILP; one-hot choice of a raise level per task.
    Intended for small boards (n <~ 120)."""
    n, m = S.shape
    x = S[t]
    oth, R, pts = borda_prep(S, t)
    p0 = (R <= x[None, :]).sum(1)
    Cr = pts + (m - p0)
    base = (R <= x[None, :]).sum(0)
    Bt0 = float(base.sum())
    if Cr.max() - Bt0 <= 1e-9:
        return 0.0
    var = []   # (task, level, cost, gain, passes(bool vec over rivals))
    for j in range(m):
        var.append((j, x[j], 0.0, 0, np.zeros(len(oth), bool)))
        lv = np.unique(R[:, j][(R[:, j] > x[j]) & (R[:, j] <= u[j] + EPS)])
        for l in lv:
            newly = (R[:, j] > x[j]) & (R[:, j] <= l)
            var.append((j, l, float(l - x[j]), int(newly.sum()), newly))
    V = len(var)
    A_eq = np.zeros((m, V))
    for k, v in enumerate(var):
        A_eq[v[0], k] = 1
    G = np.array([v[3] for v in var], float)
    P = np.array([v[4] for v in var], float).T      # rivals x V
    A_ub = P + G[None, :]
    lo = Cr - Bt0
    c = np.array([v[2] for v in var]) if obj == "l1" else np.array([0.0 if v[3] == 0 and v[2] == 0 else 1.0 for v in var])
    cons = [LinearConstraint(A_eq, 1, 1), LinearConstraint(A_ub, lo - 1e-9, np.inf)]
    r = milp(c, constraints=cons, integrality=np.ones(V), bounds=Bounds(0, 1), options={"time_limit": 120})
    return INF if r.status != 0 else float(r.fun)


def plural_cost(S, t, u):
    """Plurality (number of first places). Returns (l1, breadth) exact via MILP; ties favour target."""
    n, m = S.shape
    x = S[t]
    oth = np.array([i for i in range(n) if i != t])
    R = S[oth]
    top = R.max(0)
    owner = R.argmax(0)                     # rival that is first (lowest index among ties)
    A = x >= top - EPS
    nA = int(A.sum())
    free = np.where(~A)[0]
    allowed = [j for j in free if u[j] >= top[j] - EPS]
    cost_j = {j: float(top[j] - x[j]) for j in allowed}
    # variables z_j for allowed tasks
    owners = {}
    for j in free:
        owners.setdefault(owner[j], []).append(j)
    L = len(allowed)
    if L == 0:
        mx = max((len(v) for v in owners.values()), default=0)
        return (0.0, 0) if nA >= mx else (INF, INF)
    idx = {j: i for i, j in enumerate(allowed)}
    rows, lo_ = [], []
    for r, js in owners.items():
        # nA + sum_all z >= |O_r| - sum_{j in O_r} z_j   (taking a task adds 1 to target and removes 1 from owner)
        row = np.array([2.0 if (allowed[i] in js) else 1.0 for i in range(L)])
        rows.append(row); lo_.append(len(js) - nA)
    res = {}
    for obj in ("l1", "br"):
        c = np.array([cost_j[j] for j in allowed]) if obj == "l1" else np.ones(L)
        r = milp(c, constraints=LinearConstraint(np.array(rows), lo_, np.inf), integrality=np.ones(L),
                 bounds=Bounds(0, 1))
        res[obj] = (INF if r.status != 0 else float(r.fun))
    if res["l1"] == INF:
        return INF, INF
    # L1 optimal solution's breadth is not necessarily minimal -> report separately
    return res["l1"], res["br"]


# ----------------------------------------------------------------------------- dispatcher
def target_costs(rule, S, t, u, fv=None):
    """Return dict(l1=..., br=...) min depth / min breadth to make model t first under `rule`.
    S in score points (n x m); u per-task cap (m,). fv: precomputed f_values(rule,S) for score rules."""
    n, m = S.shape
    x = S[t]
    if rule in SCORE_RULES:
        fv = f_values(rule, S) if fv is None else fv
        fo = np.delete(fv, t)
        tau = fo.max()
        if fv[t] >= tau - 1e-12:
            return {"l1": 0.0, "br": 0}
        k = kth_from_top(rule, m)
        if rule == "mean":
            l1, br = mean_cost(x, u, tau)
        elif rule == "gmean":
            l1, br = gmean_cost(x, u, tau)
        elif k is not None:
            l1, br = order_stat_cost(x, u, k, tau)
        else:
            a = n_trim(rule, m)
            l1 = trim_l1_lp(x, u, a, tau)
            br = trim_breadth_ub(x, u, a, tau) if l1 < INF else INF
        return {"l1": l1, "br": br}
    if rule == "borda":
        if n <= 120:
            l1 = borda_milp(S, t, u, "l1")
            br = borda_milp(S, t, u, "br") if l1 < INF else INF
            return {"l1": l1, "br": br, "l1_lb": l1, "br_lb": br}
        o = borda_cost(S, t, u)
        return {"l1": o["l1_ub"], "br": o["k_ub"], "l1_lb": o["l1_lb"], "br_lb": o["k_lb"]}
    if rule == "plural":
        l1, br = plural_cost(S, t, u)
        return {"l1": l1, "br": br}
    raise ValueError(rule)
