"""Monte Carlo cover-time estimation for small connected graphs (n <= 30).

Cover time here = expected number of steps for a simple random walk, started at
a uniformly random vertex, to have visited every vertex.

Usage:  python cover.py --walks 2000 --seed 0 --out ../results/cover.csv
"""
import argparse
import csv
import math
import time

import networkx as nx
import numpy as np


def make_graphs(seed=0):
    """Return list of (family, name, graph) for connected graphs with 6 <= n <= 30."""
    rng = np.random.default_rng(seed)
    out = []

    def add(fam, name, G):
        G = nx.convert_node_labels_to_integers(G)
        if G.number_of_nodes() >= 6 and G.number_of_nodes() <= 30 and nx.is_connected(G):
            out.append((fam, name, G))

    for n in [6, 10, 14, 18, 22, 26, 30]:
        add("path", f"P{n}", nx.path_graph(n))
        add("cycle", f"C{n}", nx.cycle_graph(n))
        add("star", f"S{n}", nx.star_graph(n - 1))
        add("complete", f"K{n}", nx.complete_graph(n))
        add("wheel", f"W{n}", nx.wheel_graph(n))
        # heap-shaped binary tree: first n nodes of a complete binary tree (connected)
        add("binary_tree", f"BT{n}", nx.balanced_tree(2, 5).subgraph(range(n)).copy())
        for k in [3, 4]:
            if n * k % 2 == 0:
                add(f"regular{k}", f"R{k}_{n}", nx.random_regular_graph(k, n, seed=int(rng.integers(1 << 30))))
        # lollipop / barbell: clique + path, two cliques + path
        c = max(3, n // 3)
        add("lollipop", f"LP{n}", nx.lollipop_graph(c, n - c))
        b = max(3, (n - 2) // 3)
        add("barbell", f"BB{n}", nx.barbell_graph(b, n - 2 * b))
        # 2D grids with r*c close to n
        r = int(math.sqrt(n))
        while n % r and r > 1:
            r -= 1
        if r > 1:
            add("grid", f"G{r}x{n // r}", nx.grid_2d_graph(r, n // r))
        # random trees (3 seeds each)
        for s in range(3):
            add("random_tree", f"T{n}_{s}", nx.random_labeled_tree(n, seed=int(rng.integers(1 << 30))))
        # Erdos-Renyi, resampled until connected (3 densities x 2 seeds)
        for p in [0.1, 0.2, 0.4]:
            for s in range(2):
                for _ in range(1000):
                    G = nx.gnp_random_graph(n, p, seed=int(rng.integers(1 << 30)))
                    if nx.is_connected(G):
                        break
                add(f"gnp_p{p}", f"E{n}_{p}_{s}", G)
    return out


def estimate_cover(G, walks, rng):
    """Vectorized simulation of `walks` independent walks; uniform random start.

    Returns numpy array of cover times (one per walk)."""
    n = G.number_of_nodes()
    deg = np.array([G.degree(v) for v in range(n)])
    maxd = deg.max()
    nbr = np.zeros((n, maxd), dtype=np.int64)
    for v in range(n):
        nbr[v, : deg[v]] = sorted(G.neighbors(v))
    pos = rng.integers(0, n, size=walks)
    visited = np.zeros((walks, n), dtype=bool)
    visited[np.arange(walks), pos] = True
    count = np.ones(walks, dtype=np.int64)
    cover = np.full(walks, -1, dtype=np.int64)
    active = np.arange(walks)
    t = 0
    while active.size:
        t += 1
        p = pos[active]
        choice = (rng.random(active.size) * deg[p]).astype(np.int64)
        q = nbr[p, choice]
        pos[active] = q
        new = ~visited[active, q]
        visited[active[new], q[new]] = True
        count[active] += new
        done = count[active] == n
        cover[active[done]] = t
        active = active[~done]
    return cover


def graph_stats(G):
    n = G.number_of_nodes()
    m = G.number_of_edges()
    degs = np.array([d for _, d in G.degree()])
    return dict(n=n, m=m, avg_deg=degs.mean(), max_deg=degs.max(),
                diam=nx.diameter(G), min_deg=degs.min())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--walks", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="../results/cover.csv")
    args = ap.parse_args()

    graphs = make_graphs(seed=args.seed)
    rng = np.random.default_rng(args.seed + 1)
    rows = []
    t0 = time.time()
    for fam, name, G in graphs:
        s = graph_stats(G)
        c = estimate_cover(G, args.walks, rng).astype(float)
        mean = c.mean()
        se = c.std(ddof=1) / math.sqrt(len(c))
        rows.append(dict(family=fam, name=name, **s, cover_mean=mean, cover_se=se,
                         cover_sd=c.std(ddof=1), walks=args.walks,
                         bound_2m_n1=2 * s["m"] * (s["n"] - 1)))
        print(f"{name:14s} n={s['n']:2d} m={s['m']:3d} C~{mean:9.1f} +- {se:6.1f}", flush=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} graphs in {time.time() - t0:.1f}s -> {args.out}")


if __name__ == "__main__":
    main()
