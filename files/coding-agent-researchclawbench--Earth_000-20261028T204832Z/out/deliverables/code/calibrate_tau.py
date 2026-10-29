"""Calibrate the representativeness error tau (m w.e. per year, independent between years)
of the glaciological annual variability such that leave-one-pentad-out predictions of the
DEM-differencing pentads (mean-offset extension) have normalised errors with RMS = 1."""
import sys; sys.path.insert(0, '/work/code')
import numpy as np, pandas as pd
from scipy.optimize import brentq
from glambie_lib import *

recs = []
for reg in REGIONS:
    hy, meta = reconcile_region(reg, dict(tau=0.0))
    dg = meta['group_detail']['DG']
    a = dg['a']; sa = dg['sig_rand'].reindex(a.index).fillna(dg['sig_rand'].mean())
    starts = a.index.values
    sol = [s for s in meta['solutions'] if s['source'] == 'demdiff' and s['author'].startswith('Hugonnet')][0]
    ent = []
    for (t0, t1, val, err) in sol['periods']:
        w = period_weights(t0, t1, starts)
        rp = (val - np.sum(w[w > 0] * a.values[w > 0])) / w.sum()
        tm = np.sum(w * (starts + 0.5)) / w.sum()
        ent.append((w, rp, err / (t1 - t0), tm, val, err))
    for k in range(len(ent)):
        tr = [e for j, e in enumerate(ent) if j != k]
        w, rp, se, tm, val, err = ent[k]
        rp_ = np.array([e[1] for e in tr]); se_ = np.array([e[2] for e in tr]); tm_ = np.array([e[3] for e in tr])
        wt = 1 / se_ ** 2
        # extension predictor used in the reconciliation: duration-weighted mean offset
        pw = np.array([e[0].sum() for e in tr])
        c = np.sum(pw * rp_) / pw.sum()
        sc = np.sqrt(np.sum((pw * se_) ** 2)) / pw.sum()
        pred = np.sum(w[w > 0] * (a.values[w > 0] + c))
        recs.append(dict(region=SHORT[reg], e=pred - val, var0=err ** 2 + (sc * w.sum()) ** 2 +
                         np.sum((w * sa.values) ** 2), sw2=np.sum(w ** 2)))
df = pd.DataFrame(recs)
f = lambda tau: np.mean(df.e ** 2 / (df.var0 + tau ** 2 * df.sw2)) - 1
print('RMS z without tau: %.2f' % np.sqrt(np.mean(df.e ** 2 / df.var0)))
tau = brentq(f, 0, 3)
print('calibrated tau = %.3f m w.e.' % tau)
# robustness: median-based (z median abs = 0.674)
g = lambda t: np.median(np.abs(df.e) / np.sqrt(df.var0 + t ** 2 * df.sw2)) - 0.6745
print('robust (median) tau = %.3f' % brentq(g, 0, 3))
pd.Series(dict(tau=tau)).to_csv('/work/outputs/tau_calibration.csv')
