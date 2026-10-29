"""Check the closed-form start-averaged cover times used in closed_form_gap.py against exact subset-DP values (n=7)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))


def exact(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    full = (1 << n) - 1
    val = {}
    for S in sorted(range(1, full + 1), key=lambda s: -bin(s).count("1")):
        vs = [v for v in range(n) if S >> v & 1]
        if S == full:
            for v in vs:
                val[(S, v)] = 0.0
            continue
        idx = {v: i for i, v in enumerate(vs)}
        A, b = np.eye(len(vs)), np.ones(len(vs))
        for v in vs:
            d = len(adj[v])
            for w in adj[v]:
                if S >> w & 1:
                    A[idx[v], idx[w]] -= 1 / d
                else:
                    b[idx[v]] += val[(S | 1 << w, w)] / d
        x = np.linalg.solve(A, b)
        for v in vs:
            val[(S, v)] = x[idx[v]]
    return float(np.mean([val[(1 << v, v)] for v in range(n)]))


if __name__ == "__main__":
    import importlib.util
    n = 7
    H = lambda k: sum(1 / i for i in range(1, k + 1))
    N = n - 1
    cases = {
        "path": ([(i, i + 1) for i in range(n - 1)], N * N + N * (N - 1) / 6),
        "cycle": ([(i, (i + 1) % n) for i in range(n)], n * (n - 1) / 2),
        "complete": ([(i, j) for i in range(n) for j in range(i + 1, n)], (n - 1) * H(n - 1)),
        "star": ([(0, i) for i in range(1, n)], 2 * N * H(N - 1) + 1 / (N + 1)),
    }
    for name, (edges, closed) in cases.items():
        ex = exact(n, edges)
        print(name, ex, closed, abs(ex - closed) < 1e-9)
