"""Cluster-level deletion: the unit of deletion is a group of votes (MT-Bench question, Arena session).
Greedy first-order ranking of clusters by the summed effect of their votes on the contrast, apply a
fraction of the predicted number, refit, bisect (same scheme as bt.min_edits)."""
import numpy as np
from bt import LABELS


def votes_index(board, lo, hi, lab):
    """Map raw votes (item indices lo<hi from the first item's view, label index 0/1/2) to configuration ids."""
    cfg = {(int(a), int(b)): c for c, (a, b) in enumerate(board.pairs)}
    return np.array([cfg[(int(a), int(b))] for a, b in zip(lo, hi)]), np.asarray(lab)


def min_clusters(board, v_cfg, v_lab, v_cl, i, j, zcrit=None, max_clusters=None):
    """Smallest found number of clusters whose removal reverses i over j (or brings z to zcrit).  inf if none."""
    th = board.fit(); c = board.contrast(i, j)
    ncl = int(v_cl.max()) + 1
    C = len(board.pairs)
    cell = v_cfg * 3 + v_lab
    removed = np.zeros(ncl, bool)
    Ntot = np.bincount(cell, minlength=C * 3).reshape(C, 3)
    assert (Ntot == board.N).all()

    def counts(rem):
        keep = ~rem[v_cl]
        return np.bincount(cell[keep], minlength=C * 3).reshape(C, 3)

    def margin(N_, th_):
        if zcrit is None:
            return c @ th_
        return c @ th_ - zcrit * board.with_counts(N_).ij_se(th_, i, j)

    N = Ntot.copy(); gap = margin(N, th)
    if gap <= 0:
        return 0
    used = 0
    max_clusters = ncl if max_clusters is None else max_clusters
    for _ in range(100):
        H, p = board.hessian(th, N)
        u = np.linalg.solve(H, c); xu = board.X @ u
        gain_vote = xu[:, None] * (LABELS[None, :] - p[:, None])          # reduction of contrast if the vote is deleted
        gain = np.bincount(v_cl[~removed[v_cl]], weights=gain_vote[v_cfg, v_lab][~removed[v_cl]], minlength=ncl)
        gain[removed] = -np.inf
        order = np.argsort(-gain); order = order[gain[order] > 0]
        if len(order) == 0:
            return np.inf
        cs = np.cumsum(gain[order]); need = int(np.searchsorted(cs, gap)) + 1
        take = max(1, int(np.ceil(0.5 * need))) if need <= len(order) else max(1, len(order) // 2)
        take = min(take, len(order))

        def rem_with(t):
            r = removed.copy(); r[order[:t]] = True
            return r
        r2 = rem_with(take); N2 = counts(r2); th2 = board.fit(N2, th)
        if margin(N2, th2) <= 0:
            lo, hi = 0, take
            while hi - lo > 1:
                mid = (lo + hi) // 2
                Nm = counts(rem_with(mid))
                if margin(Nm, board.fit(Nm, th)) <= 0:
                    hi = mid
                else:
                    lo = mid
            return used + hi
        removed, N, th, used = r2, N2, th2, used + take
        gap = margin(N, th)
        if used >= max_clusters or (~removed).sum() <= 1:
            return np.inf
    return np.inf
