"""Core library: Bradley-Terry fitting on aggregated cells and worst-case data-perturbation attacks.

Data representation ("Board"):
  X  : (C, P) design matrix; row c = e_a - e_b (+ optional covariate columns, e.g. home advantage)
  W  : (C, 3) vote counts per cell: [a wins, b wins, ties]   (ties count as half a win for each side)
  ins_ok : (C,) bool, cells in which new (inserted) votes are allowed
  n_ent  : number of entities (first n_ent parameters are the scores theta)
Model: P(a beats b) = sigmoid(X_c @ theta).  Ridge lam on all parameters (pins the free additive constant).
"""
import numpy as np

LAM = 1e-3


def sigmoid(z):
    return 0.5 * (1.0 + np.tanh(0.5 * z))


class Board:
    def __init__(self, name, dataset, design, ents, X, W, ins_ok=None, clusters=None, meta=None):
        self.name, self.dataset, self.design = name, dataset, design
        self.ents = list(ents)
        self.n_ent = len(ents)
        self.X = np.asarray(X, float)
        self.W = np.asarray(W, float)
        self.C, self.P = self.X.shape
        self.ins_ok = np.ones(self.C, bool) if ins_ok is None else np.asarray(ins_ok, bool)
        self.clusters = clusters  # optional (G, C, 3) per-cluster counts for cluster bootstrap
        self.meta = meta or {}
        self.N = int(round(self.W.sum()))

    def cluster_resample(self, rng):
        """Cluster bootstrap: resample clusters (questions or sessions) with replacement -> counts (C,3)."""
        G = self.clusters.shape[0]
        cnt = rng.multinomial(G, np.full(G, 1.0 / G)).astype(float)
        return np.asarray(self.clusters.T @ cnt).reshape(self.C, 3)


def fit(X, W, theta=None, lam=LAM, tol=1e-10, maxit=60):
    C, P = X.shape
    n = W.sum(1)
    S = W[:, 0] + 0.5 * W[:, 2]
    th = np.zeros(P) if theta is None else theta.copy()
    I = np.eye(P)

    def obj(t):
        z = X @ t
        return np.sum(S * z - n * np.logaddexp(0.0, z)) - 0.5 * lam * t @ t

    f = obj(th)
    for _ in range(maxit):
        p = sigmoid(X @ th)
        g = X.T @ (S - n * p) - lam * th
        w = n * p * (1 - p)
        H = (X.T * w) @ X + lam * I
        step = np.linalg.solve(H, g)
        t = 1.0
        while t > 1e-6:
            f2 = obj(th + t * step)
            if f2 >= f - 1e-12:
                break
            t *= 0.5
        th = th + t * step
        if abs(f2 - f) < tol * max(1.0, abs(f)) and np.max(np.abs(t * step)) < 1e-7:
            f = f2
            break
        f = f2
    return th


def hessian(X, W, th, lam=LAM):
    n = W.sum(1)
    p = sigmoid(X @ th)
    w = n * p * (1 - p)
    return (X.T * w) @ X + lam * np.eye(X.shape[1]), p


def contrast(P, i, j):
    q = np.zeros(P)
    q[i], q[j] = 1.0, -1.0
    return q


def fisher_se(board, th, q):
    H, _ = hessian(board.X, board.W, th)
    return float(np.sqrt(q @ np.linalg.solve(H, q)))


# --------------------------------------------------------------------------------------------
# Attacks. All return the modified count matrix W' (C,3) given a budget K of modified votes.
# Delta = q @ theta; the attacker wants to flip the sign of Delta.
# --------------------------------------------------------------------------------------------
Y = np.array([1.0, 0.0, 0.5])  # outcome value (from a's side) of the three count columns


def _alloc(benefit, cap, K):
    """Greedy allocation: take units in decreasing benefit order up to K units. benefit,cap: flat arrays."""
    order = np.argsort(-benefit)
    take = np.zeros_like(cap)
    left = K
    for idx in order:
        if benefit[idx] <= 0 or left <= 0:
            break
        t = min(cap[idx], left)
        take[idx] = t
        left -= t
    return take


def _select_flip(board, W0, th, q, K, Hmat):
    sgn = np.sign(q @ th)
    g = np.linalg.solve(Hmat, q)
    s = board.X @ g  # (C,)
    # dy_dir: sign of change of S needed in each cell to push Delta towards zero/opposite
    dydir = -sgn * np.sign(s)
    ben = np.zeros((board.C, 3))
    # increasing S (dydir>0): sources Wb (0->1, dy=1) and T (0.5->1, dy=.5); decreasing: Wa (1->0), T (0.5->0)
    pos = dydir > 0
    ben[:, 1] = np.where(pos, np.abs(s) * 1.0, 0.0)
    ben[:, 0] = np.where(~pos, np.abs(s) * 1.0, 0.0)
    ben[:, 2] = np.abs(s) * 0.5
    cap = W0.copy()
    take = _alloc(ben.ravel(), cap.ravel(), K).reshape(board.C, 3)
    W = W0.copy()
    # apply
    # source Wb -> Wa ; source Wa -> Wb ; source T -> Wa (pos) or Wb (neg)
    W[:, 1] -= take[:, 1]; W[:, 0] += take[:, 1]
    W[:, 0] -= take[:, 0]; W[:, 1] += take[:, 0]
    W[:, 2] -= take[:, 2]
    W[:, 0] += np.where(pos, take[:, 2], 0.0)
    W[:, 1] += np.where(~pos, take[:, 2], 0.0)
    return W, ben, take


def _select_remove(board, W0, th, q, K, Hmat):
    sgn = np.sign(q @ th)
    g = np.linalg.solve(Hmat, q)
    s = board.X @ g
    Hinv_x = np.linalg.solve(Hmat, board.X.T)  # (P,C)
    v = np.einsum('cp,pc->c', board.X, Hinv_x)
    p = sigmoid(board.X @ th)
    w1 = p * (1 - p)
    den = np.maximum(1.0 - w1 * v, 0.05)
    ben = np.zeros((board.C, 3))
    for k in range(3):
        e = -s * (Y[k] - p) / den  # effect on Delta of removing one vote with outcome Y[k]
        ben[:, k] = -sgn * e
    take = _alloc(ben.ravel(), W0.ravel(), K).reshape(board.C, 3)
    return W0 - take, ben, take


def attack_modify(board, mode, q, K, th0, rounds=3, W0=None):
    """Return list of candidate modified count matrices (one per re-linearisation round)."""
    W0 = board.W if W0 is None else W0
    cands = []
    th = th0
    Wcur = W0
    for r in range(rounds):
        Hmat, _ = hessian(board.X, Wcur, th)
        if mode == 'flip':
            Wn, _, _ = _select_flip(board, W0, th, q, K, Hmat)
        elif mode == 'remove':
            Wn, _, _ = _select_remove(board, W0, th, q, K, Hmat)
        else:
            raise ValueError(mode)
        cands.append(Wn)
        th = fit(board.X, Wn, th)
        Wcur = Wn
        if q @ th * np.sign(q @ th0) < 0:
            break
    return cands


def attack_insert(board, q, K, th0, rounds=10, cell_mask=None):
    """Add K new votes, each chosen greedily (in batches) to push Delta across zero."""
    sgn = np.sign(q @ th0)
    W = board.W.copy()
    th = th0
    left = K
    nb = min(rounds, K)
    for b in range(nb):
        m = int(np.ceil(left / (nb - b)))
        Hmat, p = hessian(board.X, W, th)
        g = np.linalg.solve(Hmat, q)
        s = board.X @ g
        Hinv_x = np.linalg.solve(Hmat, board.X.T)
        v = np.einsum('cp,pc->c', board.X, Hinv_x)
        w1 = p * (1 - p)
        den = 1.0 + w1 * v
        # adding a vote with outcome y: effect on Delta = s (y - p)/den ; y in {1,0}
        e1 = s * (1 - p) / den
        e0 = s * (0 - p) / den
        ok_c = board.ins_ok if cell_mask is None else (board.ins_ok & cell_mask)
        b1 = np.where(ok_c, -sgn * e1, -np.inf)
        b0 = np.where(ok_c, -sgn * e0, -np.inf)
        c1, c0 = int(np.argmax(b1)), int(np.argmax(b0))
        if b1[c1] >= b0[c0]:
            W[c1, 0] += m
        else:
            W[c0, 1] += m
        left -= m
        th = fit(board.X, W, th)
    return W, th


def reversed_(th, q, sgn0):
    return (q @ th) * sgn0 < -1e-6


def min_budget(board, mode, q, th0, Kmax=None, rounds=3):
    # modes: 'flip', 'remove', 'insert' (anywhere), 'insert_target' (only votes involving the challenger, q==-1)
    """Smallest K (found by exponential + bisection search; heuristic => upper bound on the true minimum)
    such that the attack reverses sign(q @ theta). Returns (K, censored)."""
    sgn0 = np.sign(q @ th0)
    if Kmax is None:
        Kmax = int(0.3 * board.N)

    def ok(K):
        if K == 0:
            return False
        if mode == 'insert':
            _, th = attack_insert(board, q, K, th0)
            return reversed_(th, q, sgn0)
        if mode == 'insert_target':
            jj = int(np.argmin(q * sgn0))  # challenger index
            _, th = attack_insert(board, q, K, th0, cell_mask=np.abs(board.X[:, jj]) > 0)
            return reversed_(th, q, sgn0)
        for Wn in attack_modify(board, mode, q, K, th0, rounds):
            th = fit(board.X, Wn, th0)
            if reversed_(th, q, sgn0):
                return True
        return False

    K = 1
    lo = 0
    while K <= Kmax and not ok(K):
        lo = K
        K *= 2
    if K > Kmax:
        if lo < Kmax and ok(Kmax):
            K = Kmax
        else:
            return Kmax, True
    hi = K
    while hi - lo > 1 and (hi - lo) > max(1, 0.01 * hi):
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi, False


def linear_budget(board, mode, q, th0):
    """First-order (influence-function / AMIP style) estimate: smallest K s.t. summed linearised effects of the
    best K units reach |Delta|. Uses the full-data fit only."""
    Delta = abs(q @ th0)
    Hmat, _ = hessian(board.X, board.W, th0)
    Kbig = board.N
    if mode == 'flip':
        _, ben, _ = _select_flip(board, board.W, th0, q, Kbig, Hmat)
    else:
        _, ben, _ = _select_remove(board, board.W, th0, q, Kbig, Hmat)
    b = ben.ravel()
    cap = board.W.ravel()
    order = np.argsort(-b)
    tot = 0.0
    K = 0.0
    for idx in order:
        if b[idx] <= 0:
            break
        need = Delta - tot
        full = b[idx] * cap[idx]
        if full >= need:
            return int(np.ceil(K + need / b[idx]))
        tot += full
        K += cap[idx]
    return np.inf


def direct_flip_budget(board, i, j, q, th0):
    """Naive baseline: only flip votes in the direct (i,j) cell(s). Returns smallest K (exact refit) or inf."""
    sgn0 = np.sign(q @ th0)
    cells = np.where((np.abs(board.X[:, i]) > 0) & (np.abs(board.X[:, j]) > 0))[0]
    # Direct cells: votes favouring the leader (sign of contrast) are flipped to the challenger.
    # Orientation of cell relative to q: x_c[i]-x_c[j] sign.
    def build(K):
        W = board.W.copy()
        left = K
        for c in cells:
            o = board.X[c, i] * sgn0  # +1 if 'a' is leader side
            src, dst = (0, 1) if o > 0 else (1, 0)
            t = min(W[c, src], left)
            W[c, src] -= t; W[c, dst] += t
            left -= t
            t2 = min(W[c, 2], left)  # ties -> challenger win (counts as one modified vote)
            W[c, 2] -= t2; W[c, dst] += t2
            left -= t2
        return W
    cap = sum(board.W[c, 0] + board.W[c, 1] + board.W[c, 2] for c in cells)
    if cap == 0:
        return np.inf
    def ok(K):
        return reversed_(fit(board.X, build(K), th0), q, sgn0)
    if not ok(int(cap)):
        return np.inf
    lo, hi = 0, int(cap)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi
