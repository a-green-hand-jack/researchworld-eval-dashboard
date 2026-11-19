import sys, numpy as np
from analysis_lib import *
name = sys.argv[1]
keys = sys.argv[2].split(",")
rows = load(name)
g = group(rows, lambda r: tuple(r["cfg"][k] for k in keys))
for k, rs in g.items():
    fin = [r["final"] for r in rs]
    print(k, "n=%d" % len(rs), "final train acc", np.round([f[1] for f in fin], 3), "final val acc", np.round([f[3] for f in fin], 3),
          "wnorm", np.round(np.mean([f[5] for f in fin]), 1))
