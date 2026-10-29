"""Monte Carlo + exact cover times of simple random walks on small connected graphs.

Outputs results.csv with per-graph statistics: n, m, max degree, diameter,
MC estimate of the (worst-start) expected cover time with standard error,
exact value for n <= 10 (validation), and the classic bound 2m(n-1).
Run: python3 cover_experiment.py --seed 0 --R 1000
"""
import argparse
import csv
import itertools
from collections import deque

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


# ---------------- graph generators (adjacency as list of sets) ----------------
def path(n):
    E = [(i, i + 1) for i in range(n - 1)]
    return n, E


def cycle(n):
    E = [(i, (i + 1) % n) for i in range(n)]
    return n, E


def star(n):
    return n, [(0, i) for i in range(1, n)]


def complete(n):
    return n, list(itertools.combinations(range(n), 2))


def grid(n):
    r = max(1, int(np.floor(np.sqrt(n))))
    c = int(np.ceil(n / r))
    E = []
    idx = lambda i, j: i * c + j
    for i in range(r):
        for j in range(c):
            if idx(i, j) >= n:
                continue
            if j + 1 < c and idx(i, j + 1) < n:
                E.append((idx(i, j), idx(i, j + 1)))
            if i + 1 < r and idx(i + 1, j) < n:
                E.append((idx(i, j), idx(i + 1, j)))
    return n, E


def lollipop(n):
    k = max(3, n // 2)  # clique of size k, path of length n-k attached
    E = list(itertools.combinations(range(k), 2))
    E += [(k - 1 + i, k + i) for i in range(n - k)]
    return n, E


def binary_tree(n):
    return n, [((i - 1) // 2, i) for i in range(1, n)]


def random_tree(n, rng):
    E = []
    for i in range(1, n):
        E.append((int(rng.integers(0, i)), i))  # random recursive tree
    return n, E


def gnp_connected(n, rng):
    p = min(1.0, 2.0 * np.log(n) / n + 0.05)
    while True:
        E = [(i, j) for i, j in itertools.combinations(range(n), 2) if rng.random() < p]
        if is_connected(n, E):
            return n, E


def sparse_connected(n, rng):
    """Random tree plus a few extra random edges (sparse, cycle-rich)."""
    _, E = random_tree(n, rng)
    S = set(tuple(sorted(e)) for e in E)
    extra = max(1, n // 4)
    while extra > 0:
        i, j = sorted(rng.choice(n, 2, replace=False))
        if (i, j) not in S:
            S.add((i, j))
            extra -= 1
    return n, list(S)


def barbell(n):
    k = max(3, n // 2)
    E = list(itertools.combinations(range(k), 2))
    E += list(itertools.combinations(range(n - k, n), 2))
    E += [(k - 1, n - k)]
    return n, E


DET_FAMILIES = {
    "path": path, "cycle": cycle, "star": star, "complete": complete,
    "grid": grid, "lollipop": lollipop, "barbell": barbell, "binary_tree": binary_tree,
}
RAND_FAMILIES = {"random_tree": random_tree, "gnp": gnp_connected, "sparse_random": sparse_connected}


def is_connected(n, E):
    adj = [[] for _ in range(n)]
    for i, j in E:
        adj[i].append(j)
        adj[j].append(i)
    seen = {0}
    q = deque([0])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                q.append(v)
    return len(seen) == n


def adjacency(n, E):
    adj = [set() for _ in range(n)]
    for i, j in E:
        if i != j:
            adj[i].add(j)
            adj[j].add(i)
    return adj


def stats(n, adj):
    m = sum(len(a) for a in adj) // 2
    dmax = max(len(a) for a in adj)
    # diameter via BFS from every vertex (n <= 30)
    D = 0
    for s in range(n):
        dist = [-1] * n
        dist[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if dist[v] < 0:
                    dist[v] = dist[u] + 1
                    q.append(v)
        D = max(D, max(dist))
    return m, dmax, D


# ---------------- estimators ----------------
def mc_cover_from(nbr, deg, n, start, R, rng):
    """Vectorised simulation of R independent walks from `start` until all vertices visited."""
    pos = np.full(R, start, dtype=np.int64)
    vis = np.zeros((R, n), dtype=bool)
    vis[:, start] = True
    cnt = np.ones(R, dtype=np.int64)
    T = np.zeros(R, dtype=np.float64)
    active = np.arange(R)
    steps = 0
    while active.size:
        steps += 1
        p = pos[active]
        r = (rng.random(active.size) * deg[p]).astype(np.int64)
        q = nbr[p, r]
        pos[active] = q
        newly = ~vis[active, q]
        cnt[active] += newly
        vis[active, q] = True
        fin = cnt[active] == n
        T[active[fin]] = steps
        active = active[~fin]
    return T


def mc_cover(n, adj, R, rng):
    deg = np.array([len(a) for a in adj], dtype=np.int64)
    D = deg.max()
    nbr = np.zeros((n, D), dtype=np.int64)
    for v in range(n):
        nbr[v, : len(adj[v])] = sorted(adj[v])
    if n <= 8:
        starts = list(range(n))
    else:
        # candidate starts: endpoints of a double-sweep diameter path, max-degree vertex, one random
        def bfs(s):
            dist = [-1] * n
            dist[s] = 0
            q = deque([s])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if dist[v] < 0:
                        dist[v] = dist[u] + 1
                        q.append(v)
            return dist
        d0 = bfs(0)
        a = int(np.argmax(d0))
        da = bfs(a)
        b = int(np.argmax(da))
        starts = sorted({a, b, int(np.argmax(deg)), int(rng.integers(n))})
    best = None
    for s in starts:
        T = mc_cover_from(nbr, deg, n, s, R, rng)
        mean, se = T.mean(), T.std(ddof=1) / np.sqrt(R)
        if best is None or mean > best[0]:
            best = (mean, se, s)
    return best  # (mean, se, argmax start)


def exact_cover_max(n, adj):
    """Exact worst-start expected cover time via linear system over states (v, S), v in S."""
    full = (1 << n) - 1
    idx = {}
    states = []
    for S in range(1, full):
        for v in range(n):
            if S >> v & 1:
                idx[(v, S)] = len(states)
                states.append((v, S))
    N = len(states)
    rows, cols, vals = [], [], []
    b = np.ones(N)
    for k, (v, S) in enumerate(states):
        rows.append(k); cols.append(k); vals.append(1.0)
        d = len(adj[v])
        for u in adj[v]:
            S2 = S | (1 << u)
            if S2 == full:
                continue  # absorbing, zero remaining cost
            rows.append(k); cols.append(idx[(u, S2)]); vals.append(-1.0 / d)
    A = sp.csr_matrix((vals, (rows, cols)), shape=(N, N))
    E = spla.spsolve(A.tocsc(), b)
    return max(E[idx[(s, 1 << s)]] for s in range(n))


# ---------------- main ----------------
def build_instances(seed):
    rng = np.random.default_rng(seed)
    sizes = [4, 6, 8, 10, 12, 16, 20, 24, 30]
    insts = []
    for n in sizes:
        for name, f in DET_FAMILIES.items():
            insts.append((name, n, 0, f(n)))
        for name, f in RAND_FAMILIES.items():
            reps = 4 if n >= 8 else 2
            for r in range(reps):
                nn, E = f(n, rng)
                insts.append((name, n, r, (nn, E)))
    return insts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--R", type=int, default=1000)
    ap.add_argument("--out", default="results.csv")
    ap.add_argument("--exact_max_n", type=int, default=10)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed + 1000)
    insts = build_instances(args.seed)
    rows = []
    for k, (fam, n, rep, (nn, E)) in enumerate(insts):
        assert nn == n and is_connected(n, E), (fam, n, rep)
        adj = adjacency(n, E)
        m, dmax, D = stats(n, adj)
        mean, se, s = mc_cover(n, adj, args.R, rng)
        exact = exact_cover_max(n, adj) if n <= args.exact_max_n else float("nan")
        rows.append(dict(id=k, family=fam, n=n, rep=rep, m=m, dmax=dmax, diam=D,
                         cover_mc=mean, cover_se=se, argmax_start=s,
                         cover_exact=exact, bound_2m_nm1=2 * m * (n - 1)))
        print(k, fam, n, rep, m, round(mean, 1), round(se, 1), exact, flush=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", args.out, len(rows), "graphs")


if __name__ == "__main__":
    main()
