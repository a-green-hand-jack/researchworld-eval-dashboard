"""Generate graphs, estimate start-averaged cover times by Monte Carlo, compute
easy statistics, Matthews bound, and exact values for small graphs (validation).
Usage: python run_experiments.py  -> writes ../results/graphs.csv, ../results/validation.csv
Seeds: graph generation seed=0, simulation seed=12345."""
import csv
import numpy as np
import networkx as nx
from cover import make_graphs, mc_cover_avg, exact_cover_avg, matthews_upper

WALKS_PER_START = 100
rng = np.random.default_rng(12345)
graphs = make_graphs(seed=0, per_family=30)

rows, val = [], []
for i, (fam, G) in enumerate(graphs):
    n, m = G.number_of_nodes(), G.number_of_edges()
    deg = np.array([d for _, d in G.degree()])
    steps = mc_cover_avg(G, WALKS_PER_START, rng).astype(float)
    C = steps.mean()
    se = steps.std(ddof=1) / np.sqrt(steps.size)
    row = dict(id=i, family=fam, n=n, m=m, dmin=int(deg.min()), dmax=int(deg.max()),
               davg=2 * m / n, diam=nx.diameter(G), C_mc=C, C_se=se,
               matthews=matthews_upper(G), bound_2m_n1=2 * m * (n - 1))
    rows.append(row)
    if n <= 9:
        ex = exact_cover_avg(G)
        val.append(dict(id=i, family=fam, n=n, exact=ex, mc=C, se=se,
                        z=(C - ex) / se))

with open("../results/graphs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
with open("../results/validation.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(val[0].keys()))
    w.writeheader(); w.writerows(val)
print("graphs:", len(rows), "exact-validated:", len(val))
print("max |z| in validation:", max(abs(v["z"]) for v in val))
