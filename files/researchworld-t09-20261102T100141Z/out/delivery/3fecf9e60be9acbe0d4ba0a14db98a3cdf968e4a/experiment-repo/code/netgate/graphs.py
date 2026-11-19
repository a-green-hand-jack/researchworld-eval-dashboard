"""Graph generators / loaders. All return a `Net` (largest connected component, relabelled 0..n-1)."""
import gzip, zipfile, io, os
import numpy as np, scipy.sparse as sp, networkx as nx
from dataclasses import dataclass, field

DATA = os.environ.get("NETGATE_DATA", "/hutian/data/raw")


@dataclass
class Net:
    A: sp.csr_matrix              # symmetric 0/1 adjacency, no self loops
    name: str
    deg: np.ndarray = field(init=False)
    W: sp.csr_matrix = field(init=False)   # row-normalised adjacency D^-1 A
    clust: np.ndarray = field(default=None)  # local clustering coefficient
    comm_cache: dict = field(default_factory=dict)

    def __post_init__(self):
        self.A = sp.csr_matrix(self.A)
        self.deg = np.asarray(self.A.sum(1)).ravel()
        self.W = sp.diags(1.0 / self.deg) @ self.A
        self.W = sp.csr_matrix(self.W)

    @property
    def n(self):
        return self.A.shape[0]

    def clustering(self):
        if self.clust is None:
            A = self.A
            tri = np.asarray(A.multiply(A @ A).sum(1)).ravel() / 2.0
            d = self.deg
            self.clust = np.where(d > 1, 2 * tri / np.maximum(d * (d - 1), 1), 0.0)
        return self.clust

    def communities(self, resolution=1.0, seed=0):
        """Louvain partition (labels 0..k-1), cached per (resolution, seed)."""
        key = (resolution, seed)
        if key not in self.comm_cache:
            G = nx.from_scipy_sparse_array(self.A)
            parts = nx.community.louvain_communities(G, resolution=resolution, seed=seed)
            lab = np.empty(self.n, int)
            for k, s in enumerate(parts):
                lab[list(s)] = k
            self.comm_cache[key] = lab
        return self.comm_cache[key]


def _from_nx(G, name):
    G = nx.Graph(G)
    G.remove_edges_from(nx.selfloop_edges(G))
    cc = max(nx.connected_components(G), key=len)
    G = nx.convert_node_labels_to_integers(G.subgraph(cc))
    A = nx.to_scipy_sparse_array(G, format="csr", dtype=float)
    A.data[:] = 1.0
    return Net(sp.csr_matrix(A), name)


def make_graph(kind, n, seed, **kw):
    """kind in {er, ba, ws, sbm, geo, fb_stanford, fb_ego}. `d` = target mean degree."""
    rng = np.random.default_rng(seed)
    s = int(rng.integers(2**31))
    d = kw.get("d", 20)
    if kind == "er":
        G = nx.fast_gnp_random_graph(n, d / (n - 1), seed=s)
    elif kind == "ba":
        G = nx.barabasi_albert_graph(n, max(1, int(round(d / 2))), seed=s)
    elif kind == "ws":
        G = nx.watts_strogatz_graph(n, int(round(d / 2)) * 2, kw.get("beta", 0.1), seed=s)
    elif kind == "sbm":
        mu = kw.get("mu", 0.1)          # fraction of edges that leave the block
        k = kw.get("k", max(4, n // 100))
        k = int(max(2, min(k, n / (d * (1 - mu) / 0.9 + 1))))   # keep within-block edge probability <= 0.9
        sizes = [n // k] * k
        sizes[-1] += n - sum(sizes)
        pin = d * (1 - mu) / (n / k - 1)
        pout = d * mu / (n - n / k)
        P = np.full((k, k), pout) + np.eye(k) * (pin - pout)
        G = nx.stochastic_block_model(sizes, P.tolist(), seed=s)
    elif kind == "geo":   # random geometric graph (strong local clustering)
        r = np.sqrt(d / (np.pi * n))
        G = nx.random_geometric_graph(n, r, seed=s)
    elif kind == "fb_stanford":
        return load_stanford()
    elif kind == "fb_ego":
        return load_ego()
    else:
        raise ValueError(kind)
    return _from_nx(G, f"{kind}_n{n}_d{d}")


_cache = {}


def load_stanford():
    if "stan" not in _cache:
        with zipfile.ZipFile(os.path.join(DATA, "stanford3.zip")) as z:
            nm = [x for x in z.namelist() if x.endswith(".mtx")][0]
            txt = z.read(nm).decode().splitlines()
        rows = []
        for ln in txt:
            if ln.startswith("%") or not ln.strip():
                continue
            rows.append(ln.split()[:2])
        hdr, edges = rows[0], np.array(rows[1:], dtype=int) - 1
        n = int(hdr[0])
        A = sp.coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(n, n))
        A = ((A + A.T) > 0).astype(float)
        A.setdiag(0); A.eliminate_zeros()
        G = nx.from_scipy_sparse_array(A)
        _cache["stan"] = _from_nx(G, "fb_stanford3")
    return _cache["stan"]


def load_ego():
    if "ego" not in _cache:
        with gzip.open(os.path.join(DATA, "fb.txt.gz"), "rt") as f:
            e = np.loadtxt(f, dtype=int)
        n = e.max() + 1
        A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
        A = ((A + A.T) > 0).astype(float)
        _cache["ego"] = _from_nx(nx.from_scipy_sparse_array(A), "fb_ego")
    return _cache["ego"]
