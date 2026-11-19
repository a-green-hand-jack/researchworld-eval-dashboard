"""Precompute and cache Louvain clusterings for the two real graphs (and report summary stats)."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_lib import *

kinds = sys.argv[1:] or ["egofb", "stanford3"]
for kind in kinds:
    t = time.time()
    net = get_net(dict(kind=kind, gseed=0))
    print(kind, "n", net.n, "edges", int(net.A.nnz / 2), "mean deg %.1f" % net.dbar, "max deg", int(net.deg.max()),
          "harm deg %.1f" % (1 / np.mean(net.invdeg)), flush=True)
    for res in [1.0, 0.5, 3.0, 10.0]:
        lab = net.clusters(res, 0)
        sz = np.bincount(lab)
        print(f"  res={res}: K={len(sz)} median size {np.median(sz):.0f} max {sz.max()} intra-edge frac "
              f"{net.intra_fraction(lab):.3f}  ({time.time()-t:.0f}s)", flush=True)
