#!/usr/bin/env python3
"""Cells run vs cells in each grid (src/netgate/experiments.py) -> results/COMPLETENESS.csv, plus the list of cells not run.
A grid is 'complete' only if every cell index has a raw file; partial grids must not be presented as complete."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import os, sys, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from netgate.experiments import EXPERIMENTS

R = results_dir()
rows, miss = [], []
for e, f in EXPERIMENTS.items():
    cells = f()
    done = {int(os.path.basename(p).split(".")[0]) for p in glob.glob(os.path.join(R, "raw", e, "*.csv.gz"))}
    for i in sorted(set(range(len(cells))) - done):
        c = cells[i]
        miss.append({"exp": e, "cell": i, "graph": c["graph"], "design": c["design"], "outcome": str(c["outcome"]), "tag": c["tag"]})
    rows.append({"exp": e, "cells_total": len(cells), "cells_run": len(done), "cells_not_run": len(cells) - len(done), "complete": len(done) == len(cells)})
pd.DataFrame(rows).to_csv(os.path.join(R, "COMPLETENESS.csv"), index=False)
pd.DataFrame(miss, columns=["exp", "cell", "graph", "design", "outcome", "tag"]).to_csv(os.path.join(R, "CELLS_NOT_RUN.csv"), index=False)
print(pd.DataFrame(rows).to_string(index=False))
