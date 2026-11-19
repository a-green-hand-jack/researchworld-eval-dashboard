"""Build, cache, and describe all graphs used in the study.

Writes /work/data/processed/<name>.npz (LCC edge list + Louvain partition)
and /work/results/graph_stats.csv. Run once: python -m prepare_graphs
"""
import os
import sys
import time

import pandas as pd

sys.path.insert(0, "/work/code")
from gate import graphs as gr  # noqa: E402

rows = []
specs = [
    ("stanford3", lambda: gr.load_stanford3()),
    ("egofb", lambda: gr.load_egofb()),
    ("ba_n5000_m3", lambda: gr.make_ba(5000, 3, seed=1)),
]
for d in [5, 10, 20, 50, 100, 200]:
    specs.append((f"er_n5000_d{d}", lambda d=d: gr.make_er(5000, d, seed=1)))
for n in [1000, 4000, 16000]:
    specs.append((f"er_n{n}_d20", lambda n=n: gr.make_er(n, 20, seed=1)))

for name, make in specs:
    t0 = time.time()
    G = make()
    target = max(20, G.number_of_nodes() // 60)
    row = gr.build_and_cache(name, G, target)
    row["build_sec"] = round(time.time() - t0, 1)
    rows.append(row)
    print(row, flush=True)

pd.DataFrame(rows).to_csv("/work/results/graph_stats.csv", index=False)
print("done", flush=True)
