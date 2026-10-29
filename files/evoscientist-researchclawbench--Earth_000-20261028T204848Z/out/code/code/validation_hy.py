"""Hydrological-year validation against official GlaMBIE regional and data-group series."""
import sys; sys.path.insert(0, 'code')
import numpy as np, pandas as pd, recon
rows, allx, ally = [], [], []
for rid, name in recon.REGIONS.items():
    h = pd.read_csv(f'outputs/hydrological_years/{rid}_{name}.csv', index_col=0)
    o = pd.read_csv(f'{recon.RES}/hydrological_years/{rid}_{name}.csv'); o.index = np.floor(o.start_dates + 1e-6).astype(int)
    k = o.index.intersection(h.index)
    allx += list(o.loc[k, 'combined_mwe']); ally += list(h.loc[k, 'mwe'])
    for g in ['combined', 'altimetry', 'gravimetry', 'demdiff_and_glaciological']:
        oc = o[g + '_mwe'] if g != 'combined' else o['combined_mwe']
        mc = h.get(g + '_mwe' if g != 'combined' else 'mwe')
        if mc is None or oc.isna().all():
            continue
        kk = [x for x in k if not np.isnan(oc[x]) and not np.isnan(mc[x]) and (g == 'combined' or h.loc[x, g + '_covered'])]
        if len(kk) < 3:
            continue
        rows.append(dict(region_id=rid, series=g, n=len(kk), r=np.corrcoef(oc[kk], mc[kk])[0, 1],
                         mean_diff=(mc[kk] - oc[kk]).mean(), rmsd=np.sqrt(((mc[kk] - oc[kk]) ** 2).mean())))
V = pd.DataFrame(rows); V.to_csv('outputs/validation_hydrological_years.csv', index=False)
allx, ally = np.array(allx), np.array(ally)
print('HY all regions: n', len(allx), 'r %.3f rmsd %.3f bias %.3f' % (np.corrcoef(allx, ally)[0, 1], np.sqrt(np.mean((allx - ally) ** 2)), np.mean(ally - allx)))
print(V.groupby('series')[['r', 'mean_diff', 'rmsd']].median().round(3))
print(V.round(3).to_string())
