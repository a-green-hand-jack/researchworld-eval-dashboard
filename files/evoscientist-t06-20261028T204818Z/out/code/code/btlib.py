"""Core library: Bradley-Terry fitting on aggregated comparison "types", influence-based
(approximate maximum influence perturbation, AMIP) search for small data perturbations that
change a ranking, refit verification, exact exhaustive search for tiny budgets, and random
perturbation baselines.

Data model
----------
Every comparison is (a, b, h, y): player a vs player b, h = 1 if a has a home/first-position
advantage covariate (only used when ``use_home``), y in {0, 0.5, 1} with y = 1 meaning a won
(ties are y = 0.5, i.e. half a win for each side; the log-likelihood is the usual
"tie = half win + half loss" convention).  Comparisons with identical (a, b, h, y) are
exchangeable under the model, so we store a "type table" with counts n_t.  Every
perturbation (dropping, flipping, adding comparisons) is a change of the count vector.

The fitted model is   logit P(a beats b) = theta_a - theta_b + h * eta
with a small ridge penalty lam/2 * ||(theta, eta)||^2 that identifies the gauge and keeps
estimates finite for players that never lost.
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

import numpy as np

Y_LEVELS = np.array([0.0, 0.5, 1.0])


def sigmoid(x):
    return 0.5 * (1.0 + np.tanh(0.5 * x))


@dataclass
class TypeTable:
    players: list
    a: np.ndarray          # (T,) int
    b: np.ndarray          # (T,) int
    h: np.ndarray          # (T,) float
    y: np.ndarray          # (T,) float
    n: np.ndarray          # (T,) float counts
    key: np.ndarray        # (T,) int, id of (a, b, h); the 3 outcome levels of a key are contiguous
    use_home: bool = False

    def __post_init__(self):
        self._hidx = None

    def design(self):
        """Dense design matrix (only used in tests)."""
        m = len(self.players)
        d = m + (1 if self.use_home else 0)
        T = len(self.a)
        X = np.zeros((T, d))
        X[np.arange(T), self.a] += 1.0
        X[np.arange(T), self.b] -= 1.0
        if self.use_home:
            X[:, m] = self.h
        return X

    @property
    def m(self):
        return len(self.players)

    @property
    def N(self):
        return float(self.n.sum())

    def player_counts(self, n=None):
        n = self.n if n is None else n
        c = np.bincount(self.a, weights=n, minlength=self.m) + np.bincount(self.b, weights=n, minlength=self.m)
        return c


def build_table(a_names, b_names, y, h=None, use_home=False, players=None, all_pairs=False):
    """Aggregate raw comparisons into a TypeTable.

    a_names, b_names : sequences of player names; y : outcome for a (1 win, 0.5 tie, 0 loss);
    h : optional home indicator for a. all_pairs=True adds zero-count types for every ordered
    pair (needed for the 'add' perturbation)."""
    a_names = np.asarray(a_names)
    b_names = np.asarray(b_names)
    y = np.asarray(y, dtype=float)
    if h is None:
        h = np.zeros(len(y))
    h = np.asarray(h, dtype=float)
    if players is None:
        players = sorted(set(a_names.tolist()) | set(b_names.tolist()))
    idx = {p: k for k, p in enumerate(players)}
    ai = np.array([idx[s] for s in a_names])
    bi = np.array([idx[s] for s in b_names])
    yl = np.searchsorted(Y_LEVELS, y)
    assert np.allclose(Y_LEVELS[yl], y), "outcomes must be in {0, 0.5, 1}"
    m = len(players)
    hk = h.astype(int)
    raw_key = (ai * m + bi) * 2 + hk
    if all_pairs:
        extra = np.array([(p * m + q) * 2 for p in range(m) for q in range(m) if p != q])
        ukeys = np.unique(np.concatenate([raw_key, extra]))
    else:
        ukeys = np.unique(raw_key)
    kid = np.searchsorted(ukeys, raw_key)
    K = len(ukeys)
    counts = np.bincount(kid * 3 + yl, minlength=3 * K).astype(float)
    ka = (ukeys // 2) // m
    kb = (ukeys // 2) % m
    kh = (ukeys % 2).astype(float)
    tt = TypeTable(players=list(players), a=np.repeat(ka, 3), b=np.repeat(kb, 3), h=np.repeat(kh, 3),
                   y=np.tile(Y_LEVELS, K), n=counts, key=np.repeat(np.arange(K), 3), use_home=use_home)
    return tt


# ----------------------------------------------------------------------------- fitting

@dataclass
class Fit:
    theta: np.ndarray
    p: np.ndarray
    H: np.ndarray
    n_iter: int
    converged: bool


def _hess_index(tt):
    """Precomputed scatter indices so that H = bincount(idx, coef * W[rep]) (O(T) instead of O(T d^2))."""
    if getattr(tt, "_hidx", None) is not None:
        return tt._hidx
    m = tt.m
    d = m + (1 if tt.use_home else 0)
    a, b, h = tt.a, tt.b, tt.h
    idx = [a * d + a, b * d + b, a * d + b, b * d + a]
    coef = [np.ones_like(h), np.ones_like(h), -np.ones_like(h), -np.ones_like(h)]
    if tt.use_home:
        idx += [a * d + m, m * d + a, b * d + m, m * d + b, np.full_like(a, m * d + m)]
        coef += [h, h, -h, -h, h * h]
    tt._hidx = (np.concatenate(idx), np.concatenate(coef), len(idx), d)
    return tt._hidx


def _eta(tt, th):
    e = th[tt.a] - th[tt.b]
    if tt.use_home:
        e = e + tt.h * th[tt.m]
    return e


def _xt_dot(tt, r):
    """X^T r without forming X."""
    m = tt.m
    d = m + (1 if tt.use_home else 0)
    g = np.bincount(tt.a, weights=r, minlength=d) - np.bincount(tt.b, weights=r, minlength=d)
    if tt.use_home:
        g[m] += float(np.sum(tt.h * r))
    return g


def hessian(tt, W, lam):
    idx, coef, reps, d = _hess_index(tt)
    H = np.bincount(idx, weights=coef * np.tile(W, reps), minlength=d * d).reshape(d, d)
    return H + lam * np.eye(d)


def fit_bt(tt: TypeTable, n=None, lam=0.01, theta0=None, tol=1e-9, maxit=100):
    """Penalised maximum likelihood via damped Newton. Returns Fit."""
    n = tt.n if n is None else n
    y = tt.y
    d = tt.m + (1 if tt.use_home else 0)
    th = np.zeros(d) if theta0 is None else theta0.copy()

    def obj(t):
        eta = _eta(tt, t)
        lp = -np.logaddexp(0.0, -eta)
        lq = -np.logaddexp(0.0, eta)
        return float(np.sum(n * (y * lp + (1 - y) * lq)) - 0.5 * lam * t @ t)

    f = obj(th)
    converged = False
    it = 0
    for it in range(1, maxit + 1):
        p = sigmoid(_eta(tt, th))
        g = _xt_dot(tt, n * (y - p)) - lam * th
        H = hessian(tt, n * p * (1 - p), lam)
        step = np.linalg.solve(H, g)
        t = 1.0
        while True:
            th_new = th + t * step
            f_new = obj(th_new)
            if f_new >= f - 1e-12 * abs(f) or t < 1e-8:
                break
            t *= 0.5
        th, f = th_new, f_new
        if np.max(np.abs(t * step)) < tol:
            converged = True
            break
    p_all = sigmoid(_eta(tt, th))
    H = hessian(tt, n * p_all * (1 - p_all), lam)
    return Fit(theta=th, p=p_all, H=H, n_iter=it, converged=converged)


def ranking(theta, m):
    """Indices of players sorted by decreasing score (ignores home parameter)."""
    return np.argsort(-theta[:m], kind="stable")


def pair_se(tt, fit, i, j, n=None):
    """Model-based and sandwich standard errors of theta_i - theta_j."""
    n = tt.n if n is None else n
    d = tt.m + (1 if tt.use_home else 0)
    v = np.zeros(d); v[i] = 1; v[j] = -1
    u = np.linalg.solve(fit.H, v)
    se_model = math.sqrt(max(v @ u, 0))
    c = _eta(tt, u)
    psi = c * (tt.y - fit.p)          # per-item influence on the gap (dropping removes +psi from score)
    se_sand = math.sqrt(float(np.sum(n * psi ** 2)))
    return se_model, se_sand


# ----------------------------------------------------------------------------- influence

def gap_direction(tt, fit, i, j):
    d = tt.m + (1 if tt.use_home else 0)
    v = np.zeros(d); v[i] = 1; v[j] = -1
    u = np.linalg.solve(fit.H, v)
    return _eta(tt, u)   # c_t = v^T H^{-1} x_t


def candidate_moves(tt, fit, n, i, j, kind):
    """First-order predicted change in gap = theta_i - theta_j for ONE unit move of each candidate.

    Returns arrays (effect, src, dst, cap). src/dst are type indices (-1 = none).
    kind: 'drop' (remove one comparison of type src), 'flip' (relabel one comparison of type src
    to outcome type dst of the same key), 'add' (insert one comparison of type dst)."""
    c = gap_direction(tt, fit, i, j)
    r = tt.y - fit.p
    T = len(tt.y)
    if kind == "drop":
        eff = -c * r
        return eff, np.arange(T), -np.ones(T, int), n.copy()
    if kind == "add":
        # only decisive outcomes are added (a fabricated win or loss)
        eff = c * r
        ok = tt.y != 0.5
        idx = np.where(ok)[0]
        return eff[idx], -np.ones(len(idx), int), idx, np.full(len(idx), np.inf)
    if kind == "flip":
        effs, srcs, dsts = [], [], []
        base = (np.arange(T) // 3) * 3
        lvl = np.arange(T) % 3
        for dl in (-2, -1, 1, 2):
            tl = lvl + dl
            ok = (tl >= 0) & (tl <= 2)
            src = np.where(ok)[0]
            dst = base[src] + tl[src]
            dy = tt.y[dst] - tt.y[src]
            effs.append(c[src] * dy); srcs.append(src); dsts.append(dst)
        eff = np.concatenate(effs); src = np.concatenate(srcs); dst = np.concatenate(dsts)
        # keep, for each source type, only its best destination
        order = np.lexsort((eff, src))
        src_o = src[order]
        first = np.ones(len(order), bool); first[1:] = src_o[1:] != src_o[:-1]
        sel = order[first]
        return eff[sel], src[sel], dst[sel], n[src[sel]].copy()
    raise ValueError(kind)


def _take_items(eff, cap, budget_gap, max_items=None):
    """Greedy (sorted) selection of unit moves with negative effect until the predicted gap
    change exceeds budget_gap (a positive number).  Returns (order, counts, k_pred, reached)."""
    neg = np.where((eff < 0) & (cap > 0))[0]
    order = neg[np.argsort(eff[neg], kind="stable")]
    caps = cap[order]
    gains = -eff[order]
    finite_caps = np.where(np.isinf(caps), 1e12, caps)
    cum_cap = np.cumsum(finite_caps)
    cum_gain = np.cumsum(finite_caps * gains)
    pos = np.searchsorted(cum_gain, budget_gap, side="right")
    if pos >= len(order):
        k_pred = float(cum_cap[-1]) if len(order) else 0.0
        reached = False
    else:
        prev_cap = cum_cap[pos - 1] if pos > 0 else 0.0
        prev_gain = cum_gain[pos - 1] if pos > 0 else 0.0
        need = math.floor((budget_gap - prev_gain) / gains[pos]) + 1
        k_pred = float(prev_cap + need)
        reached = True
    return order, caps, k_pred, reached


def _apply(n, moves, L=None):
    """Apply first L unit moves of a move list [(src, dst, cnt), ...] to a copy of n."""
    n2 = n.copy()
    left = np.inf if L is None else L
    for s, d, cnt in moves:
        if left <= 0:
            break
        q = min(cnt, left)
        if s >= 0:
            n2[s] -= q
        if d >= 0:
            n2[d] += q
        left -= q
    return n2


def _gap_after(tt, n2, i, j, lam, theta0):
    f = fit_bt(tt, n2, lam=lam, theta0=theta0)
    return f.theta[i] - f.theta[j], f


def _min_prefix(tt, n, moves, total, i, j, lam, theta0, lo_hint=0):
    """Smallest prefix length L of `moves` whose refit has theta_i - theta_j < 0 (binary search,
    assumes monotonicity; the returned L is always verified by a refit)."""
    total = int(round(total))
    g, _ = _gap_after(tt, _apply(n, moves, total), i, j, lam, theta0)
    if not g < 0:
        return None
    lo, hi = 0, total          # invariant: prefix lo does not flip (gap0 > 0), prefix hi flips
    if 0 < lo_hint < total:
        g, _ = _gap_after(tt, _apply(n, moves, lo_hint), i, j, lam, theta0)
        if g < 0:
            hi = lo_hint
        else:
            lo = lo_hint
    while hi - lo > 1:
        mid = (lo + hi) // 2
        g, _ = _gap_after(tt, _apply(n, moves, mid), i, j, lam, theta0)
        if g < 0:
            hi = mid
        else:
            lo = mid
    return hi


def _order_to_moves(order, caps, src, dst, upto):
    moves, tot = [], 0
    for o, cp in zip(order, caps):
        if tot >= upto:
            break
        cnt = min(cp, upto - tot)
        moves.append((int(src[o]), int(dst[o]), float(cnt)))
        tot += cnt
    return moves, tot


def min_perturbation(tt, i, j, kind="drop", lam=0.01, batch_frac=0.25, max_iter=400,
                     max_total=None, fit0=None):
    """Find a small set of unit perturbations that makes player j rank strictly above player i
    (requires theta_i > theta_j initially).  Returns a dict with:
      k            : size of the verified perturbation found by iterative AMIP + prefix pruning
      k_oneshot    : verified size using the one-shot (initial influence) ordering (None if fails)
      k_pred       : one-shot first-order prediction of the required size
      moves        : the verified move list (src, dst, count)
    All reported k are verified by refitting the model (they are upper bounds on the exact minimum).
    """
    n0 = tt.n.copy()
    f0 = fit0 if fit0 is not None else fit_bt(tt, n0, lam=lam)
    gap0 = f0.theta[i] - f0.theta[j]
    assert gap0 > 0, "need theta_i > theta_j"
    if max_total is None:
        max_total = tt.N if kind != "add" else 10 * tt.N
    # --- one-shot AMIP
    eff, src, dst, cap = candidate_moves(tt, f0, n0, i, j, kind)
    order, caps, k_pred, reached = _take_items(eff, cap, gap0)
    k_oneshot = None
    lin_pred_at_k = None
    if len(order):
        upto = min(max(k_pred, 1), max_total)
        # grow until the refit flips, then binary-search the prefix
        while True:
            mv, tot = _order_to_moves(order, caps, src, dst, upto)
            g, _ = _gap_after(tt, _apply(n0, mv), i, j, lam, f0.theta)
            if g < 0:
                k_oneshot = _min_prefix(tt, n0, mv, tot, i, j, lam, f0.theta, lo_hint=int(0.5 * min(k_pred, tot)))
                break
            cap_total = float(np.sum(np.where(np.isinf(caps), max_total, caps)))
            if upto >= min(cap_total, max_total):
                break
            upto = min(2 * upto, max_total, cap_total)
    # --- iterative AMIP with refits
    n = n0.copy()
    f = f0
    moves = []
    total = 0.0
    it = 0
    while it < max_iter:
        it += 1
        gap = f.theta[i] - f.theta[j]
        if gap < 0:
            break
        eff, src_, dst_, cap_ = candidate_moves(tt, f, n, i, j, kind)
        order_, caps_, kp, _ = _take_items(eff, cap_, gap)
        if len(order_) == 0 or total >= max_total:
            break
        m_take = max(1, math.ceil(batch_frac * kp))
        m_take = min(m_take, max_total - total)
        mv, tot = _order_to_moves(order_, caps_, src_, dst_, m_take)
        if tot <= 0:
            break
        n = _apply(n, mv)
        moves.extend(mv)
        total += tot
        f = fit_bt(tt, n, lam=lam, theta0=f.theta)
    k_iter = None
    if f.theta[i] - f.theta[j] < 0:
        k_iter = _min_prefix(tt, n0, moves, total, i, j, lam, f0.theta, lo_hint=int(0.5 * total))
    cands = [k for k in (k_iter, k_oneshot) if k is not None]
    k_best = min(cands) if cands else None
    best_moves = None
    if k_best is not None:
        if k_iter is not None and k_iter == k_best:
            best_moves = _trim(moves, k_iter)
        else:
            mv, _ = _order_to_moves(order, caps, src, dst, k_oneshot)
            best_moves = mv
    return dict(i=i, j=j, kind=kind, gap0=float(gap0), k=k_best, k_iter=k_iter, k_oneshot=k_oneshot,
                k_pred=float(k_pred) if reached else None, n_iter=it, moves=best_moves)


def _trim(moves, L):
    out, left = [], L
    for s, d, c in moves:
        if left <= 0:
            break
        q = min(c, left)
        out.append((s, d, q))
        left -= q
    return out


# ----------------------------------------------------------------------------- exact search

def exact_min_drop(tt, i, j, kmax=3, lam=0.01, fit0=None, kind="drop"):
    """Exhaustive search over multisets of types (exact minimum number of dropped comparisons
    (or flips) up to kmax).  Exchangeability within a type makes this exact.  Returns the
    minimum k <= kmax that makes theta_j > theta_i, or None if no such k <= kmax."""
    f0 = fit0 if fit0 is not None else fit_bt(tt, lam=lam)
    n0 = tt.n
    if kind == "drop":
        units = [(t, -1) for t in np.where(n0 > 0)[0]]
    else:
        units = []
        for t in np.where(n0 > 0)[0]:
            base = (t // 3) * 3
            for d in range(base, base + 3):
                if d != t:
                    units.append((t, d))
    for k in range(1, kmax + 1):
        for combo in itertools.combinations_with_replacement(range(len(units)), k):
            n2 = n0.copy()
            ok = True
            for u in combo:
                s, d = units[u]
                n2[s] -= 1
                if d >= 0:
                    n2[d] += 1
                if n2[s] < 0:
                    ok = False
                    break
            if not ok:
                continue
            f = fit_bt(tt, n2, lam=lam, theta0=f0.theta, maxit=30)
            if f.theta[i] - f.theta[j] < 0:
                return k
    return None


# ----------------------------------------------------------------------------- random baselines

def random_drop_counts(rng, n, k):
    ni = n.astype(np.int64)
    dropped = rng.multivariate_hypergeometric(ni, int(k))
    return n - dropped


def random_flip_counts(rng, tt, n, k):
    """Relabel k uniformly chosen comparisons to a different, uniformly chosen outcome among the
    decisive/tie levels (win<->loss; tie->win or loss; win/loss -> the opposite)."""
    ni = n.astype(np.int64)
    chosen = rng.multivariate_hypergeometric(ni, int(k)).astype(float)
    n2 = n - chosen
    lvl = np.arange(len(n)) % 3
    base = (np.arange(len(n)) // 3) * 3
    for t in np.where(chosen > 0)[0]:
        c = int(chosen[t])
        if lvl[t] == 1:   # tie -> win or loss at random
            w = rng.binomial(c, 0.5)
            n2[base[t] + 2] += w
            n2[base[t] + 0] += c - w
        else:             # decisive -> opposite outcome
            n2[base[t] + (2 - lvl[t])] += c
    return n2


def kendall_tau(r1, r2):
    """Kendall tau between two score vectors (no ties assumed)."""
    from scipy.stats import kendalltau
    return float(kendalltau(r1, r2).statistic)
