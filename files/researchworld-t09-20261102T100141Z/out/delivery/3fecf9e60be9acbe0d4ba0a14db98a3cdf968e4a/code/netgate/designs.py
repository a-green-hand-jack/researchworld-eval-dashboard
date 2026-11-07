"""Treatment assignment designs and exposure probabilities."""
import numpy as np, scipy.sparse as sp


class Design:
    def __init__(self, kind, p, net, labels=None):
        self.kind, self.p, self.net, self.labels = kind, p, net, labels
        n = net.n
        if kind == "cluster":
            k = labels.max() + 1
            self.C = sp.csr_matrix((np.ones(n), (np.arange(n), labels)), shape=(n, k))
            # number of distinct clusters in each closed neighbourhood -> exact exposure probabilities
            B = (net.A + sp.identity(n)) @ self.C
            self.ncl = np.asarray((B > 0).sum(1)).ravel()
        self.nclu = None

    def draw(self, rng):
        n = self.net.n
        if self.kind == "bernoulli":
            return (rng.random(n) < self.p).astype(float)
        if self.kind == "cluster":
            zc = (rng.random(self.C.shape[1]) < self.p).astype(float)
            return zc[self.labels]
        raise ValueError(self.kind)

    def prob_full(self, treated=True):
        """P(unit and all neighbours treated)  (or all control)."""
        q = self.p if treated else 1 - self.p
        if self.kind == "bernoulli":
            return q ** (self.net.deg + 1)
        return q ** self.ncl
