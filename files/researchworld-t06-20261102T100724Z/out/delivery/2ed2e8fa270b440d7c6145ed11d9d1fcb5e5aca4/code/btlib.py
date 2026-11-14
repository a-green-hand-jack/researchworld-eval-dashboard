"""Bradley-Terry fitting and worst-case edit analysis on aggregated pairwise cells.

A *cell* c has a feature vector x_c (e_i - e_j, optionally + a shared home-advantage
column), `w_c` (fractional) successes and `n_c` trials; P(success) = sigmoid(x_c . beta).
Ties are half-wins (w += .5, n += 1).  Individual comparisons in a cell with the same
outcome are interchangeable, so a cell keeps counts of win / loss / tie votes.
"""
import numpy as np

LAM = 1e-6  # tiny ridge so that the Hessian is invertible (scores are centred afterwards)
EPS = 1e-9  # a flip needs a strictly negative gap


def sig(z):
    return 0.5 * (1.0 + np.tanh(0.5 * z))


class Board:
    """Counts per cell. Cell k: pair (i[k], j[k]) [+ home column h[k] in {0,1}], counts of
    'i beats j' (W), 'j beats i' (L), ties (T). beta has P participants (+1 home param)."""

    def __init__(self, P, i, j, W, L, T, home=None, names=None):
        self.P = P
        self.i, self.j = np.asarray(i), np.asarray(j)
        self.W, self.L, self.T = (np.asarray(a, float) for a in (W, L, T))
        self.home = None if home is None else np.asarray(home, float)  # 1 where i is home
        self.names = names
        self.d = P + (1 if home is not None else 0)

    def copy(self):
        b = Board(self.P, self.i, self.j, self.W.copy(), self.L.copy(), self.T.copy(),
                  self.home, self.names)
        return b

    @property
    def n_cells(self):
        return len(self.i)

    @property
    def N(self):
        return float((self.W + self.L + self.T).sum())

    def X(self):
        m = self.n_cells
        X = np.zeros((m, self.d))
        r = np.arange(m)
        X[r, self.i] = 1.0
        X[r, self.j] = -1.0
        if self.home is not None:
            X[:, self.P] = self.home
        return X

    def wn(self):
        return self.W + 0.5 * self.T, self.W + self.L + self.T

    def fit(self, beta0=None, tol=1e-9, maxit=60):
        X = self.X()
        w, n = self.wn()
        beta = np.zeros(self.d) if beta0 is None else beta0.copy()
        for _ in range(maxit):
            p = sig(X @ beta)
            g = X.T @ (w - n * p) - LAM * beta
            H = (X * (n * p * (1 - p))[:, None]).T @ X + LAM * np.eye(self.d)
            step = np.linalg.solve(H, g)
            # damped Newton (guards against separation-type overshoot)
            m = np.abs(step).max()
            if m > 5:
                step *= 5 / m
            beta += step
            if np.abs(step).max() < tol:
                break
        beta[: self.P] -= beta[: self.P].mean()
        self._X = X
        return beta

    def hessian(self, beta):
        X = self.X()
        w, n = self.wn()
        p = sig(X @ beta)
        return (X * (n * p * (1 - p))[:, None]).T @ X + LAM * np.eye(self.d), X, p


# ---------------------------------------------------------------- edit types
# Each edit changes (dw, dn) of a cell (success = 'i beats j').  Availability is the
# count of the source vote type.  Family: remove / flip (relabel) / inject.
# (name, dw, dn, source) with source in {'W','L','T',None}; target dict for the new type.
EDITS = {
    "remove": [("rW", -1.0, -1.0, "W"), ("rL", 0.0, -1.0, "L"), ("rT", -0.5, -1.0, "T")],
    "flip": [("W>L", -1.0, 0.0, "W"), ("L>W", 1.0, 0.0, "L"),
             ("T>W", 0.5, 0.0, "T"), ("T>L", -0.5, 0.0, "T"),
             ("W>T", -0.5, 0.0, "W"), ("L>T", 0.5, 0.0, "L")],
    "inject": [("iW", 1.0, 1.0, None), ("iL", 0.0, 1.0, None), ("iT", 0.5, 1.0, None)],
}
# how an edit moves the (W, L, T) counts of its cell
APPLY = {
    "rW": (-1, 0, 0), "rL": (0, -1, 0), "rT": (0, 0, -1),
    "W>L": (-1, 1, 0), "L>W": (1, -1, 0), "T>W": (1, 0, -1), "T>L": (0, 1, -1),
    "W>T": (-1, 0, 1), "L>T": (0, -1, 1),
    "iW": (1, 0, 0), "iL": (0, 1, 0), "iT": (0, 0, 1),
}
SRC = {"rW": "W", "rL": "L", "rT": "T", "W>L": "W", "L>W": "L", "T>W": "T", "T>L": "T",
       "W>T": "W", "L>T": "L", "iW": None, "iL": None, "iT": None}
DWN = {name: (dw, dn) for fam in EDITS.values() for (name, dw, dn, _) in fam}


def influence(board, beta, cvec, families=("remove",), cell_mask=None):
    """Linearised effect on c.beta of ONE edit of each (cell, type).  Returns list of
    (effect_array over cells, name).  Negative effect = decreases c.beta."""
    H, X, p = board.hessian(beta)
    v = np.linalg.solve(H, cvec)
    xv = X @ v  # per cell
    out = []
    for fam in families:
        for (name, dw, dn, src) in EDITS[fam]:
            eff = (dw - dn * p) * xv
            if src is None:
                avail = np.full(board.n_cells, np.inf)
            else:
                avail = getattr(board, src).copy()
            if cell_mask is not None:
                avail = np.where(cell_mask, avail, 0.0)
            out.append((name, eff, avail))
    return out


def apply_edits(board, edits):
    """edits: list of (cell, name, count). Mutates board."""
    for c, name, k in edits:
        a, b, t = APPLY[name]
        board.W[c] += a * k
        board.L[c] += b * k
        board.T[c] += t * k


def wald_se(board, beta, cvec):
    H = board.hessian(beta)[0]
    return float(np.sqrt(cvec @ np.linalg.solve(H, cvec)))


def min_edits_to_flip(board, a, b, families=("remove",), cell_mask=None, frac=0.3,
                      max_edits=None, beta0=None, return_trace=False, claim="order", zcrit=1.959964):
    """Smallest set of edits found (greedy with re-linearisation + exact refits) that makes
    beta_a <= beta_b, starting from beta_a > beta_b.  Returns dict with k (int or None if
    infeasible), k_lin (one-shot linear estimate at the original fit), initial gap."""
    P = board.P
    cvec = np.zeros(board.d)
    cvec[a], cvec[b] = 1.0, -1.0
    beta = board.fit(beta0)
    margin = lambda bd, bt: (bt[a] - bt[b]) - (zcrit * wald_se(bd, bt, cvec) if claim == "sig" else 0.0)
    gap0 = margin(board, beta)
    if gap0 <= 0:
        return dict(k=None, k_lin=None, gap0=gap0, feasible=False, applicable=False)
    # one-shot linear estimate (AMIP-style): sort single-edit effects at the full-data fit
    inf0 = influence(board, beta, cvec, families, cell_mask)
    effs = np.concatenate([np.minimum(e, 0) for _, e, _ in inf0])
    avs = np.concatenate([av for _, _, av in inf0])
    k_lin = _linear_budget(gap0, effs, avs)
    cur = board.copy()
    used = 0
    trace = []
    gap = gap0
    while True:
        beta = cur.fit(beta)
        gap = margin(cur, beta)
        if gap < -EPS:
            break
        inf = influence(cur, beta, cvec, families, cell_mask)
        effs = np.stack([e for _, e, _ in inf])  # types x cells
        avs = np.stack([av for _, _, av in inf])
        names = [nm for nm, _, _ in inf]
        flat = np.where(effs < 0, effs, 0).ravel()
        order = np.argsort(flat)
        target = frac * gap
        batch, pred, used_src = [], 0.0, {}
        for idx in order[:4000]:
            e = flat[idx]
            if e >= 0 or (batch and pred >= target):
                break
            ty, c = divmod(idx, effs.shape[1])
            src = SRC[names[ty]]
            av = avs[ty, c] - (used_src.get((c, src), 0) if src else 0)
            if av < 1:
                continue
            k = int(min(np.floor(min(av, 1e9)), max(1, np.ceil((target - pred) / (-e)))))
            if src:
                used_src[(c, src)] = used_src.get((c, src), 0) + k
            batch.append((c, names[ty], k))
            pred += k * (-e)
        if not batch:
            return dict(k=None, k_lin=k_lin, gap0=gap0, feasible=False, applicable=True)
        trial = cur.copy()
        apply_edits(trial, batch)
        bt = trial.fit(beta)
        if margin(trial, bt) < -EPS:
            # bisect on prefix of the batch (expand to unit edits in the batch order)
            units = [(c, nm) for (c, nm, k) in batch for _ in range(k)]
            lo, hi = 0, len(units)  # hi flips, lo does not
            while hi - lo > 1:
                mid = (lo + hi) // 2
                t2 = cur.copy()
                apply_edits(t2, _compress(units[:mid]))
                b2 = t2.fit(beta)
                if margin(t2, b2) < -EPS:
                    hi = mid
                else:
                    lo = mid
            used += hi
            if return_trace:
                trace.append((used, 0.0))
            break
        cur = trial
        used += sum(k for _, _, k in batch)
        if return_trace:
            trace.append((used, margin(trial, bt)))
        if max_edits is not None and used > max_edits:
            return dict(k=None, k_lin=k_lin, gap0=gap0, feasible=False, applicable=True, exceeded=True)
    out = dict(k=int(used), k_lin=k_lin, gap0=gap0, feasible=True, applicable=True)
    if return_trace:
        out["trace"] = trace
    return out


def _compress(units):
    d = {}
    for c, nm in units:
        d[(c, nm)] = d.get((c, nm), 0) + 1
    return [(c, nm, k) for (c, nm), k in d.items()]


def _linear_budget(gap0, effs, avs):
    """Fractional number of single edits (sorted by one-shot influence) needed to cancel gap0
    if influences were exactly additive (AMIP prediction); inf if unreachable."""
    order = np.argsort(effs)
    left = gap0
    k = 0.0
    for idx in order:
        e = effs[idx]
        if e >= 0:
            break
        av = avs[idx] if np.isfinite(avs[idx]) else 1e12
        if av * (-e) >= left:
            return k + left / (-e)
        left -= av * (-e)
        k += av
    return np.inf
