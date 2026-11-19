"""Graph context: adjacency, degree and the exposure map (g1, g2, c1) of an assignment."""
import numpy as np
import scipy.sparse as sp


class Ctx:
    def __init__(self, A, blocks=None):
        self.A = A.tocsr().astype(float)
        self.n = A.shape[0]
        self.deg = np.asarray(self.A.sum(1)).ravel()
        self.dbar = float(self.deg.mean())
        self.nbr2 = np.asarray(self.A @ self.deg).ravel() - self.deg  # off-diagonal row sums of A^2
        self.blocks = blocks
        self._S = None

    def state(self, z):
        z = np.asarray(z, dtype=float)
        c1 = self.A @ z
        g1 = c1 / self.deg
        g2 = (self.A @ c1 - self.deg * z) / np.maximum(self.nbr2, 1e-12)
        return dict(z=z, c1=c1, g1=g1, g2=g2)

    def corner(self, v):
        one = np.full(self.n, float(v))
        return dict(z=one, c1=self.deg * v, g1=one.copy(), g2=one.copy())

    def S_pattern(self):
        """Dependence pattern for 1-hop features: i~j iff closed neighbourhoods intersect (distance <= 2)."""
        if self._S is None:
            B = (self.A + sp.identity(self.n, format="csr")).tocsr()
            S = (B @ B).tocsr()
            S.data[:] = 1.0
            self._S = S
        return self._S

    def graph_stats(self):
        d = self.deg
        return dict(n_eff=self.n, d_mean=self.dbar, d_hm=float(len(d) / np.sum(1 / d)), d_med=float(np.median(d)),
                    d_cv=float(d.std() / d.mean()), m_sqrt=float(np.mean(1 / np.sqrt(d))))
