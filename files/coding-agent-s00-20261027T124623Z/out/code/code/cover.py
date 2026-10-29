"""Graph families, Monte-Carlo and exact cover-time computation, hitting times."""
import numpy as np
import networkx as nx


def relabel(G):
    return nx.convert_node_labels_to_integers(G, ordering="sorted")


def make_graphs(seed=0, per_family=30):
    """Random connected graphs with 4 <= n <= 30 from 12 families."""
    rng = np.random.default_rng(seed)
    out = []

    def add(fam, G):
        if G is None:
            return
        G = relabel(G)
        n = G.number_of_nodes()
        if 4 <= n <= 30 and nx.is_connected(G):
            out.append((fam, G))

    def tryit(fam, f):
        try:
            add(fam, f())
        except Exception:
            pass

    for _ in range(per_family):
        n = int(rng.integers(4, 31))
        tryit("path", lambda: nx.path_graph(n))
        tryit("cycle", lambda: nx.cycle_graph(n))
        tryit("star", lambda: nx.star_graph(n - 1))
        tryit("complete", lambda: nx.complete_graph(min(n, 20)))
        tryit("wheel", lambda: nx.wheel_graph(n))
        a = int(rng.integers(2, n - 1))
        tryit("bipartite", lambda: nx.complete_bipartite_graph(a, n - a))
        k = int(rng.integers(3, n))
        tryit("lollipop", lambda: nx.lollipop_graph(k, n - k))
        if n >= 6:
            k = int(rng.integers(3, n // 2 + 1))
            tryit("barbell", lambda: nx.barbell_graph(k, n - 2 * k))
        tryit("random_tree", lambda: nx.from_prufer_sequence(list(rng.integers(0, n, n - 2))))
        r = int(rng.integers(2, 6))
        c = int(rng.integers(2, 30 // r + 1))
        tryit("grid", lambda: nx.grid_2d_graph(r, c))
        tryit("hypercube", lambda: nx.hypercube_graph(int(rng.integers(2, 5))))
        p = rng.uniform(0.1, 0.5)
        tryit("gnp", lambda: nx.gnp_random_graph(n, p, seed=int(rng.integers(1 << 30))))
        d = int(rng.integers(3, 5))
        if (n * d) % 2 == 0:
            tryit("regular", lambda: nx.random_regular_graph(d, n, seed=int(rng.integers(1 << 30))))
    return out


def adjacency_arrays(G):
    n = G.number_of_nodes()
    deg = np.array([G.degree(v) for v in range(n)])
    nbr = np.zeros((n, deg.max()), dtype=np.int64)
    for v in range(n):
        nbr[v, : deg[v]] = sorted(G.neighbors(v))
    return nbr, deg


def mc_cover_avg(G, walks_per_start, rng):
    """Simulate SRW from every start; return per-walk cover times (start-balanced)."""
    n = G.number_of_nodes()
    nbr, deg = adjacency_arrays(G)
    starts = np.repeat(np.arange(n), walks_per_start)
    R = starts.size
    pos = starts.copy()
    visited = np.zeros((R, n), dtype=bool)
    visited[np.arange(R), pos] = True
    cnt = np.ones(R, dtype=np.int64)
    steps = np.zeros(R, dtype=np.int64)
    active = np.arange(R)
    while active.size:
        p = pos[active]
        j = np.floor(rng.random(active.size) * deg[p]).astype(np.int64)
        q = nbr[p, j]
        pos[active] = q
        steps[active] += 1
        new = ~visited[active, q]
        visited[active, q] = True
        cnt[active] += new
        active = active[cnt[active] < n]
    return steps


def exact_cover_avg(G):
    """Exact start-averaged cover time via DP over visited sets (use n <= 9)."""
    n = G.number_of_nodes()
    nbrs = [sorted(G.neighbors(v)) for v in range(n)]
    full = (1 << n) - 1
    f = {}  # f[S] = array x[v] = expected remaining steps at v with visited set S
    for S in sorted(range(1 << n), key=lambda s: -bin(s).count("1")):
        if S == full:
            f[S] = np.zeros(n)
            continue
        if S == 0:
            continue
        verts = [v for v in range(n) if S >> v & 1]
        idx = {v: i for i, v in enumerate(verts)}
        A = np.eye(len(verts))
        b = np.ones(len(verts))
        for v in verts:
            d = len(nbrs[v])
            for u in nbrs[v]:
                if S >> u & 1:
                    A[idx[v], idx[u]] -= 1.0 / d
                else:
                    S2 = S | (1 << u)
                    b[idx[v]] += f[S2][u] / d
        x = np.linalg.solve(A, b)
        val = np.zeros(n)
        for v in verts:
            val[v] = x[idx[v]]
        f[S] = val
    return float(np.mean([f[1 << v][v] for v in range(n)]))


def hitting_times(G):
    """H[u, t] = expected steps from u to first hit t (SRW)."""
    n = G.number_of_nodes()
    nbr, deg = adjacency_arrays(G)
    P = np.zeros((n, n))
    for v in range(n):
        for u in nbr[v, : deg[v]]:
            P[v, u] += 1.0 / deg[v]
    H = np.zeros((n, n))
    for t in range(n):
        keep = [u for u in range(n) if u != t]
        A = np.eye(len(keep)) - P[np.ix_(keep, keep)]
        h = np.linalg.solve(A, np.ones(len(keep)))
        H[keep, t] = h
    return H


def matthews_upper(G):
    """Matthews' bound: C <= h_max * H_{n-1}."""
    n = G.number_of_nodes()
    H = hitting_times(G)
    hmax = H.max()
    Hn1 = sum(1.0 / k for k in range(1, n))
    return float(hmax * Hn1)
