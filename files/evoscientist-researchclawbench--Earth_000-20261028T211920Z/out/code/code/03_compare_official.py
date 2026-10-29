"""Compare the reconciled estimates with the published GlaMBIE (2024) consensus (benchmark)."""
import sys, os, pickle, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import glambie_lib as L

OUT = os.path.join(L.ROOT, 'outputs')
M = pickle.load(open(os.path.join(OUT, 'main_results.pkl'), 'rb'))
res, cal, glob_ = M['res'], M['cal'], M['glob']
dirs = L.region_dirs()


def official(rid, kind='calendar_years'):
    return pd.read_csv(os.path.join(L.RES, kind, os.path.basename(dirs[rid]) + '.csv'))


rows, grows, ann = [], [], []
for rid in range(1, 20):
    o = official(rid); c = cal[rid]
    m = c.merge(o, on='start_dates')
    m = m[(m.start_dates >= 2000) & (m.start_dates <= 2023)]
    for _, r in m.iterrows():
        ann.append(dict(region_id=rid, year=r.start_dates, ours_mwe=r.mwe, ours_err=r.mwe_err, off_mwe=r.combined_mwe,
                        off_err=r.combined_mwe_errors, ours_gt=r['gt'], off_gt=r.combined_gt))
    d = m.mwe - m.combined_mwe
    rows.append(dict(region_id=rid, region=L.REGION_NAMES[rid], ours_mean_mwe=m.mwe.mean(), off_mean_mwe=m.combined_mwe.mean(),
                     ours_mean_gt=m['gt'].mean(), off_mean_gt=m.combined_gt.mean(),
                     bias_mwe=d.mean(), rmse_mwe=np.sqrt((d ** 2).mean()), r=np.corrcoef(m.mwe, m.combined_mwe)[0, 1],
                     ours_err_mean=m.mwe_err.mean(), off_err_mean=m.combined_mwe_errors.mean()))
    # per-group comparison on hydrological years
    oh = official(rid, 'hydrological_years')
    rr = res[rid]
    for g_ours, g_off in [('altimetry', 'altimetry'), ('gravimetry', 'gravimetry'), ('demdiff_glac', 'demdiff_and_glaciological')]:
        if g_ours not in rr['groups'] or oh[g_off + '_mwe'].isna().all():
            grows.append(dict(region_id=rid, group=g_ours, ours=g_ours in rr['groups'], official=not oh[g_off + '_mwe'].isna().all()))
            continue
        gs = pd.DataFrame(dict(start_dates=np.round(rr['starts'], 3), v=rr['groups'][g_ours]['mwe'], e=rr['groups'][g_ours]['err']))
        oh2 = oh.assign(start_dates=oh.start_dates.round(3))
        mm = gs.merge(oh2[['start_dates', g_off + '_mwe', g_off + '_mwe_errors']], on='start_dates').dropna()
        dd = mm.v - mm[g_off + '_mwe']
        grows.append(dict(region_id=rid, group=g_ours, ours=True, official=True, n=len(mm), ours_mean=mm.v.mean(),
                          off_mean=mm[g_off + '_mwe'].mean(), bias=dd.mean(), rmse=np.sqrt((dd ** 2).mean()),
                          r=np.corrcoef(mm.v, mm[g_off + '_mwe'])[0, 1] if len(mm) > 2 else np.nan,
                          ours_err=mm.e.mean(), off_err=mm[g_off + '_mwe_errors'].mean()))
reg = pd.DataFrame(rows); grp = pd.DataFrame(grows); ann = pd.DataFrame(ann)
og = official(1).iloc[:0]
og = pd.read_csv(os.path.join(L.RES, 'calendar_years', '0_global.csv'))
gm = glob_.merge(og, on='start_dates', suffixes=('', '_off'))
gm = gm[(gm.start_dates >= 2000) & (gm.start_dates <= 2023)]
d = gm['gt'] - gm.combined_gt
glob_cmp = dict(ours_total_gt=gm['gt'].sum(), ours_total_err=np.sqrt((gm.gt_err ** 2).sum()),
                off_total_gt=gm.combined_gt.sum(), off_total_err_quad=np.sqrt((gm.combined_gt_errors ** 2).sum()),
                ours_mean_gt=gm['gt'].mean(), off_mean_gt=gm.combined_gt.mean(), bias_gt=d.mean(),
                rmse_gt=np.sqrt((d ** 2).mean()), r=np.corrcoef(gm['gt'], gm.combined_gt)[0, 1],
                ours_err_mean=gm.gt_err.mean(), off_err_mean=gm.combined_gt_errors.mean())
reg.to_csv(os.path.join(OUT, 'compare_official_regional.csv'), index=False)
grp.to_csv(os.path.join(OUT, 'compare_official_groups.csv'), index=False)
ann.to_csv(os.path.join(OUT, 'compare_official_annual.csv'), index=False)
gm.to_csv(os.path.join(OUT, 'compare_official_global_annual.csv'), index=False)
pd.Series(glob_cmp).to_csv(os.path.join(OUT, 'compare_official_global.csv'))
pd.set_option('display.width', 250)
print(reg.round(3).to_string()); print(grp.round(3).to_string()); print(pd.Series(glob_cmp).round(3))
