"""Monte Carlo cover-time estimates for small connected graphs (n <= 30).

Usage: python run_experiments.py --out ../results/cover.csv --walks 400 --seed 1
For each graph we simulate R independent simple random walks started at
vertex 0 and record the first time all vertices are visited.
"""
import argparse, csv, time
import numpy as np
import networkx as nx


def families(rng):
    """Yield (family, graph). Sizes n in 6..30, two random instances per random family."""
    for n in range(6, 31, 2):
        yield "path", nx.path_graph(n)
        yield "cycle", nx.cycle_graph(n)
        yield "star", nx.star_graph(n - 1)
        yield "complete", nx.complete_graph(n)
        yield "wheel", nx.wheel_graph(n)
        yield "binary_tree", nx.balanced_tree(2, int(np.log2(n + 1)) - 1)  # 2^k-1 nodes, see n filter
        yield "lollipop", nx.lollipop_graph(max(3, n // 2), n - n // 2)
        r = int(np.sqrt(n))
        yield "grid", nx.grid_2d_graph(r, n // r)
        for rep in range(2):
            s = int(rng.integers(1 << 30))
            yield "random_tree", nx.random_labeled_tree(n, seed=s) if hasattr(nx, "random_labeled_tree") else nx.random_tree(n, seed=s)
            p = float(rng.uniform(0.15, 0.6))
            g = nx.gnp_random_graph(n, p, seed=s)
            if nx.is_connected(g):
                yield "gnp", g
            yield "random_3reg", nx.random_regular_graph(3, n if n % 2 == 0 else n + 1, seed=s)


def simulate(g, walks, rng, max_steps=2_000_000):
    g = nx.convert_node_labels_to_integers(g, ordering="sorted")
    n = g.number_of_nodes()
    nbrs = [np.array(sorted(g.neighbors(v)), dtype=np.int64) for v in range(n)]
    deg = np.array([len(a) for a in nbrs], dtype=np.int64)
    ptr = np.concatenate([[0], np.cumsum(deg)])
    adj = np.concatenate(nbrs)
    pos = np.zeros(walks, dtype=np.int64)
    seen = np.zeros((walks, n), dtype=bool)
    seen[:, 0] = True
    count = np.ones(walks, dtype=np.int64)
    times = np.zeros(walks, dtype=np.int64)
    active = np.arange(walks)
    t = 0
    while active.size and t < max_steps:
        t += 1
        p = pos[active]
        u = rng.random(active.size)
        nxt = adj[ptr[p] + (u * deg[p]).astype(np.int64)]
        pos[active] = nxt
        new = ~seen[active, nxt]
        seen[active[new], nxt[new]] = True
        count[active[new]] += 1
        done = count[active] == n
        times[active[done]] = t
        active = active[~done]
    if active.size:
        raise RuntimeError("walk did not cover within max_steps")
    m = g.number_of_edges()
    diam = nx.diameter(g)
    return dict(n=n, m=m, avg_deg=2 * m / n, max_deg=int(deg.max()), diam=diam,
                cover_mean=times.mean(), cover_sd=times.std(ddof=1),
                cover_se=times.std(ddof=1) / np.sqrt(walks))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--walks", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    rows, t0 = [], time.time()
    for fam, g in families(rng):
        n = g.number_of_nodes()
        if n > 30 or n < 4 or not nx.is_connected(g) or g.number_of_edges() == 0:
            continue
        r = simulate(g, a.walks, rng)
        r["family"] = fam
        rows.append(r)
    fields = ["family", "n", "m", "avg_deg", "max_deg", "diam", "cover_mean", "cover_sd", "cover_se"]
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(r[k], 4) if isinstance(r[k], float) else r[k]) for k in fields})
    print(f"wrote {len(rows)} graphs to {a.out} in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
