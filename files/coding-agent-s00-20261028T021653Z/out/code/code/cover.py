"""Monte Carlo cover times on small connected graphs and simple predictors.

Usage: python3 -I cover.py --out /work/results --seed 2026 --trials 200
Pure standard library (no numpy/networkx needed).
"""
import argparse, csv, json, math, os, random
from collections import deque

# ---------------------------------------------------------------- graph generators
def from_edges(n, edges):
    adj = [set() for _ in range(n)]
    for u, v in edges:
        if u != v:
            adj[u].add(v); adj[v].add(u)
    return [sorted(a) for a in adj]

def path(n):   return from_edges(n, [(i, i + 1) for i in range(n - 1)])
def cycle(n):  return from_edges(n, [(i, (i + 1) % n) for i in range(n)])
def star(n):   return from_edges(n, [(0, i) for i in range(1, n)])
def complete(n): return from_edges(n, [(i, j) for i in range(n) for j in range(i + 1, n)])
def wheel(n):
    rim = [(i, i + 1) for i in range(1, n - 1)] + [(1, n - 1)]
    return from_edges(n, [(0, i) for i in range(1, n)] + rim)
def lollipop(n):
    k = max(3, n // 2); edges = [(i, j) for i in range(k) for j in range(i + 1, k)]
    edges += [(k - 1 + i, k + i) for i in range(n - k)]
    return from_edges(n, edges)
def barbell(n):
    k = max(3, n // 3); b = n - 2 * k
    edges = [(i, j) for i in range(k) for j in range(i + 1, k)]
    edges += [(k + b + i, k + b + j) for i in range(k) for j in range(i + 1, k)]
    chain = [k - 1] + [k + i for i in range(b)] + [k + b]
    edges += [(chain[i], chain[i + 1]) for i in range(len(chain) - 1)]
    return from_edges(n, edges)
def grid(n):
    r = max(1, int(math.sqrt(n)))
    while n % r and r > 1: r -= 1
    c = n // r
    edges = []
    for i in range(r):
        for j in range(c):
            v = i * c + j
            if j + 1 < c: edges.append((v, v + 1))
            if i + 1 < r: edges.append((v, v + c))
    return from_edges(n, edges)
def binary_tree(n):
    return from_edges(n, [((i - 1) // 2, i) for i in range(1, n)])
def random_tree(n, rng):
    return from_edges(n, [(rng.randrange(i), i) for i in range(1, n)])
def gnp_connected(n, p, rng):
    while True:
        edges = [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p]
        g = from_edges(n, edges)
        if is_connected(g): return g

# ---------------------------------------------------------------- graph statistics
def bfs(g, s):
    d = [-1] * len(g); d[s] = 0; q = deque([s])
    while q:
        u = q.popleft()
        for v in g[u]:
            if d[v] < 0: d[v] = d[u] + 1; q.append(v)
    return d

def is_connected(g):
    return all(x >= 0 for x in bfs(g, 0))

def stats(g):
    n = len(g); m = sum(len(a) for a in g) // 2
    diam = max(max(bfs(g, s)) for s in range(n))
    degs = [len(a) for a in g]
    return dict(n=n, m=m, avg_deg=2 * m / n, max_deg=max(degs), diam=diam,
                bound_2m_n1=2 * m * (n - 1))

# ---------------------------------------------------------------- simulation
def cover_steps(g, start, rng):
    n = len(g); seen = [False] * n; seen[start] = True; left = n - 1
    u = start; t = 0
    while left:
        nb = g[u]; u = nb[int(rng.random() * len(nb))]; t += 1
        if not seen[u]: seen[u] = True; left -= 1
    return t

def estimate_cover(g, trials, rng):
    """Mean cover time with the start vertex drawn uniformly at random per trial."""
    xs = [cover_steps(g, rng.randrange(len(g)), rng) for _ in range(trials)]
    mean = sum(xs) / trials
    var = sum((x - mean) ** 2 for x in xs) / (trials - 1)
    return mean, math.sqrt(var / trials)

# ---------------------------------------------------------------- regression (OLS via normal equations)
def solve(A, b):
    n = len(A); M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c])); M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c and M[c][c] != 0:
                f = M[r][c] / M[c][c]
                for k in range(c, n + 1): M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]

def ols(X, y, ridge=1e-9):
    k = len(X[0])
    A = [[sum(X[r][i] * X[r][j] for r in range(len(X))) + (ridge if i == j else 0) for j in range(k)] for i in range(k)]
    b = [sum(X[r][i] * y[r] for r in range(len(X))) for i in range(k)]
    return solve(A, b)

FEATURES = {
    "nm":        lambda s: [1, math.log(s["n"]), math.log(s["m"])],
    "full":      lambda s: [1, math.log(s["n"]), math.log(s["m"]), math.log(s["max_deg"]), math.log(s["diam"])],
}

# ---------------------------------------------------------------- main
def build_suite(rng):
    suite = []  # (family, graph)
    for n in range(4, 31, 2):
        for name, f in [("path", path), ("cycle", cycle), ("star", star), ("complete", complete),
                        ("wheel", wheel), ("lollipop", lollipop), ("barbell", barbell),
                        ("grid", grid), ("binary_tree", binary_tree)]:
            if name == "wheel" and n < 5: continue
            suite.append((name, f(n)))
    for n in range(4, 31, 2):
        for _ in range(2):
            suite.append(("random_tree", random_tree(n, rng)))
        for p in (0.1, 0.25, 0.5):
            suite.append((f"gnp_{p}", gnp_connected(n, p, rng)))
    return suite

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/work/results")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--trials", type=int, default=200)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rng = random.Random(a.seed)
    suite = build_suite(rng)
    rows = []
    for i, (fam, g) in enumerate(suite):
        s = stats(g)
        mean, se = estimate_cover(g, a.trials, random.Random(a.seed * 100003 + i))
        rows.append(dict(family=fam, **s, cover=mean, se=se))
    with open(os.path.join(a.out, "graphs.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    # Evaluation: leave-one-family-out CV in log space (the model never sees the test family).
    fams = sorted({r["family"] for r in rows})
    report = {"n_graphs": len(rows), "trials": a.trials, "seed": a.seed, "models": {}}
    for mname, feat in FEATURES.items():
        beta = ols([feat(r) for r in rows], [math.log(r["cover"]) for r in rows])
        report["models"][mname] = {"coef_full_data": beta}
    def record(name, pred_fn):
        rel = []; per = {}
        for r in rows:
            p = pred_fn(r); e = abs(math.log(p) - math.log(r["cover"]))
            rel.append(e)
            per.setdefault(r["family"], []).append(e)
        rel.sort()
        report.setdefault("eval", {})[name] = {
            "median_abs_log_err": rel[len(rel) // 2],
            "median_factor_error": math.exp(rel[len(rel) // 2]),
            "p90_factor_error": math.exp(rel[int(0.9 * (len(rel) - 1))]),
            "per_family_median_factor": {f: math.exp(sorted(v)[len(v) // 2]) for f, v in per.items()}}
    # Cross-validated predictions keyed by graph identity
    for mname in FEATURES:
        cv = {}
        for hold in fams:
            tr = [r for r in rows if r["family"] != hold]
            beta = ols([FEATURES[mname](r) for r in tr], [math.log(r["cover"]) for r in tr])
            for r in rows:
                if r["family"] == hold:
                    cv[id(r)] = math.exp(sum(b * x for b, x in zip(beta, FEATURES[mname](r))))
        record(f"cv_{mname}", lambda r, cv=cv: cv[id(r)])
    # Constant-only baseline: CT ~ c * 2m(n-1) with c fitted on all data (in-sample, optimistic)
    c = math.exp(sum(math.log(r["cover"] / r["bound_2m_n1"]) for r in rows) / len(rows))
    record("bound_scaled_2m(n-1)", lambda r: c * r["bound_2m_n1"])
    record("raw_bound_2m(n-1)", lambda r: r["bound_2m_n1"])
    report["bound_ratio_cover_over_2m(n-1)_by_family"] = {
        f: math.exp(sum(math.log(r["cover"] / r["bound_2m_n1"]) for r in rows if r["family"] == f) /
                    sum(1 for r in rows if r["family"] == f)) for f in fams}
    with open(os.path.join(a.out, "report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report["eval"], indent=1)[:4000])

if __name__ == "__main__":
    main()
