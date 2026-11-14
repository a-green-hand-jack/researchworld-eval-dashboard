"""Treatment assignment designs and the exact probabilities of exposure events they induce."""
import numpy as np
import scipy.sparse as sp


class Bernoulli:
    kind = "bernoulli"

    def __init__(self, p=0.5):
        self.p = p
        self.name = f"bern_p{p}"

    def draw(self, g, rng):
        return (rng.random(g.n) < self.p).astype(np.float64)

    def full_exposure_prob(self, g):
        return self.p ** (g.deg + 1), (1 - self.p) ** (g.deg + 1)


class Cluster:
    """Independent Bernoulli(p) per cluster. labels: integer cluster id per node."""
    kind = "cluster"

    def __init__(self, labels, p=0.5, name="cluster"):
        self.p = p
        self.labels = labels
        self.name = f"{name}_p{p}"
        self.C = int(labels.max()) + 1
        self._k = None

    def draw(self, g, rng):
        zc = (rng.random(self.C) < self.p).astype(np.float64)
        return zc[self.labels]

    def n_clusters_in_closed_nbhd(self, g):
        if self._k is None:
            n = g.n
            M = sp.csr_matrix((np.ones(n), (np.arange(n), self.labels)), shape=(n, self.C))
            B = ((g.A + sp.identity(n)) @ M).tocsr()
            self._k = np.diff(B.indptr)  # structural nonzeros per row
        return self._k

    def full_exposure_prob(self, g):
        k = self.n_clusters_in_closed_nbhd(g)
        return self.p ** k, (1 - self.p) ** k


def _kappa_exposure_prob(self, g, kappa):
    """Exact P(unit i has treated exposure) = P(own cluster treated and >= kappa of its neighbours treated) and
    P(control exposure) = P(own cluster control and <= 1-kappa treated), under independent Bernoulli(p) per cluster.
    Neighbours of i lie in clusters j with n_ij neighbours each; the treated-neighbour count is a sum of independent
    n_ij * Bernoulli(p), whose distribution is built by convolution (per distinct cluster, O(k_i d_i) per unit)."""
    n, p, lab = g.n, self.p, self.labels
    A = g.A.tocsr()
    pi1, pi0 = np.zeros(n), np.zeros(n)
    for i in range(n):
        nb = A.indices[A.indptr[i]:A.indptr[i + 1]]
        d = len(nb)
        cl, cnt = np.unique(lab[nb], return_counts=True)
        own = np.flatnonzero(cl == lab[i])
        # distribution of the number of treated neighbours, separately for own cluster treated (T) and control (C)
        rest = [(c, k) for c, k in zip(cl, cnt) if c != lab[i]]
        dist = np.zeros(d + 1)
        dist[0] = 1.0
        for _, k in rest:
            new = dist * (1 - p)
            new[k:] += dist[:d + 1 - k] * p
            dist = new
        k_own = int(cnt[own[0]]) if len(own) else 0
        t = np.zeros(d + 1); t[k_own:] = dist[:d + 1 - k_own]      # own cluster treated: its k_own neighbours count as treated
        c_ = dist                                                   # own cluster control: they count as control
        cum_t = np.cumsum(t[::-1])[::-1]                            # P(count >= m, own treated), given as joint with own=1 (p factor below)
        lo = int(np.ceil(kappa * d - 1e-12))
        pi1[i] = p * cum_t[min(lo, d)] if lo <= d else 0.0
        hi = int(np.floor((1 - kappa) * d + 1e-12))
        pi0[i] = (1 - p) * np.cumsum(c_)[min(hi, d)]
    return pi1, pi0


Cluster.kappa_exposure_prob = _kappa_exposure_prob


def random_clusters(g, size_labels, rng):
    """Control: clusters with the same size distribution as `size_labels` but random membership."""
    return rng.permutation(size_labels)
