"""Evaluation toolkit: slice-wise coverage lookups and reference-mass lookups that make evaluating
many calibration draws cheap (a calibration draw only changes the thresholds q)."""
import numpy as np
from .volume import sample_proposal


class SliceCoverage:
    """Given test scores `s` (m,) and integer slice ids (m,), cov(q)[b] = mean_{i in slice b} 1[s_i <= q]."""

    def __init__(self, s, slice_ids, n_slices):
        self.n_slices = n_slices
        self.sorted = [np.sort(s[slice_ids == b]) for b in range(n_slices)]
        self.sizes = np.array([len(x) for x in self.sorted])
        self.all_sorted = np.sort(s)

    def marginal(self, q):
        return np.searchsorted(self.all_sorted, q, side="right") / len(self.all_sorted)

    def per_slice(self, q):
        """q: scalar or (n_slices,) array of per-slice thresholds (Mondrian)."""
        q = np.broadcast_to(q, (self.n_slices,))
        return np.array([np.searchsorted(self.sorted[b], q[b], side="right") / self.sizes[b]
                         for b in range(self.n_slices)])


def quantile_bins(x, n_bins, edges=None):
    if edges is None:
        edges = np.quantile(x, np.linspace(0, 1, n_bins + 1)[1:-1])
    return np.searchsorted(edges, x, side="right"), edges


class MassLookup:
    """For C centres, pre-draw importance samples and score them under every geometry; then
    mass_j,c(q) = P_ref(score_j(Y, centre_c) <= q) is a cheap table lookup."""

    def __init__(self, centres, score_fns, a=1.0, n_per=1500, seed=0):
        rng = np.random.default_rng(seed)
        self.names = list(score_fns)
        self.tab = {n: [] for n in self.names}
        self.ess = []
        for c in centres:
            Y, logq, logu = sample_proposal(c, a, n_per, rng)
            w = np.exp(logu - logq)
            w /= len(w)
            self.ess.append(w.sum() ** 2 / (w ** 2).sum())
            for n, fn in score_fns.items():
                s = fn(Y, c[None, :])
                o = np.argsort(s)
                self.tab[n].append((s[o], np.concatenate([[0.0], np.cumsum(w[o])])))
        self.n_centres = len(centres)

    def mass(self, name, c_idx, q):
        s, cw = self.tab[name][c_idx]
        return cw[np.searchsorted(s, q, side="right")]

    def mean_log_mass(self, name, q, floor=1e-300):
        """q: scalar or array over centres."""
        q = np.broadcast_to(q, (self.n_centres,))
        m = np.array([self.mass(name, c, q[c]) for c in range(self.n_centres)])
        return np.log(np.maximum(m, floor)).mean(), m
