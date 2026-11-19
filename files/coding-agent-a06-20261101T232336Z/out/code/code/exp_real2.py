"""Real-II: model x prompt pool (40 configurations from 5 small models, 8 prompt variants each) on the items scored for all models."""
import sys; sys.path.insert(0, "/work/code")
from runner import *
from realdata import load_pool2
procs = int(sys.argv[1]); nrep = int(sys.argv[2])
Y, names = load_pool2(return_names=True); N, K = Y.shape; print("items", N, "configs", K)
W = dict(kind="real2", n_items=N)
cells = []
for n in (50, 100, 200):
    for algo, kw in [("rs", dict(B=8)), ("rs", dict(B=K)), ("sh", dict(B=K))]:
        cells.append(dict(world=W, n=n, algo=algo, kw=kw, method_set="main", wr=True))
    cells.append(dict(world=W, n=n, algo="rs", kw=dict(B=K), method_set="rs_extras", wr=True))
run_cells(cells, nrep, "/work/results/real2_main.parquet", procs)
cells = [dict(world=W, n=n, algo="rs", kw=dict(B=B), method_set="naive", wr=True) for n in (50, 100, 200) for B in (1, 2, 4, 8, 16, 40)]
run_cells(cells, 4 * nrep, "/work/results/real2_sweep.parquet", procs)
