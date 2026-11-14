"""Smallest budget n reaching a target MAE (C4/Q2), by log-log interpolation of mean-MAE over the n grid.
usage: python items_needed.py summary.csv out.csv"""
import sys, numpy as np, pandas as pd
s = pd.read_csv(sys.argv[1]); rows = []
for (b, sp, m), g in s.groupby(["benchmark", "split_type", "method"]):
    g = g.sort_values("n"); n, e = g.n.values.astype(float), g.mae.values
    for tgt in (0.01, 0.02, 0.03):
        if e.min() > tgt:
            val = np.inf           # not reached within the grid
        elif e[0] <= tgt:
            val = n[0]
        else:
            i = int(np.argmax(e <= tgt))
            val = float(np.exp(np.interp(np.log(tgt), [np.log(e[i]), np.log(e[i - 1])], [np.log(n[i]), np.log(n[i - 1])])))
        rows.append(dict(benchmark=b, split_type=sp, method=m, target_mae=tgt, n_needed=val, n_max=n.max()))
pd.DataFrame(rows).to_csv(sys.argv[2], index=False)
