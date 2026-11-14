"""Intervals at the datasets' native sizes (single realisation; no coverage claim possible without truth).

ballots: n=1027 labeled, N=78150 unlabeled. plankton: labeled 2013, unlabeled 2014 (shift).
Others: random 10% labeled / 90% unlabeled split (seed 0), truth = mean of all Y for reference.
"""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import data as D, estimators as E
from ppi_py import ppi_mean_ci

rows = []
for name in D.DATASETS:
    d = D.load(name); rng = np.random.default_rng(0)
    if name == "ballots":
        Y, f, fu, truth = d["Y"], d["Yhat"], d["Yhat_unlabeled"], np.nan
    elif name == "plankton":
        Y, f, fu, truth = d["Y"], d["Yhat"], d["Yhat_unlabeled"], d["Y_unlabeled"].mean()
    else:
        m = len(d["Y"]); p = rng.permutation(m); k = max(int(0.1 * m), 50)
        Y, f, fu, truth = d["Y"][p[:k]], d["Yhat"][p[:k]], d["Yhat"][p[k:]], d["Y"].mean()
    Y, f, fu = Y.astype(float), f.astype(float), fu.astype(float)
    ivs = {"classical": E.classical(Y), "ppi": E.ppi_scores(Y, f, fu, lam=1.0), "ppipp": E.ppi_scores(Y, f, fu, clip=True)}
    for kind in ["iso", "bin", "spl"]:
        ivs["cal_" + kind] = E.cal_ppi(Y, f, fu, kind, rng=np.random.default_rng(1))
    for k, (lo, hi) in ivs.items():
        rows.append(dict(dataset=name, n=len(Y), N=len(fu), method=k, lo=lo, hi=hi, width=hi - lo, truth=truth,
                         covers=(lo <= truth <= hi) if truth == truth else None))
df = pd.DataFrame(rows); df.to_csv("results/full_data_intervals.csv", index=False)
print(df.round(5).to_string())
