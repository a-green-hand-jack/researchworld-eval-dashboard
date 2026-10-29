"""Synthetic connected graph families with at most 30 vertices."""
import networkx as nx
import numpy as np


def connected_gnp(n, p, rng):
    while True:
        g = nx.gnp_random_graph(n, p, seed=int(rng.integers(2**31)))
        if nx.is_connected(g):
            return g


def make_graphs(seed=0):
    """Yield (family, name, graph) tuples. Deterministic given seed."""
    rng = np.random.default_rng(seed)
    out = []
    for n in range(3, 31):
        out.append(("path", f"P{n}", nx.path_graph(n)))
        out.append(("cycle", f"C{n}", nx.cycle_graph(n)))
        out.append(("star", f"S{n}", nx.star_graph(n - 1)))
        if n <= 20:
            out.append(("complete", f"K{n}", nx.complete_graph(n)))
        if n >= 4:
            out.append(("wheel", f"W{n}", nx.wheel_graph(n)))
            out.append(("lollipop", f"LP{n}", nx.lollipop_graph(max(3, n // 2), n - max(3, n // 2))))
            out.append(("binary-tree", f"BT{n}", nx.balanced_tree(2, int(np.floor(np.log2(n))))))
            k = n // 3
            if k >= 3 and n - 2 * k >= 0:
                out.append(("barbell", f"BB{n}", nx.barbell_graph(k, n - 2 * k)))
        for a in range(2, n // 2 + 1):
            if a * (n - a) <= 240 and a <= n - a:
                out.append(("bipartite", f"K{a},{n-a}", nx.complete_bipartite_graph(a, n - a)))
        for r in range(2, n):
            if r * r > n:
                break
            c = n // r
            if r <= c and r * c == n:
                out.append(("grid", f"G{r}x{c}", nx.grid_2d_graph(r, c)))
    # Random families: several seeds per size.
    for n in range(4, 31, 2):
        for s in range(6):
            out.append(("random-tree", f"T{n}_{s}", nx.random_labeled_tree(n, seed=int(rng.integers(2**31)))))
            p = float(rng.uniform(0.15, 0.6))
            out.append(("G(n,p)", f"E{n}_{s}", connected_gnp(n, p, rng)))
            if n % 2 == 0:
                out.append(("3-regular", f"R3_{n}_{s}", nx.random_regular_graph(3, n, seed=int(rng.integers(2**31)))))
            out.append(("small-world", f"WS{n}_{s}", nx.connected_watts_strogatz_graph(n, 4, 0.2, seed=int(rng.integers(2**31)))))
            out.append(("scale-free", f"BA{n}_{s}", nx.barabasi_albert_graph(n, 2, seed=int(rng.integers(2**31)))))
    out = [(f, nm, nx.convert_node_labels_to_integers(g)) for f, nm, g in out]
    out = [t for t in out if t[2].number_of_nodes() <= 30 and nx.is_connected(t[2]) and t[2].number_of_nodes() >= 3]
    return out
