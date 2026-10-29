"""Independent comparison: hybrid ('combined') datasets, which are NOT used in the consensus,
are compared with the reconciled regional series (hydrological years, m w.e.)."""
import sys, warnings
sys.path.insert(0, 'code'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import recon
from recon import REGIONS, LABELS

rows, series = [], []
for rid, name in REGIONS.items():
    anom, clim = recon.seasonal_cycle(rid)
    cons = pd.read_csv(f'outputs/hydrological_years/{rid}_{name}.csv', index_col=0)
    for ds in recon.list_datasets(rid):
        if ds['source'] != 'combined':
            continue
        p = recon.process_dataset(ds, rid, recon.DEFAULT_CFG, anom, clim)
        author = pd.read_csv(ds['file'], nrows=1).author.iloc[0]
        if p['annual'] is not None:
            a = p['annual']
            k = [x for x in a.index if x in cons.index and not np.isnan(cons.loc[x, 'mwe'])]
            if len(k) < 3:
                continue
            x, y = a.loc[k, 'v'], cons.loc[k, 'mwe']
            rows.append(dict(region_id=rid, region=LABELS[rid], dataset=ds['dataset'], author=author, type='annual', n=len(k),
                             hybrid_mean=x.mean(), consensus_mean=y.mean(), diff=x.mean() - y.mean(),
                             r=np.corrcoef(x, y)[0, 1] if len(k) > 2 else np.nan, rmsd=np.sqrt(np.mean((x - y) ** 2))))
            for kk in k:
                series.append(dict(region_id=rid, dataset=ds['dataset'], k=kk, hybrid=a.loc[kk, 'v'], consensus=cons.loc[kk, 'mwe']))
        for t in p['trend']:
            w = recon.hy_weights(rid, t['m0'], t['m1'])
            c = np.nansum(w * cons.reindex(recon.K_RANGE)['mwe'].values) / w.sum()
            rows.append(dict(region_id=rid, region=LABELS[rid], dataset=ds['dataset'], author=author, type='trend',
                             n=t['L'], hybrid_mean=t['mwe'] / t['L'], consensus_mean=c, diff=t['mwe'] / t['L'] - c, r=np.nan, rmsd=np.nan))
H = pd.DataFrame(rows); H.to_csv('outputs/hybrid_comparison.csv', index=False)
pd.DataFrame(series).to_csv('outputs/hybrid_comparison_series.csv', index=False)
print(H.round(3).to_string())
print(H.groupby('author')[['diff', 'r', 'rmsd']].agg(['mean', 'count']).round(3))

# global hybrid estimate from Dussaillant et al. (covers all 19 regions): calendar-year Gt sum
tot = pd.Series(0.0, index=range(2000, 2024)); ok = True
for rid, name in REGIONS.items():
    anom, clim = recon.seasonal_cycle(rid)
    ds = [d for d in recon.list_datasets(rid) if d['dataset'].startswith('DUS-combined')]
    if not ds:
        ok = False; break
    p = recon.process_dataset(ds[0], rid, recon.DEFAULT_CFG, anom, clim)
    a = p['annual'].reindex(recon.K_RANGE)
    h = pd.DataFrame(dict(mwe=a.v.values, mwe_err=a.e.values, err_rand=a.e.values, err_sys=0 * a.e.values), index=recon.K_RANGE)
    c = recon.to_calendar(rid, h, anom, clim)
    tot += c['gt']
pd.DataFrame(dict(dus_global_gt=tot)).to_csv('outputs/hybrid_dussaillant_global.csv')
print('Dussaillant global', tot.round(1).to_dict(), 'mean', tot.mean())
