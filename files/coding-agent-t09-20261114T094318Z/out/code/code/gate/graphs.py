"""Graph loading, generation, and community partitions.

Public graphs are read from /work/data/raw (see README.md for provenance and
checksums). Every graph used in the paper is reduced to its largest connected
component (LCC) and cached as an .npz file in /work/data/processed.
"""
import gzip
import os
import zlib

import networkx as nx
import numpy as np

RAW = "/work/data/raw"
PROC = "/work/data/processed"


def _largest_cc(G):
    G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    return nx.convert_node_labels_to_integers(G, ordering="sorted")


def load_stanford3():
    """Facebook100 Stanford3 (Traud, Mucha & Porter 2012), Matrix Market pattern file."""
    G = nx.Graph()
    path = os.path.join(RAW, "stanford3", "extracted", "socfb-Stanford3.mtx")
    with open(path) as fh:
        header_seen = False
        for line in fh:
            if line.startswith("%"):
                continue
            if not header_seen:  # "rows cols nnz" size line
                header_seen = True
                continue
            i, j = line.split()[:2]
            if i != j:
                G.add_edge(int(i) - 1, int(j) - 1)  # Matrix Market is 1-indexed
    return _largest_cc(G)


def load_egofb():
    """SNAP ego-Facebook (McAuley & Leskovec 2012), merged edge list."""
    G = nx.Graph()
    path = os.path.join(RAW, "egofb", "facebook_combined.txt.gz")
    with gzip.open(path, "rt") as fh:
        for line in fh:
            u, v = line.split()
            if u != v:
                G.add_edge(int(u), int(v))
    return _largest_cc(G)


def make_ba(n=5000, m=3, seed=1):
    return _largest_cc(nx.barabasi_albert_graph(n, m, seed=seed))


def make_er(n, mean_deg, seed=1):
    """Erdos-Renyi graph with expected mean degree mean_deg, restricted to its LCC."""
    G = nx.fast_gnp_random_graph(n, mean_deg / (n - 1), seed=seed)
    return _largest_cc(G)


def louvain_partition(G, target_clusters, seed=0):
    """Louvain communities with the resolution chosen so that #communities >= target.

    The resolution grid is {1, 2, 4, ..., 32}; the first resolution whose partition
    has at least target_clusters communities is used (the last one otherwise).
    Returns (labels as np.int64 array, resolution, n_communities).
    """
    labels, res, k = None, None, None
    for r in [1, 2, 4, 8, 16, 32]:
        comms = nx.community.louvain_communities(G, resolution=r, seed=seed)
        labels = np.zeros(G.number_of_nodes(), dtype=np.int64)
        for c, nodes in enumerate(comms):
            labels[list(nodes)] = c
        res, k = r, len(comms)
        if k >= target_clusters:
            break
    return labels, res, k


def graph_to_arrays(G):
    E = np.array(list(G.edges()), dtype=np.int64)
    return E[:, 0], E[:, 1]


def build_and_cache(name, G, target_clusters):
    """Compute the Louvain partition and cache graph + partition for one graph."""
    path = os.path.join(PROC, f"{name}.npz")
    src, dst = graph_to_arrays(G)
    labels, res, k = louvain_partition(G, target_clusters)
    deg = np.bincount(np.concatenate([src, dst]), minlength=G.number_of_nodes())
    np.savez_compressed(path, src=src, dst=dst, n=G.number_of_nodes(), labels=labels,
                        resolution=res, n_clusters=k)
    return {
        "name": name, "n": G.number_of_nodes(), "m": G.number_of_edges(),
        "mean_deg": float(deg.mean()), "max_deg": int(deg.max()),
        "clustering": nx.average_clustering(G) if G.number_of_edges() < 3_000_000 else float("nan"),
        "n_clusters": int(k), "louvain_res": int(res),
        "mean_cluster_size": float(G.number_of_nodes() / k),
    }


def load_cached(name):
    """Return dict with CSR-ready edge arrays, node count, and cluster labels."""
    d = np.load(os.path.join(PROC, f"{name}.npz"))
    return {"src": d["src"], "dst": d["dst"], "n": int(d["n"]), "labels": d["labels"],
            "n_clusters": int(d["n_clusters"])}


def seed_from_name(name):
    return zlib.crc32(name.encode()) % (2**31)
