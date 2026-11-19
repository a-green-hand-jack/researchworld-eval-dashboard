"""Graph generators and loaders. Every graph is returned as a symmetric binary scipy CSR matrix on its
largest connected component (so every unit has degree >= 1)."""
import gzip
import os
import zipfile

import networkx as nx
import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components

DATA_DIR = os.environ.get("NETGATE_DATA", "data/raw")


def _from_edges(n, u, v):
    u = np.asarray(u)
    v = np.asarray(v)
    m = u != v
    u, v = u[m], v[m]
    A = sp.coo_matrix((np.ones(len(u)), (u, v)), shape=(n, n)).tocsr()
    A = A + A.T
    A.data[:] = 1.0
    A.setdiag(0)
    A.eliminate_zeros()
    return A


def largest_component(A, labels=None):
    nc, lab = connected_components(A, directed=False)
    if nc > 1:
        big = np.argmax(np.bincount(lab))
        keep = np.where(lab == big)[0]
        A = A[keep][:, keep].tocsr()
        if labels is not None:
            labels = labels[keep]
    return (A, labels) if labels is not None else A


def gen_er(n, d, rng):
    p = d / (n - 1)
    m = rng.binomial(n * (n - 1) // 2, p)
    u = rng.integers(0, n, size=int(m * 1.05) + 10)
    v = rng.integers(0, n, size=len(u))
    return largest_component(_from_edges(n, u, v)), None


def gen_sbm(n, d, rng, K=10, mu=0.7):
    """K equal blocks; a fraction mu of each unit's expected edges stays inside its block."""
    blocks = np.repeat(np.arange(K), int(np.ceil(n / K)))[:n]
    sizes = np.bincount(blocks, minlength=K)
    us, vs = [], []
    for a in range(K):
        ia = np.where(blocks == a)[0]
        # within block
        pin = mu * d / max(sizes[a] - 1, 1)
        m = rng.binomial(sizes[a] * (sizes[a] - 1) // 2, min(pin, 1.0))
        us.append(rng.choice(ia, m)), vs.append(rng.choice(ia, m))
        for b in range(a + 1, K):
            ib = np.where(blocks == b)[0]
            pout = (1 - mu) * d / (n - sizes[a]) if K > 1 else 0
            m = rng.binomial(sizes[a] * sizes[b], min(pout, 1.0))
            us.append(rng.choice(ia, m)), vs.append(rng.choice(ib, m))
    A = _from_edges(n, np.concatenate(us), np.concatenate(vs))
    A, blocks = largest_component(A, blocks)
    return A, blocks


def gen_ba(n, d, rng):
    G = nx.barabasi_albert_graph(n, max(int(round(d / 2)), 1), seed=int(rng.integers(2**31)))
    return largest_component(nx.to_scipy_sparse_array(G, format="csr", dtype=float).tocsr()), None


def gen_ws(n, d, rng, rewire=0.1):
    k = max(2 * int(round(d / 2)), 2)
    G = nx.watts_strogatz_graph(n, k, rewire, seed=int(rng.integers(2**31)))
    return largest_component(nx.to_scipy_sparse_array(G, format="csr", dtype=float).tocsr()), None


def load_stanford3():
    z = zipfile.ZipFile(os.path.join(DATA_DIR, "socfb-Stanford3.zip"))
    name = [f for f in z.namelist() if f.endswith(".mtx")][0]
    with z.open(name) as f:
        lines = [l for l in f.read().decode().splitlines() if not l.startswith("%")]
    n = int(lines[0].split()[0])
    e = np.array([l.split()[:2] for l in lines[1:]], dtype=np.int64) - 1
    return largest_component(_from_edges(n, e[:, 0], e[:, 1])), None


def load_egofb():
    with gzip.open(os.path.join(DATA_DIR, "facebook_combined.txt.gz"), "rt") as f:
        e = np.array([l.split() for l in f if l.strip()], dtype=np.int64)
    n = e.max() + 1
    return largest_component(_from_edges(n, e[:, 0], e[:, 1])), None


GENERATORS = {"er": gen_er, "sbm": gen_sbm, "ba": gen_ba, "ws": gen_ws}
REAL = {"stanford3": load_stanford3, "egofb": load_egofb}
_cache = {}


def thin(A, q, seed=12345):
    """Keep each undirected edge with probability q (fixed seed: a fixed graph with controllable degree)."""
    U = sp.triu(A, 1).tocoo()
    keep = np.random.default_rng(seed).random(len(U.row)) < q
    return largest_component(_from_edges(A.shape[0], U.row[keep], U.col[keep]))


def perturb_edges(A, q, rng):
    """The graph the analyst observes: a fraction q of the true edges is dropped and the same number of uniformly random
    non-self pairs is added (degrees stay roughly equal; an isolated unit gets one random edge so exposures are defined)."""
    if q <= 0:
        return A
    n = A.shape[0]
    U = sp.triu(A, 1).tocoo()
    m = len(U.row)
    k = int(round(q * m))
    keep = np.ones(m, bool)
    keep[rng.choice(m, k, replace=False)] = False
    u = np.concatenate([U.row[keep], rng.integers(0, n, k)])
    v = np.concatenate([U.col[keep], rng.integers(0, n, k)])
    B = _from_edges(n, u, v)
    iso = np.where(np.asarray(B.sum(1)).ravel() == 0)[0]
    if len(iso):
        j = (iso + 1 + rng.integers(0, n - 1, len(iso))) % n
        B = _from_edges(n, np.concatenate([*B.nonzero()[:1], iso]), np.concatenate([*B.nonzero()[1:], j]))
    return B


def make_graph(kind, n=2000, d=20, rng=None, q=1.0, **kw):
    """Returns (A, blocks_or_None). Real graphs are cached (fixed across replicates); q < 1 thins their edges."""
    if kind in REAL:
        if (kind, q) not in _cache:
            if kind not in _cache:
                _cache[kind] = REAL[kind]()
            A, b = _cache[kind]
            _cache[(kind, q)] = (A, b) if q >= 1 else (thin(A, q), None)
        return _cache[(kind, q)]
    return GENERATORS[kind](n, d, rng, **kw)


def is_fixed(kind):
    return kind in REAL
