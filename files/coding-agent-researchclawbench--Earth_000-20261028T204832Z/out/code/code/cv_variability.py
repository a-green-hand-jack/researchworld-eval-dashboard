"""How informative is the glaciological annual variability for multi-annual (pentad) geodetic
change?  For each region and each held-out Hugonnet pentad we predict the pentad total from
(i) a constant offset fitted to the remaining pentads plus (ii) the glaciological variability
scaled by a factor k (k=0: no variability; k=1: full variability)."""
import sys; sys.path.insert(0, '/work/code')
import numpy as np, pandas as pd
from glambie_lib import *

res = []
for reg in REGIONS:
    area = Area(reg); starts = year_grid(reg); idx = pd.Index(starts)
    sols = []
    for ds in read_region_inputs(reg):
        h = homogenise(ds, reg, area); h.update(ds)
        h['annual'] = h['annual'].reindex(idx); h['annual_err'] = h['annual_err'].reindex(idx)
        sols.append(h)
    gl = [s for s in sols if s['source'] == 'glaciological' and s['annual'].notna().sum() >= 3]
    hug = [s for s in sols if s['source'] == 'demdiff' and s['author'].startswith('Hugonnet')][0]
    variants = {'both': gl, 'zemp': [s for s in gl if s['author'] != 'WGMS'], 'wgms': [s for s in gl if s['author'] == 'WGMS']}
    for vname, vs in variants.items():
        if not vs:
            continue
        a, c, sig = fixed_effects([s['annual'] for s in vs], [1.0] * len(vs))
        a = a.interpolate().bfill().ffill()
        anom = a - a.mean()
        for k in [0, 0.25, 0.5, 0.75, 1.0]:
            ak = anom * k
            ent = []
            for (t0, t1, val, err) in hug['periods']:
                w = period_weights(t0, t1, starts)
                rp = (val - np.sum(w * ak.values)) / w.sum()
                ent.append((w, rp, err / (t1 - t0), val, err, t0, t1))
            for j in range(len(ent)):
                tr = [e for i, e in enumerate(ent) if i != j]
                wt = np.array([1 / e[2] ** 2 for e in tr])
                cbar = np.sum(wt * np.array([e[1] for e in tr])) / wt.sum()
                w, rp, se, val, err, t0, t1 = ent[j]
                pred = np.sum(w * (ak.values + cbar))
                res.append(dict(region=SHORT[reg], var=vname, k=k, period=t0, err_rate=(pred - val) / (t1 - t0),
                                z=(pred - val) / err))
df = pd.DataFrame(res)
df.to_csv('/work/outputs/cv_variability.csv', index=False)
s = df.groupby(['var', 'k']).agg(rmse=('err_rate', lambda x: np.sqrt(np.mean(x ** 2))), rms_z=('z', lambda x: np.sqrt(np.mean(x ** 2))))
print(s.round(3).unstack(0))
# per-region best k (both)
b = df[df['var'] == 'both'].groupby(['region', 'k']).err_rate.apply(lambda x: np.sqrt(np.mean(x ** 2))).unstack()
print(b.round(2))
