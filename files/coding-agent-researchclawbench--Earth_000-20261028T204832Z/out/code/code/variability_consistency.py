"""Consistency of annual variability between data groups: regression slope (amplitude ratio)
and correlation of annual anomalies of gravimetry / altimetry against glaciological anomalies,
at annual and 3-year-mean scales."""
import sys; sys.path.insert(0, '/work/code')
import numpy as np, pandas as pd
from glambie_lib import *
rows = []
for reg in REGIONS:
    hy, meta = reconcile_region(reg, dict(use_grav=True))
    gd = meta['group_detail']
    if 'DG' not in gd:
        continue
    dg = gd['DG']
    glac = dg['a'].where(dg['own_var'])
    for g in ['GRAV', 'ALT']:
        if g not in gd:
            continue
        x = gd[g]['value'].where(gd[g]['own_var'])
        m = glac.notna() & x.notna()
        if m.sum() < 6:
            continue
        ga, xa = glac[m] - glac[m].mean(), x[m] - x[m].mean()
        r = np.corrcoef(ga, xa)[0, 1]
        slope = np.sum(ga * xa) / np.sum(ga ** 2)
        # 3-yr block means
        n3 = (m.sum() // 3) * 3
        gb = ga.values[:n3].reshape(-1, 3).mean(1); xb = xa.values[:n3].reshape(-1, 3).mean(1)
        r3 = np.corrcoef(gb, xb)[0, 1] if len(gb) > 2 else np.nan
        s3 = np.sum(gb * xb) / np.sum(gb ** 2) if len(gb) > 2 else np.nan
        rows.append(dict(region=SHORT[reg], group=g, n=int(m.sum()), r_annual=r, slope_annual=slope,
                         sd_glac=ga.std(), sd_other=xa.std(), r_3yr=r3, slope_3yr=s3,
                         grav_used=not meta['excl_grav']))
df = pd.DataFrame(rows)
pd.set_option('display.width', 200)
print(df.round(2).to_string())
df.to_csv('/work/outputs/variability_consistency.csv', index=False)
print(df.groupby('group')[['r_annual', 'slope_annual', 'r_3yr', 'slope_3yr']].median().round(2))
