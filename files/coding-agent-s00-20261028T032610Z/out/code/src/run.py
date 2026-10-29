"""Generate graphs, estimate cover times by Monte Carlo, compute statistics and generic bounds.
Usage: python run.py --walks 300 --seed 0 --out ../data/results.csv"""
import argparse
import csv
import time
import numpy as np
import networkx as nx
from graphs import make_graphs
from sim import mc_cover_times, hitting_times, exact_cover_from_each_vertex

ap = argparse.ArgumentParser()
ap.add_argument("--walks", type=int, default=300)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--n_starts_large", type=int, default=10)
ap.add_argument("--out", default="../data/results.csv")
args = ap.parse_args()

rng = np.random.default_rng(args.seed)
rows = []
t0 = time.time()
for fam, name, g in make_graphs(seed=args.seed):
    n, m = g.number_of_nodes(), g.number_of_edges()
    degs = np.array([d for _, d in g.degree()])
    # Start vertices: all of them for small graphs, a random subset otherwise.
    if n <= 12:
        starts = list(range(n))
    else:
        starts = sorted(rng.choice(n, size=args.n_starts_large, replace=False).tolist())
    C = mc_cover_times(g, starts, args.walks, rng).astype(float)
    means = C.mean(1)
    k = int(np.argmax(means))
    worst = C[k]
    H = hitting_times(g)
    matthews = H.max() * sum(1.0 / i for i in range(1, n))
    exact = np.nan
    if n <= 8:
        exact = float(exact_cover_from_each_vertex(g).max())
    rows.append(dict(
        family=fam, name=name, n=n, m=m,
        mean_deg=2 * m / n, max_deg=int(degs.max()), min_deg=int(degs.min()),
        diameter=nx.diameter(g),
        cover_mc=means[k], cover_se=worst.std(ddof=1) / np.sqrt(len(worst)),
        n_starts=len(starts), walks=args.walks,
        bound_2m_n1=2 * m * (n - 1), matthews=matthews,
        cover_exact=exact,
    ))
print(f"{len(rows)} graphs in {time.time()-t0:.1f}s")
with open(args.out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
