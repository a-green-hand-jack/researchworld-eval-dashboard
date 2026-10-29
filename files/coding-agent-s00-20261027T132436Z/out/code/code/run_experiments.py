"""Generate small connected graphs (n <= 30), estimate cover times by Monte Carlo
(via ./cover), and record simple graph statistics. Output: results/data.csv
Usage: python run_experiments.py [R=1000] [seed=0]"""
import os, sys, subprocess, csv, random, tempfile
from concurrent.futures import ProcessPoolExecutor
import networkx as nx

R = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 0
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "data.csv")

def families(rng):
    """Yield (family, graph) pairs; all graphs connected with 4 <= n <= 30."""
    for n in range(4, 31, 2):
        yield "path", nx.path_graph(n)
        yield "cycle", nx.cycle_graph(n)
        yield "star", nx.star_graph(n - 1)
        yield "wheel", nx.wheel_graph(n)
        yield "complete", nx.complete_graph(n)
        yield "lollipop", nx.lollipop_graph(max(3, n // 2), n - max(3, n // 2))
        a = n // 3
        yield "complete_bipartite", nx.complete_bipartite_graph(a, n - a)
    for r in range(2, 7):
        for c in range(2, 7):
            if 4 <= r * c <= 30:
                yield "grid", nx.convert_node_labels_to_integers(nx.grid_2d_graph(r, c))
    for d in (2, 3, 4):
        yield "hypercube", nx.hypercube_graph(d)
    for n in range(5, 31, 3):  # one random labelled tree per size
        yield "tree", nx.from_prufer_sequence([rng.randrange(n) for _ in range(n - 2)])
    for _ in range(40):
        n = rng.randint(4, 30)
        p = rng.uniform(0.1, 0.6)
        g = nx.gnp_random_graph(n, p, seed=rng.randrange(10**9))
        if nx.is_connected(g):
            yield "gnp", g
    for _ in range(30):
        n = rng.randint(6, 30)
        d = rng.choice([3, 4])
        if n * d % 2 == 0 and n > d:
            g = nx.random_regular_graph(d, n, seed=rng.randrange(10**9))
            if nx.is_connected(g):
                yield "regular", g
    for _ in range(30):
        n = rng.randint(6, 30)
        k = rng.randint(2, n // 2)
        g = nx.connected_watts_strogatz_graph(n, min(k * 2, n - 1), 0.1, seed=rng.randrange(10**9))
        yield "small_world", g
    for _ in range(30):
        # "dumbbell"/tadpole-type graphs: a clique with a pendant path of random length
        k = rng.randint(3, 15)
        L = rng.randint(1, 30 - k)
        yield "tadpole", nx.lollipop_graph(k, L)

def worker(args):
    fam, g, R, seed = args
    g = nx.convert_node_labels_to_integers(g)
    n, m = g.number_of_nodes(), g.number_of_edges()
    fd, path = tempfile.mkstemp(text=True)
    with os.fdopen(fd, "w") as f:
        f.write(f"{n} {m}\n")
        for u, v in g.edges():
            f.write(f"{u} {v}\n")
        f.write(f"{R} {seed}\n")
    try:
        out = subprocess.run([os.path.join(HERE, "cover")], stdin=open(path), capture_output=True, text=True, check=True).stdout
    finally:
        os.remove(path)
    rows = [list(map(float, l.split())) for l in out.strip().splitlines()]
    best = max(rows, key=lambda r: r[1])
    degs = [d for _, d in g.degree()]
    rec = dict(family=fam, n=n, m=m, avg_deg=2 * m / n, max_deg=max(degs), min_deg=min(degs),
               diameter=nx.diameter(g), cover_time=best[1], cover_se=best[2] / R ** 0.5,
               start=int(best[0]), bound_2m_n1=2 * m * (n - 1))
    return rec

if __name__ == "__main__":
    rng = random.Random(SEED)
    graphs = [(f, g) for f, g in families(rng) if g is not None]
    jobs = [(f, g, R, SEED * 100000 + i + 1) for i, (f, g) in enumerate(graphs)]
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        recs = list(ex.map(worker, jobs, chunksize=4))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
        w.writeheader(); w.writerows(recs)
    print(f"wrote {len(recs)} graphs to {OUT}")
