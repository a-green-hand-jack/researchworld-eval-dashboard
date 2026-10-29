"""Leave-one-period-out cross-validation of the offset model used to merge glaciological
annual variability with multi-annual DEM-differencing levels (Hugonnet et al. pentads)."""
import sys; sys.path.insert(0, '/work/code')
import numpy as np, pandas as pd
from glambie_lib import *

rows = []
for reg in REGIONS:
    hy, meta = reconcile_region(reg)
    a = meta['group_detail']['DG']['a']
    starts = a.index.values
    sol = [s for s in meta['solutions'] if s['source'] == 'demdiff' and s['author'].startswith('Hugonnet')][0]
    P = sol['periods']
    ent = []
    for (t0, t1, val, err) in P:
        w = period_weights(t0, t1, starts)
        rp = (val - np.sum(w[w > 0] * a.values[w > 0])) / w.sum()
        tm = np.sum(w * (starts + 0.5)) / w.sum()
        ent.append((w, rp, err / (t1 - t0), tm, val, err, t0, t1))
    for k in range(len(ent)):
        tr = [e for j, e in enumerate(ent) if j != k]
        w, rp, se, tm, val, err, t0, t1 = ent[k]
        rp_ = np.array([e[1] for e in tr]); se_ = np.array([e[2] for e in tr]); tm_ = np.array([e[3] for e in tr])
        wt = 1 / se_ ** 2
        pred = {}
        # constant
        pred['constant'] = np.sum(wt * rp_) / wt.sum()
        # nearest period
        pred['nearest'] = rp_[np.argmin(np.abs(tm_ - tm))]
        # linear drift, held at edge of training coverage
        X = np.vstack([np.ones_like(tm_), tm_ - tm_.mean()]).T
        beta = np.linalg.solve(X.T @ (X * wt[:, None]), X.T @ (wt * rp_))
        tc = np.clip(tm, tm_.min(), tm_.max())
        pred['linear'] = beta[0] + beta[1] * (tc - tm_.mean())
        # no variability information: geodetic mean rate only (a=0 baseline)
        rates = np.array([e[4] / (e[7] - e[6]) for e in tr])
        pred['geodetic_mean_rate'] = None
        for m, c in pred.items():
            if m == 'geodetic_mean_rate':
                ptot = np.sum(rates * (1 / se_ ** 2)) / np.sum(1 / se_ ** 2) * (t1 - t0)
            else:
                ptot = np.sum(w[w > 0] * (a.values[w > 0] + c))
            rows.append(dict(region=SHORT[reg], period=f'{t0:.0f}-{t1:.0f}', model=m,
                             err_rate=(ptot - val) / (t1 - t0), z=(ptot - val) / err))
df = pd.DataFrame(rows)
df.to_csv('/work/outputs/cv_offset_model.csv', index=False)
summ = df.groupby('model').agg(rmse_rate=('err_rate', lambda x: np.sqrt(np.mean(x ** 2))),
                               mae_rate=('err_rate', lambda x: np.mean(np.abs(x))),
                               bias=('err_rate', 'mean'), rms_z=('z', lambda x: np.sqrt(np.mean(x ** 2))))
interior = df[df.period.isin(['2005-2010', '2010-2015'])].groupby('model').err_rate.apply(lambda x: np.sqrt(np.mean(x ** 2)))
edge = df[df.period.isin(['2000-2005', '2015-2020'])].groupby('model').err_rate.apply(lambda x: np.sqrt(np.mean(x ** 2)))
summ['rmse_interior'] = interior
summ['rmse_edge'] = edge
print(summ.round(4))
summ.to_csv('/work/outputs/cv_offset_model_summary.csv')
