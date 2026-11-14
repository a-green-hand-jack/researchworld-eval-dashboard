"""Graph construction. Every graph is returned as a Graph: symmetric binary CSR on its largest
connected component, with cached degree and the closed-form pieces needed by the features."""
import gzip
import os
from dataclasses import dataclass, field

import networkx as nx
import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components

DATA = os.environ.get("NETGATE_DATA", "/hutian/data")
def _default_cache():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):  # nearest ancestor holding results/ (repo root, also when the code lives under code/)
        if os.path.isdir(os.path.join(d, "results")):
            return os.path.join(d, "results", "cache")
        d = os.path.dirname(d)
    return os.path.join(os.getcwd(), "results", "cache")


CACHE = os.environ.get("NETGATE_CACHE") or _default_cache()


@dataclass
class Graph:
    name: str
    A: sp.csr_matrix
    blocks: np.ndarray | None = None  # planted communities, if any
    disk_cache: bool = False  # only fixed (real) graphs may cache clusterings on disk
    deg: np.ndarray = field(init=False)
    W: sp.csr_matrix = field(init=False)
    diag2: np.ndarray = field(init=False)
    _louvain: dict = field(default_factory=dict)

    def __post_init__(self):
        self.n = self.A.shape[0]
        self.deg = np.asarray(self.A.sum(1)).ravel()
        self.W = sp.diags(1.0 / self.deg) @ self.A
        self.W = self.W.tocsr()
        # diagonal of W@W: prob. that a 2-step walk returns to its start
        self.diag2 = np.asarray(self.W.multiply(self.W.T).sum(1)).ravel()
        self.mean_deg = self.deg.mean()

    def clusters(self, resolution=1.0, seed=0):
        """Louvain communities (cached) as an integer label per node."""
        key = (resolution, seed)
        if key not in self._louvain:
            path = os.path.join(CACHE, f"{self.name}_louvain_r{resolution}_s{seed}.npy")
            if self.disk_cache and os.path.exists(path):
                lab = np.load(path)
            else:
                G = nx.from_scipy_sparse_array(self.A)
                comms = nx.community.louvain_communities(G, resolution=resolution, seed=seed)
                lab = np.zeros(self.n, dtype=np.int64)
                for k, c in enumerate(comms):
                    lab[list(c)] = k
                if self.disk_cache:
                    os.makedirs(CACHE, exist_ok=True)
                    np.save(path, lab)
            self._louvain[key] = lab
        return self._louvain[key]


def _lcc(A, blocks=None):
    A = sp.csr_matrix(A)
    A.setdiag(0)
    A.eliminate_zeros()
    A.data[:] = 1.0
    A = ((A + A.T) > 0).astype(np.float64).tocsr()
    _, lab = connected_components(A, directed=False)
    big = np.argmax(np.bincount(lab))
    keep = np.where(lab == big)[0]
    A = A[keep][:, keep].tocsr()
    return A, (None if blocks is None else blocks[keep])


def _from_nx(name, G, blocks=None):
    A, b = _lcc(nx.to_scipy_sparse_array(G, format="csr"), blocks)
    return Graph(name, A, b)


def sbm(n, k, mean_deg, in_frac, seed):
    """k equal blocks; in_frac of each node's expected edges stay inside its block."""
    m = n // k
    pin = in_frac * mean_deg / (m - 1)
    pout = (1 - in_frac) * mean_deg / (n - m)
    P = np.full((k, k), pout)
    np.fill_diagonal(P, pin)
    G = nx.stochastic_block_model([m] * k, P.tolist(), seed=seed)
    return _from_nx(f"sbm_n{n}_k{k}_d{mean_deg}_f{in_frac}", G, np.repeat(np.arange(k), m))


def ba(n, m, seed):
    return _from_nx(f"ba_n{n}_m{m}", nx.barabasi_albert_graph(n, m, seed=seed))


def ws(n, k, beta, seed):
    return _from_nx(f"ws_n{n}_k{k}_b{beta}", nx.watts_strogatz_graph(n, k, beta, seed=seed))


def er(n, mean_deg, seed):
    return _from_nx(f"er_n{n}_d{mean_deg}", nx.fast_gnp_random_graph(n, mean_deg / (n - 1), seed=seed))


def _simple_from_sequence(name, seq, seed):
    """Configuration-model graph on a degree sequence, reduced to a simple graph (loops and parallel edges dropped)."""
    seq = [int(x) for x in seq]
    if sum(seq) % 2:
        seq[int(np.argmax(seq))] -= 1
    M = nx.configuration_model(seq, seed=seed)
    G = nx.Graph(M)
    G.remove_edges_from(list(nx.selfloop_edges(G)))
    return _from_nx(name, G)


def cm_ba(n, m, seed):
    """Configuration model with the degree sequence of a Barabasi-Albert(n, m) graph (same degrees, no attachment structure)."""
    seq = [d for _, d in nx.barabasi_albert_graph(n, m, seed=seed).degree()]
    return _simple_from_sequence(f"cmba_n{n}_m{m}", seq, seed)


def regular(n, d, seed):
    return _from_nx(f"reg_n{n}_d{d}", nx.random_regular_graph(d, n, seed=seed))


def powerlaw(n, expo, mean_deg, seed, kmax=500):
    """Configuration model with i.i.d. degrees from P(k) ~ (k+s)^-expo on 1..kmax; the shift s is chosen so that the mean is mean_deg."""
    k = np.arange(1, kmax + 1)

    def mean(s):
        w = (k + s) ** (-float(expo))
        return (k * w).sum() / w.sum()

    lo, hi = -0.99, 1e5  # mean(s) increases with s
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if mean(mid) < mean_deg else (lo, mid)
    w = (k + lo) ** (-float(expo))
    rng = np.random.default_rng(seed)
    seq = rng.choice(k, size=n, p=w / w.sum())
    return _simple_from_sequence(f"pl_n{n}_e{expo}_d{mean_deg}", seq, seed)


def stanford3():
    path = os.path.join(DATA, "stanford", "socfb-Stanford3.mtx")
    with open(path) as f:
        rows = []
        for line in f:
            if line.startswith("%"):
                continue
            rows.append(line)
    n = int(rows[0].split()[0])
    e = np.loadtxt(rows[1:], dtype=np.int64) - 1
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    A, _ = _lcc(A)
    return Graph("stanford3", A, disk_cache=True)


def ego_facebook():
    path = os.path.join(DATA, "ego", "facebook_combined.txt.gz")
    with gzip.open(path, "rt") as f:
        e = np.loadtxt(f, dtype=np.int64)
    n = e.max() + 1
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    A, _ = _lcc(A)
    return Graph("ego_facebook", A, disk_cache=True)


def make(spec, seed=0):
    """spec: 'stanford3' | 'ego' | 'sbm:n,k,deg,in_frac' | 'ba:n,m' | 'ws:n,k,beta' | 'er:n,deg'
    | 'cmba:n,m' (configuration model on a BA degree sequence) | 'reg:n,deg' | 'pl:n,exponent,mean_deg' (power-law degrees; added after the freeze for e14)."""
    kind, _, args = spec.partition(":")
    a = [float(x) if "." in x else int(x) for x in args.split(",")] if args else []
    if kind == "stanford3":
        return stanford3()
    if kind == "ego":
        return ego_facebook()
    return {"sbm": sbm, "ba": ba, "ws": ws, "er": er, "cmba": cm_ba, "reg": regular, "pl": powerlaw}[kind](*a, seed=seed)
