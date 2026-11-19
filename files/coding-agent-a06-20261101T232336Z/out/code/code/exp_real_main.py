"""Real LLM + MMLU-Pro audit using the cached Qwen2.5-1.5B grid.  Usage: python exp_real_main.py PROCS NREP [CACHE]
Primary design: benchmark S drawn i.i.d. WITH replacement from the cached population P (the empirical distribution), truth = exact accuracy over P
(a benchmark drawn without replacement and scored on P\\S has fresh-item accuracy mechanically anti-correlated with S; see App.). A secondary
'fresh-items' run (S without replacement, truth on P\\S) is done for small n where n/|P| is small."""
import sys; sys.path.insert(0, "/work/code")
from runner import *
from realdata import load_Y
procs = int(sys.argv[1]); nrep = int(sys.argv[2]); cache = sys.argv[3] if len(sys.argv) > 3 else "/work/cache/q15"
W = dict(kind="real", cache=cache)
N = load_Y(cache).shape[0]; print("population size", N)
ns = (50, 100, 200, 400, 800)
cells = []
for n in ns:
    for algo, kw in [("rs", dict(B=8)), ("rs", dict(B=72)), ("sh", dict(B=72)), ("ca", {}), ("mipro", dict(B=40))]:
        cells.append(dict(world=W, n=n, algo=algo, kw=kw, method_set="main", wr=True))
run_cells(cells, nrep, "/work/results/real_main.parquet", procs)
cells = [dict(world=W, n=n, algo="rs", kw=dict(B=B), method_set="naive", wr=True) for n in ns for B in (1, 2, 4, 8, 16, 32, 72)]
run_cells(cells, 4 * nrep, "/work/results/real_sweep_naive.parquet", procs)
# secondary: S without replacement, truth on the fresh questions P \ S (only small n)
cells = [dict(world=W, n=n, algo=a, kw=kw, method_set="main", wr=False) for n in (50, 100, 200) for a, kw in [("rs", dict(B=72)), ("mipro", dict(B=40))]]
run_cells(cells, nrep, "/work/results/real_main_fresh.parquet", procs)
