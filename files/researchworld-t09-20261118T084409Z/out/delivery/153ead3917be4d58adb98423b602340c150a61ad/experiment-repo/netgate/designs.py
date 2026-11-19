"""Assignment mechanisms: Bernoulli(p) and graph cluster randomisation (GCR)."""
import numpy as np
import scipy.sparse as sp
import networkx as nx


def louvain_clusters(A, resolution, rng):
    G = nx.from_scipy_sparse_array(A)
    comms = nx.community.louvain_communities(G, resolution=resolution, seed=int(rng.integers(2**31)))
    lab = np.empty(A.shape[0], dtype=int)
    for k, c in enumerate(comms):
        lab[list(c)] = k
    return lab


class Design:
    """kind 'bern' or 'gcr'; for gcr `labels` gives the cluster of each unit."""

    def __init__(self, kind, p, labels=None):
        self.kind, self.p = kind, p
        self.labels = labels
        if kind == "gcr":
            self.K = int(labels.max()) + 1

    def draw(self, n, rng):
        if self.kind == "bern":
            return (rng.random(n) < self.p).astype(float)
        zc = (rng.random(self.K) < self.p).astype(float)
        return zc[self.labels]

    def cluster_stats(self, ctx):
        """rho = within-cluster share of neighbours; k_i = number of distinct clusters in the closed neighbourhood."""
        if self.kind == "bern":
            return dict(rho=0.0, d_eff=ctx.dbar), np.full(ctx.n, np.nan)
        C = sp.csr_matrix((np.ones(ctx.n), (np.arange(ctx.n), self.labels)), shape=(ctx.n, self.K))
        B = (ctx.A + sp.identity(ctx.n, format="csr")) @ C
        k = np.asarray((B > 0).sum(1)).ravel().astype(float)
        same = np.asarray(ctx.A.multiply(C @ C.T).sum(1)).ravel() if ctx.n < 4000 else None
        if same is None:
            same = np.asarray((ctx.A @ C).multiply(C).sum(1)).ravel()
        rho = float(np.mean(same / ctx.deg))
        d_eff = 1.0 / (rho + (1 - rho) / ctx.dbar)
        return dict(rho=rho, d_eff=d_eff, n_clusters=self.K, k_mean=float(k.mean())), k
