"""Bradley-Terry (with ties as half-wins) on aggregated count cells, and greedy adversarial
perturbation of the comparison data (remove / relabel / insert votes) to flip a pairwise order.

Model: P(a beats b) = sigmoid(theta_a - theta_b); a tie counts as 0.5 win for each side
(the same convention as the Elo/BT leaderboards of Chatbot Arena).  Penalised MLE with a small
ridge  (lam/2)*||theta||^2  (fixes the additive gauge and prevents divergence under separation).
"""
import numpy as np

YV = np.array([1.0, 0.5, 0.0])  # outcome values for cells 0:a wins, 1:tie, 2:b wins
LAM = 1e-3


def sigmoid(x):
    return 0.5 * (1.0 + np.tanh(0.5 * x))


class Cells:
    """Aggregated data: pair list (pa<pb) and integer counts C[P,3]."""

    def __init__(self, n, pa, pb, C):
        self.n, self.pa, self.pb, self.C = n, pa, pb, C

    @staticmethod
    def from_votes(n, a, b, y):
        a = np.asarray(a); b = np.asarray(b); y = np.asarray(y)
        sw = a > b
        lo = np.where(sw, b, a); hi = np.where(sw, a, b)
        yy = np.where(sw, 1.0 - y, y)
        o = np.where(yy == 1.0, 0, np.where(yy == 0.5, 1, 2))
        key = lo * n + hi
        uk, inv = np.unique(key, return_inverse=True)
        C = np.zeros((len(uk), 3), np.int64)
        np.add.at(C, (inv, o), 1)
        return Cells(n, uk // n, uk % n, C)

    def copy(self):
        return Cells(self.n, self.pa, self.pb, self.C.copy())

    @property
    def N(self):
        return int(self.C.sum())

    def npair(self):
        return self.C.sum(1)


def fit(cells, theta0=None, lam=None, tol=1e-10, maxit=100):
    lam = LAM if lam is None else lam
    n, pa, pb = cells.n, cells.pa, cells.pb
    cnt = cells.npair().astype(float)
    S = cells.C[:, 0] + 0.5 * cells.C[:, 1]
    th = np.zeros(n) if theta0 is None else theta0.copy()
    for _ in range(maxit):
        d = th[pa] - th[pb]
        p = sigmoid(d)
        r = S - cnt * p                       # score residual per pair (for a)
        g = -(np.bincount(pa, r, n) - np.bincount(pb, r, n)) + lam * th
        w = cnt * p * (1 - p)
        H = np.zeros((n, n))
        np.add.at(H, (pa, pa), w); np.add.at(H, (pb, pb), w)
        np.add.at(H, (pa, pb), -w); np.add.at(H, (pb, pa), -w)
        H[np.diag_indices(n)] += lam
        step = np.linalg.solve(H, g)
        th = th - step
        if np.max(np.abs(step)) < tol:
            break
    d = th[pa] - th[pb]
    p = sigmoid(d)
    w = cnt * p * (1 - p)
    H = np.zeros((n, n))
    np.add.at(H, (pa, pa), w); np.add.at(H, (pb, pb), w)
    np.add.at(H, (pa, pb), -w); np.add.at(H, (pb, pa), -w)
    H[np.diag_indices(n)] += lam
    return th, H


def ranking(theta):
    return np.argsort(-theta, kind="stable")


def kendall_tau(x, y):
    """Kendall tau-b between two score vectors (O(n^2), n<=~100)."""
    n = len(x)
    dx = np.sign(x[:, None] - x[None, :]); dy = np.sign(y[:, None] - y[None, :])
    iu = np.triu_indices(n, 1)
    dx = dx[iu]; dy = dy[iu]
    num = (dx * dy).sum()
    den = np.sqrt((dx != 0).sum() * (dy != 0).sum())
    return num / den if den > 0 else np.nan


# ---------------------------------------------------------------------------------------------
# Greedy adversary
# ---------------------------------------------------------------------------------------------
def _moves(cells, th, v, mode):
    """Return arrays (pair_idx, src_cell, dst_cell, gain_per_unit, capacity) of candidate moves.
    gain = decrease of the contrast c'theta predicted by one Newton step from one unit."""
    d = th[cells.pa] - th[cells.pb]
    ph = sigmoid(d)
    vx = v[cells.pa] - v[cells.pb]          # sensitivity of contrast to a unit of "a-score" in each pair
    P = len(ph)
    pidx, src, dst, gain, cap = [], [], [], [], []
    ar = np.arange(P)
    if mode == "remove":
        for o in range(3):
            g = -vx * (ph - YV[o])           # Delta c = vx*(p-y); gain = -Delta c
            pidx.append(ar); src.append(np.full(P, o)); dst.append(np.full(P, -1)); gain.append(g)
            cap.append(cells.C[:, o])
    elif mode == "relabel":
        for o in range(3):
            for o2 in range(3):
                if o == o2:
                    continue
                g = -vx * (YV[o2] - YV[o])    # Delta c = vx*(y'-y)
                pidx.append(ar); src.append(np.full(P, o)); dst.append(np.full(P, o2)); gain.append(g)
                cap.append(cells.C[:, o])
    elif mode == "insert":
        big = 10 ** 9
        for o2 in range(3):
            g = -vx * (YV[o2] - ph)           # Delta c = vx*(y'-p)
            pidx.append(ar); src.append(np.full(P, -1)); dst.append(np.full(P, o2)); gain.append(g)
            cap.append(np.full(P, big))
    else:
        raise ValueError(mode)
    return (np.concatenate(pidx), np.concatenate(src), np.concatenate(dst),
            np.concatenate(gain), np.concatenate(cap))


def greedy_flip(cells, i, j, mode, theta0=None, max_k=None, trace=False):
    """Smallest number of unit edits (found by chunked greedy with exact refits) such that
    theta_i < theta_j, starting from theta_i > theta_j.  mode in {remove, relabel, insert}.
    Returns (k, final_cells) ; k = np.inf if the heuristic finds no improving edit.
    For 'insert', new pairs that do not exist in `cells` are added as zero-count cells beforehand
    (caller should use `with_all_pairs`)."""
    cells = cells.copy()
    th, H = fit(cells, theta0)
    c = np.zeros(cells.n); c[i] = 1; c[j] = -1
    if c @ th < 1e-9:   # exact (numerical) tie, e.g. identical records: nothing to flip
        return 0, cells
    k = 0
    hist = []
    N0 = cells.N
    max_k = max_k if max_k is not None else N0 * 2
    while c @ th > -1e-9:   # strict flip required (theta_i < theta_j by more than numerical noise)
        v = np.linalg.solve(H, c)
        margin = c @ th
        pidx, src, dst, gain, cap = _moves(cells, th, v, mode)
        ok = (gain > 1e-15) & (cap > 0)
        if not ok.any():
            return np.inf, cells
        pidx, src, dst, gain, cap = pidx[ok], src[ok], dst[ok], gain[ok], cap[ok]
        order = np.argsort(-gain, kind="stable")
        est = margin / gain[order[0]]
        chunk = max(1, int(0.5 * est))
        used = 0
        C = cells.C
        avail = {}
        for t in order:
            if used >= chunk:
                break
            p, s, dd = pidx[t], src[t], dst[t]
            room = int(cap[t]) if s < 0 else int(C[p, s])
            take = min(chunk - used, room)
            if take <= 0:
                continue
            if s >= 0:
                C[p, s] -= take
            if dd >= 0:
                C[p, dd] += take
            used += take
        if used == 0:
            return np.inf, cells
        k += used
        th, H = fit(cells, th)
        if trace:
            hist.append((k, float(c @ th)))
        if k > max_k:
            return np.inf, cells
    return k, (cells if not trace else (cells, hist))


def with_all_pairs(cells):
    """Add zero-count cells for every unordered pair (for the 'insert' adversary)."""
    n = cells.n
    ia, ib = np.triu_indices(n, 1)
    key = ia * n + ib
    have = cells.pa * n + cells.pb
    C = np.zeros((len(key), 3), np.int64)
    pos = np.searchsorted(key, have)
    C[pos] = cells.C
    return Cells(n, ia, ib, C)


def remove_random(cells, k, rng):
    """Remove k votes uniformly at random (without replacement)."""
    C = cells.C.copy()
    flat = C.ravel()
    idx = rng.choice(np.repeat(np.arange(flat.size), flat), size=k, replace=False)
    rem = np.bincount(idx, minlength=flat.size)
    return Cells(cells.n, cells.pa, cells.pb, (flat - rem).reshape(C.shape))


def bootstrap_cells(cells, rng):
    """Nonparametric bootstrap of the votes (resample N votes with replacement)."""
    flat = cells.C.ravel()
    N = flat.sum()
    return Cells(cells.n, cells.pa, cells.pb, rng.multinomial(N, flat * (1.0 / N)).reshape(cells.C.shape))


def oneshot_k(cells, i, j, mode, th=None, H=None):
    """First-order (single linearisation, no refit) estimate of the edits needed: sort per-unit
    predicted gains and accumulate until the predicted contrast change exceeds the margin."""
    if th is None:
        th, H = fit(cells)
    c = np.zeros(cells.n); c[i] = 1; c[j] = -1
    v = np.linalg.solve(H, c)
    margin = c @ th
    pidx, src, dst, gain, cap = _moves(cells, th, v, mode)
    ok = (gain > 1e-15) & (cap > 0)
    gain, cap = gain[ok], cap[ok]
    o = np.argsort(-gain)
    tot = np.cumsum(gain[o] * cap[o].astype(float))
    pos = np.searchsorted(tot, margin)
    if pos >= len(tot):
        return np.inf
    prev = tot[pos - 1] if pos > 0 else 0.0
    cap_prev = cap[o][:pos].sum() if pos > 0 else 0
    return int(cap_prev + np.ceil((margin - prev) / gain[o][pos]))
