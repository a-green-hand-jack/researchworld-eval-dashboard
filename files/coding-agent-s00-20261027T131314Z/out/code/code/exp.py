"""Monte-Carlo cover times of simple random walks on small connected graphs
and a comparison of simple predictors. Pure Python, standard library only.
Usage: python3 exp.py --seed 0 --walks 300 --out results.json
"""
import argparse, json, math, random
from collections import deque

def make_graph(name, n, rng):
    E = set()
    def add(u, v):
        if u != v: E.add((min(u, v), max(u, v)))
    if name == "path":
        for i in range(n - 1): add(i, i + 1)
    elif name == "cycle":
        for i in range(n): add(i, (i + 1) % n)
    elif name == "star":
        for i in range(1, n): add(0, i)
    elif name == "complete":
        for i in range(n):
            for j in range(i + 1, n): add(i, j)
    elif name == "wheel":
        for i in range(1, n): add(0, i); add(i, 1 + (i % (n - 1)))
    elif name == "grid":
        c = max(2, int(math.sqrt(n))); r = n // c
        n = r * c
        for i in range(r):
            for j in range(c):
                v = i * c + j
                if j + 1 < c: add(v, v + 1)
                if i + 1 < r: add(v, v + c)
    elif name == "lollipop":  # clique on n/2 plus path on the rest
        k = n // 2
        for i in range(k):
            for j in range(i + 1, k): add(i, j)
        for i in range(k - 1, n - 1): add(i, i + 1)
    elif name == "barbell":  # two cliques joined by a path
        k = n // 3; p = n - 2 * k
        for base in (0, n - k):
            for i in range(base, base + k):
                for j in range(i + 1, base + k): add(i, j)
        chain = [k - 1] + list(range(k, k + p)) + [n - k]
        for a, b in zip(chain, chain[1:]): add(a, b)
    elif name == "binary_tree":
        for i in range(1, n): add(i, (i - 1) // 2)
    elif name == "random_tree":
        for i in range(1, n): add(i, rng.randrange(i))
    elif name == "gnp_sparse" or name == "gnp_dense":
        p = 0.12 if name == "gnp_sparse" else 0.4
        while True:
            E = set()
            for i in range(n):
                for j in range(i + 1, n):
                    if rng.random() < p: add(i, j)
            if connected(n, E): break
    elif name == "regular3":
        if n % 2: n -= 1
        while True:  # configuration model with rejection
            stubs = [v for v in range(n) for _ in range(3)]
            rng.shuffle(stubs); E = set(); ok = True
            for a, b in zip(stubs[::2], stubs[1::2]):
                if a == b or (min(a, b), max(a, b)) in E: ok = False; break
                add(a, b)
            if ok and connected(n, E): break
            E = set()
    else:
        raise ValueError(name)
    return n, sorted(E)

def adj_list(n, E):
    A = [[] for _ in range(n)]
    for u, v in E: A[u].append(v); A[v].append(u)
    return A

def bfs(A, s):
    d = [-1] * len(A); d[s] = 0; q = deque([s])
    while q:
        u = q.popleft()
        for w in A[u]:
            if d[w] < 0: d[w] = d[u] + 1; q.append(w)
    return d

def connected(n, E):
    return all(x >= 0 for x in bfs(adj_list(n, E), 0))

def diameter(A):
    return max(max(bfs(A, s)) for s in range(len(A)))

def cover_time(A, start, rng):
    n = len(A); seen = [False] * n; seen[start] = True; left = n - 1
    u = start; t = 0
    while left:
        u = A[u][rng.randrange(len(A[u]))]; t += 1
        if not seen[u]: seen[u] = True; left -= 1
    return t

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--walks", type=int, default=300)
    ap.add_argument("--out", default="results.json")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    families = ["path", "cycle", "star", "complete", "wheel", "grid", "lollipop",
                "barbell", "binary_tree", "random_tree", "gnp_sparse", "gnp_dense", "regular3"]
    sizes = [8, 12, 16, 20, 24, 28]
    rows = []
    for fam in families:
        reps = 3 if fam in ("random_tree", "gnp_sparse", "gnp_dense", "regular3") else 1
        for n0 in sizes:
            for r in range(reps):
                n, E = make_graph(fam, n0, rng)
                A = adj_list(n, E)
                if not connected(n, E): continue
                m = len(E); D = diameter(A)
                ts = [cover_time(A, rng.randrange(n), rng) for _ in range(a.walks)]
                mu = sum(ts) / len(ts)
                sd = math.sqrt(sum((t - mu) ** 2 for t in ts) / (len(ts) - 1))
                rows.append(dict(family=fam, n=n, m=m, D=D,
                                 dmax=max(len(x) for x in A), dmean=2 * m / n,
                                 cover=mu, ci=1.96 * sd / math.sqrt(len(ts)),
                                 bound=2 * m * (n - 1)))
        print(fam, "done", flush=True)
    json.dump(dict(seed=a.seed, walks=a.walks, rows=rows), open(a.out, "w"), indent=1)
    print("graphs:", len(rows))

if __name__ == "__main__":
    main()
