"""Core library: count-based Bradley-Terry model with soft tie labels, influence
computations and greedy worst-case edit search (drop / relabel / insert).

A leaderboard is stored as a count tensor N[c, l]: number of votes in
configuration c (an ordered/canonical item pair, plus optional home-field
indicator) with label l in {0, 0.5, 1} (outcome from the "first" item's
perspective; 0.5 = tie).  A unit "edit" changes one vote.
"""
import numpy as np

LABELS = np.array([0.0, 0.5, 1.0])
RIDGE = 1e-3  # tiny L2 on item scores, only for numerical uniqueness


class Board:
    def __init__(self, names, pairs, counts, home=None, name=""):
        """names: list of item names; pairs: (C,2) int array (first, second);
        counts: (C,3) int array; home: (C,) float feature (+1 if first item is
        at home, 0 if neutral/none) or None."""
        self.names = list(names)
        self.m = len(names)
        self.pairs = np.asarray(pairs)
        self.N = np.asarray(counts, dtype=np.int64).copy()
        self.name = name
        C = len(self.pairs)
        self.has_home = home is not None
        P = self.m + (1 if self.has_home else 0)
        X = np.zeros((C, P))
        X[np.arange(C), self.pairs[:, 0]] += 1.0
        X[np.arange(C), self.pairs[:, 1]] -= 1.0
        if self.has_home:
            X[:, self.m] = home
        self.X = X
        self.P = P
        self.lam = np.full(P, RIDGE)
        if self.has_home:
            self.lam[self.m] = 1e-6

    @property
    def n(self):
        return int(self.N.sum())

    def with_counts(self, N):
        b = object.__new__(Board)
        b.__dict__.update(self.__dict__)
        b.N = np.asarray(N, dtype=np.int64)
        return b

    # ---------------------------------------------------------------- fit
    def fit(self, N=None, theta0=None, tol=1e-10, maxit=100):
        N = self.N if N is None else N
        S = N.sum(1).astype(float)
        Y = N @ LABELS
        th = np.zeros(self.P) if theta0 is None else theta0.copy()
        X, lam = self.X, self.lam

        def nll(t):
            z = X @ t
            # sum_c S*log(1+e^z) - Y*z  (logistic with soft labels)
            return np.sum(S * np.logaddexp(0, z) - Y * z) + 0.5 * np.sum(lam * t * t)

        f = nll(th)
        for _ in range(maxit):
            z = X @ th
            p = 1 / (1 + np.exp(-z))
            g = X.T @ (S * p - Y) + lam * th
            if np.max(np.abs(g)) < tol * max(1.0, S.sum()) * 1e-3 and np.max(np.abs(g)) < 1e-8:
                break
            H = X.T @ ((S * p * (1 - p))[:, None] * X) + np.diag(lam)
            d = np.linalg.solve(H, g)
            s = 1.0
            while True:
                tn = th - s * d
                fn = nll(tn)
                if fn <= f + 1e-12 or s < 1e-6:
                    break
                s *= 0.5
            th, f = tn, fn
            if np.max(np.abs(s * d)) < 1e-11:
                break
        return th

    def hessian(self, th, N=None):
        N = self.N if N is None else N
        S = N.sum(1).astype(float)
        p = 1 / (1 + np.exp(-(self.X @ th)))
        return self.X.T @ ((S * p * (1 - p))[:, None] * self.X) + np.diag(self.lam), p

    def contrast(self, i, j):
        c = np.zeros(self.P)
        c[i] = 1
        c[j] = -1
        return c

    def scores(self, th):
        return th[: self.m]

    # --------------------------------------------------------- influence/SE
    def ij_se(self, th, i, j):
        """Infinitesimal-jackknife (sandwich) s.e. of theta_i - theta_j."""
        H, p = self.hessian(th)
        u = np.linalg.solve(H, self.contrast(i, j))
        xu = self.X @ u
        # per-vote psi = xu*(y-p); sum over votes of psi^2
        r = LABELS[None, :] - p[:, None]
        return float(np.sqrt(np.sum(self.N * (xu[:, None] * r) ** 2)))

    def bootstrap(self, B, rng, theta0=None):
        """Multinomial (nonparametric) bootstrap of full vote set; returns (B,P)."""
        n = self.n
        pr = (self.N / n).ravel()
        out = np.empty((B, self.P))
        th0 = self.fit() if theta0 is None else theta0
        for b in range(B):
            Nb = rng.multinomial(n, pr).reshape(self.N.shape)
            out[b] = self.fit(Nb, th0)
        return out

    def subsample(self, n, rng):
        """Subsample n votes without replacement."""
        flat = self.N.ravel()
        if n >= flat.sum():
            return self.with_counts(self.N)
        s = rng.multivariate_hypergeometric(flat, n)
        return self.with_counts(s.reshape(self.N.shape))

    def restrict(self, keep, name=None):
        """Keep only items in `keep` (list of indices); drop votes involving others."""
        keep = list(keep)
        remap = -np.ones(self.m, dtype=int)
        remap[keep] = np.arange(len(keep))
        msk = (remap[self.pairs[:, 0]] >= 0) & (remap[self.pairs[:, 1]] >= 0)
        pairs = remap[self.pairs[msk]]
        home = self.X[msk, self.m] if self.has_home else None
        return Board([self.names[k] for k in keep], pairs, self.N[msk], home,
                     name or self.name)


# ----------------------------------------------------------------- attacks
def _moves(board, N, th, u, kind, allowed=None):
    """First-order effect on c^T theta of every unit move (per unit).

    Returns arrays (effect, cfg, src, dst, cap). src=-1 for insertion,
    dst=-1 for drop. cap = available units (inf for insertion)."""
    xu = board.X @ u
    p = 1 / (1 + np.exp(-(board.X @ th)))
    C = len(xu)
    eff, cfg, src, dst, cap = [], [], [], [], []
    ar = np.arange(C)
    if kind == "drop":
        for l in range(3):
            eff.append(-xu * (LABELS[l] - p))
            cfg.append(ar); src.append(np.full(C, l)); dst.append(np.full(C, -1))
            cap.append(N[:, l].astype(float))
    elif kind == "relabel":
        for l in range(3):
            for l2 in range(3):
                if l == l2:
                    continue
                eff.append(xu * (LABELS[l2] - LABELS[l]))
                cfg.append(ar); src.append(np.full(C, l)); dst.append(np.full(C, l2))
                cap.append(N[:, l].astype(float))
    elif kind == "insert":
        for l2 in (0, 2):
            eff.append(xu * (LABELS[l2] - p))
            cfg.append(ar); src.append(np.full(C, -1)); dst.append(np.full(C, l2))
            cap.append(np.full(C, np.inf))
    else:
        raise ValueError(kind)
    out = tuple(np.concatenate(a) for a in (eff, cfg, src, dst, cap))
    if allowed is not None:
        keep = allowed[out[1]]
        out = tuple(a[keep] for a in out)
    return out


def _plan(moves, nunits, direction=-1, rng=None):
    """Choose up to nunits unit moves with the largest effect in `direction`
    (-1: decrease contrast). Respects source capacities (relabel moves of the
    same source share capacity). Returns list of (cfg, src, dst, count) in
    order of decreasing effect, and the first-order effect per unit."""
    eff, cfg, src, dst, cap = moves
    e = direction * eff
    order = np.argsort(-e) if rng is None else rng.permutation(len(e))   # rng: random helpful edits (baseline)
    plan, used, left = [], {}, nunits
    effs = []
    for idx in order:
        if left <= 0:
            break
        if e[idx] <= 0:
            if rng is None:
                break
            continue
        c, s, d = int(cfg[idx]), int(src[idx]), int(dst[idx])
        avail = cap[idx] - (used.get((c, s), 0) if s >= 0 else 0)
        if avail <= 0:
            continue
        t = int(min(avail, left))
        if s >= 0:
            used[(c, s)] = used.get((c, s), 0) + t
        plan.append((c, s, d, t))
        effs.append((e[idx], t))
        left -= t
    return plan, effs


def _apply(N, plan, nunits=None):
    N = N.copy()
    left = nunits if nunits is not None else 10 ** 18
    for c, s, d, t in plan:
        t = min(t, left)
        if t <= 0:
            break
        if s >= 0:
            N[c, s] -= t
        if d >= 0:
            N[c, d] += t
        left -= t
    return N


def predicted_units(effs, gap):
    """Units needed under a linear model given sorted per-unit effects."""
    tot = 0.0
    k = 0
    for e, t in effs:
        if tot + e * t >= gap:
            return k + int(np.ceil((gap - tot) / e))
        tot += e * t
        k += t
    return np.inf


def min_edits(board, i, j, kind, max_k, th0=None, frac=0.5, with_N=False, thr=0.0, zcrit=None,
              allowed=None, rng=None):
    """Greedy search for a small edit set that makes theta_i <= theta_j (given
    theta_i > theta_j at the start).  Each round: first-order influence ranking
    at the current refit, apply a fraction of the predicted number of units, refit.
    If zcrit is given the target is instead to bring the z-statistic
    (theta_i-theta_j)/se (se = IJ s.e. recomputed on the edited board) down to zcrit.
    Returns dict(k=verified #edits (upper bound on minimum, inf if > max_k),
    k_lin=first-order (AMIP-style) prediction at the original fit)."""
    N = board.N.copy()
    th = board.fit(N) if th0 is None else th0.copy()
    c = board.contrast(i, j)

    def margin(N_, th_):
        if zcrit is None:
            return c @ th_ - thr
        return c @ th_ - zcrit * board.with_counts(N_).ij_se(th_, i, j)

    gap = margin(N, th)
    if gap <= 0:
        return dict(k=0, k_lin=0)
    used = 0
    k_lin = None
    for rnd in range(200):
        H, _ = board.hessian(th, N)
        u = np.linalg.solve(H, c)
        mv = _moves(board, N, th, u, kind, allowed)
        plan, effs = _plan(mv, int(max_k - used), rng=rng)
        kp = predicted_units(effs, gap)
        if k_lin is None:
            k_lin = kp + used
        if not np.isfinite(kp):
            step = int(max_k - used)
            if step <= 0:
                return dict(k=np.inf, k_lin=k_lin)
            take = max(1, step // 2) if rnd > 0 else max(1, step // 4)
        else:
            take = max(1, int(np.ceil(frac * kp)))
        take = int(min(take, max_k - used))
        if take <= 0:
            return dict(k=np.inf, k_lin=k_lin)
        Nn = _apply(N, plan, take)
        thn = board.fit(Nn, th)
        if margin(Nn, thn) <= 0:
            lo, hi = 0, take  # lo: not flipped, hi: flipped
            while hi - lo > 1:
                mid = (lo + hi) // 2
                Nm = _apply(N, plan, mid)
                if margin(Nm, board.fit(Nm, th)) <= 0:
                    hi = mid
                else:
                    lo = mid
            out = dict(k=used + hi, k_lin=k_lin)
            if with_N:
                out["N"] = _apply(N, plan, hi)
            return out
        if used + take >= max_k:
            return dict(k=np.inf, k_lin=k_lin)
        N, th, used = Nn, thn, used + take
        gap = margin(N, th)
    return dict(k=np.inf, k_lin=k_lin)


def rank_order(th_scores):
    return np.argsort(-th_scores)


def pair_records(board, th, i, j, kinds=("drop", "relabel", "insert"), modes=("flip", "sig"),
                 maxfrac=0.3, extra=None):
    """Minimal-edit records for the ordered pair (i above j) of a fitted board."""
    s = th[: board.m]
    gap = s[i] - s[j]
    se = board.ij_se(th, i, j)
    touch = (board.pairs[:, 0] == i) | (board.pairs[:, 1] == i) | (board.pairs[:, 0] == j) | (board.pairs[:, 1] == j)
    ntouch = int(board.N[touch].sum())
    rk = np.empty(board.m, int); rk[np.argsort(-s)] = np.arange(board.m)
    rows = []
    for kind in kinds:
        for mode in modes:
            if mode == "sig" and gap / se <= 1.96:
                continue
            r = min_edits(board, i, j, kind, max_k=int(maxfrac * board.n), th0=th,
                          zcrit=1.96 if mode == "sig" else None)
            row = dict(i=i, j=j, ri=int(rk[i]), rj=int(rk[j]), gap=gap, se=se, n=board.n, m=board.m,
                       ntouch=ntouch, kind=kind, mode=mode, k=r["k"], k_lin=r["k_lin"])
            if extra:
                row.update(extra)
            rows.append(row)
    return rows
