"""Monte Carlo cover times of simple random walks on small connected graphs (n<=30).

Usage:  python3 code/cover.py --walks 1000 --seed 0 --out results/graphs.csv
Outputs one row per graph: family, name, n, m, max degree, diameter,
MC mean cover time (start vertex uniform over V), standard error, 95% CI.
Also computes exact expected cover times for graphs with n<=8 (validation).
"""
import argparse
import csv
import math
import os
from collections import deque

import numpy as np


# ---------------------------------------------------------------- graph utils
def make_adj(n, edges):
    adj = [set() for _ in range(n)]
    for u, v in edges:
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    return adj


def is_connected(adj):
    seen = {0}
    stack = [0]
    while stack:
        u = stack.pop()
        for w in adj[u]:
            if w not in seen:
                seen.add(w)
                stack.append(w)
    return len(seen) == len(adj)


def diameter(adj):
    n = len(adj)
    best = 0
    for s in range(n):
        dist = [-1] * n
        dist[s] = 0
        dq = deque([s])
        while dq:
            u = dq.popleft()
            for w in adj[u]:
                if dist[w] < 0:
                    dist[w] = dist[u] + 1
                    dq.append(w)
        best = max(best, max(dist))
    return best


def random_tree(n, rng):
    edges = []
    for v in range(1, n):
        edges.append((int(rng.integers(0, v)), v))
    return edges


def random_regular(n, d, rng):
    for _ in range(20000):
        stubs = np.repeat(np.arange(n), d)
        rng.shuffle(stubs)
        edges = set()
        ok = True
        for i in range(0, len(stubs), 2):
            u, v = int(stubs[i]), int(stubs[i + 1])
            e = (min(u, v), max(u, v))
            if u == v or e in edges:
                ok = False
                break
            edges.add(e)
        if ok:
            return list(edges)
    return None


def gnp_connected(n, p, rng):
    for _ in range(10000):
        edges = [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p]
        if is_connected(make_adj(n, edges)):
            return edges
    return None


def build_graphs(seed=0):
    """Return list of (family, name, adj) covering diverse structures with n<=30."""
    rng = np.random.default_rng(seed)
    out = []

    def add(fam, name, n, edges):
        if edges is None:
            return
        adj = make_adj(n, edges)
        if is_connected(adj) and n <= 30:
            out.append((fam, name, adj))

    for n in range(4, 31, 2):
        add("path", f"P{n}", n, [(i, i + 1) for i in range(n - 1)])
        add("cycle", f"C{n}", n, [(i, (i + 1) % n) for i in range(n)])
        add("star", f"S{n}", n, [(0, i) for i in range(1, n)])
        add("wheel", f"W{n}", n, [(0, i) for i in range(1, n)] + [(i, i % (n - 1) + 1) for i in range(1, n)])
        if n <= 20:
            add("complete", f"K{n}", n, [(i, j) for i in range(n) for j in range(i + 1, n)])
    for n in range(5, 31, 2):  # odd sizes for path/cycle/star too
        add("path", f"P{n}", n, [(i, i + 1) for i in range(n - 1)])
        add("star", f"S{n}", n, [(0, i) for i in range(1, n)])
    for a in range(2, 6):
        for b in range(a, 31 // a + 1):
            if 6 <= a * b <= 30:
                add("grid", f"G{a}x{b}", a * b,
                    [(r * b + c, r * b + c + 1) for r in range(a) for c in range(b - 1)] +
                    [(r * b + c, (r + 1) * b + c) for r in range(a - 1) for c in range(b)])
    for a in [2, 3, 5, 8]:
        for b in range(a + 2, 31 - a + 1, 4):
            add("bipartite", f"K{a},{b}", a + b,
                [(i, a + j) for i in range(a) for j in range(b)])
    for n in [10, 16, 22, 28, 30]:  # lollipop: clique K_k with pendant path
        for k in range(3, n - 2, 4):
            edges = [(i, j) for i in range(k) for j in range(i + 1, k)]
            edges += [(k - 1 + t, k + t) for t in range(n - k)]
            add("lollipop", f"L{k}_{n}", n, edges)
    for k in [3, 5, 7, 10]:  # barbell: two K_k joined by a path with L internal vertices
        for L in [0, 2, 5, 10]:
            n = 2 * k + L
            if n > 30:
                continue
            edges = [(i, j) for i in range(k) for j in range(i + 1, k)]
            edges += [(k + i, k + j) for i in range(k) for j in range(i + 1, k)]
            path = [k - 1] + list(range(2 * k, 2 * k + L)) + [k]
            edges += [(path[t], path[t + 1]) for t in range(len(path) - 1)]
            add("barbell", f"B{k}_{L}", n, edges)
    for n in range(6, 31, 4):
        for s in range(2):
            add("tree", f"T{n}_{s}", n, random_tree(n, rng))
    for n in [10, 16, 22, 30]:
        for d in [3, 4]:
            for s in range(2):
                if n * d % 2 == 0:
                    add(f"regular{d}", f"R{d}_{n}_{s}", n, random_regular(n, d, rng))
    for n in [10, 20, 30]:
        for p in [0.1, 0.2, 0.4, 0.7]:
            for s in range(2):
                add(f"gnp", f"E{n}_{p}_{s}", n, gnp_connected(n, p, rng))
    # special small graphs
    add("special", "Q3", 8, [(i, i ^ b) for i in range(8) for b in (1, 2, 4) if i < i ^ b])
    add("special", "Q4", 16, [(i, i ^ b) for i in range(16) for b in (1, 2, 4, 8) if i < i ^ b])
    pet = [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)] + \
          [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    add("special", "Petersen", 10, pet)
    return out


# ------------------------------------------------------------ simulation
def mc_cover(adj, R, rng):
    """Cover times (in steps) of R independent walks, start vertex uniform on V."""
    n = len(adj)
    deg = np.array([len(a) for a in adj], dtype=np.int64)
    nbr = np.zeros((n, deg.max()), dtype=np.int64)
    for i, a in enumerate(adj):
        nbr[i, :len(a)] = sorted(a)
    pos = rng.integers(0, n, size=R)
    vis = np.zeros((R, n), dtype=bool)
    vis[np.arange(R), pos] = True
    cnt = np.ones(R, dtype=np.int64)
    steps = np.zeros(R, dtype=np.int64)
    active = np.arange(R)
    t = 0
    while active.size > 0:
        p = pos[active]
        k = (rng.random(active.size) * deg[p]).astype(np.int64)
        newp = nbr[p, k]
        pos[active] = newp
        t += 1
        newly = ~vis[active, newp]
        vis[active[newly], newp[newly]] = True
        cnt[active[newly]] += 1
        done = cnt[active] == n
        steps[active[done]] = t
        active = active[~done]
    return steps


def exact_cover(adj):
    """Exact expected cover time from a uniform start, via linear system on (v, S) states."""
    n = len(adj)
    full = (1 << n) - 1
    states = {}
    for S in range(1 << n):
        if S == 0 or S == full:
            continue
        for v in range(n):
            if S >> v & 1:
                states[(v, S)] = len(states)
    N = len(states)
    A = np.eye(N)
    b = np.ones(N)
    for (v, S), idx in states.items():
        for w in adj[v]:
            T = S | (1 << w)
            if T == full:
                continue
            A[idx, states[(w, T)]] -= 1.0 / len(adj[v])
    E = np.linalg.solve(A, b)
    # start uniform over vertices, S = {v}
    return float(np.mean([E[states[(v, 1 << v)]] for v in range(n)]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--walks", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results/graphs.csv")
    ap.add_argument("--exact_max_n", type=int, default=8)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    graphs = build_graphs(seed=args.seed)
    rng = np.random.default_rng(1000 + args.seed)
    rows = []
    for idx, (fam, name, adj) in enumerate(graphs):
        n = len(adj)
        m = sum(len(a) for a in adj) // 2
        dmax = max(len(a) for a in adj)
        D = diameter(adj)
        s = mc_cover(adj, args.walks, rng).astype(float)
        mean = s.mean()
        se = s.std(ddof=1) / math.sqrt(len(s))
        exact = exact_cover(adj) if n <= args.exact_max_n else float("nan")
        rows.append(dict(family=fam, name=name, n=n, m=m, dmax=dmax, diam=D,
                         mc_mean=mean, mc_se=se, mc_ci_lo=mean - 1.96 * se,
                         mc_ci_hi=mean + 1.96 * se, exact=exact, walks=len(s)))
        print(f"[{idx+1}/{len(graphs)}] {name:12s} n={n:2d} m={m:3d} D={D:2d} "
              f"C={mean:9.1f} +- {se:6.1f}" + (f" exact={exact:9.2f}" if n <= args.exact_max_n else ""),
              flush=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", args.out, len(rows), "graphs")


if __name__ == "__main__":
    main()
