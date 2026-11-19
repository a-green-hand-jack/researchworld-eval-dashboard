"""Graph loading / generation and partitioning utilities."""
from __future__ import annotations

import gzip
import os
from functools import lru_cache

import networkx as nx
import numpy as np
import scipy.io
import scipy.sparse as sp

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(DATA, "cache")
os.makedirs(CACHE, exist_ok=True)


def _clean(A: sp.spmatrix) -> sp.csr_matrix:
    """Symmetrise, binarise, drop self loops."""
    A = sp.csr_matrix(A)
    A = A.maximum(A.T)
    A.setdiag(0)
    A.eliminate_zeros()
    A.data[:] = 1.0
    return A.tocsr()


def _lcc(A: sp.csr_matrix, labels=None):
    nc, comp = sp.csgraph.connected_components(A, directed=False)
    big = np.argmax(np.bincount(comp))
    keep = np.where(comp == big)[0]
    A2 = A[keep][:, keep].tocsr()
    return (A2, None if labels is None else labels[keep])


def _pairs_to_adj(n, i, j):
    A = sp.coo_matrix((np.ones(len(i)), (i, j)), shape=(n, n)).tocsr()
    return _clean(A)


def gen_er(n, d, rng):
    m = int(n * d / 2)
    i = rng.integers(0, n, size=m)
    j = rng.integers(0, n, size=m)
    return _pairs_to_adj(n, i, j), None


def gen_sbm(n, d, rng, K=100, mix=0.2):
    """Planted-partition SBM with K equal blocks; expected fraction `mix` of edges between blocks."""
    lab = np.repeat(np.arange(K), int(np.ceil(n / K)))[:n]
    size = n / K
    m_in = int(n * d * (1 - mix) / 2)
    m_out = int(n * d * mix / 2)
    # within-block edges: pick random node, then random node of same block
    i = rng.integers(0, n, size=m_in)
    off = rng.integers(0, int(size), size=m_in)
    j = np.minimum((i // int(np.ceil(size))) * int(np.ceil(size)) + off, n - 1)
    i2 = rng.integers(0, n, size=m_out)
    j2 = rng.integers(0, n, size=m_out)
    return _pairs_to_adj(n, np.r_[i, i2], np.r_[j, j2]), lab


def gen_ba(n, d, rng):
    g = nx.barabasi_albert_graph(n, max(1, d // 2), seed=int(rng.integers(2**31)))
    return _clean(nx.to_scipy_sparse_array(g)), None


def gen_ws(n, d, rng, beta=0.1):
    g = nx.watts_strogatz_graph(n, d, beta, seed=int(rng.integers(2**31)))
    return _clean(nx.to_scipy_sparse_array(g)), None


@lru_cache(maxsize=None)
def load_stanford3():
    A = scipy.io.mmread(os.path.join(DATA, "socfb-Stanford3.mtx"))
    return _lcc(_clean(A))[0]


@lru_cache(maxsize=None)
def load_egofb():
    with gzip.open(os.path.join(DATA, "facebook_combined.txt.gz"), "rt") as f:
        e = np.loadtxt(f, dtype=np.int64)
    n = e.max() + 1
    return _lcc(_pairs_to_adj(n, e[:, 0], e[:, 1]))[0]


def partition(A: sp.csr_matrix, K: int, seed: int, tag: str | None = None) -> np.ndarray:
    """Louvain partition with resolution raised until >= K communities (cached on disk if tag given)."""
    path = None if tag is None else os.path.join(CACHE, f"part_{tag}_K{K}_s{seed}.npy")
    if path and os.path.exists(path):
        return np.load(path)
    g = nx.from_scipy_sparse_array(A)
    lab = None
    for res in (1, 2, 4, 8, 16, 32):
        comms = nx.community.louvain_communities(g, resolution=res, seed=seed)
        if len(comms) >= K:
            break
    lab = np.zeros(A.shape[0], dtype=np.int64)
    for c, nodes in enumerate(comms):
        lab[list(nodes)] = c
    if path:
        np.save(path, lab)
    return lab


def get_graph(kind: str, n: int = 0, d: int = 0, seed: int = 0, K: int = 100, mix: float = 0.2,
              need_labels: bool = True):
    """Return (A, labels) with labels = cluster partition used for cluster designs / community effects.
    need_labels=False skips the (slow) Louvain partition for synthetic non-SBM graphs (labels then None)."""
    if kind == "stanford3":
        A = load_stanford3()
        return A, partition(A, K, seed=0, tag="stanford3")
    if kind == "egofb":
        A = load_egofb()
        return A, partition(A, min(K, 40), seed=0, tag="egofb")
    rng = np.random.default_rng([seed, 7919, n, d])
    if kind == "er":
        A, lab = gen_er(n, d, rng)
    elif kind == "sbm":
        A, lab = gen_sbm(n, d, rng, K=K, mix=mix)
    elif kind == "ba":
        A, lab = gen_ba(n, d, rng)
    elif kind == "ws":
        A, lab = gen_ws(n, d, rng)
    else:
        raise ValueError(kind)
    A, lab = _lcc(A, lab)
    if lab is None:
        if not need_labels:
            return A, None
        lab = partition(A, K, seed=seed, tag=f"{kind}_{n}_{d}_{seed}")
    else:
        _, lab = np.unique(lab, return_inverse=True)
    return A, lab.astype(np.int64)


def graph_stats(A, lab):
    deg = np.asarray(A.sum(1)).ravel()
    r, c = A.nonzero()
    within = float(np.mean(lab[r] == lab[c]))
    return dict(n=A.shape[0], m=int(A.nnz // 2), mean_deg=float(deg.mean()), harm_deg=float(1 / np.mean(1 / deg)),
                max_deg=int(deg.max()), n_clusters=int(lab.max() + 1), edge_within_cluster=within)
