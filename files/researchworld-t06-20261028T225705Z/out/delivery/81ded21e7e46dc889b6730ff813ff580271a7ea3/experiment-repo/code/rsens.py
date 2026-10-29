"""Core library: comparison data loaders, Bradley-Terry fit, influence-based worst-case search (drop / flip / inject).

A dataset is Comp(names, I, J, Y[, x]): comparison c is between items I[c] and J[c]; Y[c] in {0,.5,1} is the score
of I[c] (1 = I wins, .5 = tie). Optional x[c] in {-1,0,1} is a home indicator for I[c] (one shared home-advantage
parameter h, used for sports data). All datasets go through the same fitter. Parameters are in natural-log-odds units.
Every budget reported by `worst_case`/`inject_case` is verified by an exact refit of the altered data.
"""
import numpy as np, pandas as pd, os, scipy.sparse as sp

DATA = os.environ.get("RSENS_DATA", "/hutian/data")
LAM = 1e-3  # weak ridge on all parameters: fixes the additive gauge, handles perfect separation


class Comp:
    def __init__(self, names, I, J, Y, label="", x=None):
        self.names, self.I, self.J, self.Y, self.label = list(names), np.asarray(I), np.asarray(J), np.asarray(Y, float), label
        self.x = None if x is None else np.asarray(x, float)
        self.p, self.n = len(self.names), len(self.I)
        self.P = self.p + (self.x is not None)
        self._X = None

    @property
    def X(self):
        if self._X is None:
            n, r = self.n, np.arange(self.n)
            rows = [r, r]; cols = [self.I, self.J]; vals = [np.ones(n), -np.ones(n)]
            if self.x is not None: rows.append(r); cols.append(np.full(n, self.p)); vals.append(self.x)
            self._X = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, self.P))
        return self._X

    def with_Y(self, Y):
        c = Comp.__new__(Comp); c.__dict__.update(self.__dict__); c.Y = Y; return c

    def subset(self, idx):
        return Comp(self.names, self.I[idx], self.J[idx], self.Y[idx], self.label, None if self.x is None else self.x[idx])


def _encode(a, b, y, label, keep_ties=True, x=None, names=None):
    a, b, y = np.asarray(a), np.asarray(b), np.asarray(y, float)
    m = np.ones(len(y), bool) if keep_ties else (y != 0.5)
    a, b, y = a[m], b[m], y[m]; x = None if x is None else np.asarray(x, float)[m]
    names = sorted(set(a) | set(b)) if names is None else names; ix = {n: i for i, n in enumerate(names)}
    return Comp(names, [ix[v] for v in a], [ix[v] for v in b], y, label, x)


def load(name, keep_ties=True, home=True):
    """name: arena55k | mtbench_human | mtbench_gpt4 | nba (all games) | nba:<year_id> (one regular season)"""
    if name == "arena55k":
        d = pd.read_csv(f"{DATA}/arena55k_train.csv", usecols=["model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
        y = np.where(d.winner_model_a == 1, 1., np.where(d.winner_model_b == 1, 0., .5))
        return _encode(d.model_a, d.model_b, y, name, keep_ties)
    if name in ("mtbench_human", "mtbench_gpt4"):
        d = pd.read_parquet(f"{DATA}/{'mtbench_human' if name == 'mtbench_human' else 'mtbench_gpt4pair'}.parquet",
                            columns=["model_a", "model_b", "winner"])
        w = d.winner.astype(str)
        y = np.where(w == "model_a", 1., np.where(w == "model_b", 0., .5))  # 'tie' and 'tie (inconsistent)' -> tie
        return _encode(d.model_a, d.model_b, y, name, keep_ties)
    if name.startswith("nba"):
        # "nba": all NBA-league games (lg_id NBA; the 1968-76 ABA is a separate, only weakly linked league and is excluded);
        # "nba:YEAR": one regular season of the NBA; "nba:YEAR:ABA": one ABA regular season (separate leaderboard).
        d = pd.read_csv(f"{DATA}/nbaallelo.csv", usecols=["_iscopy", "year_id", "lg_id", "fran_id", "opp_fran", "game_result", "is_playoffs", "game_location"])
        parts = name.split(":"); d = d[(d._iscopy == 0) & (d.lg_id == (parts[2] if len(parts) > 2 else "NBA"))]
        if len(parts) > 1: d = d[(d.year_id == int(parts[1])) & (d.is_playoffs == 0)]
        x = d.game_location.map({"H": 1., "A": -1., "N": 0.}).values if home else None
        return _encode(d.fran_id, d.opp_fran, (d.game_result == "W").astype(float), name, keep_ties, x)
    raise ValueError(name)


def sigmoid(x):
    return 0.5 * (1 + np.tanh(0.5 * x))


def _eta(c, th):
    return th[c.I] - th[c.J] + (0 if c.x is None else th[c.p] * c.x)


def hess(c, th, w=None, lam=None):
    lam = LAM if lam is None else lam
    w = np.ones(c.n) if w is None else w
    s = sigmoid(_eta(c, th)); v = w * s * (1 - s)
    H = (c.X.T @ sp.diags(v) @ c.X).toarray()
    H[np.diag_indices(c.P)] += lam
    return H


def fit(c, w=None, theta0=None, lam=None, iters=50, tol=1e-9):
    """Weighted ridge-penalised BT MLE by Newton. Returns theta (length P; last entry = home advantage if c.x)."""
    lam = LAM if lam is None else lam
    w = np.ones(c.n) if w is None else w
    th = np.zeros(c.P) if theta0 is None else theta0.copy()
    for _ in range(iters):
        s = sigmoid(_eta(c, th))
        g = c.X.T @ (w * (s - c.Y)) + lam * th
        step = np.linalg.solve(hess(c, th, w, lam), g); th -= step
        if np.abs(step).max() < tol: break
    return th


def n_components(c, w=None):
    """number of connected components of the comparison graph over ALL p participants (weights 0 = removed comparisons);
    a participant without any comparison counts as its own component."""
    from scipy.sparse.csgraph import connected_components
    m = np.ones(c.n, bool) if w is None else (w > 0)
    A = sp.coo_matrix((np.ones(m.sum()), (c.I[m], c.J[m])), shape=(c.p, c.p))
    return connected_components(A, directed=False)[0]


def ranking(th, p):
    return np.argsort(-th[:p], kind="stable")


def qvec(c, a, b):
    q = np.zeros(c.P); q[a], q[b] = 1, -1; return q


def worst_case(c, a, b, mode="drop", max_frac=0.5, shrink=0.5, allowed=None, state0=None, th0=None):
    """Smallest set of comparisons to drop (or flip) so that th[a] <= th[b] (a currently above b).
    Iterated influence ranking (first-order, Koh&Liang / Broderick et al.) with exact refits, then bisection on the
    prefix of the alteration order. `allowed`: boolean mask restricting which comparisons may be altered (baselines).
    `state0=(w,Y)`: start from an already-altered dataset. Returns dict(k, k_first_order, phi0, w, Y); k is an upper
    bound on the minimum, verified by an exact refit (nan if not reached within max_frac*N alterations)."""
    n = c.n
    w0, Y0 = (np.ones(n), c.Y.copy()) if state0 is None else (state0[0].copy(), state0[1].copy())
    w, Y = w0.copy(), Y0.copy(); order = []
    th0 = fit(c.with_Y(Y0), w0, th0) if th0 is None or state0 is not None else th0
    phi0 = th0[a] - th0[b]
    if phi0 <= 1e-9: return dict(k=0, k_first_order=0, phi0=phi0, w=w0, Y=Y0)   # already tied/inverted
    th = th0; kmax = int(max_frac * n); first_order = None; q = qvec(c, a, b)
    ncomp0 = n_components(c, w0)
    ok_graph = lambda ww: mode != "drop" or n_components(c, ww) <= ncomp0     # an attack must not disconnect the comparison graph
    used = (w0 == 0) | (Y0 != c.Y) | (Y0 == 0.5)
    if allowed is not None: used = used | ~allowed
    cw = c.with_Y(Y)
    while len(order) < kmax:
        u = c.X @ np.linalg.solve(hess(cw, th, w), q)
        s = sigmoid(_eta(c, th)); r = s - Y
        gain = -(r * u if mode == "drop" else (1 - 2 * Y) * u)      # first-order decrease of phi per alteration
        gain[used] = -np.inf
        o = np.argsort(-gain); cs = np.cumsum(gain[o]); phi = th[a] - th[b]
        hit = int(np.searchsorted(cs, phi))
        if first_order is None: first_order = hit + 1 if hit < n else np.nan
        m = int(max(1, min(np.ceil(shrink * (hit + 1)), kmax - len(order))))
        sel = o[:m]; sel = sel[gain[sel] > 0]
        if len(sel) == 0: break
        used[sel] = True; order += list(sel)
        if mode == "drop": w[sel] = 0
        else: Y[sel] = 1 - Y[sel]
        th = fit(cw, w, th)
        if th[a] - th[b] <= 0 and ok_graph(w): break
        if th[a] - th[b] <= 0: return dict(k=np.nan, k_first_order=first_order, phi0=phi0, w=None, Y=None)   # flip only via disconnection: not counted
    if th[a] - th[b] > 0:
        return dict(k=np.nan, k_first_order=first_order, phi0=phi0, w=None, Y=None)
    order = np.array(order, int)

    def apply(k):
        ww, YY = w0.copy(), Y0.copy(); idx = order[:k]
        if mode == "drop": ww[idx] = 0
        else: YY[idx] = 1 - YY[idx]
        return ww, YY
    def flips(k):
        ww, YY = apply(k); t = fit(c.with_Y(YY), ww, th0); return t[a] - t[b] <= 0 and ok_graph(ww)
    lo, hi = 0, len(order)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if flips(mid): hi = mid
        else: lo = mid
    ww, YY = apply(hi)
    return dict(k=hi, k_first_order=first_order, phi0=phi0, w=ww, Y=YY)


def inject_case(c, a, b, kind="a_wins", max_m=None, th0=None, ncand=6):
    """Smallest number m of NEW comparisons, all involving the target a (kind='a_wins': a beats some opponent j) or
    b (kind='b_loses': some j beats b), whose addition makes th[a] <= th[b] ... here a is the LOWER-ranked target
    that is promoted: call with a below b, success when th[a] >= th[b]. All m injected comparisons use the single
    best opponent j (minimum over j, each by doubling + bisection with exact refits). Weighted fit (weight m on one
    injected row) is exactly equivalent to m identical comparisons. Returns dict(k, j)."""
    th0 = fit(c) if th0 is None else th0
    n, best = c.n, dict(k=np.nan, j=-1)
    max_m = max_m or c.n
    Hinv = np.linalg.inv(hess(c, th0)); q = qvec(c, a, b); hq = Hinv @ q; cand = []
    for j in range(c.p):                                   # first-order screen: gain per injected vote, keep ncand best
        if j in (a, b) and not (kind == "a_wins" and j == b) and not (kind == "b_loses" and j == a): continue
        I, J = (a, j) if kind == "a_wins" else (j, b)
        if I == J: continue
        e = np.zeros(c.P); e[I] += 1; e[J] -= 1
        cand.append((-(1 - sigmoid(th0[I] - th0[J])) * (e @ hq), j))
    for _, j in sorted(cand)[:ncand]:
        if kind == "a_wins": I, J = a, j
        else: I, J = j, b
        if I == J: continue
        def ok(m):
            cc = Comp(c.names, np.append(c.I, I), np.append(c.J, J), np.append(c.Y, 1.0), c.label,
                      None if c.x is None else np.append(c.x, 0.))
            ww = np.append(np.ones(n), m); t = fit(cc, ww, th0); return t[a] >= t[b]
        cap = best["k"] - 1 if best["k"] == best["k"] else max_m
        if cap < 1 or not ok(int(cap)): continue
        lo, hi = 0, int(cap)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if ok(mid): hi = mid
            else: lo = mid
        best = dict(k=hi, j=j)
    return best


def discordant(order_ref_pos, th, p):
    """number of item pairs ordered differently by th than by the reference positions (rank positions, 0=top)."""
    from scipy.stats import kendalltau
    rk = np.empty(p, int); rk[ranking(th, p)] = np.arange(p)
    t = kendalltau(order_ref_pos, rk).statistic
    return t


def tau_attack(c, mode, thr, th0=None, max_frac=0.5, max_steps=400):
    """Greedy attack on Kendall tau (vs the original ranking): repeatedly perform the adjacent swap with the smallest
    first-order cost, using exact-refit-verified worst_case on the current altered data, until tau < thr.
    Returns dict(k=total altered comparisons (verified upper bound), steps, tau)."""
    n, p = c.n, c.p
    th0 = fit(c) if th0 is None else th0
    ref = np.empty(p, int); ref[ranking(th0, p)] = np.arange(p)
    w, Y = np.ones(n), c.Y.copy(); th = th0; k_tot = 0
    for step in range(max_steps):
        tau = discordant(ref, th, p)
        if tau < thr: return dict(k=k_tot, steps=step, tau=tau)
        cw = c.with_Y(Y); Hinv = np.linalg.inv(hess(cw, th, w)); r_ = ranking(th, p)
        s = sigmoid(_eta(c, th)); res = s - Y; cost = []
        for pos in range(p - 1):
            a, b = r_[pos], r_[pos + 1]
            if ref[a] > ref[b]: continue                     # swapping would repair a past swap
            u = c.X @ (Hinv @ qvec(c, a, b))
            gain = -(res * u if mode == "drop" else (1 - 2 * Y) * u)
            gain[(w == 0) | (Y != c.Y) | (Y == .5)] = -np.inf
            cs = np.cumsum(np.sort(gain)[::-1]); cost.append((int(np.searchsorted(cs, th[a] - th[b])), a, b))
        if not cost: break
        _, a, b = min(cost)
        out = worst_case(c, a, b, mode, max_frac=max_frac, state0=(w, Y), th0=th)
        if out["w"] is None: break
        k_tot += out["k"]; w, Y = out["w"], out["Y"]; th = fit(c.with_Y(Y), w, th)
        if k_tot > max_frac * n: break
    return dict(k=np.nan, steps=step, tau=discordant(ref, th, p))
