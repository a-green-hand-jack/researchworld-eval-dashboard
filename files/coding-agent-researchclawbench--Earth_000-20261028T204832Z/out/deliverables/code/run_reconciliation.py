"""Run the reconciliation for all 19 regions, convert to calendar years and aggregate globally.
Usage: python3 run_reconciliation.py [tag] [json-options]
"""
import sys, json, os, pickle
sys.path.insert(0, '/work/code')
import numpy as np
import pandas as pd
from glambie_lib import REGIONS, SHORT, reconcile_region, to_calendar, Area

OUT = '/work/outputs'


def run(opts=None, tag='main', save=True, regions=REGIONS):
    hy_all, cal_all, metas = {}, {}, {}
    for reg in regions:
        hy, meta = reconcile_region(reg, opts)
        cal = to_calendar(reg, hy)
        area = Area(reg)
        cal['area'] = area(cal.index.values + 0.5)
        cal['gt'] = cal.mwe * cal.area / 1000
        for k in ['sig', 'sig_rand', 'sig_sys']:
            cal[k + '_gt'] = cal[k] * cal.area / 1000
        hy_all[reg], cal_all[reg] = hy, cal
        metas[reg] = dict(groups=meta['groups'], offsets=meta['group_offsets'],
                          sig_struct=meta['sig_struct'], excl_grav=meta['excl_grav'])
    # global aggregation (regions independent)
    years = cal_all[regions[0]].index
    g = pd.DataFrame(index=years)
    g['area'] = sum(cal_all[r].area for r in regions)
    g['gt'] = sum(cal_all[r]['gt'] for r in regions)
    for k in ['sig', 'sig_rand', 'sig_sys']:
        g[k + '_gt'] = np.sqrt(sum(cal_all[r][k + '_gt'] ** 2 for r in regions))
    g['mwe'] = g['gt'] * 1000 / g.area
    g['sig'] = g.sig_gt * 1000 / g.area
    if save:
        d = f'{OUT}/{tag}'
        os.makedirs(d, exist_ok=True)
        for r in regions:
            hy_all[r].to_csv(f'{d}/hydro_{r}.csv', index=False)
            cal_all[r].to_csv(f'{d}/calendar_{r}.csv')
        g.to_csv(f'{d}/calendar_global.csv')
        with open(f'{d}/meta.json', 'w') as f:
            json.dump({r: dict(groups=m['groups'], offsets={k: float(v) for k, v in m['offsets'].items()},
                               sig_struct=float(m['sig_struct']), excl_grav=bool(m['excl_grav']))
                       for r, m in metas.items()}, f, indent=1)
    return hy_all, cal_all, g, metas


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'main'
    opts = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
    hy, cal, g, metas = run(opts, tag)
    pd.set_option('display.width', 200)
    print(g.round(3).to_string())
    print('mean 2000-2023 Gt/yr', g['gt'].mean(), 'cum', g['gt'].sum())
    for r in REGIONS:
        print(SHORT[r], metas[r]['groups'], 'mean Gt/yr %.2f' % cal[r]['gt'].mean(), 'mwe/yr %.3f' % cal[r].mwe.mean())
