"""Graph construction utilities. All graphs are returned as symmetric scipy CSR
adjacency matrices (0/1, no self loops) restricted to the largest connected component."""
import gzip
import numpy as np
import scipy.sparse as sp
import scipy.sparse.csgraph as csg
import networkx as nx

DATA = "/work/data"


def _finish(A):
    A = sp.csr_matrix(A)
    A = ((A + A.T) > 0).astype(np.float64)
    A.setdiag(0)
    A.eliminate_zeros()
    ncomp, lab = csg.connected_components(A, directed=False)
    big = np.argmax(np.bincount(lab))
    keep = np.where(lab == big)[0]
    A = A[keep][:, keep].tocsr()
    return A


def nx_to_csr(G):
    return _finish(nx.to_scipy_sparse_array(G, format="csr"))


def load_stanford3():
    rows, cols = [], []
    with open(f"{DATA}/stanford3_raw/socfb-Stanford3.mtx") as f:
        for line in f:
            if line.startswith("%"):
                continue
            a = line.split()
            if len(a) == 3:  # header "n n nnz"
                n = int(a[0])
                continue
            rows.append(int(a[0]) - 1)
            cols.append(int(a[1]) - 1)
    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    return _finish(A)


def load_egofb():
    e = np.loadtxt(gzip.open(f"{DATA}/ego_raw/facebook_combined.txt.gz"), dtype=int)
    n = e.max() + 1
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    return _finish(A)


def er(n, d, rng):
    G = nx.fast_gnp_random_graph(n, d / (n - 1), seed=int(rng.integers(2**31)))
    return nx_to_csr(G)


def regular(n, d, rng):
    G = nx.random_regular_graph(d, n, seed=int(rng.integers(2**31)))
    return nx_to_csr(G)


def sbm(n, d, K, ratio, rng):
    """K equal blocks; expected degree d; p_in/p_out = ratio."""
    m = n // K
    # d = (m-1) p_in + (n-m) p_out, p_in = ratio p_out
    p_out = d / ((m - 1) * ratio + (n - m))
    p_in = min(1.0, ratio * p_out)
    sizes = [m] * K
    P = np.full((K, K), p_out)
    np.fill_diagonal(P, p_in)
    G = nx.stochastic_block_model(sizes, P.tolist(), seed=int(rng.integers(2**31)))
    return nx_to_csr(G)


def ba(n, m, rng):
    return nx_to_csr(nx.barabasi_albert_graph(n, m, seed=int(rng.integers(2**31))))


def ws(n, d, beta, rng):
    return nx_to_csr(nx.watts_strogatz_graph(n, d, beta, seed=int(rng.integers(2**31))))


def louvain_clusters(A, rng, resolution=1.0):
    G = nx.from_scipy_sparse_array(A)
    comms = nx.community.louvain_communities(G, resolution=resolution, seed=int(rng.integers(2**31)))
    lab = np.zeros(A.shape[0], dtype=int)
    for k, c in enumerate(comms):
        lab[list(c)] = k
    return lab


def stats(A):
    n = A.shape[0]
    deg = np.asarray(A.sum(1)).ravel()
    G = nx.from_scipy_sparse_array(A)
    return dict(n=n, m=int(A.nnz // 2), mean_deg=deg.mean(), med_deg=float(np.median(deg)),
                max_deg=int(deg.max()), min_deg=int(deg.min()),
                cc=nx.average_clustering(G))


if __name__ == "__main__":
    for name, f in [("Stanford3", load_stanford3), ("egoFB", load_egofb)]:
        A = f()
        print(name, stats(A))


import os, hashlib, json

CLUSTER_CACHE = "/work/results/cluster_cache"


def cluster_graph(A, K_target, seed=0, key=None):
    """Louvain clustering with the resolution tuned (log-bisection) so that the number of
    clusters is close to K_target.  Returns integer labels (n,).  Cached on disk if `key`."""
    if key is not None:
        os.makedirs(CLUSTER_CACHE, exist_ok=True)
        fn = f"{CLUSTER_CACHE}/{key}_K{K_target}_s{seed}.npy"
        if os.path.exists(fn):
            return np.load(fn)
    Gx = nx.from_scipy_sparse_array(A)
    lo, hi = np.log(0.05), np.log(60.0)
    best = None
    for it in range(9):
        mid = 0.5 * (lo + hi)
        comms = nx.community.louvain_communities(Gx, resolution=float(np.exp(mid)), seed=seed)
        k = len(comms)
        if best is None or abs(np.log(k / K_target)) < abs(np.log(best[0] / K_target)):
            best = (k, comms)
        if abs(np.log(k / K_target)) < 0.15:
            break
        if k < K_target:
            lo = mid
        else:
            hi = mid
    lab = np.zeros(A.shape[0], dtype=int)
    for j, c in enumerate(best[1]):
        lab[list(c)] = j
    if key is not None:
        np.save(fn, lab)
    return lab
