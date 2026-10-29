"""Exact cover-time solver (small n) and vectorised Monte Carlo cover-time estimator."""
import itertools
import numpy as np


def adjacency_arrays(g):
    n = g.number_of_nodes()
    deg = np.array([g.degree(v) for v in range(n)])
    nbr = np.zeros((n, deg.max()), dtype=np.int64)
    for v in range(n):
        nb = sorted(g.neighbors(v))
        nbr[v, : len(nb)] = nb
    return nbr, deg


def mc_cover_times(g, starts, n_walks, rng):
    """Return array shape (len(starts), n_walks) of cover times (steps) for simple random walks."""
    n = g.number_of_nodes()
    nbr, deg = adjacency_arrays(g)
    S = len(starts)
    W = S * n_walks
    pos = np.repeat(np.asarray(starts), n_walks)
    visited = np.zeros((W, n), dtype=bool)
    ar = np.arange(W)
    visited[ar, pos] = True
    count = np.ones(W, dtype=np.int64)
    cover = np.full(W, -1, dtype=np.int64)
    step = 0
    active = np.arange(W)
    while active.size:
        step += 1
        p = pos[active]
        choice = (rng.random(active.size) * deg[p]).astype(np.int64)
        p = nbr[p, choice]
        pos[active] = p
        new = ~visited[active, p]
        visited[active, p] = True
        count[active] += new
        done = count[active] == n
        cover[active[done]] = step
        active = active[~done]
    return cover.reshape(S, n_walks)


def exact_cover_from_each_vertex(g):
    """Exact expected cover time from every start vertex via the (vertex, visited-set) Markov chain.
    Only intended for n <= 8."""
    n = g.number_of_nodes()
    nbr, deg = adjacency_arrays(g)
    full = (1 << n) - 1
    states = [(v, S) for S in range(1 << n) for v in range(n) if S >> v & 1 and S != full]
    idx = {st: i for i, st in enumerate(states)}
    N = len(states)
    A = np.eye(N)
    b = np.ones(N)
    for (v, S), i in idx.items():
        for k in range(deg[v]):
            u = nbr[v, k]
            T = S | (1 << u)
            if T == full:
                continue
            A[i, idx[(u, T)]] -= 1.0 / deg[v]
    E = np.linalg.solve(A, b)
    return np.array([E[idx[(v, 1 << v)]] for v in range(n)])


def hitting_times(g):
    """Matrix H[u,v] = expected hitting time of v from u."""
    n = g.number_of_nodes()
    nbr, deg = adjacency_arrays(g)
    P = np.zeros((n, n))
    for v in range(n):
        for k in range(deg[v]):
            P[v, nbr[v, k]] += 1.0 / deg[v]
    H = np.zeros((n, n))
    for t in range(n):
        keep = [i for i in range(n) if i != t]
        M = np.eye(n - 1) - P[np.ix_(keep, keep)]
        h = np.linalg.solve(M, np.ones(n - 1))
        H[keep, t] = h
    return H
