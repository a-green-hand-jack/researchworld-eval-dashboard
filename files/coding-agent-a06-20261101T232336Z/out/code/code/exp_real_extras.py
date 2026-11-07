"""Methods that need B fully evaluated candidates (EB, worst-case correction, conditional, simultaneous, Ladder, Thresholdout) on the real pool."""
import sys; sys.path.insert(0, "/work/code")
from runner import *
procs = int(sys.argv[1]); nrep = int(sys.argv[2]); cache = "/work/cache/q15"
W = dict(kind="real", cache=cache)
cells = [dict(world=W, n=n, algo="rs", kw=dict(B=B), method_set="rs_extras", wr=True) for n in (50, 100, 200, 400, 800) for B in (8, 72)]
run_cells(cells, nrep, "/work/results/real_extras.parquet", procs)
