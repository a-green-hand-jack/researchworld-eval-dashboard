import sys, pickle; sys.path.insert(0, '/work/code')
from combine import *
OUT = '/work/outputs'
def cal_area(rid):
    return pd.read_csv(f"{D}/results/calendar_years/{rid}_{REGIONS[rid]}.csv").glacier_area.values

def run(kind='calendar', allow_fn=allowed_groups, **kw):
    rows, store = [], {}
    for rid in REGIONS:
        if kind == 'calendar': y0, T = 2000.0, 24
        else:
            o = official(rid); y0, T = o.start_dates.iloc[0], len(o)
        r = run_region(rid, y0, T, allow_fn(rid), **kw)
        store[rid] = r
        area = cal_area(rid) if kind == 'calendar' else official(rid).glacier_area.values
        for t in range(T):
            rows.append(dict(region_id=rid, region=REGIONS[rid], start=y0+t, end=y0+t+1, area_km2=area[t],
                             mwe=r['mu'][t], mwe_err=r['err'][t], mwe_err_trend=r['diag']['err_tr'][t],
                             gt=r['mu'][t]*area[t]/1000, gt_err=r['err'][t]*area[t]/1000, gt_err_trend=r['diag']['err_tr'][t]*area[t]/1000,
                             n_groups=int(r['diag']['n'][t])))
    return pd.DataFrame(rows), store

def global_series(df):
    g = df.groupby('start').apply(lambda d: pd.Series(dict(
        end=d.end.iloc[0], area_km2=d.area_km2.sum(), gt=d['gt'].sum(), gt_err=np.sqrt((d.gt_err**2).sum()),
        gt_err_trend=np.sqrt((d.gt_err_trend**2).sum()))), include_groups=False).reset_index()
    g['mwe'] = g['gt']*1000/g.area_km2; g['mwe_err'] = g.gt_err*1000/g.area_km2
    return g

if __name__ == '__main__':
    df, store = run('calendar')
    df.to_csv(f'{OUT}/regional_calendar_years.csv', index=False)
    g = global_series(df); g.to_csv(f'{OUT}/global_calendar_years.csv', index=False)
    dh, storeh = run('hydrological'); dh.to_csv(f'{OUT}/regional_hydrological_years.csv', index=False)
    # group-level series (calendar)
    rows = []
    for rid, r in store.items():
        for gname, gg in r['groups'].items():
            for t in range(24):
                rows.append(dict(region_id=rid, group=gname, start=2000+t, mwe=gg['y'][t], mwe_err=gg['sig'][t], n_annual=int(gg['na'][t])))
    pd.DataFrame(rows).to_csv(f'{OUT}/group_series_calendar_years.csv', index=False)
    pickle.dump({k: {kk: vv for kk, vv in v.items()} for k, v in store.items()}, open(f'{OUT}/store_calendar.pkl', 'wb'))
    print(g.round(2).to_string())
    off = pd.read_csv(D+'/results/calendar_years/0_global.csv')
    print('mine mean Gt/yr', g['gt'].mean(), 'official', off.combined_gt.mean(), 'rmsd', np.sqrt(np.mean((g['gt'].values-off.combined_gt.values)**2)))
