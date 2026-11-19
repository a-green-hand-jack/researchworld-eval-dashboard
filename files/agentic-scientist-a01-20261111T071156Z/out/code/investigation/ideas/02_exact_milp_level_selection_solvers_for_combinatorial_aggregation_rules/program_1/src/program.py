"""Minimal targeted-boost planner for the *targeted-investment* leaderboard task (python_rpc_v1:handle).

PROBLEM
-------
A leaderboard is a score matrix X of shape [N, T] (N models = rows, T tasks = columns, scores on a
0..100 scale, higher is better). A *rule* maps X to one aggregate value per model (higher is better).
One row, the *target*, wants to be strictly first. It may raise its own scores on chosen tasks
(non-negative gains g[t], g[t] <= caps[t] - x[t], no spillover); nothing else changes.

  cost_model "l1_points": cost = sum_t g[t]            (caps[t] = 100)
  cost_model "l0_tasks" : cost = #{t : g[t] > 0}       (caps[t] = best score on task t + 1e-6)

RULES: mean, median, trimmed_mean_20, zscore_mean, borda, plurality, copeland, maximin.

PROTOCOL (unchanged from the starter): reset / load_begin / load_chunk / load_commit / solve; the solve
response is {"status": "plan", "gains": [{"task", "gain"}, ...]} or {"status": "infeasible"}.

THIS CANDIDATE
--------------
Per-rule minimal-investment solvers (``min_investment_*``). Exact (up to the numerical margin):
  * mean      closed form (L1: total gap * T, any allocation; L0: fewest tasks whose headroom covers it)
  * median    odd T: cheapest tasks to push above the best rival's median; even T: enumerate the pair of
              middle order statistics (exact for L1 with uniform caps and for L0)
  * maximin   raise every task below the best rival's minimum
  * plurality choose which tasks to win; rivals lose a win when the target overtakes their unique lead, so
              per task-count s the rival-specific quotas are met by cheapest-first picks (exact)
Heuristic (near-optimal, always verified, then coordinate-pruned):
  * trimmed   L1: "floor" plans (raise everything except the p lowest tasks to a common level, bisection);
              the rate-1 phase of the trimmed mean is solved exactly by this family
  * borda     L1: convex-hull (cost per rank passed) greedy over tasks; L0: greedy with restarts
  * copeland  L1: ratio greedy over (task, level) moves; L0: greedy with restarts
  * zscore    L1: floor family + steepest-ascent steps; L0: greedy with restarts
Every candidate plan (including the starter's baseline plan) is re-applied to X and re-scored with an
exact replica of the rules (``verify_ranks_first``); the cheapest verified plan is returned. Any internal
error falls back to the original starter routine.

MILP layer (added in this candidate): for borda, copeland, plurality and trimmed_mean_20 a level-selection MILP
(scipy.optimize.milp / HiGHS, time-limited, incumbent cost as cutoff) proposes an extra plan; all plans go through
``_select_best_verified`` and any MILP error or timeout keeps the heuristic plan. zscore_mean L0 gets an exchange polish.

The module also holds offline analysis helpers (data manifest, bootstrap CI, Holm-corrected paired Wilcoxon
tests, task subsampling, ablations, breadth-constrained cost curves). ``handle`` never calls them.
"""
import base64
import hashlib
import json
import time

import numpy as np

_MARGIN = 1e-7          # starter margin
_SUCCESS = 2e-8         # margin demanded locally (evaluator needs > 1e-9)
_ALREADY = 1e-8         # target already first if margin above this
_TARGET_EPS = 1.5e-7    # aggregate-scale margin aimed at by closed forms
_TIE_EPS = 1e-6         # per-task strict-win offset
_BUDGET_S = 5.0         # solve-time budget (evaluator limit is 12 s per episode in total)
_MILP_BUDGET_S = 4.0    # total HiGHS time per episode (all MILP solves together)
_EPISODE_LIMIT_S = 9.0  # wall-clock ceiling we plan for inside one solve (evaluator limit is 12 s)
_REFINE_RESERVE_S = 1.5  # kept free for verification / pruning after the MILP layer
_TRIM_MARGIN = 1e-5     # slack (on the sum of kept scores) demanded by the trimmed-mean MILP; pruning removes it
_STATE = {}

_SIMPLE = ("mean", "median", "trimmed_mean_20", "maximin")
_EXACT = ("mean", "median", "maximin", "plurality")


def _b64_array(spec_or_text, shape=None):
    raw = base64.b64decode(spec_or_text, validate=True)
    arr = np.frombuffer(raw, dtype="<f8")
    return arr.reshape(shape) if shape is not None else arr


def _scores(X, rule):
    N, T = X.shape
    if rule == "mean":
        return X.mean(axis=1)
    if rule == "median":
        return np.median(X, axis=1)
    if rule == "trimmed_mean_20":
        k = T // 5
        return np.sort(X, axis=1)[:, k:T - k].mean(axis=1)
    if rule == "zscore_mean":
        sd = X.std(axis=0)
        z = np.where(sd > 1e-12, (X - X.mean(axis=0)) / np.where(sd > 1e-12, sd, 1.0), 0.0)
        return z.mean(axis=1)
    if rule == "borda":
        total = np.zeros(N)
        for t in range(T):
            c = X[:, t]
            higher = (c[None, :] > c[:, None]).sum(axis=1)
            tied = (c[None, :] == c[:, None]).sum(axis=1) - 1
            total += 1.0 + higher + 0.5 * tied
        return -total / T
    if rule == "plurality":
        wins = np.zeros(N)
        for t in range(T):
            c = X[:, t]
            if (c == c.max()).sum() == 1:
                wins[int(np.argmax(c))] += 1.0
        return wins
    if rule == "copeland":
        better = (X[:, None, :] > X[None, :, :]).sum(axis=2)
        return (better > better.T).sum(axis=1) + 0.5 * ((better == better.T).sum(axis=1) - 1)
    if rule == "maximin":
        return X.min(axis=1)
    raise ValueError("unknown rule")


def _row_value(rule, y):
    T = y.shape[0]
    if rule == "mean":
        return float(y.mean())
    if rule == "median":
        return float(np.median(y))
    if rule == "trimmed_mean_20":
        k = T // 5
        return float(np.sort(y)[k:T - k].mean())
    if rule == "maximin":
        return float(y.min())
    raise ValueError("not a row-wise rule")


def verify_ranks_first(X, target, gains, rule, tol=1e-9):
    """Re-apply ``gains`` to row ``target`` of X and return (strictly_first, margin) under ``rule``."""
    X2 = np.array(X, dtype=float, copy=True)
    X2[target] = X2[target] + np.asarray(gains, dtype=float)
    v = _scores(X2, rule)
    m = float(v[target] - np.delete(v, target).max())
    return bool(m > tol), m


# --------------------------------------------------------------------------------------------------
# instance wrapper with fast, target-only margin evaluation
# --------------------------------------------------------------------------------------------------
class _Inst:
    def __init__(self, X, target, rule, cost_model, caps, deadline, seed=0):
        self.X = np.asarray(X, dtype=float)
        self.i = int(target)
        self.rule = rule
        self.cost_model = cost_model
        self.l1 = cost_model == "l1_points"
        self.N, self.T = self.X.shape
        self.x = self.X[self.i].copy()
        self.Xo = np.delete(self.X, self.i, axis=0)
        self.room = np.maximum(np.asarray(caps, dtype=float) - self.x, 0.0)
        self.cap = self.x + self.room
        self.deadline = deadline
        self.rng = np.random.default_rng(int(seed))
        self.theta = None
        if self.Xo.shape[0] == 0:
            return
        T = self.T
        if rule in _SIMPLE:
            self.theta = float(_scores(self.Xo, rule).max())
        elif rule == "borda":
            ro = np.zeros(self.Xo.shape[0])
            for t in range(T):
                c = self.Xo[:, t]
                higher = (c[None, :] > c[:, None]).sum(axis=1)
                tied = (c[None, :] == c[:, None]).sum(axis=1) - 1
                ro += 1.0 + higher + 0.5 * tied
            self.ro = ro
        elif rule == "copeland":
            better = (self.Xo[:, None, :] > self.Xo[None, :, :]).sum(axis=2)
            self.B = (better > better.T).sum(axis=1) + 0.5 * ((better == better.T).sum(axis=1) - 1)

    def out_of_time(self):
        return time.perf_counter() > self.deadline

    def ref_margin(self, y):
        X = self.X.copy()
        X[self.i] = y
        v = _scores(X, self.rule)
        return float(v[self.i] - np.delete(v, self.i).max())

    def margin(self, y):
        r = self.rule
        if r in _SIMPLE:
            return _row_value(r, y) - self.theta
        if r == "borda":
            Xo = self.Xo
            gt = Xo > y[None, :]
            eq = Xo == y[None, :]
            Rm = self.T + gt.sum() + 0.5 * eq.sum()
            cm = (Xo < y[None, :]) + 0.5 * eq
            return float((self.ro + cm.sum(axis=1)).min() - Rm) / self.T
        if r == "copeland":
            D = (y[None, :] > self.Xo).sum(axis=1) - (y[None, :] < self.Xo).sum(axis=1)
            res = (D > 0) + 0.5 * (D == 0)
            return float(res.sum() - (self.B + 1 - res).max())
        return self.ref_margin(y)

    def cope_obj(self, D):
        """Copeland margin with a small slope below D=0 so greedy search sees progress on plateaus."""
        res = (D > 0) + 0.5 * (D == 0)
        res = res + 0.05 * np.clip(D, -self.T, 0) / self.T
        return res.sum(axis=-1) - (self.B + 1 - res).max(axis=-1)

    def obj(self, y):
        if self.rule == "copeland":
            D = (y[None, :] > self.Xo).sum(axis=1) - (y[None, :] < self.Xo).sum(axis=1)
            return float(self.cope_obj(D))
        return self.margin(y)

    def clip(self, g):
        g = np.clip(np.nan_to_num(np.asarray(g, dtype=float)), 0.0, self.room)
        g[g < 1e-12] = 0.0
        return g

    def cost(self, g):
        return float(g.sum()) if self.l1 else float(np.count_nonzero(g > 0))


# --------------------------------------------------------------------------------------------------
# refinement helpers
# --------------------------------------------------------------------------------------------------
def _prune_l1(inst, g):
    """Coordinate-wise reduction of gains while the plan stays successful (bisection per task)."""
    g = g.copy()
    x = inst.x
    for _ in range(2):
        for t in sorted(np.where(g > 0)[0], key=lambda k: g[k]):
            if inst.out_of_time():
                return g
            if g[t] <= 0:
                continue
            g2 = g.copy()
            g2[t] = 0.0
            if inst.margin(x + g2) >= _SUCCESS:
                g = g2
                continue
            lo, hi = 0.0, g[t]
            for _ in range(40):
                mid = 0.5 * (lo + hi)
                g2[t] = mid
                if inst.margin(x + g2) >= _SUCCESS:
                    hi = mid
                else:
                    lo = mid
            g[t] = hi
    return g


def _prune_l0(inst, g):
    """Drop tasks one at a time while the plan stays successful."""
    g = g.copy()
    x = inst.x
    changed = True
    while changed:
        changed = False
        for t in sorted(np.where(g > 0)[0], key=lambda k: g[k]):
            if inst.out_of_time():
                return g
            g2 = g.copy()
            g2[t] = 0.0
            if inst.margin(x + g2) >= _SUCCESS:
                g = g2
                changed = True
    return g


def _refine(inst, g):
    """Verify with the exact rule replica; prune heuristic plans; return a verified plan or None."""
    g = inst.clip(g)
    if inst.ref_margin(inst.x + g) < _SUCCESS:
        return None
    if inst.rule not in _EXACT:
        g2 = _prune_l1(inst, g) if inst.l1 else _prune_l0(inst, g)
        g2 = inst.clip(g2)
        if inst.ref_margin(inst.x + g2) >= _SUCCESS:
            g = g2
    return g


# --------------------------------------------------------------------------------------------------
# generic searches
# --------------------------------------------------------------------------------------------------
def _baseline(inst):
    """Starter plan (uniform gain for L1, headroom-ordered fill for L0), via the fast margin."""
    x, room = inst.x, inst.room
    if inst.margin(x + room) < _SUCCESS:
        return None
    if inst.l1:
        lo, hi = 0.0, float(room.max())
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if inst.margin(x + np.minimum(mid, room)) >= _SUCCESS:
                hi = mid
            else:
                lo = mid
        return np.minimum(hi, room)
    g = np.zeros_like(room)
    for t in np.argsort(-room, kind="stable"):
        g[t] = room[t]
        if inst.margin(x + g) >= _SUCCESS:
            break
    return g


def _greedy_l0(inst, noise=0.0):
    """Add, one at a time, the task whose lift to its cap improves the objective most."""
    x, room, T = inst.x, inst.room, inst.T
    chosen = np.zeros(T, dtype=bool)
    y = x.copy()
    avail = room > 1e-12
    while True:
        if inst.margin(y) >= _SUCCESS:
            break
        if inst.out_of_time():
            return None
        vals = []
        for t in np.where(avail & ~chosen)[0]:
            y2 = y.copy()
            y2[t] = x[t] + room[t]
            vals.append((inst.obj(y2) + 1e-9 * room[t] / (1.0 + room.max()), int(t)))
        if not vals:
            return None
        vals.sort(reverse=True)
        pick = 0
        if noise > 0 and len(vals) > 1 and inst.rng.random() < noise:
            pick = int(inst.rng.integers(0, min(3, len(vals))))
        t = vals[pick][1]
        chosen[t] = True
        y[t] = x[t] + room[t]
    return np.where(chosen, room, 0.0)


def _greedy_l0_restarts(inst, runs=4):
    out = []
    for r in range(runs):
        if r > 0 and inst.out_of_time():
            break
        g = _greedy_l0(inst, noise=0.0 if r == 0 else 0.35)
        if g is not None:
            g = _prune_l0(inst, g)
            out.append(g)
    return out


def _floor_gains(inst, lam, p, order):
    y = inst.x.copy()
    mask = np.ones(inst.T, dtype=bool)
    mask[order[:p]] = False
    y[mask] = np.minimum(np.maximum(inst.x[mask], lam), inst.cap[mask])
    return y - inst.x


def _best_floor(inst):
    """L1 plans: leave the p lowest tasks alone, lift the others to a common floor lambda (bisection)."""
    x = inst.x
    order = np.argsort(x, kind="stable")
    hi0 = float(inst.cap.max())
    best, best_c = None, np.inf
    for p in range(inst.T):
        if inst.out_of_time():
            break
        if inst.margin(x + _floor_gains(inst, hi0, p, order)) < _SUCCESS:
            continue
        lo, hi = float(x.min()), hi0
        for _ in range(45):
            mid = 0.5 * (lo + hi)
            if inst.margin(x + _floor_gains(inst, mid, p, order)) >= _SUCCESS:
                hi = mid
            else:
                lo = mid
        g = _floor_gains(inst, hi, p, order)
        c = g.sum()
        if c < best_c:
            best, best_c = g, c
    return best


def _step_greedy_l1(inst, step=2.0):
    """Steepest ascent of the margin per point spent, in fixed steps (for non-monotone rules)."""
    x, room, T = inst.x, inst.room, inst.T
    g = np.zeros(T)
    for _ in range(600):
        base = inst.margin(x + g)
        if base >= _SUCCESS:
            return g
        if inst.out_of_time():
            return None
        best = (1e-15, -1, 0.0)
        for t in range(T):
            h = min(step, room[t] - g[t])
            if h <= 1e-12:
                continue
            g[t] += h
            m = inst.margin(x + g)
            g[t] -= h
            rate = (m - base) / h
            if rate > best[0]:
                best = (rate, t, h)
        if best[1] < 0:
            return None
        g[best[1]] += best[2]
    return None


# --------------------------------------------------------------------------------------------------
# per-rule minimal-investment solvers; each returns a list of candidate gain vectors
# --------------------------------------------------------------------------------------------------
def min_investment_mean(inst):
    """Exact: need sum(g) >= T*(best rival mean - own mean); L1 cost = that sum, L0 = fewest tasks covering it."""
    T, room = inst.T, inst.room
    need = max(0.0, T * (inst.theta + _TARGET_EPS - float(inst.x.mean())))
    order = np.argsort(-room, kind="stable")
    g = np.zeros(T)
    if not inst.l1:
        cs = np.cumsum(room[order])
        k = min(int(np.searchsorted(cs, need, side="left")) + 1, T)
        g[order[:k]] = room[order[:k]]
    else:
        rem = need
        for t in order:
            take = min(room[t], rem)
            g[t] = take
            rem -= take
            if rem <= 0:
                break
    return [g]


def min_investment_maximin(inst):
    """Exact: every task below the best rival minimum must be lifted to it."""
    thr = inst.theta + _TARGET_EPS
    low = inst.x < thr
    if np.any(inst.cap[low] < thr):
        return []
    g = np.zeros(inst.T)
    g[low] = thr - inst.x[low]
    return [g]


def min_investment_median(inst):
    """Exact: odd T needs (T+1)/2 tasks above the best rival median; even T enumerates the two middle values."""
    T, x, cap = inst.T, inst.x, inst.cap
    thr = inst.theta + _TARGET_EPS
    g = np.zeros(T)
    if T % 2 == 1:
        m = (T + 1) // 2
        have = x >= thr
        need = m - int(have.sum())
        if need <= 0:
            return [g]
        cand = np.where((~have) & (cap >= thr))[0]
        if cand.size < need:
            return []
        sel = cand[np.argsort(thr - x[cand], kind="stable")][:need]
        g[sel] = thr - x[sel]
        return [g]
    h = T // 2
    idx = np.arange(T)
    if inst.l1:
        order = np.argsort(-x, kind="stable")
        xs = x[order]
        bs = {float(thr)}
        bs.update(float(v) for v in x if v >= thr)
        bs.update(float(v) for v in cap if v >= thr)
        if 2 * thr - xs[h] >= thr:
            bs.add(float(2 * thr - xs[h]))
        best, best_c = None, np.inf
        for b in bs:
            a = 2 * thr - b
            y = x.copy()
            y[order[:h]] = np.maximum(x[order[:h]], b)
            y[order[h]] = max(x[order[h]], a)
            gg = y - x
            if np.any(gg > inst.room + 1e-12):
                continue
            c = gg.sum()
            if c < best_c:
                best, best_c = gg, c
        return [] if best is None else [best]
    V = np.unique(np.concatenate([x, cap]))
    V = V[V >= thr]
    best = None
    for b in V:
        a = 2 * thr - b
        free = idx[x >= b]
        f = min(h, free.size)
        bfree = free[np.argsort(-x[free], kind="stable")][:f]
        r1 = h - f
        raisable = idx[(x < b) & (cap >= b)]
        if raisable.size < r1:
            continue
        R1 = raisable[np.argsort(x[raisable], kind="stable")][:r1]
        chosen = np.zeros(T, dtype=bool)
        chosen[bfree] = True
        chosen[R1] = True
        rest = idx[~chosen]
        extra = -1
        if not np.any(x[rest] >= a):
            cand = rest[cap[rest] >= a]
            if cand.size == 0:
                continue
            extra = int(cand[0])
        cost = r1 + (1 if extra >= 0 else 0)
        if best is None or cost < best[0]:
            best = (cost, R1.copy(), extra)
    if best is None:
        return []
    g[best[1]] = inst.room[best[1]]
    if best[2] >= 0:
        g[best[2]] = inst.room[best[2]]
    return [g]


def min_investment_trimmed(inst):
    """L1: floor-family plans (exact in the rate-1 phase); L0: greedy with restarts."""
    if inst.l1:
        g = _best_floor(inst)
        return [] if g is None else [g]
    return _greedy_l0_restarts(inst)


def min_investment_zscore(inst):
    """Non-monotone rule: floor family and steepest-ascent steps (L1); greedy with restarts (L0)."""
    if inst.l1:
        out = []
        g = _best_floor(inst)
        if g is not None:
            out.append(g)
        g = _step_greedy_l1(inst)
        if g is not None:
            out.append(g)
        return out
    return _greedy_l0_restarts(inst)


def _borda_hull_greedy(inst):
    x, Xo, cap, T = inst.x, inst.Xo, inst.cap, inst.T
    hulls = []
    segs = []
    for t in range(T):
        col = Xo[:, t]
        h0 = float((col > x[t]).sum() + 0.5 * (col == x[t]).sum())
        pts = [(0.0, 0.0, float(x[t]))]
        for v in np.unique(col[col >= x[t]]):
            lev = float(v) + _TIE_EPS
            if lev > cap[t] + 1e-12:
                break
            h = float((col > lev).sum() + 0.5 * (col == lev).sum())
            passes = h0 - h
            if passes <= pts[-1][0]:
                continue
            pts.append((passes, lev - x[t], lev))
        hull = [pts[0]]
        for p in pts[1:]:
            while len(hull) >= 2:
                p1, c1, _ = hull[-2]
                p2, c2, _ = hull[-1]
                if (c2 - c1) * (p[0] - p2) >= (p[1] - c2) * (p2 - p1):
                    hull.pop()
                else:
                    break
            hull.append(p)
        hulls.append(hull)
        for k in range(1, len(hull)):
            segs.append(((hull[k][1] - hull[k - 1][1]) / (hull[k][0] - hull[k - 1][0]), t, k))
    segs.sort()
    y = x.copy()
    for _, t, k in segs:
        y[t] = hulls[t][k][2]
        if inst.margin(y) >= _SUCCESS:
            return y - x
    return None


def min_investment_borda(inst):
    """L1: rank positions passed per point (hull greedy, then pruning); L0: greedy with restarts."""
    if inst.l1:
        g = _borda_hull_greedy(inst)
        return [] if g is None else [g]
    return _greedy_l0_restarts(inst)


def min_investment_plurality(inst):
    """Exact. Winning task t costs (best rival - x_t); it also removes that rival's win if the lead was unique.
    For s newly won tasks, rival j needs s + (#won tasks led by j) >= w_j - W0 + 1; take cheapest tasks per quota."""
    T, x, Xo = inst.T, inst.x, inst.Xo
    mx = Xo.max(axis=0)
    argm = Xo.argmax(axis=0)
    nmax = (Xo == mx[None, :]).sum(axis=0)
    lead = x > mx
    W0 = int(lead.sum())
    grp = np.full(T, -1)
    sel = (~lead) & (x < mx) & (nmax == 1)
    grp[sel] = argm[sel]
    M = Xo.shape[0]
    wj = np.bincount(grp[grp >= 0], minlength=M)
    y_need = mx + _TIE_EPS
    feas = (~lead) & (inst.cap >= y_need - 1e-12)
    cost_t = np.where(feas, (y_need - x) if inst.l1 else 1.0, np.inf)
    n_av = int(feas.sum())
    d = wj - W0 + 1
    rivals = np.where(wj > 0)[0]
    has_zero = bool((wj == 0).any())
    best = None
    for s in range(0, n_av + 1):
        if has_zero and W0 + s < 1:
            continue
        r = np.maximum(d[rivals] - s, 0)
        if r.sum() > s:
            continue
        used = np.zeros(T, dtype=bool)
        ok = True
        for j, rj in zip(rivals, r):
            if rj == 0:
                continue
            tj = np.where((grp == j) & feas)[0]
            if tj.size < rj:
                ok = False
                break
            used[tj[np.argsort(cost_t[tj], kind="stable")][:rj]] = True
        if not ok:
            continue
        k = s - int(used.sum())
        rest = np.where(feas & ~used)[0]
        if rest.size < k:
            continue
        used[rest[np.argsort(cost_t[rest], kind="stable")][:k]] = True
        c = float(cost_t[used].sum())
        if best is None or c < best[0] - 1e-12:
            best = (c, used.copy())
    if best is None:
        return []
    g = np.zeros(T)
    if inst.l1:
        g[best[1]] = np.minimum(y_need[best[1]] - x[best[1]], inst.room[best[1]])
    else:
        g[best[1]] = inst.room[best[1]]
    return [g]


def _copeland_level_greedy(inst):
    x, Xo, cap, T = inst.x, inst.Xo, inst.cap, inst.T
    y = x.copy()
    for _ in range(3000):
        if inst.margin(y) >= _SUCCESS:
            return y - x
        if inst.out_of_time():
            return None
        S = np.sign(y[None, :] - Xo)
        D = S.sum(axis=1)
        cur = float(inst.cope_obj(D))
        best = None
        for t in range(T):
            col = Xo[:, t]
            vals = np.unique(col[col >= y[t]])
            if vals.size == 0:
                continue
            lv = vals + _TIE_EPS
            lv = lv[lv <= cap[t] + 1e-12]
            if lv.size == 0:
                continue
            if lv.size > 32:
                lv = lv[np.unique(np.linspace(0, lv.size - 1, 32).astype(int))]
            Dn = D[None, :] - S[:, t][None, :] + np.sign(lv[:, None] - col[None, :])
            ratio = (inst.cope_obj(Dn) - cur) / (lv - y[t])
            k = int(np.argmax(ratio))
            if ratio[k] > 1e-15 and (best is None or ratio[k] > best[0]):
                best = (float(ratio[k]), t, float(lv[k]))
        if best is None:
            return None
        y[best[1]] = best[2]
    return None


def min_investment_copeland(inst):
    """L1: ratio greedy over (task, level) moves; L0: greedy with restarts (each lifted task beats every rival)."""
    if inst.l1:
        g = _copeland_level_greedy(inst)
        return [] if g is None else [g]
    return _greedy_l0_restarts(inst)


_SOLVERS = {
    "mean": min_investment_mean,
    "median": min_investment_median,
    "trimmed_mean_20": min_investment_trimmed,
    "zscore_mean": min_investment_zscore,
    "borda": min_investment_borda,
    "plurality": min_investment_plurality,
    "copeland": min_investment_copeland,
    "maximin": min_investment_maximin,
}


# --------------------------------------------------------------------------------------------------
# MILP level-selection layer (scipy.optimize.milp / HiGHS). Candidate generator only: every plan it
# returns is re-verified by _select_best_verified, and any failure falls back to the heuristic plans.
#
# Borda, Copeland and plurality depend only on the order of the target's score against each rival on
# each task, so an optimal plan only ever uses, per task, the final level "just above rival k's score"
# (or the cap, or unchanged).  Binary z[e] picks the level of entry e = (task t, level k) with
# sum_k z[t, k] <= 1; rank / duel / win indicators are linear in z.  The incumbent heuristic cost is
# imposed as a cutoff row, so the MILP either finds a strictly cheaper plan or is infeasible.
# --------------------------------------------------------------------------------------------------
_MILP_RULES = ("borda", "copeland", "plurality", "trimmed_mean_20")


def _select_best_verified(inst, cands):
    """Re-score every candidate plan with the exact rule replica and return the cheapest verified one (or None)."""
    best, best_c = None, np.inf
    for g in sorted(cands, key=lambda a: inst.cost(inst.clip(a))):
        try:
            g = _refine(inst, g)
        except Exception:
            continue
        if g is None:
            continue
        ok, _ = verify_ranks_first(inst.X, inst.i, g, inst.rule, tol=_SUCCESS)
        if not ok:
            continue
        c = inst.cost(g)
        if c < best_c - 1e-12:
            best, best_c = g, c
    return best


def _run_milp(c, integrality, lb, ub, rows, time_limit):
    """Solve min c.x over the stacked (A, row_lo, row_hi) blocks; return x or None if no solution was found."""
    from scipy.optimize import Bounds, LinearConstraint, milp
    A = np.vstack([r[0] for r in rows])
    lo = np.concatenate([r[1] for r in rows])
    hi = np.concatenate([r[2] for r in rows])
    res = milp(c=c, integrality=integrality, bounds=Bounds(lb, ub),
               constraints=[LinearConstraint(A, lo, hi)],
               options={"time_limit": float(time_limit), "mip_rel_gap": 0.0, "disp": False})
    if res.x is None or res.status not in (0, 1):
        return None
    return np.asarray(res.x, dtype=float)


def _level_entries(inst):
    """Per-task candidate final levels: every rival score + eps above x[t] (and the cap when it cuts the grid)."""
    max_levels = max(6, min(64, 4000 // max(inst.T, 1)))
    tt, lv = [], []
    for t in range(inst.T):
        if inst.room[t] <= 1e-12:
            continue
        col = inst.Xo[:, t]
        cap = float(inst.cap[t])
        v = np.unique(col) + _TIE_EPS
        v = np.minimum(v[v <= cap + 1e-12], cap)
        if col.max() + _TIE_EPS > cap + 1e-12:
            v = np.append(v, cap)
        v = np.unique(v)
        v = v[v > inst.x[t] + 1e-12]
        if v.size > max_levels:
            v = v[np.unique(np.round(np.linspace(0, v.size - 1, max_levels)).astype(int))]
        tt.extend([t] * int(v.size))
        lv.extend(v.tolist())
    return np.array(tt, dtype=int), np.array(lv, dtype=float)


def _task_rows(inst, tt, n_cols):
    """sum_k z[t, k] <= 1 for every task t (z occupies the first len(tt) columns)."""
    A = np.zeros((inst.T, n_cols))
    A[tt, np.arange(tt.size)] = 1.0
    return (A, np.full(inst.T, -np.inf), np.ones(inst.T))


def _decode_levels(inst, z, tt, lv):
    """Selected levels -> gains (first level reached by float rounding is bumped up by an ulp or two)."""
    g = np.zeros(inst.T)
    for e in np.where(z[:tt.size] > 0.5)[0]:
        t = int(tt[e])
        gt = float(lv[e] - inst.x[t])
        for _ in range(4):
            if inst.x[t] + gt >= lv[e]:
                break
            gt = float(np.nextafter(gt, np.inf))
        g[t] = max(g[t], gt)
    return inst.clip(g)


def _cutoff_for(inst, incumbent_cost, slack):
    """Upper bound on the MILP objective: strictly below the incumbent (None if nothing can be gained)."""
    if incumbent_cost is None:
        return np.inf
    if inst.l1:
        return incumbent_cost - slack if incumbent_cost > slack else None
    return incumbent_cost - 0.5 if incumbent_cost >= 1.0 else None


def _milp_borda(inst, cutoff, time_limit):
    """Borda: rank of target and of every rival are linear in z; require every rival total rank >= target + 0.5."""
    tt, lv = _level_entries(inst)
    E = lv.size
    if E == 0 or cutoff is None:
        return None
    Xo, x, T = inst.Xo, inst.x, inst.T
    Xt, V, xe = Xo[:, tt], lv[None, :], x[tt][None, :]
    h = (Xt > V).sum(axis=0) + 0.5 * (Xt == V).sum(axis=0)
    h0 = (Xt > xe).sum(axis=0) + 0.5 * (Xt == xe).sum(axis=0)
    c = (Xt < V) + 0.5 * (Xt == V)
    c0 = (Xt < xe) + 0.5 * (Xt == xe)
    A_r = (c - c0) - (h - h0)[None, :]
    Rm0 = T + (Xo > x[None, :]).sum() + 0.5 * (Xo == x[None, :]).sum()
    Rj0 = inst.ro + ((Xo < x[None, :]) + 0.5 * (Xo == x[None, :])).sum(axis=1)
    cost = (lv - x[tt]) if inst.l1 else np.ones(E)
    M = Xo.shape[0]
    rows = [(A_r, 0.5 + Rm0 - Rj0, np.full(M, np.inf)),
            _task_rows(inst, tt, E),
            (cost[None, :], np.array([-np.inf]), np.array([cutoff]))]
    z = _run_milp(cost, np.ones(E), np.zeros(E), np.ones(E), rows, time_limit)
    return None if z is None else _decode_levels(inst, z, tt, lv)


def _milp_copeland(inst, cutoff, time_limit):
    """Copeland: duel margin D_j = D0_j + dS_j.z; a_j / e_j binaries flag a duel win / tie (never overstated);
    require target score + own duel result >= B_j + 1.5 for every rival j."""
    tt, lv = _level_entries(inst)
    E = lv.size
    if E == 0 or cutoff is None:
        return None
    Xo, x, T = inst.Xo, inst.x, inst.T
    M = Xo.shape[0]
    Xt, V, xe = Xo[:, tt], lv[None, :], x[tt][None, :]
    dS = np.sign(V - Xt) - np.sign(xe - Xt)
    D0 = np.sign(x[None, :] - Xo).sum(axis=1)
    n = E + 2 * M
    I = np.eye(M)
    ones = np.ones((M, M))
    R1 = np.zeros((M, n))
    R1[:, :E] = dS
    R1[:, E:E + M] = -(1.0 + T) * I
    R1[:, E + M:] = -float(T) * I
    R2 = np.zeros((M, n))
    R2[:, E:E + M] = I
    R2[:, E + M:] = I
    R3 = np.zeros((M, n))
    R3[:, E:E + M] = ones + I
    R3[:, E + M:] = 0.5 * (ones + I)
    cost = (lv - x[tt]) if inst.l1 else np.ones(E)
    c = np.zeros(n)
    c[:E] = cost
    A_cut = np.zeros((1, n))
    A_cut[0, :E] = cost
    rows = [(R1, -float(T) - D0, np.full(M, np.inf)),
            (R2, np.full(M, -np.inf), np.ones(M)),
            (R3, inst.B + 1.5, np.full(M, np.inf)),
            _task_rows(inst, tt, n),
            (A_cut, np.array([-np.inf]), np.array([cutoff]))]
    z = _run_milp(c, np.ones(n), np.zeros(n), np.ones(n), rows, time_limit)
    return None if z is None else _decode_levels(inst, z, tt, lv)


def _milp_plurality(inst, cutoff, time_limit):
    """Plurality: per non-led task a 'win' level (best rival + eps) or a 'tie' level (kills a unique lead);
    require target wins >= every rival's remaining wins + 1."""
    Xo, x, T = inst.Xo, inst.x, inst.T
    M = Xo.shape[0]
    if cutoff is None:
        return None
    mx = Xo.max(axis=0)
    argm = Xo.argmax(axis=0)
    nmax = (Xo == mx[None, :]).sum(axis=0)
    lead = x > mx
    W0 = int(lead.sum())
    uniq = (~lead) & (x < mx) & (nmax == 1)
    wj = np.bincount(argm[uniq], minlength=M)
    tt, lv, is_win, owner = [], [], [], []
    for t in range(T):
        if lead[t] or inst.room[t] <= 1e-12:
            continue
        cap = float(inst.cap[t])
        w = float(mx[t]) + _TIE_EPS
        own = int(argm[t]) if uniq[t] else -1
        if w <= cap + 1e-12:
            tt.append(t); lv.append(min(w, cap)); is_win.append(1.0); owner.append(own)
        if uniq[t] and float(mx[t]) <= cap + 1e-12:
            tt.append(t); lv.append(float(mx[t])); is_win.append(0.0); owner.append(own)
    E = len(tt)
    if E == 0:
        return None
    tt, lv, is_win, owner = np.array(tt, dtype=int), np.array(lv), np.array(is_win), np.array(owner, dtype=int)
    A_r = np.tile(is_win[None, :], (M, 1)) + (owner[None, :] == np.arange(M)[:, None])
    cost = (lv - x[tt]) if inst.l1 else np.ones(E)
    rows = [(A_r, 1.0 - W0 + wj.astype(float), np.full(M, np.inf)),
            _task_rows(inst, tt, E),
            (cost[None, :], np.array([-np.inf]), np.array([cutoff]))]
    z = _run_milp(cost, np.ones(E), np.zeros(E), np.ones(E), rows, time_limit)
    return None if z is None else _decode_levels(inst, z, tt, lv)


def _milp_trimmed(inst, cutoff, time_limit):
    """Trimmed mean: k-subset binaries s mark the dropped-low tasks (w >= y on s), the LP dual of the top-k sum
    (lam, u) bounds the dropped-high tasks; kept-sum >= (best rival + eps) * (T - 2k). L0 adds support binaries."""
    T, x, cap, room = inst.T, inst.x, inst.cap, inst.room
    if cutoff is None or inst.theta is None:
        return None
    k = T // 5
    scale = float(max(np.abs(x).max(), np.abs(cap).max(), 1.0)) + 1.0
    n = 4 * T + 1 + (0 if inst.l1 else T)
    G, S, W, U, LAM, B = 0, T, 2 * T, 3 * T, 4 * T, 4 * T + 1
    I = np.eye(T)
    Rm = np.zeros((1, n))
    Rm[0, G:G + T] = 1.0
    Rm[0, U:U + T] = -1.0
    Rm[0, W:W + T] = -1.0
    Rm[0, LAM] = -float(k)
    rhs = (inst.theta + _TARGET_EPS) * (T - 2 * k) - float(x.sum()) + _TRIM_MARGIN
    Rw = np.zeros((T, n))
    Rw[:, W:W + T] = I
    Rw[:, G:G + T] = -I
    Rw[:, S:S + T] = -np.diag(cap)
    Ru = np.zeros((T, n))
    Ru[:, U:U + T] = I
    Ru[:, G:G + T] = -I
    Ru[:, LAM] = 1.0
    Rs = np.zeros((1, n))
    Rs[0, S:S + T] = 1.0
    A_cut = np.zeros((1, n))
    c = np.zeros(n)
    integ = np.zeros(n)
    integ[S:S + T] = 1
    lb = np.zeros(n)
    ub = np.full(n, scale)
    ub[G:G + T] = room
    ub[U:U + T] = 2.0 * scale
    ub[S:S + T] = 1.0
    lb[LAM], ub[LAM] = -scale, scale
    rows = [(Rm, np.array([rhs]), np.array([np.inf])),
            (Rw, x - cap, np.full(T, np.inf)),
            (Ru, x.copy(), np.full(T, np.inf)),
            (Rs, np.array([float(k)]), np.array([float(k)]))]
    if inst.l1:
        c[G:G + T] = 1.0
        A_cut[0, G:G + T] = 1.0
    else:
        integ[B:B + T] = 1
        ub[B:B + T] = 1.0
        c[B:B + T] = 1.0
        c[G:G + T] = 1e-6
        A_cut[0, B:B + T] = 1.0
        Rb = np.zeros((T, n))
        Rb[:, G:G + T] = I
        Rb[:, B:B + T] = -np.diag(room)
        rows.append((Rb, np.full(T, -np.inf), np.zeros(T)))
    rows.append((A_cut, np.array([-np.inf]), np.array([cutoff])))
    z = _run_milp(c, integ, lb, ub, rows, time_limit)
    return None if z is None else inst.clip(z[G:G + T])


def _l0_exchange_polish(inst, g, budget_s):
    """Swap one raised task for an untouched one (lifted to its cap) and prune; keep only strictly cheaper plans."""
    x, room = inst.x, inst.room
    dl = time.perf_counter() + budget_s
    inst.deadline = dl
    cur = g.copy()
    improved = True
    while improved and time.perf_counter() < dl:
        improved = False
        raised = np.where(cur > 0)[0]
        free = np.where((cur <= 0) & (room > 1e-12))[0]
        for t in raised:
            for u in free:
                if time.perf_counter() > dl:
                    return cur
                g2 = cur.copy()
                g2[t] = 0.0
                g2[u] = room[u]
                if inst.ref_margin(x + g2) >= _SUCCESS:
                    g3 = inst.clip(_prune_l0(inst, g2))
                    if inst.cost(g3) < inst.cost(cur) and inst.ref_margin(x + g3) >= _SUCCESS:
                        cur, improved = g3, True
                        break
            if improved:
                break
    return cur


_MILP_SOLVERS = {
    "borda": _milp_borda,
    "copeland": _milp_copeland,
    "plurality": _milp_plurality,
    "trimmed_mean_20": _milp_trimmed,
}


def _milp_candidates(inst, best, t0):
    """Extra candidate plans (unverified) from the MILP / exchange layer; [] when out of budget or on any error."""
    out = []
    remaining = min(_MILP_BUDGET_S, _EPISODE_LIMIT_S - _REFINE_RESERVE_S - (time.perf_counter() - t0))
    if remaining < 0.25:
        return out
    inc = inst.cost(best)
    if inst.rule in _MILP_SOLVERS:
        try:
            slack = 1e-3 if inst.rule == "trimmed_mean_20" else 1e-5
            cutoff = _cutoff_for(inst, inc, slack)
            g = _MILP_SOLVERS[inst.rule](inst, cutoff, remaining)
            if g is not None:
                out.append(g)
        except Exception:
            pass  # solver unavailable / numerical failure: keep heuristic plans
    elif inst.rule == "zscore_mean" and not inst.l1:
        try:
            g = _l0_exchange_polish(inst, best, min(2.0, remaining))
            if g is not None:
                out.append(g)
        except Exception:
            pass
    return out


def _solve_inst(inst):
    """Gains ndarray, None if infeasible; raises if no verified plan could be produced."""
    T = inst.T
    if inst.Xo.shape[0] == 0:
        return np.zeros(T)
    if inst.ref_margin(inst.x) > _ALREADY:
        return np.zeros(T)
    if inst.ref_margin(inst.x + inst.room) < _SUCCESS:
        if inst.rule == "zscore_mean":  # non-monotone: full caps need not be the best plan
            g = _step_greedy_l1(inst)
            if g is not None and inst.ref_margin(inst.x + inst.clip(g)) >= _SUCCESS:
                return inst.clip(g)
        return None
    t0 = time.perf_counter()
    cands = []
    b = _baseline(inst)
    if b is not None:
        cands.append(b)
    try:
        cands.extend(_SOLVERS[inst.rule](inst))
    except Exception:
        pass  # keep the baseline candidate
    best = _select_best_verified(inst, cands)
    if best is None:
        raise RuntimeError("no verified plan")
    # MILP / exchange layer: extra candidates only; the verified heuristic plan stays as the fallback.
    try:
        extra = _milp_candidates(inst, best, t0)
        if extra:
            inst.deadline = time.perf_counter() + 2.0  # room for pruning the new plans
            best = _select_best_verified(inst, [best] + extra) or best
    except Exception:
        pass  # any MILP failure keeps the heuristic plan
    return best


# --------------------------------------------------------------------------------------------------
# starter routine (fallback on internal errors)
# --------------------------------------------------------------------------------------------------
def _margin(gains):
    X = _STATE["X"].copy()
    i = _STATE["target"]
    X[i] = X[i] + gains
    v = _scores(X, _STATE["rule"])
    return v[i] - np.delete(v, i).max()


def _plan(gains, room=None):
    gains = np.asarray(gains, dtype=float)
    if room is not None:
        gains = np.minimum(gains, room)
    return {"status": "plan", "gains": [{"task": int(t), "gain": float(g)} for t, g in enumerate(gains) if g > 0]}


def _solve_starter():
    s = _STATE
    x = s["X"][s["target"]]
    room = np.maximum(s["caps"] - x, 0.0)
    if _margin(np.zeros_like(room)) >= _MARGIN:
        return {"status": "plan", "gains": []}
    if _margin(room) < _MARGIN:
        return {"status": "infeasible"}
    if s["cost_model"] == "l1_points":
        lo, hi = 0.0, float(room.max())
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if _margin(np.minimum(mid, room)) >= _MARGIN:
                hi = mid
            else:
                lo = mid
        return _plan(np.minimum(hi, room))
    gains = np.zeros_like(room)
    for t in np.argsort(-room, kind="stable"):
        gains[t] = room[t]
        if _margin(gains) >= _MARGIN:
            break
    return _plan(gains)


def _solve():
    s = _STATE
    try:
        inst = _Inst(s["X"], s["target"], s["rule"], s["cost_model"], s["caps"],
                     time.perf_counter() + _BUDGET_S, seed=s.get("seed", 0))
        g = _solve_inst(inst)
        if g is None:
            return {"status": "infeasible"}
        return _plan(g, inst.room)
    except Exception:
        return _solve_starter()


def handle(request):
    op = request.get("op")
    if op == "reset":
        _STATE.clear()
        _STATE["seed"] = int(request["seed"])
        _STATE["rng"] = np.random.default_rng(int(request["seed"]))
        return {"ok": True}
    if op == "load_begin":
        N, T = request["shape"]
        _STATE.update(rule=request["rule"], cost_model=request["cost_model"], target=int(request["target_row"]),
                      shape=(int(N), int(T)), chunk_count=int(request["chunk_count"]), chunks=[], committed=False,
                      caps=_b64_array(request["caps"]["data"], (int(T),)).copy())
        return {"ok": True}
    if op == "load_chunk":
        _STATE["chunks"].append(_b64_array(request["data"]).copy())
        return {"ok": True}
    if op == "load_commit":
        N, T = _STATE["shape"]
        _STATE["X"] = np.concatenate(_STATE["chunks"]).reshape(N, T)
        _STATE["committed"] = True
        return {"ok": True}
    if op == "solve":
        return _solve()
    raise ValueError("unknown op")


# ==================================================================================================
# Offline analysis helpers (data manifest, uncertainty, ablations). NOT used by ``handle``.
# ==================================================================================================
DATA_SNAPSHOTS = {
    "helm_mmlu": "https://storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/",
    "open_llm_contents": "huggingface.co/datasets/open-llm-leaderboard/contents@9c09a7cae43334062a82cb164f2ef255013dafa2",
    "open_llm_results": "huggingface.co/datasets/open-llm-leaderboard/results@aa81ecc38fdc5708254b833923368970efdf5ef5",
    "license": "undeclared for score data (HELM code Apache-2.0)",
}


def data_manifest(paths, out_json=None):
    """SHA256 checksums + snapshot identifiers for the local copies of the public tables."""
    files = {}
    for p in paths:
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for blk in iter(lambda: fh.read(1 << 20), b""):
                h.update(blk)
        files[str(p)] = h.hexdigest()
    man = {"snapshots": DATA_SNAPSHOTS, "sha256": files}
    if out_json:
        with open(out_json, "w") as fh:
            json.dump(man, fh, indent=2, sort_keys=True)
    return man


def make_caps(X, target, ceiling_mode="scale100"):
    """ceiling_mode: 'scale100' (cap 100 everywhere) or 'max_observed' (best observed score + 1e-6)."""
    X = np.asarray(X, dtype=float)
    x = X[target]
    if ceiling_mode == "scale100":
        return np.full(X.shape[1], 100.0)
    best = X.max(axis=0) + 1e-6
    others = np.delete(X, target, axis=0).max(axis=0)
    return np.where(x > others, x, best)


def bootstrap_ci(values, n_boot=1000, alpha=0.05, seed=0, stat=np.median):
    """Percentile bootstrap CI of ``stat`` over finite values; returns (estimate, lo, hi)."""
    rng = np.random.default_rng(seed)
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return float("nan"), float("nan"), float("nan")
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    s = stat(v[idx], axis=1)
    return float(stat(v)), float(np.quantile(s, alpha / 2)), float(np.quantile(s, 1 - alpha / 2))


def holm_adjust(pvals):
    """Holm step-down adjusted p-values."""
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    m = p.size
    adj = np.empty(m)
    run = 0.0
    for rank, k in enumerate(order):
        run = max(run, (m - rank) * p[k])
        adj[k] = min(1.0, run)
    return adj


def paired_wilcoxon_holm(cost_by_rule):
    """Paired Wilcoxon signed-rank tests between all rule pairs (same targets), Holm-corrected."""
    from scipy.stats import wilcoxon
    names = sorted(cost_by_rule)
    pairs, ps = [], []
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            u, v = np.asarray(cost_by_rule[names[a]], float), np.asarray(cost_by_rule[names[b]], float)
            ok = np.isfinite(u) & np.isfinite(v)
            if ok.sum() < 5 or np.allclose(u[ok], v[ok]):
                p = 1.0
            else:
                p = float(wilcoxon(u[ok], v[ok]).pvalue)
            pairs.append((names[a], names[b]))
            ps.append(p)
    adj = holm_adjust(ps) if ps else []
    return [{"pair": pr, "p": p, "p_holm": float(q)} for pr, p, q in zip(pairs, ps, adj)]


def subsample_tasks(X, K, seed=0):
    """Random K-task column subsample (without replacement); returns (X_sub, column_indices)."""
    rng = np.random.default_rng(seed)
    cols = np.sort(rng.choice(X.shape[1], size=min(K, X.shape[1]), replace=False))
    return X[:, cols], cols


def normalise_scores(X, mode="raw"):
    X = np.asarray(X, dtype=float)
    if mode == "raw":
        return X
    if mode == "minmax":
        lo, hi = X.min(axis=0), X.max(axis=0)
        return 100.0 * (X - lo) / np.where(hi > lo, hi - lo, 1.0)
    if mode == "zscore":
        sd = X.std(axis=0)
        return (X - X.mean(axis=0)) / np.where(sd > 1e-12, sd, 1.0)
    raise ValueError("unknown normalisation")


def min_cost(X, target, rule, cost_model="l1_points", ceiling_mode="scale100", seed=0, budget_s=5.0):
    """Minimal investment for one (matrix, target, rule); inf if infeasible."""
    X = np.asarray(X, dtype=float)
    caps = make_caps(X, target, ceiling_mode)
    inst = _Inst(X, target, rule, cost_model, caps, time.perf_counter() + budget_s, seed)
    g = _solve_inst(inst)
    return float("inf") if g is None else inst.cost(g)


def breadth_constrained_cost(X, target, rule, ks=None, ceiling_mode="scale100", seed=0):
    """L1 cost when at most k tasks may be boosted, k in ks (default 1..T). Forward-greedy task selection; each
    candidate set is priced with the full L1 solver restricted to that set (a heuristic upper bound)."""
    X = np.asarray(X, dtype=float)
    T = X.shape[1]
    ks = list(range(1, T + 1)) if ks is None else sorted(ks)
    caps = make_caps(X, target, ceiling_mode)
    x = X[target]

    def price(tasks):
        c = x.copy()
        c[list(tasks)] = caps[list(tasks)]
        inst = _Inst(X, target, rule, "l1_points", c, time.perf_counter() + 2.0, seed)
        g = _solve_inst(inst)
        return np.inf if g is None else inst.cost(g)

    chosen, out = [], {}
    headroom = np.maximum(caps - x, 0.0)
    for k in range(1, max(ks) + 1):
        best_t, best_c = None, np.inf
        for t in range(T):
            if t in chosen:
                continue
            c = price(chosen + [t])
            if c < best_c or (best_t is None and not np.isfinite(c)) or (c == best_c and headroom[t] > headroom[best_t]):
                best_t, best_c = t, c
        chosen.append(best_t)
        if k in ks:
            out[k] = best_c
    return out


def run_ablations(X, rules=None, cost_models=("l1_points", "l0_tasks"), n_targets=10, seed=0,
                  ceiling_modes=("scale100", "max_observed"), top_n_pool=(None, 10, 50, 200),
                  norms=("raw", "minmax"), Ks=(6, 10, 20, 40)):
    """Median minimal cost per rule across targets for ceiling_mode / top_n_pool / normalisation / task-count
    ablations. X: [N models, T tasks] on a 0..100 scale. Returns a nested dict (offline helper)."""
    rules = list(_SOLVERS) if rules is None else rules
    X = np.asarray(X, dtype=float)
    rng = np.random.default_rng(seed)

    def med_costs(M, ceiling_mode, cm):
        order = np.argsort(-M.mean(axis=1))
        pool = order[1:min(len(order), 1 + n_targets * 3)]
        tg = rng.choice(pool, size=min(n_targets, pool.size), replace=False)
        res = {}
        for r in rules:
            cs = [min_cost(M, int(t), r, cm, ceiling_mode, seed, 2.0) for t in tg]
            fin = [c for c in cs if np.isfinite(c)]
            res[r] = {"median": float(np.median(fin)) if fin else float("nan"), "infeasible": len(cs) - len(fin)}
        return res

    out = {"ceiling_mode": {}, "top_n_pool": {}, "normalisation": {}, "task_subsample": {}}
    for cm in cost_models:
        for cmode in ceiling_modes:
            out["ceiling_mode"][f"{cm}|{cmode}"] = med_costs(X, cmode, cm)
        for n in top_n_pool:
            sub = X if n is None else X[np.argsort(-X.mean(axis=1))[:n]]
            out["top_n_pool"][f"{cm}|{n}"] = med_costs(sub, "scale100", cm)
        for nm in norms:
            out["normalisation"][f"{cm}|{nm}"] = med_costs(normalise_scores(X, nm), "scale100", cm)
        for K in Ks:
            if K <= X.shape[1]:
                sub, _ = subsample_tasks(X, K, seed)
                out["task_subsample"][f"{cm}|{K}"] = med_costs(sub, "scale100", cm)
    return out


def _selfcheck(n_trials=30, seed=0):
    """Offline: random small instances; every rule must return a verified plan, and the exact L0 solvers must
    match brute force over all task subsets lifted to their caps. Returns the number of checks passed."""
    import itertools
    rng = np.random.default_rng(seed)
    passed = 0
    for _ in range(n_trials):
        N, T = int(rng.integers(4, 9)), int(rng.integers(4, 8))
        X = np.round(rng.uniform(20, 90, size=(N, T)), 1)
        tgt = int(rng.integers(0, N))
        for rule in _SOLVERS:
            for cm in ("l1_points", "l0_tasks"):
                caps = np.full(T, 100.0) if cm == "l1_points" else X.max(axis=0) + 1e-6
                inst = _Inst(X, tgt, rule, cm, caps, time.perf_counter() + 5.0, seed)
                g = _solve_inst(inst)
                if g is None:
                    continue
                ok, _ = verify_ranks_first(X, tgt, g, rule)
                assert ok, (rule, cm)
                passed += 1
                if cm == "l0_tasks" and rule in _EXACT and inst.ref_margin(inst.x) <= _ALREADY:
                    best = None
                    for k in range(T + 1):
                        for S in itertools.combinations(range(T), k):
                            gg = np.zeros(T)
                            gg[list(S)] = inst.room[list(S)]
                            if verify_ranks_first(X, tgt, gg, rule, tol=_SUCCESS)[0]:
                                best = k
                                break
                        if best is not None:
                            break
                    assert best is not None and inst.cost(g) <= best, (rule, inst.cost(g), best)
                    passed += 1
    return passed


def _selfcheck_milp(n_trials=20, seed=0, budget_s=5.0):
    """Offline (never called by ``handle``): on random small instances, the MILP layer's plan must verify and the
    final plan must cost no more than the heuristic-only plan (borda / copeland / plurality / trimmed, both cost
    models). Returns {(rule, cost_model): [n, n_milp_strictly_better, total_gain]}; asserts on any violation."""
    rng = np.random.default_rng(seed)
    stats = {}
    for _ in range(n_trials):
        N, T = int(rng.integers(4, 9)), int(rng.integers(5, 9))
        X = np.round(rng.uniform(20, 90, size=(N, T)), 1)
        tgt = int(rng.integers(0, N))
        for rule in _MILP_RULES:
            for cm in ("l1_points", "l0_tasks"):
                caps = np.full(T, 100.0) if cm == "l1_points" else X.max(axis=0) + 1e-6
                caps = np.where(X[tgt] > np.delete(X, tgt, axis=0).max(axis=0), X[tgt], caps) if cm == "l0_tasks" else caps
                inst = _Inst(X, tgt, rule, cm, caps, time.perf_counter() + budget_s, seed)
                if inst.ref_margin(inst.x) > _ALREADY or inst.ref_margin(inst.x + inst.room) < _SUCCESS:
                    continue
                cands = [g for g in [_baseline(inst)] if g is not None] + _SOLVERS[rule](inst)
                heur = _select_best_verified(inst, cands)
                assert heur is not None, (rule, cm)
                final = _solve_inst(_Inst(X, tgt, rule, cm, caps, time.perf_counter() + budget_s, seed))
                ok, _ = verify_ranks_first(X, tgt, final, rule)
                assert ok, (rule, cm)
                ch, cf = inst.cost(heur), inst.cost(final)
                assert cf <= ch + 1e-6, (rule, cm, cf, ch)
                s = stats.setdefault((rule, cm), [0, 0, 0.0])
                s[0] += 1
                s[1] += int(cf < ch - 1e-6)
                s[2] += ch - cf
    return stats
