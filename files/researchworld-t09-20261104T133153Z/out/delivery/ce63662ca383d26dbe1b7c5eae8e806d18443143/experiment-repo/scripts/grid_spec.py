#!/usr/bin/env python3
"""Exact grid specification read from netgate.experiments: cells, graphs, designs, worlds x assignments, plus the real-graph sizes
(as loaded, largest component) -> results/tables/t13_grid_spec.csv and t13b_real_graphs.csv."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
from netgate import experiments as E
from netgate.graphs import make
import os, pandas as pd

R = results_dir(); rows = []
fn = E.EXPERIMENTS
for k, f in fn.items():
    c = f()
    pairs = sorted({(x["worlds"], x["reps"]) for x in c})
    rows.append(dict(exp=k, cells=len(c), graphs=";".join(sorted({x["graph"] for x in c})), n_designs=len({x["design"] for x in c}),
                     worlds_x_assignments=" / ".join(f"{w}x{r}" for w, r in pairs),
                     estimates_per_estimator_per_cell=" / ".join(str(w * r) for w, r in pairs)))
D = pd.DataFrame(rows); D.to_csv(os.path.join(R, "tables", "t13_grid_spec.csv"), index=False)
G = []
for g in ["stanford3", "ego"]:
    gr = make(g)
    A = gr.A
    G.append(dict(graph=g, n=A.shape[0], edges=int(A.nnz // 2), mean_degree=round(A.nnz / A.shape[0], 1)))
pd.DataFrame(G).to_csv(os.path.join(R, "tables", "t13b_real_graphs.csv"), index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 80); print(D.to_string(index=False)); print(pd.DataFrame(G))
