"""Graph construction, hashes and reproducible BFS cluster partition."""
import hashlib
from pathlib import Path
import gzip
import networkx as nx
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from .core import Graph


def bfs_clusters(adjacency, target=32, seed=97):
    """Partition into connected BFS pieces of at most target nodes.

    Partition is made before assignment, with no outcome information. Small
    leftovers remain separate rather than being silently discarded.
    """
    rng = np.random.default_rng(seed)
    n = adjacency.shape[0]
    labels = np.full(n, -1, dtype=int)
    label = 0
    for start in rng.permutation(n):
        if labels[start] >= 0:
            continue
        labels[start] = label
        queue = [start]
        reached = 1
        head = 0
        while head < len(queue) and reached < target:
            i = queue[head]
            head += 1
            neighbors = adjacency.indices[adjacency.indptr[i]:adjacency.indptr[i+1]]
            for j in rng.permutation(neighbors):
                if labels[j] < 0:
                    labels[j] = label
                    queue.append(j)
                    reached += 1
                    if reached == target:
                        break
        label += 1
    return labels


def from_networkx(name, g, seed=1, cluster_size=32):
    a = nx.to_scipy_sparse_array(g, format="csr", dtype=float)
    a.setdiag(0)
    a.eliminate_zeros()
    x = np.random.default_rng(seed+123456).normal(size=a.shape[0])
    return Graph(name, sparse.csr_matrix(a), x, bfs_clusters(a, cluster_size, seed+97))


def synthetic(kind, n, degree, seed=1, cluster_size=32, mixing=.15):
    if kind == "regular":
        g = nx.random_regular_graph(degree, n, seed=seed)
    elif kind == "er":
        g = nx.fast_gnp_random_graph(n, degree/(n-1), seed=seed)
    elif kind == "ba":
        g = nx.barabasi_albert_graph(n, max(1, degree//2), seed=seed)
    elif kind == "sbm":
        blocks = 8
        sizes = [n//blocks]*blocks
        sizes[-1] += n-sum(sizes)
        outside = degree*mixing/(n-n/blocks)
        inside = degree*(1-mixing)/(n/blocks-1)
        p = np.full((blocks, blocks), outside)
        np.fill_diagonal(p, inside)
        g = nx.stochastic_block_model(sizes, p, seed=seed, sparse=True)
    else:
        raise ValueError(kind)
    return from_networkx(f"{kind}_n{n}_d{degree}_g{seed}" + (f"_mix{mixing}" if kind=="sbm" else ""), g, seed, cluster_size)


def public_facebook(path, seed=1, cluster_size=32):
    expected="125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7"
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual!=expected:
        raise ValueError(f"Public graph input hash differs from frozen snapshot: {actual}")
    with gzip.open(path, "rt") as f:
        edges = np.loadtxt(f, dtype=int)
    n = int(edges.max()+1)
    a = sparse.coo_matrix((np.ones(2*len(edges)), (np.r_[edges[:,0], edges[:,1]],
                                                np.r_[edges[:,1], edges[:,0]])), shape=(n,n)).tocsr()
    a.data[:] = 1
    g = nx.from_scipy_sparse_array(a)
    return from_networkx("snap_facebook", g, seed, cluster_size)


def graph_summary(graph):
    a = graph.adjacency
    degree = graph.degree
    cluster_sizes = np.bincount(graph.clusters)
    row, col = a.nonzero()
    return dict(name=graph.name, n=graph.n, edges=int(a.nnz//2),
                mean_degree=float(degree.mean()), degree_sd=float(degree.std()),
                degree_q10=float(np.quantile(degree,.1)), degree_median=float(np.median(degree)),
                degree_q90=float(np.quantile(degree,.9)),
                components=int(connected_components(a,directed=False,return_labels=False)),
                min_degree=int(degree.min()),
                max_degree=int(degree.max()), mean_inverse_degree=float(np.mean(1/np.maximum(degree,1))),
                isolates=int(np.sum(degree==0)), clusters=len(cluster_sizes),
                median_cluster_size=float(np.median(cluster_sizes)),
                within_cluster_edge_fraction=float(np.mean(graph.clusters[row]==graph.clusters[col])),
                adjacency_sha256=hashlib.sha256(a.indptr.tobytes()+a.indices.tobytes()+a.data.tobytes()).hexdigest())
